"""Entry point for the hospital AI calling bot - Pipecat edition.

Stack: self-hosted Whisper (STT, faster-whisper backend) + OpenAI gpt-4o-mini (LLM)
+ self-hosted Piper (TTS). No Deepgram/ElevenLabs/VideoSDK anymore - only
OPENAI_API_KEY is required (see docs/03_DECISIONS_LOG.md for why).

LANGUAGE is fixed at startup via the LANGUAGE env var ("en" or "ar") - NOT yet
switchable mid-call. This is a known, deliberate scope cut for this pass - see
docs/05_NEXT_STEPS.md for the plan to add real-time switching via Pipecat's
ServiceSwitcher once that's been verified properly (not guessed).

Run with: python app/main.py
Opens a local WebRTC dev server at http://localhost:7860/client - open that in
a browser to talk to the agent. Meant to run on the VPS where the STT/TTS
models were benchmarked (2-core CPU, confirmed real-time-capable).
"""

import os

from dotenv import load_dotenv

load_dotenv()

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext, LLMContextAggregatorPair
from pipecat.runner.types import SmallWebRTCRunnerArguments
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from error_helpers import classify_error
from prompts import build_system_instructions

LANGUAGE = os.getenv("LANGUAGE", "en")  # "en" or "ar" for this run - see module docstring

# STT/TTS model picks validated on the actual 2-core VPS target (see
# vps_benchmark/) - specialized per-language models beat generic multilingual
# ones for Arabic, and generic "base" beat distil-small.en for English on this
# specific hardware despite distil's marketing.
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
    stt = WhisperSTTService(settings=WhisperSTTService.Settings(model=STT_MODEL[LANGUAGE]))
    tts = PiperTTSService(settings=PiperTTSService.Settings(voice=PIPER_VOICE[LANGUAGE]))
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAILLMService.Settings(
            model="gpt-4o-mini",
            temperature=0.6,
            system_instruction=build_system_instructions(language=LANGUAGE),
        ),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

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
            vad_analyzer=SileroVADAnalyzer(),
        ),
        webrtc_connection=runner_args.webrtc_connection,
    )
    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
