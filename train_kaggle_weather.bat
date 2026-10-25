@echo off
setlocal
cd /d "%~dp0"
set "TRAIN_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "TRAIN_PYTHON=.venv\Scripts\python.exe"
"%TRAIN_PYTHON%" -m pip install -r backend\requirements-training.txt
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.train_kaggle_weather %*
if errorlevel 1 exit /b 1
echo Kaggle download, model selection, evaluation and portable inference checks complete.
echo Restart the backend to load the verified model.
endlocal
