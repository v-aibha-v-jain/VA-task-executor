"""
CLI wrapper for running the assistant directly.

Usage:
  # from project root
  python voice_assistant/cli.py        # interactive
  python voice_assistant/cli.py test   # run one-shot smoke test

This script is defensive about sys.path so you can run it from inside the package
folder or from the project root.
"""
import sys
from pathlib import Path


def ensure_parent_on_path():
    """Ensure the project root (parent of this file's parent) is on sys.path.

    This allows running `python voice_assistant/cli.py` from inside the `voice_assistant`
    folder without ImportError for package imports.
    """
    here = Path(__file__).resolve()
    project_root = here.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def main(argv=None):
    import argparse

    argv = argv if argv is not None else sys.argv[1:]
    ensure_parent_on_path()
    try:
        # import lazily after path fix
        from voice_assistant.main import run_interactive, run_test
    except Exception as e:
        print("Failed to import voice_assistant.main:", e)
        sys.exit(1)

    parser = argparse.ArgumentParser(prog="voice_assistant", description="Run the offline assistant")
    parser.add_argument("mode", nargs="?", choices=["run", "test"], default="run", help="run or test")
    parser.add_argument("--allow-exec", dest="allow_exec", action="store_true", help="Allow executing system commands")
    parser.add_argument("--allow-tts", dest="allow_tts", action="store_true", help="Enable TTS output (pyttsx3 required)")
    parser.add_argument("--use-ollama", dest="use_ollama", action="store_true", help="Use local Ollama LLM for intent parsing")
    parser.add_argument("--use-ollama-decider", dest="use_ollama_decider", action="store_true", help="Let the LLM decide actions (outputs JSON 'action' objects)")
    parser.add_argument("--ollama-path", dest="ollama_path", type=str, help="Full path to ollama executable (overrides PATH)")
    parser.add_argument("--llm-model", dest="llm_model", type=str, default="phi3", help="LLM model name to request from Ollama")
    parser.add_argument("--debug-llm", dest="debug_llm", action="store_true", help="Log raw LLM output to assist tuning")
    parser.add_argument("--always-listen", dest="always_listen", action="store_true", help="Disable wake word and process all input immediately")

    args = parser.parse_args(argv)

    # Build config overrides to pass into run_interactive/run_test
    config_overrides = {}
    if args.allow_exec:
        config_overrides["allow_execution"] = True
    if args.allow_tts:
        config_overrides["allow_tts"] = True
    if args.use_ollama:
        config_overrides["use_ollama"] = True
    if args.use_ollama_decider:
        config_overrides["use_ollama_decider"] = True
    if args.always_listen:
        config_overrides["always_listen"] = True
    if args.ollama_path:
        config_overrides["ollama_path"] = args.ollama_path
    if args.llm_model:
        config_overrides["llm_model"] = args.llm_model
    if args.debug_llm:
        config_overrides["debug_llm"] = True

    # If the user asked for the Ollama decider, implicitly enable execution so
    # the decider's chosen action will be performed rather than only dry-run.
    # The user can still explicitly disable execution by editing config.yaml.
    if config_overrides.get("use_ollama_decider") and not config_overrides.get("allow_execution"):
        print("Ollama decider requested — enabling execution by default. Use --allow-exec to control this behavior.")
        config_overrides["allow_execution"] = True

    if args.mode == "test":
        run_test(config_overrides=config_overrides)
    else:
        run_interactive(config_overrides=config_overrides)


if __name__ == '__main__':
    main()
