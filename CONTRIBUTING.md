# Contributing

Thanks for your interest in contributing to this project. This document explains the basic workflow for reporting issues, suggesting features, and submitting pull requests.

## Reporting issues

- Before opening an issue, search existing issues in `.github/ISSUES` (local) to avoid duplicates.
- For bugs, include: steps to reproduce, environment (OS, Python version), what you expected, and what happened.

## Feature requests

- Please describe the user story, an example workflow, and any UI mockups if available.

## Quick checklist for PRs

- Keep changes small and focused.
- Include unit tests when possible.
- Run formatting (black) and linting (flake8) locally.
- Update `README.md` and `requirements.txt` if you add/remove dependencies.

## Developer setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
.venv\Scripts\pip install -r requirements.txt
```

3. Run the GUI during development:

```powershell
python -m voice_assistant.gui
```

## Style and tests

- Use Black for formatting and add tests under `tests/` when adding non-trivial logic.

## Contact

- If you want help, open an issue in `.github/ISSUES/` or contact the maintainer via the repo comments.
