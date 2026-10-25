@echo off
setlocal
cd /d "%~dp0"
set "SIM_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "SIM_PYTHON=.venv\Scripts\python.exe"
set "ENABLE_ML=0"
echo [1/4] Backend unit and API checks
"%SIM_PYTHON%" -m pytest backend\tests -q
if errorlevel 1 exit /b 1
echo [2/4] Integration checks - backend must be running on port 8000
"%SIM_PYTHON%" -m pytest e2e -q --strict-live
if errorlevel 1 exit /b 1
echo [3/4] Self-contained report checks
cd frontend
node --test tests/scenario-report.test.cjs
if errorlevel 1 exit /b 1
echo [4/4] Frontend production build - stop the dev server before running
call npm.cmd run build
if errorlevel 1 exit /b 1
echo All checks passed.
pause
