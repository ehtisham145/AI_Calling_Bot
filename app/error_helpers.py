"""Best-effort classification of runtime errors so a failure mid-call points at
the likely cause instead of a raw traceback. Pattern matching, not a guaranteed
taxonomy - run check_api_keys.py first for a reliable OpenAI-key preflight read.

Only OpenAI is a remote/paid service now; Whisper (STT) and Piper (TTS) are
self-hosted, so their failures look different (missing model, OOM) rather than
auth/quota - both are covered below.
"""

_OPENAI_CREDIT_HINTS = ["insufficient_quota", "429", "rate_limit", "quota"]
_OPENAI_AUTH_HINTS = ["401", "unauthorized", "invalid_api_key", "incorrect api key"]
_OPENAI_HINTS = ["openai", "gpt-4o", "chat/completions"]

_LOCAL_MODEL_HINTS = ["whisper", "piper", "onnx", "ctranslate2", "out of memory", "oom", "no such file"]


def classify_error(exc: Exception) -> str:
    text = str(exc).lower()

    if any(h in text for h in _OPENAI_HINTS):
        if any(h in text for h in _OPENAI_CREDIT_HINTS):
            diagnosis = "OpenAI: likely OUT OF CREDITS or RATE-LIMITED"
        elif any(h in text for h in _OPENAI_AUTH_HINTS):
            diagnosis = "OpenAI: likely an INVALID API KEY"
        else:
            diagnosis = "OpenAI: unrecognized error - see raw message below"
    elif any(h in text for h in _LOCAL_MODEL_HINTS):
        diagnosis = "Local STT/TTS (Whisper or Piper): likely a missing/corrupt model file or out-of-memory - check disk space and that the model name is spelled correctly"
    else:
        diagnosis = "Unrecognized error - see raw message below"

    return (
        f"\n{'=' * 60}\n"
        f"AGENT ERROR - {diagnosis}\n"
        f"Raw error: {exc}\n"
        f"Tip: run `python check_api_keys.py` to verify the OpenAI key first.\n"
        f"{'=' * 60}\n"
    )
