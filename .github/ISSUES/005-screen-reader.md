Title: Screen-reading / describe-screen feature

Description:
User wants the assistant to be able to "read the screen" and narrate or summarize what's visible.

Suggested approach / components:

- Use OCR (Tesseract via `pytesseract`) to capture text from screen regions.
- Use a lightweight CV model or heuristics to detect windows/controls and extract metadata (e.g., title bars, selected text areas).
- Add a permission/consent step before screen capture.
- Provide commands like "describe screen", "read selection", "summarize window".

Dependencies (optional):

- pytesseract
- pillow
- opencv-python

Priority: Medium
Assignee: Unassigned
