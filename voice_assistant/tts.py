"""
tts.py — simple TTS wrapper using pyttsx3 with graceful fallback.

Usage:
  from voice_assistant import tts
  tts.speak("Hello world")

If `pyttsx3` is not installed, `speak()` will print a dry-run message.
"""
from typing import Optional

HAS_PYTTSX3 = False
engine = None

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except Exception:
    pyttsx3 = None


def _init_engine():
    global engine
    if engine is None and HAS_PYTTSX3:
        engine = pyttsx3.init()
    return engine


def speak(text: str, blocking: bool = True) -> None:
    """Speak `text` using pyttsx3 when available, otherwise print a dry-run message.

    This function never raises on missing optional dependencies — it falls back.
    """
    if not text:
        return
    if HAS_PYTTSX3:
        try:
            eng = _init_engine()
            eng.say(text)
            if blocking:
                eng.runAndWait()
        except Exception as e:
            print(f"[TTS error] {e}")
    else:
        # dry-run: print to stdout so tests and CI can see it
        print(f"[TTS dry-run] {text}")


if __name__ == '__main__':
    speak('This is a test of the emergency broadcast system.')
