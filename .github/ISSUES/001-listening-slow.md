Title: Listening is slow — improve latency

Description:
The GUI/stt currently feels slow to respond: there is a noticeable lag between speaking and the recognized text appearing or the assistant acting. Steps to reproduce:

1. Run the GUI (python -m voice_assistant.gui)
2. Speak a short command ("open spotify")
3. Observe the time to recognized text and response

Suggested improvements:

- Use Vosk partial results (rec.PartialResult) to show live transcription in the GUI while audio is streaming.
- Move expensive calls (LLM, TTS) to a dedicated worker pool and add timeouts.
- Consider reducing sample blocksize or experimenting with sounddevice settings for lower latency.

Priority: High
Assignee: Unassigned
