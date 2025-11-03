# Offline Voice Assistant

This repository contains an offline voice assistant implemented in Python. It uses Vosk for local speech-to-text, pyttsx3 for TTS, and optionally the Ollama CLI as a local LLM decider. The project provides a CLI and a lightweight Tkinter GUI.

Features

- Real-time local STT using Vosk (optional - falls back to typed input when missing)
- Local LLM decider integration via the `ollama` CLI (optional)
- TTS via `pyttsx3` (optional)
- Safe execution mode (dry-run by default) and an option to allow direct execution of actions
- Clickable GUI launcher included: `run_voice_assistant_ui.bat`

Quick start (recommended)
 
1. Create a virtual environment and activate it (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Make sure the Vosk model folder `vosk-model-en-in-0.5/` is present in the project root. If not, download and place it in that folder.

4. Run the GUI:

```powershell
python -m voice_assistant.gui
# or double-click run_voice_assistant_ui.bat
```

Notes about Ollama

- Ollama is used via its CLI binary (`ollama`). It's not a pip package. Install Ollama and ensure `ollama` is available on PATH or configure `ollama_path` in `config.yaml`.

Configuration

- Edit `config.yaml` to change defaults (wake word, allow_execution, use_ollama, etc.). Command-line flags are available via `python -m voice_assistant`.

Development

- The package is structured as a Python module `voice_assistant/`. Run `python -m voice_assistant` for CLI usage or `python -m voice_assistant.gui` for the UI.

Troubleshooting

- If the GUI shows "Simulated input - type or speak", Vosk or sounddevice may not be installed in the Python used to launch the GUI. Ensure you run the GUI using the same Python that has deps installed (the included `run_voice_assistant_ui.bat` tries local virtualenvs first).
- To see which Python the GUI uses, run it from a terminal and compare `python -c "import sys; print(sys.executable)"` output.

License

- This project is provided as-is. Add your preferred license if you plan to distribute.
  Offline Voice Assistant - skeleton

This repository contains a minimal, dependency-free skeleton for an offline voice assistant. It's intended as a starting point to integrate:

- Vosk (offline speech recognition)
- Ollama + local LLM (intent parsing)
- pyttsx3 (offline TTS)

What I created:

- `voice_assistant/main.py` - runner with `run_interactive()` and `run_test()` (one-shot smoke test)
- `voice_assistant/stt.py` - simulated STT (reads stdin)
- `voice_assistant/nlp_model.py` - tiny rule-based intent parser
- `voice_assistant/executor.py` - safe executor (dry-run by default)
- `voice_assistant/config.yaml` - wake word and options
- `voice_assistant/memory.json` - persistent memory
- `voice_assistant/requirements.txt` - recommended optional deps

Quick smoke test (one-shot, no external deps):

From the project root (parent of `voice_assistant`) run:

```powershell
python -c "from voice_assistant.main import run_test; run_test()"
```

Or run the package directly (recommended) from the project root:

```powershell
python -m voice_assistant --test
```

This will simulate: "hey gng open github" and print the parsed intent and dry-run result.

Next steps to integrate full features:

- Install Vosk and replace `stt.listen()` with a real audio capture + recognizer pipeline
- Integrate Ollama or another local LLM in `nlp_model.parse_intent()` for better intent/entity extraction
- Integrate Ollama or another local LLM in `nlp_model.parse_intent()` for better intent/entity extraction (now implemented; enable with `use_ollama: true` in `config.yaml` and install Ollama).
- Integrate Ollama or another local LLM in `nlp_model.parse_intent()` for better intent/entity extraction (now implemented; enable with `use_ollama: true` in `config.yaml` and install Ollama).
- LLM-driven decision mode: the LLM can also act as a decider that maps a user's utterance directly to an actionable JSON plan (open a URL, launch an app, tell the time). Enable with `use_ollama_decider: true` in `config.yaml` or pass `--use-ollama --ollama-path <path> --debug-llm` to the CLI. When enabled the LLM returns a JSON `action` object which the assistant validates and executes (or dry-runs if `allow_execution: false`).
- LLM-driven decision mode: the LLM can also act as a decider that maps a user's utterance directly to an actionable JSON plan (open a URL, launch an app, tell the time). Enable with `use_ollama_decider: true` in `config.yaml` or pass `--use-ollama --ollama-path <path> --debug-llm` to the CLI. When enabled the LLM returns a JSON `action` object which the assistant validates and executes (or dry-runs if `allow_execution: false`).

Wake-word / always-on listening

- By default this skeleton used a wake word (e.g., "hey gng"). If you find the wake word annoying you can disable it and let the assistant process all input immediately by setting `always_listen: true` in `config.yaml` or by passing `--always-listen` to the CLI. Use this with care - enabling `always_listen` means every captured phrase will be interpreted as a command.
- Enable `allow_execution: true` carefully in `config.yaml` when you're ready to allow system commands
- Add TTS with `pyttsx3` in `executor.execute()` or a separate `tts.py`
- Add TTS with `pyttsx3` in `executor.execute()` or a separate `tts.py` (now included). To enable voice output set `allow_tts: true` in `config.yaml` and install `pyttsx3`.
