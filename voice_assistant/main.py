"""
voice_assistant.main

Minimal offline assistant skeleton (stubbed). Designed to be extended with Vosk (STT), Ollama (LLM), and pyttsx3 (TTS).

This file provides:
- run_interactive(): simple REPL (simulated mic via input)
- run_test(): one-shot simulated command for smoke testing

No external dependencies required for this skeleton.
"""
import json
import time
import os
from pathlib import Path

from . import stt
from . import nlp_model
from . import executor

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
MEMORY_PATH = ROOT / "memory.json"


def load_config(path=CONFIG_PATH):
    # naive YAML-like parser for the minimal config we ship
    config = {}
    if not path.exists():
        return config
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]

    key = None
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            # list item or nested
            if key and line.strip().startswith("-"):
                config.setdefault(key, [])
                config[key].append(line.strip()[1:].strip())
        else:
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                if v == "":
                    config[k] = []
                    key = k
                elif v.lower() in ("true", "false"):
                    config[k] = v.lower() == "true"
                    key = None
                else:
                    config[k] = v
                    key = None
    return config


def load_memory(path=MEMORY_PATH):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(mem, path=MEMORY_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def process_text(text, config, memory):
    # check wake word unless always_listen is enabled
    text_l = text.lower()
    if not bool(config.get("always_listen", False)):
        wake = config.get("wake_word", "hey gng").lower()
        if wake not in text_l:
            return {"handled": False, "reason": "wake_word_not_detected"}
        # remove wake word
        cmd = text_l.replace(wake, "", 1).strip()
    else:
        cmd = text_l
    if not cmd:
        return {"handled": True, "response": "Yes?"}

    # parse intent
    parsed = nlp_model.parse_intent(cmd, config)

    # execute intent (dry-run unless allow_execution=True)
    result = executor.execute(parsed.get("intent"), parsed.get("entities"), config)

    # store last command in memory
    memory["last_command"] = {"text": cmd, "intent": parsed.get("intent"), "entities": parsed.get("entities")}
    save_memory(memory)

    return {"handled": True, "parsed": parsed, "result": result}


def run_interactive(config_overrides: dict = None):
    """Interactive listen loop.

    `config_overrides` is a dict of settings that override values loaded from
    `config.yaml`. This is useful for CLI flags or tests.
    """
    print("Offline assistant skeleton — type simulated speech and press Enter (Ctrl+C to quit)")
    config = load_config()
    if config_overrides:
        config.update(config_overrides)
    memory = load_memory()
    while True:
        try:
            text = stt.listen()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting")
            break
        if not text:
            continue
        out = process_text(text, config, memory)
        if not out.get("handled"):
            print("(wake word not detected — say: {} )".format(config.get("wake_word", "hey gng")))
        else:
            print("Response:", out.get("result", {}))


def run_test(config_overrides: dict = None):
    """Run a one-shot simulated command for smoke testing.

    Accepts `config_overrides` like `run_interactive`.
    """
    test_input = "hey gng open github"
    print("[test] simulating input:", test_input)
    config = load_config()
    if config_overrides:
        config.update(config_overrides)
    memory = load_memory()
    out = process_text(test_input, config, memory)
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    run_interactive()
