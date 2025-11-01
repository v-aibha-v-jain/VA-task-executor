"""
nlp_model.py — intent parser.

This module keeps a small rule-based fallback parser but adds optional integration
with a local LLM via the `ollama` CLI. Enable LLM parsing by setting
`use_ollama: true` and `llm_model: <model-name>` in `config.yaml` (default model: `phi3`).

Behavior:
- If `use_ollama` is True and the `ollama` CLI is available, the module will call
  the model with a short prompt and expect JSON output with `intent` and `entities`.
- If LLM parsing fails for any reason, the code falls back to the rule-based parser.
"""

import json
import shutil
import subprocess
import re
from pathlib import Path
from typing import Dict, Any


def _ollama_available(ollama_path: str = None) -> bool:
    """Return True if an ollama executable is available.

    If `ollama_path` is provided, check that path exists; otherwise use shutil.which.
    """
    if ollama_path:
        return Path(ollama_path).exists()
    return shutil.which("ollama") is not None


def _call_ollama(prompt: str, model: str = "phi3", timeout: int = 10, ollama_exec: str = None) -> str:
    """Call `ollama run <model>` with `prompt` on stdin and return stdout as text.

    This is intentionally simple and robust: we capture stdout/stderr and return
    whatever the model produced, leaving the caller to parse JSON within the output.
    """
    try:
        cmd = [ollama_exec, "run", model] if ollama_exec else ["ollama", "run", model]
        proc = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True, timeout=timeout)
        out = proc.stdout.decode("utf-8", errors="ignore")
        err = proc.stderr.decode("utf-8", errors="ignore")
        if err and not out:
            # sometimes model prints to stderr — include it
            out += "\n" + err
        return out
    except Exception:
        return ""


def _extract_json(text: str) -> Dict[str, Any]:
    """Find and parse the first JSON object in `text`. Returns {} on failure."""
    # simple regex to find {...} block — not robust for nested braces but OK for model output
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return {}
    s = m.group(0)
    try:
        return json.loads(s)
    except Exception:
        return {}


def _rule_based_parse(text: str, config: dict) -> Dict[str, Any]:
    t = text.lower()
    entities = {}
    intent = "unknown"

    # App mappings: prefer launching native apps or protocol URIs when available.
    # Each entry maps a short name to a dict describing how to launch it.
    # - type: 'protocol' will be opened as a URI (e.g., ms-windows-store://)
    # - type: 'app' will be launched via 'start' with the provided value
    app_map = {
        "microsoft store": {"type": "protocol", "value": "ms-windows-store://home"},
        "microsoft": {"type": "protocol", "value": "ms-windows-store://home"},
        "xbox": {"type": "protocol", "value": "xbox:"},
        "spotify": {"type": "app", "value": "spotify"},
    }

    # Common website mappings (fallback to opening in browser)
    site_map = {
        "github": "https://github.com",
        "linkedin": "https://www.linkedin.com",
        "xbox": "https://www.xbox.com",
        "steam": "https://store.steampowered.com",
    }

    # Normalize some common mishearings
    aliases = {
        "mic store": "microsoft store",
        "microsft store": "microsoft store",
    }

    # apply aliases first
    for a, b in aliases.items():
        if a in t and b not in t:
            t = t.replace(a, b)

    # Only consider commands that begin with/open containing 'open'
    if "open" in t:
        # Prefer app_map matches (exact word match) so 'microsoft store' opens the
        # Store app/protocol instead of the website.
        for name, info in app_map.items():
            # exact-word matching to avoid false positives
            if re.search(r"\b" + re.escape(name) + r"\b", t):
                intent = "open_app"
                # return the raw info so executor can decide how to launch
                entities["app"] = info
                return {"intent": intent, "entities": entities}

        # If no app matched, fall back to known site mappings
        for name, url in site_map.items():
            if re.search(r"\b" + re.escape(name) + r"\b", t):
                intent = "open_url"
                entities["url"] = url
                return {"intent": intent, "entities": entities}

        # browser / edge / chrome -> open browser (app)
        if re.search(r"\b(edge|browser)\b", t):
            intent = "open_app"
            entities["app"] = {"type": "app", "value": "msedge"}
            return {"intent": intent, "entities": entities}
        if re.search(r"\bchrome\b", t):
            intent = "open_app"
            entities["app"] = {"type": "app", "value": "chrome"}
            return {"intent": intent, "entities": entities}

    if "what" in t and "time" in t:
        intent = "tell_time"
        return {"intent": intent, "entities": entities}

    # try fallback: check for keywords in config
    for cmd in config.get("allowed_commands", []):
        if cmd.lower() in t:
            intent = cmd
            return {"intent": intent, "entities": entities}

    return {"intent": intent, "entities": entities}


def parse_intent(text: str, config: dict) -> Dict[str, Any]:
    """Return {'intent': str, 'entities': dict}.

    If `config.get('use_ollama')` is True and the `ollama` CLI is present, call the
    LLM asking for a JSON response. On failure, fall back to the rule-based parser.
    """
    # Try LLM path first when requested
    use_llm = bool(config.get("use_ollama", False))
    model = config.get("llm_model", "phi3")

    # determine executable path (config can override)
    ollama_exec = config.get("ollama_path") if isinstance(config.get("ollama_path"), str) else None
    # Optional LLM-based decider: ask the LLM to choose an action directly.
    if config.get("use_ollama_decider", False) and use_llm and _ollama_available(ollama_exec):
        decider_prompt = (
            "You are an assistant that converts a user's short command into a single JSON"
            " object describing the action to take. Only output valid JSON. The JSON must"
            " have a top-level key 'action' whose value is an object with a 'type' field"
            " (one of: 'open_url', 'open_app', 'tell_time', 'none') and any required"
            " arguments (for example, 'url' for open_url, 'app' for open_app). Example:\n\n"
            "Input: 'Open GitHub in the browser'\n"
            "Output: {\"action\": {\"type\": \"open_url\", \"url\": \"https://github.com\"}}\n\n"
            f"Input: '{text}'\nOutput:"
        )
        out = _call_ollama(decider_prompt, model=model, ollama_exec=ollama_exec)
        parsed = _extract_json(out)
        if parsed and isinstance(parsed.get("action"), dict):
            # wrap into same return shape: intent + entities
            return {"intent": "execute", "entities": {"action": parsed.get("action")}}

    if use_llm and _ollama_available(ollama_exec):
        prompt = (
            "You are a JSON extraction assistant. Given a user command, extract the "
            "intent and any entities and return a single JSON object with the keys "
            "\"intent\" (string) and \"entities\" (object). Only output valid JSON.\n\n"
            "Examples:\n"
            "Input: 'Open GitHub in the browser'\n"
            "Output: {\"intent\": \"open_url\", \"entities\": {\"url\": \"https://github.com\"}}\n\n"
            f"Input: '{text}'\nOutput:"
        )
        out = _call_ollama(prompt, model=model, ollama_exec=ollama_exec)
        parsed = _extract_json(out)
        if parsed and isinstance(parsed.get("intent"), str) and isinstance(parsed.get("entities", {}), dict):
            return {"intent": parsed.get("intent"), "entities": parsed.get("entities", {})}

    # fallback
    return _rule_based_parse(text, config)


def test_ollama(model: str = "phi3", sample: str = "Open GitHub in the browser") -> str:
    """Helper for debugging: run a quick prompt through Ollama and return raw output.

    Returns empty string if Ollama isn't available or the call failed.
    """
    # try default path first; allow passing a path via sample if needed (not implemented here)
    exec_path = shutil.which("ollama")
    if not _ollama_available(exec_path):
        return ""
    prompt = f"Input: '{sample}'\nOutput:"
    return _call_ollama(prompt, model=model, ollama_exec=exec_path)

