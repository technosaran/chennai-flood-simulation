@echo off
setlocal
cd /d "%~dp0"
set "TRAIN_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "TRAIN_PYTHON=.venv\Scripts\python.exe"
"%TRAIN_PYTHON%" -m pip install -r backend\requirements-training.txt
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.generate_dataset
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.download_weather
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.train_weather_model
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.train_demand_ensemble
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.train_kaggle_weather
if errorlevel 1 exit /b 1
"%TRAIN_PYTHON%" -m backend.ml_pipeline.evaluate_portable_model --save
if errorlevel 1 exit /b 1
echo Training and evaluation complete. Restart the backend to load the new models.
endlocal
