# Hospital AI Calling Bot — Demo

Voice AI agent for a hospital front desk: handles Book Appointment, Insurance Information, Doctor Availability, and Find a Doctor — all against dummy data in [app/data/hospital_data.py](app/data/hospital_data.py).

> **New to this project?** Read [`docs/`](docs/README.md) first — full business context, architecture, current status, and why things are built the way they are. This file only covers setup/run steps.

**Stack:** [Pipecat](https://pipecat.ai) (orchestration) + self-hosted **Whisper** (STT) + **OpenAI gpt-4o-mini** (LLM) + self-hosted **Piper** (TTS). Only one paid API (`OPENAI_API_KEY`) is needed — STT and TTS run locally, no VideoSDK/Deepgram/ElevenLabs anymore (see [`docs/03_DECISIONS_LOG.md`](docs/03_DECISIONS_LOG.md) for why).

> **Caller picks English or Arabic at the start of the call** (`LANGUAGES=en,ar` in `.env` — set a single value like `LANGUAGES=en` to force one language instead). Urdu isn't wired up yet. See [`docs/02_CURRENT_STATUS.md`](docs/02_CURRENT_STATUS.md).

> **Run this on the VPS**, not a local dev machine — the self-hosted STT/TTS models were benchmarked specifically on that 2-core CPU (see `scripts/benchmark_voice_stack.py`) and confirmed real-time-capable there.

## Project Layout

```
app/                  # the running application
  main.py             # entry point
  prompts.py          # system prompt builder
  error_helpers.py     # runtime error diagnosis
  check_api_keys.py    # preflight key check
  data/hospital_data.py # dummy hospital data
scripts/
  benchmark_voice_stack.py  # one-time STT/TTS hardware benchmark (not part of the running app)
docs/                 # project context - read docs/README.md first
ecosystem.config.js   # PM2 process config
deploy.sh             # one-command VPS update script
requirements.txt / .env.example
```

## 1. Get the one API key you need

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) (paid account) |

Copy `.env.example` to `.env`, paste your key in, and optionally override `LANGUAGES` (defaults to `en,ar`; set it to a single value like `LANGUAGES=en` to force one language):

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
python app/check_api_keys.py
```

Hits OpenAI directly with a real tiny completion and tells you: valid / missing / invalid / out of credits — so you find out immediately, not mid-call.

## 4. Run

```bash
python app/main.py
```

This starts a local WebRTC dev server. Open `http://<your-vps-ip>:7860/client` in a browser, allow mic access, and talk to the agent. The first run downloads the Whisper and Piper models for every language in `LANGUAGES` — with the default `en,ar` that's four models total, so it can take a few minutes.

If something fails *during* a call, `app/main.py` catches it and prints a best-effort diagnosis (OpenAI auth/quota vs. a local model problem) instead of a raw traceback. See `app/error_helpers.py`.

## Production Deployment (VPS, via Git + PM2)

Steps 1-4 above are fine for a quick manual test. For anything longer-running, deploy it properly so it survives disconnects/crashes/reboots and logs to a real file instead of your terminal.

### One-time setup

```bash
git clone https://github.com/ehtisham145/AI_Calling_Bot.git
cd AI_Calling_Bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

cp .env.example .env
nano .env   # paste OPENAI_API_KEY and set LANGUAGES if you want something other than the en,ar default

mkdir -p logs
pm2 start ecosystem.config.js
pm2 save                      # survives a VPS reboot
pm2 install pm2-logrotate     # keeps logs from growing forever
```

### Every update after that

Push from your dev machine as usual (`git add` / `commit` / `push`), then on the VPS:

```bash
./deploy.sh
```

Pulls the latest code, reinstalls any changed dependencies, restarts the bot via PM2, and shows the last 20 log lines so you can confirm it came back up cleanly.

### Logs

```bash
pm2 logs ai-calling-bot            # live tail
pm2 logs ai-calling-bot --lines 100 --nostream   # last 100 lines, no follow
tail -f logs/error.log             # errors only, straight from file
pm2 status                         # is it up, how many restarts, uptime
```

## Known limitations (tracked, not bugs)

- **Dynamic English/Arabic switching is built but not yet confirmed on a real call.** `LANGUAGES=en,ar` (default) lets the caller pick live via Pipecat's `ServiceSwitcher` + a `set_language` function call — see `docs/03_DECISIONS_LOG.md` for the design and a frame-ordering race condition it had to avoid. Needs a live phone test before it's trusted for a demo. Set `LANGUAGES=en` to force single-language mode as before.
- **No Urdu yet.** No validated self-hosted Whisper/Piper pair for Urdu. Was tested and dropped for now — see `docs/02_CURRENT_STATUS.md`.
- **No phone number / telephony yet.** Testing is via the browser WebRTC client only. Twilio integration is the next step, see `docs/05_NEXT_STEPS.md`.
- **STT/TTS model picks are hardware-specific.** `STT_MODEL`/`PIPER_VOICE` in `app/main.py` were chosen based on real benchmarks on *this* VPS's 2-core CPU (see `scripts/benchmark_voice_stack.py` and its results in `docs/03_DECISIONS_LOG.md`) — re-benchmark before changing VPS specs or hardware.
- Dummy data (doctors, insurance providers, hours) lives in `app/data/hospital_data.py` — edit freely, no code changes needed elsewhere.
