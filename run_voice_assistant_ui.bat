@echo off
REM Batch launcher for the voice assistant GUI
REM Change to the batch file directory (project root)
cd /d "%~dp0"

REM Try common virtualenv locations first so double-click uses the project's interpreter
if exist ".venv\Scripts\python.exe" (
	".venv\Scripts\python.exe" -m voice_assistant.gui %*
	goto :eof
)
if exist "venv\Scripts\python.exe" (
	"venv\Scripts\python.exe" -m voice_assistant.gui %*
	goto :eof
)
if exist "Scripts\python.exe" (
	"Scripts\python.exe" -m voice_assistant.gui %*
	goto :eof
)

REM Fallback to Python launcher or system python
py -3 -m voice_assistant.gui %* 2>nul || python -m voice_assistant.gui %*
