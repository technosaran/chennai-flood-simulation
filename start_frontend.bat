@echo off
setlocal
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo Dependencies are missing. Run setup_project.bat first.
    pause
    exit /b 1
)
echo Opening the development dashboard at http://localhost:3000
call npm.cmd run dev
pause
