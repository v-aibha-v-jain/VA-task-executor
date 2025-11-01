"""Package entrypoint for `voice_assistant`.

Allows running the assistant with:
  python -m voice_assistant

This avoids relative-import issues when running `main.py` directly inside the package folder.
"""
from .main import run_interactive, run_test
import sys


def _parse_args(argv):
    import argparse

    parser = argparse.ArgumentParser(prog="python -m voice_assistant", description="Run the offline assistant (module entry)")
    parser.add_argument("mode", nargs="?", choices=["run", "test"], default="run")
    parser.add_argument("--allow-exec", dest="allow_exec", action="store_true", help="Allow executing system commands")
    parser.add_argument("--allow-tts", dest="allow_tts", action="store_true", help="Enable TTS output (pyttsx3 required)")
    parser.add_argument("--use-ollama", dest="use_ollama", action="store_true", help="Use local Ollama LLM for intent parsing")
    parser.add_argument("--use-ollama-decider", dest="use_ollama_decider", action="store_true", help="Let the LLM decide actions (outputs JSON 'action' objects)")
    parser.add_argument("--ollama-path", dest="ollama_path", type=str, help="Full path to ollama executable (overrides PATH)")
    parser.add_argument("--llm-model", dest="llm_model", type=str, default="phi3", help="LLM model name to request from Ollama")
    parser.add_argument("--always-listen", dest="always_listen", action="store_true", help="Disable wake word and process all input immediately")
    parser.add_argument("--debug-llm", dest="debug_llm", action="store_true", help="Log raw LLM output to assist tuning")
    return parser.parse_args(argv)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    args = _parse_args(argv)
    config_overrides = {}

    # If the user invoked `python -m voice_assistant` with NO args (argv empty),
    # or with only the 'test' positional (no extra flags), default to using
    # Ollama as the decider and allow execution so the module behaves as a
    # direct voice-driven assistant. Passing any explicit args will override
    # these defaults.
    if (not argv) or (len(argv) == 1 and argv[0] == "test"):
        print("No CLI args (or only 'test') detected — enabling Ollama decider and execution by default.")
        config_overrides["use_ollama"] = True
        config_overrides["use_ollama_decider"] = True
        config_overrides["allow_execution"] = True
        # keep TTS off by default (avoid unexpected audio); user can pass --allow-tts
    else:
        if args.allow_exec:
            config_overrides["allow_execution"] = True
        if args.allow_tts:
            config_overrides["allow_tts"] = True
        if args.use_ollama:
            config_overrides["use_ollama"] = True
        if args.use_ollama_decider:
            config_overrides["use_ollama_decider"] = True
        if args.ollama_path:
            config_overrides["ollama_path"] = args.ollama_path
        if args.llm_model:
            config_overrides["llm_model"] = args.llm_model
        if args.always_listen:
            config_overrides["always_listen"] = True
        if args.debug_llm:
            config_overrides["debug_llm"] = True

        # If the Ollama decider is requested, implicitly enable execution
        # so the decider's chosen action will be performed instead of a dry-run.
        if config_overrides.get("use_ollama_decider") and not config_overrides.get("allow_execution"):
            print("Ollama decider requested — enabling execution by default. Pass --allow-exec to control this.")
            config_overrides["allow_execution"] = True

    if args.mode == "test":
        run_test(config_overrides=config_overrides)
    else:
        run_interactive(config_overrides=config_overrides)


if __name__ == '__main__':
    main()
