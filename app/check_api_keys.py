"""Preflight check — run this BEFORE main.py to confirm the OpenAI key works
and has usable quota, instead of finding out mid-call.

Only one key is needed now: OPENAI_API_KEY. STT (Whisper) and TTS (Piper) are
self-hosted and need no API key - see docs/03_DECISIONS_LOG.md for why
VideoSDK/Deepgram/Google/ElevenLabs were dropped.

Usage: python check_api_keys.py
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def check_openai():
    # Uses a real (tiny, 1-token) chat completion call rather than just /v1/models,
    # since OpenAI no longer exposes a reliable billing/credits endpoint for API
    # keys - the only honest way to confirm quota is actually available is to use it.
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "MISSING", "No OPENAI_API_KEY in .env"
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_completion_tokens": 1,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return "OK", "Key valid, test completion succeeded"
        if r.status_code == 401:
            return "AUTH_FAILED", f"HTTP 401: {r.text[:250]}"
        if r.status_code == 429:
            return "NO_CREDITS", f"HTTP 429 (quota or rate limit): {r.text[:250]}"
        return "UNKNOWN", f"HTTP {r.status_code}: {r.text[:250]}"
    except requests.RequestException as e:
        return "ERROR", str(e)


STATUS_LABEL = {
    "OK": "[OK]",
    "MISSING": "[MISSING]",
    "AUTH_FAILED": "[AUTH FAILED]",
    "NO_CREDITS": "[NO CREDITS]",
    "UNKNOWN": "[UNKNOWN]",
    "ERROR": "[ERROR]",
}


def main():
    print("Checking OPENAI_API_KEY...\n")
    status, detail = check_openai()
    label = STATUS_LABEL.get(status, status)
    print(f"{label:16} OpenAI   {detail}")
    print()
    if status != "OK":
        print("Fix the key above before running app/main.py.")
    else:
        print("Key is valid. Safe to run: python app/main.py")
        print("(STT/TTS are self-hosted - Whisper/Piper models download automatically on first run.)")


if __name__ == "__main__":
    main()
