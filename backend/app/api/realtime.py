"""Opt-in external data. GET is strictly local; only POST refresh uses internet."""
from fastapi import APIRouter, Request

router = APIRouter()

@router.get('/realtime/cache')
def cached_data(request: Request):
    return request.app.state.realtime_data.snapshot()

@router.post('/realtime/refresh')
def refresh_data(request: Request):
    return request.app.state.realtime_data.refresh()
