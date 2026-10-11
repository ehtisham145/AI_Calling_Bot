# Project Overview

## What This Is
A demo AI voice calling bot for a **hospital** client. A caller dials a number, the AI picks up, lets them choose a language, then handles: Book Appointment, Insurance Information, Doctor Availability, Find a Doctor.

## Business Context
- **Client**: A hospital business based in **Saudi Arabia**.
- **Developer**: Solo full-stack developer, based in **Pakistan**, building this independently and selling it to the client.
- **Goal**: Build a working demo first (dummy data, no real phone number) to prove the concept, then negotiate a larger production contract.
- **Why a demo first**: Lets the client evaluate the approach before committing budget to a full production build (real phone number, real hospital data integration, Saudi telephony compliance).

## Pricing (agreed/discussed, not yet invoiced)
- **Demo/proof-of-concept**: ~$500 (floor — don't go lower; covers the dev effort fairly and is still an easy yes for the client).
- **Full production system** (real number, real DB integration, Saudi-compliant telephony, multilingual, support): expected to be quoted separately later, realistically **$5,000–15,000+** or a monthly retainer, once the demo lands the client.
- Payment structure recommended: 50% upfront / 50% on delivery for the demo.

## Required Demo Behavior (target - see `02_CURRENT_STATUS.md` for what's actually wired up today)
1. Caller is greeted and asked to pick a language: **Arabic, English, or Urdu** (corrected from an earlier "Hindi" - the client needs Urdu, not Hindi).
2. Conversation continues entirely in the chosen language.
3. Main menu with exactly 4 options:
   - Book an Appointment
   - Insurance Information
   - Doctor Availability
   - Find a Doctor
4. Each option is handled using dummy hospital data (no real database yet).

**Current reality**: only English and Arabic are wired up, and language is fixed per run rather than caller-selectable mid-call - both are known, tracked gaps (not forgotten), see `02_CURRENT_STATUS.md` and `05_NEXT_STEPS.md`.

See [`01_ARCHITECTURE.md`](01_ARCHITECTURE.md) for how this is actually built, and [`02_CURRENT_STATUS.md`](02_CURRENT_STATUS.md) for what currently works vs. what's still pending.
