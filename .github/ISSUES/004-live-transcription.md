Title: Live transcription (auto-type as I speak)

Description:
User requested that the GUI auto-start typing in the recognized entry as they speak (live partials), instead of waiting for final result.

Suggested implementation:

- Use Vosk partial results via `rec.PartialResult()` and expose a callback from `stt.listen()` for partials.
- In GUI, update the bottom recognized entry on each partial result; on final result, commit and process.
- Provide a toggle to enable/disable live transcription to the entry.

Priority: High
Assignee: Unassigned
