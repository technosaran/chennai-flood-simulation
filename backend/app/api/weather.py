"""Offline rainfall evaluation and historical replay endpoints."""
from datetime import date
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


@router.get('/weather/kaggle/evaluation')
def kaggle_evaluation(request: Request):
    model = request.app.state.kaggle_weather_predictor
    if model.model is None:
        raise HTTPException(503, 'Kaggle evidence unavailable. Run train_kaggle_weather.bat and restart the backend.')
    return dict(evaluation_status='verified', evaluation=model.report)


@router.get('/weather/kaggle/prediction')
def kaggle_replay(request: Request, as_of: date = date(2021, 11, 6)):
    model = request.app.state.kaggle_weather_predictor
    if model.model is None:
        raise HTTPException(503, 'Kaggle model unavailable. Run train_kaggle_weather.bat and restart the backend.')
    try:
        return model.replay(as_of.isoformat())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def predictor(request):
    model = request.app.state.weather_predictor
    if model.model is None:
        raise HTTPException(503, 'Weather artifacts unavailable or stale. Run the download and training commands.')
    return model


class DailyWeather(BaseModel):
    date: date
    PRECTOTCORR: float = Field(ge=0, le=2000, allow_inf_nan=False)
    T2M: float = Field(ge=-60, le=70, allow_inf_nan=False)
    RH2M: float = Field(ge=0, le=100, allow_inf_nan=False)
    WS10M: float = Field(ge=0, le=150, allow_inf_nan=False)
    PS: float = Field(ge=50, le=120, allow_inf_nan=False)


class WeatherHistory(BaseModel):
    history: list[DailyWeather] = Field(min_length=7, max_length=7)


@router.get('/weather/evaluation')
def evaluation(request: Request):
    model = predictor(request)
    return dict(evaluation_status='verified', evaluation=model.report,
                dataset=dict(rows=len(model.rows), start=min(model.rows), end=max(model.rows),
                             source_url='https://power.larc.nasa.gov/docs/services/api/temporal/daily/'),
                reproduce_command='python -m backend.ml_pipeline.download_weather && python -m backend.ml_pipeline.train_weather_model')


@router.get('/weather/prediction')
def replay(request: Request, as_of: date = date(2025, 12, 30)):
    try:
        return predictor(request).replay(as_of.isoformat())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post('/weather/predict')
def predict(body: WeatherHistory, request: Request):
    try:
        return predictor(request).predict([row.model_dump(mode='json') for row in body.history])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
