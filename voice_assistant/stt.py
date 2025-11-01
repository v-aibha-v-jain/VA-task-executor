"""
stt.py — Vosk STT integration with graceful fallback.

Behavior:
- If `vosk` and `sounddevice` are installed and a model exists at the default path,
  `listen()` will capture audio from the default microphone, run the Vosk recognizer
  and return recognized text (blocking until a final result is produced).
- If the real audio stack is unavailable, `listen()` falls back to simulated stdin input
  so the rest of the skeleton remains usable.

Usage:
  from voice_assistant import stt
  text = stt.listen()

Notes:
- This module intentionally avoids hard failures. It prints status messages to help
  diagnose missing dependencies or model files.
"""

from pathlib import Path
import json
import time
import queue
import sys

HAS_VOSK = False
HAS_SD = False

try:
    from vosk import Model, KaldiRecognizer
    HAS_VOSK = True
except Exception:
    Model = None
    KaldiRecognizer = None

try:
    import sounddevice as sd
    HAS_SD = True
except Exception:
    sd = None


def default_model_path():
    # default to a sibling folder in the project root
    p = Path(__file__).resolve().parent.parent / "vosk-model-en-in-0.5"
    return p


def available():
    """Return True if a real Vosk+sounddevice STT pipeline is available."""
    if not HAS_VOSK or not HAS_SD:
        return False
    model_path = default_model_path()
    return model_path.exists()


def listen(model_path: str = None, samplerate: int = 16000, timeout: float = None, status_cb=None) -> str:
    """Listen from microphone and return recognized text.

    - If Vosk+sounddevice and a model are available, stream from mic until a final
      result is produced and return it.
    - Otherwise fall back to reading a line from stdin (simulated mic).

    Arguments:
      model_path: path to vosk model directory (optional)
      samplerate: audio sample rate (default 16000)
      timeout: optional maximum seconds to wait; None means block until a result
    """
    # prefer real STT when possible
    model_dir = Path(model_path) if model_path else default_model_path()
    if HAS_VOSK and HAS_SD and model_dir.exists():
        try:
            if status_cb:
                try:
                    status_cb("loading")
                except Exception:
                    pass
            print(f"[stt] Loading Vosk model from: {str(model_dir)}")
            model = Model(str(model_dir))
            rec = KaldiRecognizer(model, samplerate)
            q = queue.Queue()

            def callback(indata, frames, time_info, status):
                # indata is a memoryview or numpy array depending on the build
                q.put(bytes(indata))

            stream = sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=callback)
            with stream:
                start = time.time()
                if status_cb:
                    try:
                        status_cb("listening")
                    except Exception:
                        pass
                print("[stt] Listening (press Ctrl+C to cancel)...")
                while True:
                    try:
                        data = q.get()
                    except KeyboardInterrupt:
                        raise
                    if rec.AcceptWaveform(data):
                        res = rec.Result()
                        try:
                            j = json.loads(res)
                            text = j.get('text', '').strip()
                        except Exception:
                            text = ''
                        return text
                    else:
                        # partial results available via rec.PartialResult() if needed
                        if timeout is not None and (time.time() - start) > timeout:
                            # try to get final from remaining buffer
                            final = rec.FinalResult()
                            try:
                                j = json.loads(final)
                                return j.get('text', '').strip()
                            except Exception:
                                return ''
        except Exception as e:
            print(f"[stt] Vosk listen failed: {e}")

    # fallback to simulated input
    try:
        if status_cb:
            try:
                status_cb("simulated")
            except Exception:
                pass
        print("(simulated mic) ", end='', flush=True)
        line = sys.stdin.readline()
        if not line:
            return ''
        return line.strip()
    except (KeyboardInterrupt, EOFError):
        raise


def simulate(text: str) -> str:
    """Return a simulated recognition result (keeps compatibility with previous API)."""
    return text


if __name__ == '__main__':
    # quick local test: print availability and optionally run a short listen
    print('VOSK available:', HAS_VOSK, 'sounddevice available:', HAS_SD)
    print('Model exists at default path:', default_model_path().exists())
