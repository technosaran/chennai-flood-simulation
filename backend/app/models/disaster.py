from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, model_validator
import math


class FloodZoneInput(BaseModel):
    id: str = "FZ-01"
    type: Literal["circle", "polygon", "preset"] = "circle"
    center: Optional[List[float]] = None  # [lat, lon]
    radius_meters: Optional[float] = Field(None, ge=50.0, le=25000.0)
    coordinates: Optional[List[Any]] = None  # [[lat, lon], ...] or [lat, lon]
    preset_key: Optional[str] = None
    initial_depth_m: Optional[float] = Field(None, ge=0.0, le=6.0)

    @model_validator(mode="after")
    def validate_geometry(self):
        def pair(value):
            return (isinstance(value, (list, tuple)) and len(value) == 2
                    and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                            and math.isfinite(v) for v in value))
        if self.type == "preset":
            if not self.preset_key:
                raise ValueError("A preset key is required.")
            return self
        if self.center is not None and not pair(self.center):
            raise ValueError("The center must be a finite [latitude, longitude] pair.")
        if self.type == "circle":
            coords = self.coordinates
            if self.center is None and not (pair(coords) or
                    isinstance(coords, list) and len(coords) == 1 and pair(coords[0])):
                raise ValueError("A circle needs one center coordinate.")
        else:
            coords = self.coordinates
            if not coords or not all(pair(p) for p in coords):
                raise ValueError("A polygon needs coordinate pairs.")
            ring = coords[:-1] if coords[0] == coords[-1] else coords
            if len({tuple(p) for p in ring}) < 3:
                raise ValueError("A polygon needs at least three distinct vertices.")
            area = sum(ring[i][0] * ring[(i+1) % len(ring)][1]
                       - ring[(i+1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))
            if abs(area) < 1e-10:
                raise ValueError("A polygon must enclose a nonzero area.")
            from backend.app.services.geometry import segments_intersect
            for i in range(len(ring)):
                for j in range(i + 1, len(ring)):
                    if j == i + 1 or (i == 0 and j == len(ring) - 1):
                        continue
                    if segments_intersect(*ring[i], *ring[(i+1) % len(ring)],
                                          *ring[j], *ring[(j+1) % len(ring)]):
                        raise ValueError("Polygon edges must not cross. Draw the boundary in order.")
        return self


class DisasterParameters(BaseModel):
    model_config = {"allow_inf_nan": False}
    rainfall_intensity_mm_hr: float = Field(65.0, ge=0.0, le=350.0)
    flood_depth_meters: float = Field(1.2, ge=0.0, le=6.0)
    spread_rate_meters_hr: float = Field(150.0, ge=0.0, le=2000.0)
    duration_hours: int = Field(6, ge=1, le=24)
    time_step_hours: float = Field(1.0, ge=0.25, le=6.0)


class RescueVehiclePool(BaseModel):
    model_config = {"allow_inf_nan": False}
    count: int = Field(0, ge=0, le=20)
    seats: int = Field(12, ge=1, le=100)
    speed_kmh: float = Field(20, ge=1, le=180)
    handling_minutes: float = Field(10, ge=5, le=60)
    ready_after_minutes: float = Field(0, ge=0, le=240)


class RescueFleetConfig(BaseModel):
    model_config = {"allow_inf_nan": False}
    continue_across_hours: bool = False
    anticipate_road_closures: bool = True
    enable_intermodal_transfers: bool = True
    destination_shelter_id: Optional[str] = Field(None, min_length=1, max_length=80)
    planning_window_minutes: float = Field(60, ge=15, le=240)
    base_location: tuple[float, float] = (13.0838, 80.2764)
    trucks: RescueVehiclePool = Field(default_factory=lambda: RescueVehiclePool(count=6, seats=24, speed_kmh=30))
    boats: RescueVehiclePool = Field(default_factory=lambda: RescueVehiclePool(count=4, seats=12, speed_kmh=15))
    helicopters: RescueVehiclePool = Field(default_factory=lambda: RescueVehiclePool(count=1, seats=6, speed_kmh=120))

    @model_validator(mode='after')
    def bounded_fleet(self):
        lat, lon = self.base_location
        if not (math.isfinite(lat) and math.isfinite(lon) and 12.8 <= lat <= 13.35 and 80 <= lon <= 80.4):
            raise ValueError('Fleet base must be within Chennai operational bounds')
        if sum(pool.count for pool in (self.trucks, self.boats, self.helicopters)) > 30:
            raise ValueError('At most 30 rescue vehicles are supported')
        return self


class SimulationRequest(BaseModel):
    rescue_fleet: Optional[RescueFleetConfig] = None
    planning_strategy: Literal['min_cost_flow', 'greedy'] = 'min_cost_flow'
    scenario_name: Optional[str] = "Chennai Flood Simulation Scenario"
    flood_zones: List[FloodZoneInput] = Field(default_factory=list)
    parameters: Optional[DisasterParameters] = None
    shelter_ids: Optional[List[str]] = None
    warehouse_ids: Optional[List[str]] = None


class FloodPolygonProperties(BaseModel):
    zone_id: str
    water_depth_m: float
    severity: Literal["advisory", "moderate", "severe", "catastrophic"]
    fill_color: str
    stroke_color: str
    fill_opacity: float
    time_step: int
