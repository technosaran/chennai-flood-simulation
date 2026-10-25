@echo off
title Chennai Flood Lab - 1-Click Launcher
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_project.ps1"
