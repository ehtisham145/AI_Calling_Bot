"""Entry point for the hospital AI calling bot - Pipecat edition.

Stack: self-hosted Whisper (STT, faster-whisper backend) + OpenAI gpt-4o-mini (LLM)
+ self-hosted Piper (TTS). No Deepgram/ElevenLabs/VideoSDK anymore - only
OPENAI_API_KEY is required (see docs/03_DECISIONS_LOG.md for why).

LANGUAGES controls which languages are pre-loaded and offered (comma-separated,
e.g. "en,ar"; default both). With more than one, the caller picks a language at
the start of the call and the bot switches STT/TTS/persona live for the rest of
it - see docs/03_DECISIONS_LOG.md for how the ServiceSwitcher + function-call
handoff is wired (and the race condition it has to avoid). Set it to a single
language (e.g. "en") to skip the chooser and force that language only.

Run with: python app/main.py
Opens a local WebRTC dev server at http://localhost:7860/client - open that in
a browser to talk to the agent. Meant to run on the VPS where the STT/TTS
models were benchmarked (2-core CPU, confirmed real-time-capable).
"""

import os

from dotenv import load_dotenv

load_dotenv()

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame, LLMUpdateSettingsFrame, ManuallySwitchServiceFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.service_switcher import ServiceSwitcher
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.runner.types import SmallWebRTCRunnerArguments
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from error_helpers import classify_error
from prompts import build_language_detection_instructions, build_system_instructions

# Comma-separated list of languages to pre-load and offer - see module docstring.
LANGUAGES = [lang.strip() for lang in os.getenv("LANGUAGES", "en,ar").split(",") if lang.strip()]

# STT/TTS model picks validated on the actual 2-core VPS target (see
# scripts/benchmark_voice_stack.py) - specialized per-language models beat
# generic multilingual ones for Arabic, and generic "base" beat distil-small.en
# for English on this specific hardware despite distil's marketing.
STT_MODEL = {
    "en": "base",
    "ar": "Omar10lfc/whisper-small-arabic-ct2-int8",
}
PIPER_VOICE = {
    "en": "en_US-amy-medium",
    # NOTE: no validated Urdu voice/model pair yet - ar_JO-kareem-medium only
    # covers Arabic. See docs/02_CURRENT_STATUS.md.
    "ar": "ar_JO-kareem-medium",
}


async def run_bot(transport: BaseTransport):
    multi_language = len(LANGUAGES) > 1

    stt_by_lang = {
        lang: WhisperSTTService(settings=WhisperSTTService.Settings(model=STT_MODEL[lang]))
        for lang in LANGUAGES
    }
    tts_by_lang = {
        lang: PiperTTSService(settings=PiperTTSService.Settings(voice=PIPER_VOICE[lang]))
        for lang in LANGUAGES
    }

    # ServiceSwitcher defaults its active service to services[0], so LANGUAGES[0]
    # (English by default) is who answers before any language has been chosen.
    stt_switcher = ServiceSwitcher(services=[stt_by_lang[lang] for lang in LANGUAGES])
    tts_switcher = ServiceSwitcher(services=[tts_by_lang[lang] for lang in LANGUAGES])

    initial_system_instruction = (
        build_language_detection_instructions(LANGUAGES)
        if multi_language
        else build_system_instructions(language=LANGUAGES[0])
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAILLMService.Settings(
            model="gpt-4o-mini",
            temperature=0.6,
            system_instruction=initial_system_instruction,
        ),
    )

    if multi_language:

        async def set_language_handler(params: FunctionCallParams):
            language = params.arguments.get("language")
            if language not in stt_by_lang:
                await params.result_callback(
                    {"status": "error", "reason": f"unsupported language '{language}'"}
                )
                return

            new_instructions = build_system_instructions(language=language)

            # Queued directly onto llm's own input queue, and BEFORE
            # result_callback - NOT via task.queue_frames(). Once
            # result_callback runs, the assistant context aggregator
            # (downstream of llm) pushes a retrigger back UPSTREAM through
            # transport.output() -> tts_switcher -> llm (3 hops) to generate
            # the real reply. A frame sent via task.queue_frames() instead
            # re-enters at transport.input() and has to cross
            # transport.input() -> stt_switcher -> context_aggregator.user()
            # -> llm -> tts_switcher - more, heavier hops, not guaranteed to
            # win that race. Queuing straight onto llm puts both frames ahead
            # of the eventual retrigger in llm's own strict-arrival-order
            # queue, since they're enqueued here, before result_callback even
            # starts the retrigger cascade. Verified against the installed
            # pipecat-ai 1.12.0 source (FrameProcessorQueue/ServiceSwitcher),
            # not guessed - see docs/03_DECISIONS_LOG.md.
            await params.llm.queue_frame(
                ManuallySwitchServiceFrame(service=tts_by_lang[language]),
                FrameDirection.DOWNSTREAM,
            )
            await params.llm.queue_frame(
                LLMUpdateSettingsFrame(
                    delta=OpenAILLMService.Settings(system_instruction=new_instructions)
                ),
                FrameDirection.DOWNSTREAM,
            )

            # STT has no such race - stt_switcher sits upstream of llm, so
            # nothing competes to beat this frame there. task.queue_frames()
            # (plural, list) is the one confirmed-working call on `task` in
            # this codebase (already used below for LLMRunFrame) - using it
            # here too instead of an unverified singular queue_frame().
            await task.queue_frames([ManuallySwitchServiceFrame(service=stt_by_lang[language])])

            # Belt-and-suspenders: correct independent of the queue-ordering
            # argument above, since the model reads its own tool result in the
            # same turn regardless of frame travel time. The router prompt
            # tells it to follow `instructions` verbatim, so correctness for
            # the reply's *content* never depends on winning any race - only
            # the TTS *voice* does, and that's what the queuing above is for.
            await params.result_callback({"status": "ok", "instructions": new_instructions})

        set_language_schema = FunctionSchema(
            name="set_language",
            description=(
                "Set the caller's chosen language. Call this exactly once, as soon as you "
                "know which language the caller wants, and say nothing else until it returns."
            ),
            properties={
                "language": {
                    "type": "string",
                    "enum": LANGUAGES,
                    "description": "The language code the caller chose.",
                }
            },
            required=["language"],
            handler=set_language_handler,
        )
        context = LLMContext(tools=[set_language_schema])
    else:
        context = LLMContext()

    # VAD lives here (on the user aggregator), not on the transport - in Pipecat
    # 1.0+ this is what actually feeds speech start/stop into turn detection and
    # triggers STT. Putting it only on TransportParams (the old pre-1.0 way)
    # loads the VAD model but never wires it into anything - confirmed by hours
    # of silent failure: connection fine, TTS/text fine, but zero STT/VAD events
    # ever fired for real microphone input. See docs/03_DECISIONS_LOG.md.
    context_aggregator = LLMContextAggregatorPair(
        context, user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer())
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt_switcher,
            context_aggregator.user(),
            llm,
            tts_switcher,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    # The LLM only speaks when it has something to respond to - without this,
    # the bot would silently wait for the caller to speak first, which is
    # backwards for a receptionist (it should greet first). Triggering an
    # LLMRunFrame with no new user message makes it generate an opening turn
    # straight from the system prompt's "greet + present the menu" instruction.
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        await task.queue_frames([LLMRunFrame()])

    try:
        await runner.run(task)
    except Exception as e:
        print(classify_error(e))
        raise


async def bot(runner_args: SmallWebRTCRunnerArguments):
    """Entry point the Pipecat dev runner calls per connection."""
    transport = SmallWebRTCTransport(
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
        webrtc_connection=runner_args.webrtc_connection,
    )
    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
