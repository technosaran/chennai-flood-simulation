"""Explicit save and view-only reopening. Never activates saved inventory."""
from copy import deepcopy
import sqlite3
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field, field_validator
from backend.app.models.disaster import SimulationRequest, DisasterParameters
from backend.app.services.simulation_archive import SimulationArchive, ArchiveCorrupt
from backend.app.services.snapshot_import import MAX_IMPORT_BYTES, parse_snapshot

router = APIRouter()


class SaveSnapshot(BaseModel):
    simulation_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=80)

    @field_validator('name')
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Enter a snapshot name')
        return value


def store(request):
    return getattr(request.app.state, 'simulation_archive', None) or SimulationArchive()


@router.get('/simulations/saved')
def list_snapshots(request: Request, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    try:
        return store(request).list(offset, limit)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, 'Local archive storage is unavailable. Check backend/storage permissions.') from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(409, 'The local archive index is damaged. Restore it from a database backup.') from exc


@router.post('/simulations/saved')
def save_snapshot(body: SaveSnapshot, request: Request):
    with request.app.state.simulation_lock:
        result = getattr(request.app.state, 'latest_simulation', None)
        if result is None or result['simulation_id'] != body.simulation_id:
            raise HTTPException(409, 'This scenario is no longer active. Run it again before saving a complete snapshot.')
        from backend.app.api.map import get_map_init
        from backend.app.api.resources import get_resource_state
        from backend.app.api.evaluation import model_evaluation
        from backend.app.api.weather import evaluation as weather_evaluation
        original = SimulationRequest.model_validate(result['scenario'])
        parameters = DisasterParameters.model_validate(result['scenario']['parameters'])
        resolved = request.app.state.flood_engine.resolve_flood_zones(original.flood_zones, parameters)
        zones = [dict(id=z['id'], name=z['id'], type=z['type'],
                      coordinates=z['initial_coordinates'] if z['type'] == 'polygon' else [z['center']],
                      **({'radius_meters': z['initial_radius']} if z['type'] == 'circle' else {})) for z in resolved]
        display = parameters.model_dump()
        display['rainfall_intensity_mm_hr'] = {25: 1, 50: 2, 90: 3, 140: 4, 220: 5}.get(parameters.rainfall_intensity_mm_hr, parameters.rainfall_intensity_mm_hr)
        map_data = {**get_map_init(request), **get_resource_state(request)}
        try:
            weather = weather_evaluation(request)
        except HTTPException:
            weather = {'evaluation_status': 'unavailable_at_save_time'}
        snapshot = deepcopy(dict(schema_version=1, result=result, map_data=map_data,
                                 view=dict(parameters=display, zones=zones),
                                 evidence=dict(demand=model_evaluation(request), weather=weather)))
    try:
        return store(request).save(body.name, snapshot)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, 'The snapshot could not be saved locally. Export the current result as JSON and check backend/storage permissions.') from exc


@router.post('/simulations/saved/import')
async def import_snapshot(request: Request):
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_IMPORT_BYTES:
            raise HTTPException(413, 'Snapshot files must be 10 MB or smaller')
        raw.extend(chunk)
    try:
        name, snapshot = parse_snapshot(bytes(raw))
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError) as exc:
        raise HTTPException(422, 'Invalid full snapshot JSON. ' + str(exc)[:240]) from exc
    try:
        return store(request).save(name, snapshot)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, 'The imported snapshot could not be saved locally. Check backend/storage permissions.') from exc


@router.get('/simulations/saved/{snapshot_id}')
def read_snapshot(snapshot_id: str, request: Request):
    try:
        snapshot = store(request).get(snapshot_id)
    except ArchiveCorrupt as exc:
        raise HTTPException(409, str(exc)) from exc
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, 'Local archive storage is unavailable.') from exc
    if snapshot is None:
        raise HTTPException(404, 'Saved simulation not found')
    return snapshot
