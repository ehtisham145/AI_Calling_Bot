# Next Steps

Roughly in priority order. Update this file as items complete or priorities shift - it's meant to stay current, not be a historical record (that's what `03_DECISIONS_LOG.md` is for).

## Immediate (finishing the Pipecat migration)
1. **Run `app/main.py` live on the VPS for the first time** and confirm the full Pipecat pipeline actually connects and holds a conversation (STT/TTS model choice and Pipecat's APIs were verified individually, but the assembled pipeline hasn't been run live yet - see `02_CURRENT_STATUS.md`).
2. Manually test all 4 menu branches (Book Appointment, Insurance Information, Doctor Availability, Find a Doctor) in both `LANGUAGE=en` and `LANGUAGE=ar`, confirm responses match `app/data/hospital_data.py` correctly.
3. Tune/fix anything that sounds wrong in `app/prompts.py` or the dummy data based on that testing.

## Before showing the client
4. **Implement real-time language switching** (caller picks language mid-call instead of restarting with a different `LANGUAGE` env var) - research Pipecat's `ServiceSwitcher` and `STTUpdateSettingsFrame`/`TTSUpdateSettingsFrame` properly (verify against docs/source, don't guess) and wire it in.
5. Decide on Urdu: either find/validate a usable self-hosted Whisper+Piper pair for it (none found yet - see `03_DECISIONS_LOG.md`), or explicitly demo English+Arabic only and explain Urdu is "next" to the client.
6. Wire a real phone number so the client can call it like a real user would, instead of using the browser WebRTC client:
   - Connect via Twilio - Pipecat treats it as a first-class transport (see `01_ARCHITECTURE.md`).
   - A demo/test number is fine here - the CST-licensing requirement in `04_SAUDI_COMPLIANCE_NOTES.md` only matters for a *real Saudi production number*, not a demo test call.

## After the client approves the demo (production phase)
7. Re-read `04_SAUDI_COMPLIANCE_NOTES.md` in full and act on it: line up Unifonic (or confirmed equivalent) for the real Saudi number, get a real answer on PDPL compliance for OpenAI specifically (STT/TTS being self-hosted actually *helps* here - no third-party ever sees the raw audio for those two steps).
8. Replace dummy data with a real integration into the hospital's actual systems (doctor schedules, insurance, appointment booking) - scope/approach not yet decided, depends on what the hospital's existing systems look like.
9. Re-benchmark STT/TTS model choice if the production VPS has different specs than the one in `scripts/benchmark_voice_stack.py` - the picks in `app/main.py` are hardware-specific, not universal.
10. ~~Set up proper process management for `main.py` on the VPS~~ **Done** - code is on a private GitHub repo, deployed via `git clone` + PM2 (`ecosystem.config.js`), updates via `./deploy.sh`, log rotation via `pm2-logrotate`. See the "Production Deployment" section in `README.md`.
11. Invoice the demo (~$500, 50/50 milestone split as discussed) and scope/quote the production contract (~$5,000-15,000+ range, or a retainer).
