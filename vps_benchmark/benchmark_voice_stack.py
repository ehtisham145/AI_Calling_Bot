#!/usr/bin/env python3
"""Benchmark: Piper TTS + faster-whisper STT latency on THIS machine.

English + Arabic ONLY (Urdu dropped - generic Whisper tiny/base struggled on it
in earlier testing, not worth the extra complexity right now).

Tests specialized lightweight models instead of just generic Whisper sizes:
- English: "distil-small.en" (distil-whisper) - 6x faster, ~49% smaller than
  large, within ~1% WER of full Whisper, English-only by design.
- Arabic: "Omar10lfc/whisper-small-arabic-ct2-int8" - community fine-tune of
  Whisper-small specifically on Arabic, should beat generic multilingual
  "small"/"base" for Arabic specifically.
Both compared against generic "tiny" and "base" as a baseline.

Reports RTF (real-time factor) = time_taken / audio_duration.
RTF < 1.0 = faster than real-time (good for a live call).

Run this on the VPS (2-core target hardware), not the Windows dev machine.

Usage:
    pip install piper-tts faster-whisper "av<19"
    python3 benchmark_voice_stack.py
"""

import glob
import subprocess
import sys
import time
import wave
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "piper_models"
MODELS_DIR.mkdir(exist_ok=True)

# Candidate Whisper models to test, per language. "tiny"/"base" are generic
# multilingual baselines; the others are language-specialized.
WHISPER_CANDIDATES = {
    "en": ["tiny", "base", "distil-small.en"],
    "ar": ["tiny", "base", "Omar10lfc/whisper-small-arabic-ct2-int8"],
}

VOICES = {
    "en": "en_US-amy-medium",
    "ar": "ar_JO-kareem-medium",
}

TEST_TEXT = {
    "en": "Welcome to the hospital. How can I help you today?",
    "ar": "مرحبا بكم في المستشفى. كيف يمكنني مساعدتك اليوم؟",
}

# distil-small.en is English-only and doesn't take a "language" kwarg the same
# way multilingual models do - omit language for it, pass "en"/"ar" for others.
def whisper_language_kwarg(lang: str, model_size: str) -> dict:
    if model_size == "distil-small.en":
        return {}
    return {"language": lang}


def ensure_voice_downloaded(voice_name: str) -> Path:
    existing = glob.glob(str(MODELS_DIR / "**" / f"{voice_name}.onnx"), recursive=True)
    if existing:
        return Path(existing[0])

    print(f"  downloading {voice_name} ...")
    subprocess.run(
        [sys.executable, "-m", "piper.download_voices", "--data-dir", str(MODELS_DIR), voice_name],
        check=True,
    )
    found = glob.glob(str(MODELS_DIR / "**" / f"{voice_name}.onnx"), recursive=True)
    if not found:
        raise RuntimeError(f"Download reported success but {voice_name}.onnx not found under {MODELS_DIR}")
    return Path(found[0])


def wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def generate_test_audio() -> dict:
    from piper import PiperVoice

    audio = {}
    for lang, voice_name in VOICES.items():
        print(f"\n=== {lang.upper()} TTS ({voice_name}) ===")
        model_path = ensure_voice_downloaded(voice_name)
        voice = PiperVoice.load(str(model_path))

        text = TEST_TEXT[lang]
        wav_path = MODELS_DIR / f"test_{lang}.wav"

        t0 = time.time()
        with wave.open(str(wav_path), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        tts_time = time.time() - t0

        duration = wav_duration_seconds(wav_path)
        tts_rtf = tts_time / duration if duration else float("inf")
        print(f"  TTS: {tts_time:.2f}s to generate {duration:.2f}s of audio -> RTF {tts_rtf:.2f}")

        audio[lang] = (wav_path, duration, tts_rtf)
    return audio


def run_benchmark():
    from faster_whisper import WhisperModel

    audio = generate_test_audio()
    all_rows = []

    for lang, (wav_path, duration, tts_rtf) in audio.items():
        for model_size in WHISPER_CANDIDATES[lang]:
            print(f"\n--- Loading '{model_size}' for {lang.upper()} ---")
            try:
                whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"  FAILED to load {model_size}: {e}")
                continue

            t0 = time.time()
            segments, _info = whisper_model.transcribe(
                str(wav_path), **whisper_language_kwarg(lang, model_size)
            )
            transcribed = " ".join(seg.text for seg in segments).strip()
            stt_time = time.time() - t0
            stt_rtf = stt_time / duration if duration else float("inf")

            print(f"  Original:    {TEST_TEXT[lang]}")
            print(f"  Transcribed: {transcribed[:100]}")
            print(f"  STT: {stt_time:.2f}s -> RTF {stt_rtf:.2f}")

            all_rows.append((lang, model_size, tts_rtf, stt_rtf, transcribed))

    print("\n" + "=" * 80)
    print("SUMMARY  (RTF < 1.0 = faster than real-time; compare Transcribed text above for accuracy)")
    print("=" * 80)
    for lang, model_size, tts_rtf, stt_rtf, _transcribed in all_rows:
        worst = max(tts_rtf, stt_rtf)
        verdict = "OK" if worst < 0.7 else ("BORDERLINE" if worst < 1.0 else "TOO SLOW")
        print(f"  {lang.upper():4}  {model_size:38}  TTS RTF={tts_rtf:.2f}   STT RTF={stt_rtf:.2f}   -> {verdict}")


if __name__ == "__main__":
    run_benchmark()
