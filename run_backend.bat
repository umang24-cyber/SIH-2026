@echo off
REM ==============================================================================
REM BitKaun AML Forensics API - Windows Startup Script
REM ==============================================================================
echo =================================================================
echo   BitKaun AML Forensics Platform — Backend Server Startup (Windows)
echo =================================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

echo [+] Starting FastAPI server on http://0.0.0.0:8000 ...
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
