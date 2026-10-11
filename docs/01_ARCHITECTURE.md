# Architecture

## Pipeline (How a Call Is Processed)

```
Caller (browser WebRTC client today; a real phone number later)
     |  speaks
     v
Pipecat             -- orchestrates the whole pipeline: the SmallWebRTCTransport
(orchestration)        carries audio in/out, the Pipeline wires STT -> LLM -> TTS
                        in order with VAD-based turn-taking, and the dev runner
                        serves a connectable browser client at :7860/client.
     v
Whisper STT         -- self-hosted, converts caller's speech to text
                        (model picked per LANGUAGE - see 03_DECISIONS_LOG.md)
     v
OpenAI LLM          -- reads the text, decides what to say (model: gpt-4o-mini)
     v
Piper TTS           -- self-hosted, converts the reply text back to speech
                        (voice picked per LANGUAGE)
     v
Caller hears the reply
```

Only **one remote paid service** is in this pipeline now: OpenAI, for the LLM. STT and TTS run as local models on the same machine - no Deepgram, ElevenLabs, Google, or VideoSDK anymore. See `03_DECISIONS_LOG.md` for the full history of why (this replaced an earlier VideoSDK + Deepgram + Gemini/OpenAI + Deepgram-Aura/ElevenLabs stack that kept hitting free-tier walls).

## Why Pipecat (vs. the earlier VideoSDK approach)
- Has **official, built-in** local Whisper (`WhisperSTTService`) and Piper (`PiperTTSService`) support - no custom plugin needed to self-host, which VideoSDK would have required building from scratch.
- Telephony (Twilio) is a first-class transport, not bolted on.
- Large, actively-maintained provider ecosystem (150+ services) if requirements change again.
- Open source, free - the framework itself has no per-minute platform fee (unlike VideoSDK/Vapi).

## Why language is fixed per run (not yet mid-call)
Pipecat has a `ServiceSwitcher` utility and `STTUpdateSettingsFrame`/`TTSUpdateSettingsFrame` for runtime reconfiguration, which is the right tool for letting a caller pick their language mid-call. This wasn't implemented yet because the exact API wasn't verified in enough depth to ship with confidence (the project's rule: verify an API before building against it, don't guess - see the repeated model-name/parameter mistakes earlier in `03_DECISIONS_LOG.md`). Instead, `LANGUAGE` is set once via env var at startup. See `05_NEXT_STEPS.md` for the plan to close this gap properly.

## Project Files

```
app/                        -- the running application
  main.py                   -- entry point: run_bot() + bot()
  prompts.py                -- build_system_instructions(language)
  error_helpers.py          -- classify_error()
  check_api_keys.py         -- preflight OPENAI_API_KEY check
  data/hospital_data.py     -- dummy hospital data
scripts/
  benchmark_voice_stack.py  -- one-time STT/TTS hardware benchmark (not part of the running app)
docs/                       -- project context (this folder)
ecosystem.config.js         -- PM2 process config
deploy.sh                   -- one-command VPS update script
.env / .env.example         -- OPENAI_API_KEY and LANGUAGE
README.md                   -- setup, run, deployment instructions
```

| File | Purpose |
|---|---|
| `app/main.py` | Entry point. Defines `run_bot()` (builds the STT/LLM/TTS `Pipeline`, runs it via `PipelineTask`/`PipelineRunner`) and `bot()` (the Pipecat dev-runner entry point that wires up the `SmallWebRTCTransport`). |
| `app/prompts.py` | `build_system_instructions(language)` - builds the system prompt for a single fixed language, embedding the hospital data. |
| `app/data/hospital_data.py` | Dummy data: doctors, specialties, available days/times, accepted insurance providers, hospital hours/location. Plain Python constants, no database. |
| `app/check_api_keys.py` | Preflight script - validates `OPENAI_API_KEY` before running `app/main.py`. |
| `app/error_helpers.py` | `classify_error()` - best-effort diagnosis of runtime errors: OpenAI auth/quota vs. a local Whisper/Piper model problem. |
| `scripts/benchmark_voice_stack.py` | The benchmark script (and its results, captured in `03_DECISIONS_LOG.md`) used to pick the exact STT/TTS models in `app/main.py` for this VPS's 2-core CPU. Not part of the running app - a one-time validation tool. |
| `.env` / `.env.example` | `OPENAI_API_KEY` and `LANGUAGE`. Real values are in `.env` (gitignored, never committed). |
| `ecosystem.config.js` | PM2 process config for production - how `app/main.py` is kept running, restarted on crash, and logged. |
| `deploy.sh` | One-command update script for the VPS: `git pull` + reinstall deps + `pm2 restart`. |
| `README.md` | Setup, run, and deployment instructions. |

## State Management
There is **no custom state machine** for the conversation flow (menu navigation, etc.) - it's tracked implicitly by the LLM through `LLMContext`/conversation history, guided entirely by the instructions in `app/prompts.py`. This was a deliberate simplicity choice for the demo stage - see `03_DECISIONS_LOG.md`.
