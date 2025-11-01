Title: Improve command flow and command types

Description:
Currently the assistant primarily opens URLs or apps. We need a richer command model and better confirmations/feedback.

Suggested improvements:

- Expand `nlp_model` intent/entity extraction to support actions: search, summarize, set-timer, play-music, send-message, system-control, etc.
- Add a confirmation step for dangerous actions (allow_exec on/off and quick confirm in GUI).
- Improve fallback responses when intent is ambiguous and propose alternatives.

Priority: High
Assignee: Unassigned
