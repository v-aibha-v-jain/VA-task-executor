"""
executor.py — safe, configurable command executor with optional TTS.

By default this skeleton will NOT run system commands. Set `allow_execution: true` in
`config.yaml` to allow. To enable voice responses, set `allow_tts: true` in the config
and install `pyttsx3`.
"""
import subprocess
import time
import webbrowser
from . import tts


def _maybe_speak(result: dict, config: dict):
    """If TTS is allowed, craft a short message from result and speak it."""
    if not config.get("allow_tts", False):
        return
    # prefer explicit action
    if result.get("ok") and "action" in result:
        tts.speak(result.get("action"))
    elif result.get("ok") and "time" in result:
        tts.speak(f"The time is {result.get('time')}")
    elif not result.get("ok"):
        tts.speak(f"Error: {result.get('error')}")


def execute(intent, entities, config):
    allow = bool(config.get("allow_execution", False))
    if intent is None:
        res = {"ok": False, "error": "no_intent"}
        _maybe_speak(res, config)
        return res

    # handle a few intents
    # If the NLP returned an explicit 'action' dict (LLM-decider), honor it first
    action = None
    if isinstance(entities, dict) and "action" in entities:
        action = entities.get("action")
    if action:
        a_type = action.get("type")
        if a_type == "open_url":
            url = action.get("url")
            if not url:
                res = {"ok": False, "error": "no_url"}
                _maybe_speak(res, config)
                return res
            if allow:
                try:
                    # Use webbrowser.open which is more reliable cross-platform
                    webbrowser.open(url, new=2)
                    res = {"ok": True, "action": f"opened {url}"}
                except Exception as e:
                    res = {"ok": False, "error": str(e)}
                _maybe_speak(res, config)
                return res
            else:
                res = {"ok": True, "action": f"(dry-run) would open {url}"}
                _maybe_speak(res, config)
                return res

        if a_type == "open_app":
            app = action.get("app")
            if not app:
                res = {"ok": False, "error": "no_app_specified"}
                _maybe_speak(res, config)
                return res
            if allow:
                try:
                    # If the app mapping is a dict (from the parser), handle protocol/app
                    if isinstance(app, dict):
                        a_type2 = app.get("type")
                        a_val = app.get("value")
                        if a_type2 == "protocol":
                            # open protocol URI (e.g., ms-windows-store://)
                            webbrowser.open(a_val, new=0)
                            res = {"ok": True, "action": f"opened protocol {a_val}"}
                        elif a_type2 == "app":
                            subprocess.run(f'start "" "{a_val}"', shell=True, check=False)
                            res = {"ok": True, "action": f"launched {a_val}"}
                        else:
                            res = {"ok": False, "error": "unknown_app_mapping", "mapping": app}
                    else:
                        # On Windows, 'start' works via shell; pass a string
                        subprocess.run(f'start "" "{app}"', shell=True, check=False)
                        res = {"ok": True, "action": f"launched {app}"}
                except Exception as e:
                    res = {"ok": False, "error": str(e)}
                _maybe_speak(res, config)
                return res
            else:
                res = {"ok": True, "action": f"(dry-run) would launch {app}"}
                _maybe_speak(res, config)
                return res

        if a_type == "tell_time":
            t = time.strftime("%Y-%m-%d %H:%M:%S")
            res = {"ok": True, "time": t}
            _maybe_speak(res, config)
            return res

        # unknown action type from LLM
        res = {"ok": False, "error": "unknown_action_type", "action": action}
        _maybe_speak(res, config)
        return res

    if intent == "open_url":
        url = entities.get("url")
        if not url:
            res = {"ok": False, "error": "no_url"}
            _maybe_speak(res, config)
            return res
        if allow:
            # Windows: use start
            try:
                webbrowser.open(url, new=2)
                res = {"ok": True, "action": f"opened {url}"}
            except Exception as e:
                res = {"ok": False, "error": str(e)}
            _maybe_speak(res, config)
            return res
        else:
            res = {"ok": True, "action": f"(dry-run) would open {url}"}
            _maybe_speak(res, config)
            return res

    if intent == "open_app":
        app = entities.get("app")
        if not app:
            res = {"ok": False, "error": "no_app_specified"}
            _maybe_speak(res, config)
            return res
        if allow:
            try:
                if isinstance(app, dict):
                    a_type2 = app.get("type")
                    a_val = app.get("value")
                    if a_type2 == "protocol":
                        webbrowser.open(a_val, new=0)
                        res = {"ok": True, "action": f"opened protocol {a_val}"}
                    elif a_type2 == "app":
                        subprocess.run(f'start "" "{a_val}"', shell=True, check=False)
                        res = {"ok": True, "action": f"launched {a_val}"}
                    else:
                        res = {"ok": False, "error": "unknown_app_mapping", "mapping": app}
                else:
                    subprocess.run(f'start "" "{app}"', shell=True, check=False)
                    res = {"ok": True, "action": f"launched {app}"}
            except Exception as e:
                res = {"ok": False, "error": str(e)}
            _maybe_speak(res, config)
            return res
        else:
            res = {"ok": True, "action": f"(dry-run) would launch {app}"}
            _maybe_speak(res, config)
            return res

    if intent == "tell_time":
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        res = {"ok": True, "time": t}
        _maybe_speak(res, config)
        return res

    # fallback
    res = {"ok": False, "error": "unknown_intent", "intent": intent}
    _maybe_speak(res, config)
    return res
