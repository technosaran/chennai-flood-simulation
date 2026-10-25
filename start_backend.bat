@echo off
setlocal
cd /d "%~dp0"
set "SIM_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "SIM_PYTHON=.venv\Scripts\python.exe"
echo Starting the simulation engine at http://localhost:8000
echo Default: deterministic demand model. Set ENABLE_ML=1 for optional trained models.
"%SIM_PYTHON%" backend\run_server.py
if errorlevel 1 echo Unable to start. Run setup_project.bat and check whether port 8000 is already in use.
pause
