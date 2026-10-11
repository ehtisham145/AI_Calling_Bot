# Decisions Log

Why things are the way they are - so nobody re-litigates a settled decision without knowing the reason, and so it's easy to tell which decisions were *forced* (temporary, revert when possible) vs. *deliberate* (should stay).

**Note:** entries below from "VideoSDK over Vapi.ai..." through "Preflight key-checker script..." describe the VideoSDK-era stack, which has since been fully replaced (see "Pipecat + self-hosted Whisper/Piper over VideoSDK" below). Kept for historical context - the mistakes made there (guessed model names, wrong API scopes) are exactly why the current stack was built by verifying every API against official docs first. Current architecture is `01_ARCHITECTURE.md`.

## Pipecat + self-hosted Whisper/Piper over VideoSDK + cloud STT/TTS
**Deliberate**, the biggest single change in the project. Two things converged: (1) the VideoSDK stack kept hitting free-tier walls across four different providers (Deepgram balance, Gemini model retirement, ElevenLabs voice-library restriction - see entries below), and (2) once self-hosting was considered for cost/reliability reasons, VPS benchmarking (`vps_benchmark/`) proved a 2-core VPS could run Whisper + Piper comfortably in real-time for English and Arabic. The remaining blocker was that VideoSDK has no built-in support for self-hosted STT/TTS - using it would've meant writing a custom plugin from scratch. Pipecat does: `WhisperSTTService` and `PiperTTSService` are official, built-in services, confirmed via their docs before committing to the switch.
**Net result**: the stack went from 4 external services (VideoSDK, Deepgram, an LLM provider, ElevenLabs) down to 1 (OpenAI, for the LLM only) - STT and TTS now run locally with no per-minute cost and no free-tier policy risk.
**Trade-off accepted**: had to drop VideoSDK's built-in playground (replaced by Pipecat's local WebRTC dev client) and re-verify the entire API surface from scratch (Pipeline/PipelineTask/PipelineRunner, service classes, the `bot()`/`run_bot()` dev-runner pattern) since none of it carries over from VideoSDK.
**Scope cut alongside this migration**: mid-call language switching (caller picks language, agent switches live) was dropped for this pass in favor of a fixed-per-run `LANGUAGE` env var. Pipecat has the right tool for real switching (`ServiceSwitcher`, `STTUpdateSettingsFrame`/`TTSUpdateSettingsFrame`) but its exact usage wasn't verified deeply enough to build against with confidence in this pass - see `05_NEXT_STEPS.md`. Urdu was also dropped from this pass (see the VPS benchmark results below) - only English and Arabic are wired up.

### VPS benchmark results (2-core CPU, `scripts/benchmark_voice_stack.py`)
Round-trip test (Piper synthesizes text -> Whisper transcribes it back), RTF = time_taken / audio_duration, RTF < 1.0 = faster than real-time:

| Language | Model | STT RTF | Transcription accuracy |
|---|---|---|---|
| English | Whisper `tiny` | 0.15-0.30 | Perfect |
| English | Whisper `base` | 0.28-0.44 | Perfect (near-identical to `tiny`) |
| English | `distil-small.en` | 0.81 | Perfect, but **slowest of the three on this specific 2-core CPU** despite being marketed as 6x faster than large - don't trust marketing RTF claims over actual hardware testing |
| Arabic | Whisper `tiny`/`base` (generic multilingual) | 0.13-0.22 | Noticeable errors (e.g. "مساعدتك اليوم" became "مساعدة كليوم") |
| Arabic | `Omar10lfc/whisper-small-arabic-ct2-int8` (Arabic-specialized fine-tune) | 0.62 | **Near-perfect** - clear win over generic models |
| Urdu | Whisper `tiny`/`base` (generic multilingual) | 0.17-0.44 | **Poor even on `base`** - core words like "ہسپتال" (hospital) consistently garbled. No Urdu-specialized fine-tune found. Dropped from this pass. |

**Chosen for `app/main.py`**: English -> Whisper `base` (not `distil-small.en` - slower in practice here), Arabic -> `Omar10lfc/whisper-small-arabic-ct2-int8`. TTS: Piper `en_US-amy-medium` / `ar_JO-kareem-medium` (both TTS RTF 0.05-0.09, never the bottleneck).
**Licensing note**: a Piper Urdu voice (`ur_PK-fasih-medium`) was tested and found personal/non-commercial licensed - not usable in a paid client product regardless of accuracy. Any future Urdu voice needs its license checked, not just its quality.

## VideoSDK over Vapi.ai or a fully custom Twilio+raw-APIs build
**Deliberate.** Compared three approaches for the voice pipeline:
- Fully custom (Twilio + Deepgram + Claude + ElevenLabs wired by hand): full control, cheapest at scale, but much more dev time (manual websocket streaming, interruption handling, turn-taking).
- Vapi.ai: fastest no-code setup, but ~$0.05/min+ platform fee and less control.
- **VideoSDK (chosen)**: open-source, code-first (fits a developer), cheaper than Vapi (~$0.01-0.02/min), has a playground for testing without telephony set up yet.

## Google Gemini over Anthropic Claude for the LLM (SUPERSEDED - see "OpenAI over Gemini" below)
**Forced by budget, but worked fine.** Claude was the original plan. The developer didn't have payment credits available for the Anthropic Console (no free ongoing API tier - only a one-time $5 trial that wasn't available on this account). Google's Gemini API has a genuine permanent free tier (no card, rate-limited not credit-metered: ~1,500 requests/day on Flash). VideoSDK's plugin system supports both, so the swap was a 2-line change (`AnthropicLLM` -> `GoogleLLM`). This was later itself replaced by OpenAI - see below.

## OpenAI over Gemini for the LLM
**Deliberate**, once a paid OpenAI account became available. Gemini had caused two separate breakages in quick succession: `gemini-2.5-flash` got retired for new accounts mid-testing (live 404), and the attempted `gemini-flash-lite-latest` latency fix 400'd inside VideoSDK's actual pipeline despite working standalone (see the latency-tuning entry below for the full story). Rather than keep fighting Gemini's free-tier model-lifecycle churn, switched to OpenAI since: (a) budget was no longer the constraint, and (b) OpenAI was VideoSDK's own first-class/reference LLM integration in their quickstart docs, implying it's the most battle-tested plugin. **Model**: `gpt-4o-mini` - fast and cheap, appropriate for a menu-driven voice conversation (not deep reasoning). **Env var**: `OPENAI_API_KEY`. **Parameter note**: `OpenAILLM` takes `max_completion_tokens`, not `max_tokens` or `max_output_tokens` (each LLM plugin has used a different parameter name so far - always verify against the specific plugin's docs before assuming).
**Revisit if**: OpenAI costs become a concern at scale, or Claude credits become available later (Claude was never actually tested in this project, only planned).

## Deepgram Aura TTS over ElevenLabs
**Forced, temporary.** ElevenLabs was the original TTS plan (best multilingual voice quality). Hit a wall: free-tier ElevenLabs accounts created after March 2026 get HTTP 402 `paid_plan_required` when calling the TTS API with voices they don't own, regardless of remaining character quota - this is a voice-library access restriction, not a credits-exhausted problem (was misdiagnosed as "out of credits" initially; the actual API error message made the real cause clear).
Switched to Deepgram's own TTS (Aura) since Deepgram credits were already available and valid. **Trade-off accepted**: Aura has no Arabic or Hindi voice, so the demo is English-only until this is reverted.
**Revert condition**: pay for ElevenLabs Starter (~$5/month) - unlocks full voice library via API, restores Arabic/Hindi. The revert is a single line in `main.py` (old line kept as a comment).

## gemini-2.5-flash -> gemini-3.8-flash
**Forced.** `gemini-2.5-flash` returned a live 404 the first time the agent actually ran a conversation turn: "This model ... is no longer available to new users." Google's own error message named `gemini-3.8-flash` as the replacement, so that's what's in `main.py` now. Not a judgment call - just keeping up with Google's model lifecycle.

## Latency tuning: shorter replies, lower turn-detector threshold (+ a dead end worth remembering)
**Deliberate**, came from an explicit ask: noticeable delay before the agent responds, and the developer can't afford infra-level fixes (e.g. hosting closer to where callers will be) right now. Free, code-only changes in `main.py`:
- `max_output_tokens`/`max_completion_tokens` 300 -> 150 (shorter replies generate and speak faster; fits the existing "1-2 sentences, this is voice" rule in `prompts.py` anyway). Survived the later OpenAI switch.
- `TurnDetector` threshold 0.8 -> 0.55 (default is 0.7; agent decides the caller finished talking sooner). **Trade-off**: may occasionally start responding before the caller is fully done - raise back toward 0.7-0.8 if that happens.
- **Dead end** (while still on Gemini): tried a faster "lite" model. `gemini-3.8-flash-lite` doesn't exist (confirmed via the API's own `ListModels` - 404). `gemini-flash-lite-latest` (Google's rolling lite alias) does exist and returned 200 on a standalone test call, but threw `400 INVALID_ARGUMENT` when called through VideoSDK's actual pipeline (likely incompatible with some parameter the plugin sends - not root-caused further). This dead end directly contributed to the decision to drop Gemini for OpenAI entirely (see above) rather than keep debugging it.
Remaining latency sources not addressed yet (need infra, not just config): network distance from Pakistan to Deepgram/OpenAI/VideoSDK's servers, and whether the pipeline streams LLM output into TTS incrementally vs. waiting for the full response (VideoSDK's docs weren't conclusive on this for Cascade mode).

## No custom state machine for conversation flow
**Deliberate.** Language selection and menu-branch tracking could have been built as explicit code (a state machine), but instead it's handled entirely by the LLM through the system prompt (`prompts.py`) and conversation history. Faster to build, good enough for a demo. **Revisit if**: the conversation starts losing track of state in longer/more complex calls, or when real appointment booking (not just dummy-data lookups) needs reliable transactional state.

## Preflight key-checker script instead of relying on runtime errors only
**Deliberate**, came from an explicit ask: the developer wanted to know immediately which API's credits/auth had a problem, rather than discovering it mid-call via a buried stack trace. Led to `check_api_keys.py` (hits each provider's real endpoint before running) plus `error_helpers.py` (best-effort classification of errors that still happen mid-call). Note: the ElevenLabs check in that script originally called the wrong endpoint (`/v1/user/subscription`, which needs "User" API-key scope) against a key deliberately restricted to "Text to Speech" scope only - this produced a false "invalid key" reading before being fixed to do a real (tiny) TTS call instead, which is how the actual 402/library-voice issue was correctly diagnosed.
