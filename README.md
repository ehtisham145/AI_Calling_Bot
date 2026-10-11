# Hospital AI Calling Bot — Demo

Voice AI agent for a hospital front desk: handles Book Appointment, Insurance Information, Doctor Availability, and Find a Doctor — all against dummy data in [data/hospital_data.py](data/hospital_data.py).

> **New to this project?** Read [`docs/`](docs/README.md) first — full business context, architecture, current status, and why things are built the way they are. This file only covers setup/run steps.

**Stack:** [Pipecat](https://pipecat.ai) (orchestration) + self-hosted **Whisper** (STT) + **OpenAI gpt-4o-mini** (LLM) + self-hosted **Piper** (TTS). Only one paid API (`OPENAI_API_KEY`) is needed — STT and TTS run locally, no VideoSDK/Deepgram/ElevenLabs anymore (see [`docs/03_DECISIONS_LOG.md`](docs/03_DECISIONS_LOG.md) for why).

> **Language is fixed per run** via the `LANGUAGE` env var (`en` or `ar`) — not yet switchable mid-call. Urdu isn't wired up yet. See [`docs/02_CURRENT_STATUS.md`](docs/02_CURRENT_STATUS.md).

> **Run this on the VPS**, not a local dev machine — the self-hosted STT/TTS models were benchmarked specifically on that 2-core CPU (see `vps_benchmark/`) and confirmed real-time-capable there.

## 1. Get the one API key you need

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) (paid account) |

Copy `.env.example` to `.env`, paste your key in, and optionally set `LANGUAGE=en` or `LANGUAGE=ar`:

```bash
cp .env.example .env
```

## 2. Install (on the VPS, inside a virtualenv)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Check your key (do this before running the agent)

```bash
python check_api_keys.py
```

Hits OpenAI directly with a real tiny completion and tells you: valid / missing / invalid / out of credits — so you find out immediately, not mid-call.

## 4. Run

```bash
python main.py
```

This starts a local WebRTC dev server. Open `http://<your-vps-ip>:7860/client` in a browser, allow mic access, and talk to the agent. The first run downloads the Whisper and Piper models for whichever `LANGUAGE` is set — this can take a minute.

If something fails *during* a call, `main.py` catches it and prints a best-effort diagnosis (OpenAI auth/quota vs. a local model problem) instead of a raw traceback. See `error_helpers.py`.

## Known limitations (tracked, not bugs)

- **One language per run.** Set `LANGUAGE=en` or `LANGUAGE=ar` in `.env` and restart to switch — a caller can't pick their language mid-call yet. Real-time switching needs Pipecat's `ServiceSwitcher`, not yet implemented (verify-before-build, not guessed). See `docs/05_NEXT_STEPS.md`.
- **No Urdu yet.** No validated self-hosted Whisper/Piper pair for Urdu. Was tested and dropped for now — see `docs/02_CURRENT_STATUS.md`.
- **No phone number / telephony yet.** Testing is via the browser WebRTC client only. Twilio integration is the next step, see `docs/05_NEXT_STEPS.md`.
- **STT/TTS model picks are hardware-specific.** `STT_MODEL`/`PIPER_VOICE` in `main.py` were chosen based on real benchmarks on *this* VPS's 2-core CPU (see `vps_benchmark/benchmark_voice_stack.py` and its results in `docs/03_DECISIONS_LOG.md`) — re-benchmark before changing VPS specs or hardware.
- Dummy data (doctors, insurance providers, hours) lives in `data/hospital_data.py` — edit freely, no code changes needed elsewhere.
