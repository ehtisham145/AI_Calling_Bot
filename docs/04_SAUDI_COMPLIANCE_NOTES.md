# Saudi Arabia Compliance Notes

**These apply to a real production deployment for the Saudi client - NOT to the current demo**, which uses dummy data and no real Saudi phone number. Captured here so they aren't lost/re-researched before the production phase starts.

## Telephony: Must Route Through a CST-Licensed Carrier
Saudi Arabia's telecom regulator (**CST**, formerly CITC) requires any voice traffic that touches the Kingdom's PSTN (i.e. real phone numbers) to route through a CST-licensed operator - the main ones are **STC, Mobily, Zain**. Unauthorized bypass/grey routing is illegal and actively enforced.

**Practical implication**: Twilio cannot be used directly for a Saudi phone number in production. Options:
- **Unifonic** (Riyadh-based CPaaS, SoftBank-backed) - already CST-licensed, handles SMS/WhatsApp/Voice/OTP. Enterprise pricing (~$499-999/month base + usage, sales-conversation pricing). This is the recommended path.
- A direct licensing/partnership arrangement with a Saudi carrier (far more complex for a small dev operation - not recommended).

The current stack (Pipecat, see `01_ARCHITECTURE.md`) treats Twilio as a first-class transport - but per the CST rule above, that only matters for the demo/test number. The likely production architecture is: Unifonic (or an equivalent CST-licensed carrier) handles the actual Saudi phone number and routes it in as a SIP/telephony leg, while this project's Pipecat pipeline still handles the AI orchestration (STT/LLM/TTS) - Pipecat is telephony-provider-agnostic, so this shouldn't require a stack change, just a different transport configuration.

## Data Residency: PDPL (Personal Data Protection Law)
Enforced by **SDAIA** (Saudi Data & AI Authority), fully enforceable since September 2024.
- **Health data is explicitly classified as "sensitive personal data."**
- Sensitive personal data must be **processed and stored inside Saudi Arabia**, unless SDAIA grants a specific cross-border transfer exception (described as rare/complex to obtain for typical enterprise use cases).
- **Voice recordings count as personal data** under PDPL.
- **Practical implication for this project improved with the Pipecat migration**: STT and TTS now run self-hosted (Whisper, Piper - see `03_DECISIONS_LOG.md`), meaning that audio never leaves the server at all for those two steps - a real compliance advantage, not just a cost one. The remaining exposure is the **LLM (OpenAI)**: the transcribed text (which may contain patient info) is sent to OpenAI's international servers. That's still a compliance risk needing a real answer before go-live with real patient data - not something to guess at. Options to investigate when that phase arrives: data minimization/anonymization before sending text to OpenAI, confirming whether OpenAI offers any in-Kingdom/approved-region data handling terms, or self-hosting an open-weight LLM as well if OpenAI can't satisfy PDPL for this use case.

## Arabic STT/TTS Quality - Consider Regional Vendors for Production
The current self-hosted setup uses a community-fine-tuned Whisper model for Arabic STT (`Omar10lfc/whisper-small-arabic-ct2-int8` - validated as near-perfect accuracy on this VPS, see `03_DECISIONS_LOG.md`) and a Jordanian-dialect Piper voice for TTS (`ar_JO-kareem-medium`) - neither is Saudi-dialect-specific. For production, Saudi-dialect accuracy (and the fact these regional vendors are presumably Saudi/Gulf-hosted, which could help the PDPL question above) both point toward evaluating **regional specialists** before launch:
- **Nabrah** - Riyadh-based, STT/TTS/voice cloning built specifically for Saudi/Gulf Arabic.
- **Munsit** - Gulf dialect + MSA, low latency, native Saudi/Emirati voices.

These weren't adopted for the demo (scope was English-only validation first) but should be evaluated before a real Arabic-speaking-patient production rollout.

## Bottom Line for the Next Phase
Before handling any real patient/call data for the Saudi client: (1) confirm telephony via a CST-licensed carrier (Unifonic is the lead candidate), (2) get a straight answer - ideally from a local legal/compliance consultant, not guessed - on whether the chosen AI providers' data handling satisfies PDPL for this use case, and (3) seriously evaluate Nabrah/Munsit for Arabic quality and possible compliance advantages over international vendors.
