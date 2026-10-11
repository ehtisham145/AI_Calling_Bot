# Next Steps

Roughly in priority order. Update this file as items complete or priorities shift - it's meant to stay current, not be a historical record (that's what `03_DECISIONS_LOG.md` is for).

## Immediate (finishing the Pipecat migration)
1. **Get real Hostinger firewall access and open WebRTC's ports** (TCP+UDP 7860, plus whatever port range SmallWebRTCTransport needs for direct media). This is now the single blocker to testing the bot end-to-end. A local coturn TURN server on 443 was tried as a workaround and abandoned - see `03_DECISIONS_LOG.md` for why.
2. Once reachable, confirm the full Pipecat pipeline actually connects and holds a voice conversation (STT/TTS model choice and Pipecat's APIs were verified individually, but a live end-to-end voice exchange hasn't been confirmed yet - see `02_CURRENT_STATUS.md`).
3. **Live-test the new `LANGUAGES=en,ar` dynamic switching end-to-end** (built and verified against source, but not yet exercised with real speech - see `02_CURRENT_STATUS.md`/`03_DECISIONS_LOG.md`): confirm the opening bilingual prompt plays, saying "Arabic" mid-call actually flips both STT and TTS to Arabic (not just the text), and that the reply voice/content is correct on the very first turn after the switch (this is specifically what the frame-ordering fix was for).
4. Manually test all 4 menu branches (Book Appointment, Insurance Information, Doctor Availability, Find a Doctor) in both `LANGUAGES=en` and `LANGUAGES=ar`, confirm responses match `app/data/hospital_data.py` correctly.
5. Tune/fix anything that sounds wrong in `app/prompts.py` or the dummy data based on that testing.

## Before showing the client
6. Decide on Urdu: either find/validate a usable self-hosted Whisper+Piper pair for it (none found yet - see `03_DECISIONS_LOG.md`), or explicitly demo English+Arabic only and explain Urdu is "next" to the client.
7. Wire a real phone number so the client can call it like a real user would, instead of using the browser WebRTC client:
   - Connect via Twilio - Pipecat treats it as a first-class transport (see `01_ARCHITECTURE.md`).
   - A demo/test number is fine here - the CST-licensing requirement in `04_SAUDI_COMPLIANCE_NOTES.md` only matters for a *real Saudi production number*, not a demo test call.

## After the client approves the demo (production phase)
8. Re-read `04_SAUDI_COMPLIANCE_NOTES.md` in full and act on it: line up Unifonic (or confirmed equivalent) for the real Saudi number, get a real answer on PDPL compliance for OpenAI specifically (STT/TTS being self-hosted actually *helps* here - no third-party ever sees the raw audio for those two steps).
9. Replace dummy data with a real integration into the hospital's actual systems (doctor schedules, insurance, appointment booking) - scope/approach not yet decided, depends on what the hospital's existing systems look like.
10. Re-benchmark STT/TTS model choice if the production VPS has different specs than the one in `scripts/benchmark_voice_stack.py` - the picks in `app/main.py` are hardware-specific, not universal.
11. ~~Set up proper process management for `main.py` on the VPS~~ **Done** - code is on a private GitHub repo, deployed via `git clone` + PM2 (`ecosystem.config.js`), updates via `./deploy.sh`, log rotation via `pm2-logrotate`. See the "Production Deployment" section in `README.md`.
12. Invoice the demo (~$500, 50/50 milestone split as discussed) and scope/quote the production contract (~$5,000-15,000+ range, or a retainer).
