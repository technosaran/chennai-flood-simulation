@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r backend\requirements-core.txt
if errorlevel 1 exit /b 1
cd frontend
call npm.cmd install
if errorlevel 1 exit /b 1
echo Setup complete. Run start_project.bat to launch both services.
pause
