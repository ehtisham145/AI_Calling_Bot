# Current Status

Migrated to a **Pipecat + fully self-hosted STT/TTS + OpenAI LLM** stack. The previous VideoSDK-based build (Deepgram, then Gemini, then Deepgram Aura TTS) is retired - see `03_DECISIONS_LOG.md` for the full history of why each earlier provider got dropped.

**The full pipeline is confirmed working** (English, local machine - see below). Not yet confirmed on the VPS itself, since Hostinger firewall access is still pending (local testing was adopted as a workaround for that - see `03_DECISIONS_LOG.md`).

## What's Validated
- [x] **Full pipeline runs end-to-end with real speech and audible output**: tested locally (`LANGUAGES=en`) via phone browser on the same LAN, over `python app/main.py --host 0.0.0.0`. Bot greets first (see the `on_client_connected` fix below), STT/LLM/TTS all confirmed working together for the first time. Arabic and the 4 menu branches still need their own pass - see `05_NEXT_STEPS.md`.
- [x] **STT/TTS model choice for this VPS's 2-core CPU**, via round-trip benchmarking (Piper -> Whisper): English uses Whisper `base`; Arabic uses the community fine-tune `Omar10lfc/whisper-small-arabic-ct2-int8`, which clearly outperformed generic Whisper on Arabic accuracy. Both comfortably real-time (RTF well under 1.0). Full results in `03_DECISIONS_LOG.md`.
- [x] Every Pipecat API used in `app/main.py` (`Pipeline`, `PipelineTask`, `PipelineRunner`, `WhisperSTTService`, `OpenAILLMService`, `PiperTTSService`, `LLMContext`/`LLMContextAggregatorPair`, the `bot()`/`run_bot()` dev-runner pattern, `SmallWebRTCTransport`, `transport.event_handler("on_client_connected")` + `LLMRunFrame`) was checked against official Pipecat docs before writing the code - not guessed.
- [x] `app/prompts.py` generates valid instructions for both `en` and `ar`.
- [x] **Bot greets first.** Originally the bot silently waited for the caller to speak first (wrong for a receptionist) - fixed via an `on_client_connected` handler that queues an `LLMRunFrame()` to trigger the opening turn from the system prompt alone.
- [x] **Dynamic English/Arabic language switching, confirmed working on a live call on the actual VPS.** `LANGUAGES=en,ar` (replaces the old single-value `LANGUAGE`) pre-loads both languages' STT/TTS and lets the caller pick one at the start of the call via a `set_language` function call - selecting Arabic live switched the conversation into Arabic correctly. See `03_DECISIONS_LOG.md` for the `ServiceSwitcher` design and the frame-ordering race condition it had to avoid (verified against the actual installed `pipecat-ai` source, not just docs).
- [x] **Arabic's live-call response time investigated and explained - not a model problem.** Felt slow/"stuck" on live calls; re-benchmarking on the VPS showed this was the VPS being under load from something else at the time (every model, English included, measured slower than its documented baseline until `ai-calling-bot` was stopped for a clean run) - the Arabic model itself measured RTF 0.52 in isolation, same as originally benchmarked. Two candidate replacement models were tried and both were worse (one failed to load, one was far slower) - see `03_DECISIONS_LOG.md`. No model change made.

## Not Yet Validated / Known Gaps

### 1. Not yet run on the VPS itself
Confirmed working on the developer's local Windows machine (as a workaround for pending Hostinger firewall access - see `03_DECISIONS_LOG.md`). Still needs a real run on the VPS once that access comes through, to confirm the 2-core CPU holds up with real (not synthetic) speech end-to-end.

### 2. Only English confirmed live - Arabic and the 4 menu branches still need testing
The milestone above was English, open-ended conversation only. Still need to: switch to `LANGUAGES=ar` and confirm Arabic end-to-end, and walk through all 4 menu branches (Book Appointment, Insurance Information, Doctor Availability, Find a Doctor) to confirm responses match `app/data/hospital_data.py`.

### 3. Only English and Arabic - no Urdu
Urdu was tested with generic Whisper (`tiny`/`base`) in `scripts/benchmark_voice_stack.py` and the accuracy was poor even after trying a larger model - no community Arabic-style fine-tune was found for Urdu, and no Piper Urdu voice was adopted for production (the one tested, `ur_PK-fasih-medium`, is personal/non-commercial licensed - not usable for a paid client product anyway). Urdu is deferred, not abandoned - see `05_NEXT_STEPS.md`.

### 4. Language switching confirmed working, but the full menu flow in Arabic post-switch isn't walked through yet
The switch itself (STT/TTS/persona all flipping to Arabic on request) is confirmed live - see above. Still need the same full 4-menu-branch walkthrough in Arabic (post-switch) as item 2 above calls for.

### 5. No phone number / telephony yet
Testing is via Pipecat's local WebRTC dev client (`http://<vps-ip>:7860/client`) only. No Twilio number wired up. See `05_NEXT_STEPS.md`.

### 6. Dummy data only
`app/data/hospital_data.py` has 5 fictional doctors, 4 fictional insurance providers, made-up hours - not connected to any real hospital system.

## Credentials Status (do not store actual key values here - see `.env.example`)
- **OpenAI** - works (paid account; `gpt-4o-mini`). The only API key this project needs now.
- VideoSDK, Deepgram, Google Gemini, ElevenLabs - all retired, no longer used or required. Their keys (if still in an old `.env`) can be deleted.
