# Current Status

Migrated to a **Pipecat + fully self-hosted STT/TTS + OpenAI LLM** stack. The previous VideoSDK-based build (Deepgram, then Gemini, then Deepgram Aura TTS) is retired - see `03_DECISIONS_LOG.md` for the full history of why each earlier provider got dropped.

`main.py` has not yet been run end-to-end on the VPS with real human speech (as of this status update) - the STT/TTS *models* were validated for speed and accuracy via `vps_benchmark/` using synthetic (Piper-generated) audio, and the Pipecat API surface was verified against official docs for every piece used, but the full assembled pipeline itself is new and untested live.

## What's Validated
- [x] **STT/TTS model choice for this VPS's 2-core CPU**, via round-trip benchmarking (Piper -> Whisper): English uses Whisper `base`; Arabic uses the community fine-tune `Omar10lfc/whisper-small-arabic-ct2-int8`, which clearly outperformed generic Whisper on Arabic accuracy. Both comfortably real-time (RTF well under 1.0). Full results in `03_DECISIONS_LOG.md`.
- [x] Every Pipecat API used in `main.py` (`Pipeline`, `PipelineTask`, `PipelineRunner`, `WhisperSTTService`, `OpenAILLMService`, `PiperTTSService`, `LLMContext`/`LLMContextAggregatorPair`, the `bot()`/`run_bot()` dev-runner pattern, `SmallWebRTCTransport`) was checked against official Pipecat docs before writing the code - not guessed.
- [x] `prompts.py` generates valid instructions for both `en` and `ar`.

## Not Yet Validated / Known Gaps

### 1. Full pipeline not yet run live
`main.py` needs an actual run on the VPS (`python main.py`, connect via the WebRTC browser client) to confirm everything wires together correctly. This is the next immediate step.

### 2. Only English and Arabic - no Urdu
Urdu was tested with generic Whisper (`tiny`/`base`) in `vps_benchmark/` and the accuracy was poor even after trying a larger model - no community Arabic-style fine-tune was found for Urdu, and no Piper Urdu voice was adopted for production (the one tested, `ur_PK-fasih-medium`, is personal/non-commercial licensed - not usable for a paid client product anyway). Urdu is deferred, not abandoned - see `05_NEXT_STEPS.md`.

### 3. One language per run, not per call
Caller can't pick their language mid-call - it's fixed via the `LANGUAGE` env var at startup. Switching this to real-time mid-call selection needs Pipecat's `ServiceSwitcher`, intentionally not implemented yet until its API is verified with the same rigor as everything else here. See `01_ARCHITECTURE.md` and `05_NEXT_STEPS.md`.

### 4. No phone number / telephony yet
Testing is via Pipecat's local WebRTC dev client (`http://<vps-ip>:7860/client`) only. No Twilio number wired up. See `05_NEXT_STEPS.md`.

### 5. Dummy data only
`data/hospital_data.py` has 5 fictional doctors, 4 fictional insurance providers, made-up hours - not connected to any real hospital system.

## Credentials Status (do not store actual key values here - see `.env.example`)
- **OpenAI** - works (paid account; `gpt-4o-mini`). The only API key this project needs now.
- VideoSDK, Deepgram, Google Gemini, ElevenLabs - all retired, no longer used or required. Their keys (if still in an old `.env`) can be deleted.
