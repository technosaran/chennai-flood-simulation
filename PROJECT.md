# Project: Chennai Natural Disaster (Flood) Simulation

Portable backup restoration (19 October 2026): full snapshot JSON exports can now be imported from Experiments into fresh immutable local records. Imports validate bounded file size, schema, timeline, geometry and display data; they preserve archived results without activating solver state. File-supplied evidence is identified in the library, opened view and HTML report. Verification: 115 backend tests, 95 strict live integration tests, five report tests, production build and browser download/import/reopen/report round-trip. See [portable import instructions](docs/SAVED_SIMULATIONS.md).

Complete simulation archive (19 October 2026): Experiments now supports named local SQLite snapshots containing full timelines, map/facility inputs, inventory, allocations, fleet plans and model evidence. Read-only reopening survives backend restarts; reports use archived evidence. New allocations require rerunning the loaded settings. Verified: 104 backend tests, 95 strict live integration tests, four report tests, production build and browser save/restart/reopen/export checks. See [saved simulation details](docs/SAVED_SIMULATIONS.md).

Rescue-fleet addition (18 October 2026): configurable dedicated trucks, boats and helicopters now have finite seats, readiness delays, loading/unloading time, repeat-trip availability and residual shelter reservations. Per-snapshot provisional fleet plans appear in Relief & Supplies / Impact & Analytics and report exports; experiments retain fleet settings. Ground assignments and the stock ledger remain separate. See [fleet model semantics](docs/RESCUE_FLEET.md). Backend suite: 99 passed; report suite: four passed.

Content/features completion (18 October 2026): bundled offline GCC wards / OSM rivers / modeled roads; searchable 200-ward atlas with explicit coverage limits and shelter proximity; selectable scenario comparison deltas; self-contained HTML report export with SVG map and print-to-PDF styling. Verified with 91 backend tests, 95 live integration tests, three report tests, production build and browser checks. See [feature and verification notes](docs/OFFLINE_ATLAS_AND_REPORTS.md).

ML completion (18 October 2026): downloaded 9,131 NASA POWER daily Chennai weather records, trained and evaluated a 180-tree next-day rainfall classifier on chronological splits, retrained the 128-tree/Ridge relief-demand blend with event-based cross-validation, fixed deployed-artifact evaluation provenance, and added typed weather APIs plus dashboard historical replay. Verification: 87 backend tests, 95 strict live API tests, production build, and browser replay pass. See [training and measured results](docs/TRAINING_AND_RESULTS.md). Rainfall metrics are real sourced gridded reanalysis hindcasts; relief-demand labels remain synthetic.

Current verification (15 October 2026): 81 backend tests, 95 strict live API tests and the production frontend build pass. The original milestone table below is retained as planning history. See [current verification](docs/VERIFICATION_2026-10-15.md) and [panel preparation](docs/PANEL_PREPARATION.md) for implemented modules, demonstrated flows and limitations.

## Architecture
A decoupled full-stack architecture consisting of a Next.js frontend and a Python FastAPI backend communicating via RESTful HTTP API.
- **Frontend**: Next.js (App Router, TypeScript, Tailwind CSS, Lucide icons, Leaflet with OpenStreetMap tiles loaded with `{ ssr: false }`). Renders interactive maps, vector overlays, flood simulation controls, playback timeline slider, and supply chain inventory panels.
- **Backend**: Python 3.12 REST API using FastAPI and Uvicorn. Powered by NetworkX for dynamic road graph routing and Google OR-Tools / greedy solvers for shelter and supply allocations. Uses pure-Python geometry/Haversine distance (no SciPy dependency due to system NumPy compatibility) and bundles pre-compiled Chennai road network, shelter, warehouse, and population datasets in `backend/app/data/`.
- **Data Flow**:
  1. Frontend loads initial map state, shelters, warehouses, and distribution points via `GET /api/map/init`.
  2. User configures disaster scenario (draws flood polygon, selects radius/preset, sets rainfall intensity, flood depth, spread rate) and clicks "Run Simulation".
  3. Frontend sends payload to `POST /api/simulation/run`.
  4. Backend computes spatio-temporal flood progression across discrete time steps $t=0..T$, dynamically updates road graph edge weights, calculates safe evacuation routes to capacitated shelters, solves supply chain delivery routes from warehouses to distribution centers, and returns unified GeoJSON and metrics.
  5. Frontend receives simulation results and enables interactive playback, route overlays, shelter capacity inspectors, and resource allocation tracking.
  6. User can trigger dynamic resource reallocations via `POST /api/resources/allocate`.

## Code Layout
- `backend/`:
  - `app/main.py`: FastAPI application entry point, CORS, routers.
  - `app/api/`: REST API route handlers (`health.py`, `map.py`, `simulation.py`, `resources.py`).
  - `app/models/`: Pydantic request/response schemas (`disaster.py`, `evacuation.py`, `logistics.py`, `geojson.py`).
  - `app/services/`:
    - `flood_engine.py`: Spatio-temporal flood dilation and depth decay model.
    - `road_network.py`: Chennai OSM road graph loader, spatial index, dynamic inundation weight adjuster.
    - `evacuation_solver.py`: Dynamic A*/Dijkstra evacuation pathfinder and capacity-constrained shelter assigner.
    - `supply_solver.py`: Supply distribution pathfinder and resource inventory allocation ledger.
  - `app/data/`:
    - `chennai_roads.json`: Bundled arterial road network for Chennai.
    - `shelters.json`: 12 verified public shelters with geographic coordinates and capacities.
    - `warehouses.json`: 5 strategic relief depots with initial supply inventories.
    - `distribution_points.json`: 10 relief distribution points across flood plains.
    - `population_clusters.json`: Population density points for vulnerable Chennai wards.
  - `tests/`: Pytest unit and API test suite.
  - `requirements.txt`: Python dependencies.
- `frontend/`:
  - `src/app/page.tsx`: Main dashboard and layout.
  - `src/app/layout.tsx`: Root layout and metadata.
  - `src/components/map/`:
    - `MapContainer.tsx`: Dynamic Leaflet map wrapper (`ssr: false`).
    - `TileLayer.tsx`: OpenStreetMap tile provider.
    - `FloodOverlay.tsx`: Spatio-temporal flood polygon and buffer rendering.
    - `EvacuationOverlay.tsx`: Safe evacuation routes and shelter markers with capacity badges.
    - `SupplyOverlay.tsx`: Warehouses, distribution points, and supply route lines.
    - `PopulationHeatmap.tsx`: Population density visualization.
  - `src/components/controls/`:
    - `DisasterControls.tsx`: Rainfall, intensity, flood depth sliders and preset buttons.
    - `TimelinePlayer.tsx`: Play/pause, scrub slider, time-step step controls ($t=0..T$).
    - `ResourcePanel.tsx`: Inventory tracking (water, food, medicine) and allocation status.
  - `src/lib/api.ts`: Typed HTTP client for backend REST API.
  - `src/lib/types.ts`: TypeScript schemas matching backend Pydantic models.
  - `package.json`, `tailwind.config.js`, `tsconfig.json`.
- `e2e/`:
  - E2E test harness and test cases (Tiers 1-4) verifying end-to-end functionality.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Chennai Map Foundation | Interactive Leaflet map centered on Chennai [13.0827, 80.2707] with OSM tiles | M2 | R1, AC-1 |
| 2 | Flood Zone Drawing & Selection | Interactive polygon drawing, circle radius (500-5000m), and historical presets (Velachery, Adyar, Mudichur, T. Nagar) | M2 | R1, AC-2 |
| 3 | Disaster Parameter Controls | UI controls for rainfall intensity (1-5), flood depth (0.1-3.0m), and spread rate | M2 | R1, AC-3 |
| 4 | Spatio-Temporal Flood Simulation | Backend engine calculating time-series flood spread (t=0..T) with color-coded intensity | M1 | R1, AC-4, AC-5 |
| 5 | Simulation Timeline & Playback | Frontend timeline slider, play/pause, step controls for disaster progression | M2 | R1, AC-6 |
| 6 | Chennai Road Network Graph | Bundled Chennai road network graph with arterial corridors and bridges | M1 | R2, AC-7 |
| 7 | Dynamic Flood Avoidance Routing | Evacuation route calculation avoiding roads with flood depth >= 0.5m | M1 | R2, AC-7 |
| 8 | Evacuation Route Overlays | Map visualization of safe evacuation routes with safety indicators | M2 | R2, AC-7 |
| 9 | Population Density Heatmap | Population density layer for vulnerable wards (T. Nagar, Velachery, Saidapet, etc.) | M2 | R2, AC-8 |
| 10 | Shelter Capacity Management | 12 Chennai shelters with total capacity, current occupancy, and status indicators | M1 | R2, AC-9 |
| 11 | Evacuee-to-Shelter Allocation | Capacity-constrained allocation algorithm assigning evacuees to nearest available shelters | M1 | R2, AC-10 |
| 12 | Shelter Assignment UI & Badges | Interactive shelter markers displaying assigned population count vs. capacity | M2 | R2, AC-10 |
| 13 | Supply Warehouses & Distribution Points | 5 relief depots and 10 distribution centers with locations and metadata | M1 | R3, AC-11 |
| 14 | Warehouse & Distribution Map Markers | Visual map markers for warehouses, depots, and distribution camps | M2 | R3, AC-11 |
| 15 | Flood-Avoidant Supply Routing | Logistics pathfinding from warehouses to distribution points avoiding flood zones | M1 | R3, AC-12 |
| 16 | Supply Route Map Overlays | Visual paths showing active supply distribution routes | M2 | R3, AC-12 |
| 17 | Resource Inventory Tracking | Ledger tracking food rations, water litres, and medical kits (total, available, allocated) | M1 | R3, AC-13 |
| 18 | Resource Inventory UI Panel | Collapsible/docked UI dashboard showing supplies and allocation status | M2 | R3, AC-13 |
| 19 | Dynamic Resource Allocation API | Endpoint and UI controls to allocate specific supplies to shelters/distribution points | M1, M2 | R3, AC-14 |
| 20 | REST API Architecture | FastAPI endpoints (/api/health, /api/map/init, /api/simulation/run, /api/resources/allocate) | M1 | R4, AC-15, AC-16 |
| 21 | Full-Stack Integration Flow | Complete end-to-end user loop (configure scenario -> run -> view playback, routes, allocations) | M3 | R4, AC-17 |
| 22 | Modern & Responsive UI/UX | High-polish dark/light UI, responsive sidebar, smooth animations, status indicators | M2 | R4, AC-18 |
| 23 | E2E Testing Suite (Tiers 1-4) | Comprehensive test suite covering feature, boundary, pairwise, and application scenarios | M-E2E | VP-1, VP-2 |
| 24 | Adversarial Coverage Hardening | White-box stress-testing, extreme boundary cases, and forensic integrity audit | M-FINAL | VP-3, VP-4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M-E2E | E2E Testing Track | Independent requirement-driven test suite (Tiers 1-4), TEST_INFRA.md, TEST_READY.md | none | PLANNED |
| M1 | Python Backend Engine | FastAPI REST API, Chennai road network, flood engine, evacuation solver, supply solver, unit tests | none | PLANNED |
| M2 | Next.js Frontend Platform | App Router, Leaflet OSM map, flood drawing/controls, timeline player, route/shelter/supply overlays, inventory panel | none | PLANNED |
| M3 | Full-Stack Integration | Wiring frontend to backend, end-to-end scenario execution, cross-tier integration testing | M1, M2 | PLANNED |
| M-FINAL | E2E Pass & Adversarial Hardening | Pass 100% of E2E test suite (Tiers 1-4), Tier 5 adversarial stress testing with Challenger, Forensic Integrity Audit | M-E2E, M3 | PLANNED |

## Interface Contracts

### 1. GET `/api/health`
- **Response**: `{ "status": "ok", "service": "chennai-flood-sim", "version": "1.0.0" }`

### 2. GET `/api/map/init`
- **Response**:
  - `center`: `[13.0827, 80.2707]`
  - `bounds`: `[[12.85, 80.10], [13.25, 80.35]]`
  - `shelters`: List of `{ id, name, location: [lat, lon], capacity, current_occupancy, amenities }`
  - `warehouses`: List of `{ id, name, location: [lat, lon], supplies: { water_litres, food_rations, medical_kits } }`
  - `distribution_points`: List of `{ id, name, location: [lat, lon], target_ward, demand: { water_litres, food_rations, medical_kits } }`
  - `population_clusters`: List of `{ id, name, location: [lat, lon], estimated_population, risk_level }`
  - `presets`: List of historical scenario presets (e.g., Velachery 2015, Adyar Basin, Chembarambakkam outflow)

### 3. POST `/api/simulation/run`
- **Request**:
  - `flood_zones`: List of `{ id, type: "polygon"|"circle", coordinates: [[lat, lon], ...], radius_meters?: number }`
  - `parameters`: `{ rainfall_intensity_mm_hr: number, flood_depth_meters: number, spread_rate_meters_hr: number, duration_hours: number }`
- **Response**:
  - `simulation_id`: string
  - `timeline`: List of time step objects ($t=0..T$) with:
    - `time_step`: integer (hour)
    - `flood_polygons`: GeoJSON FeatureCollection of inundation zones with depth and severity level (`advisory`, `moderate`, `severe`, `catastrophic`)
    - `evacuation_routes`: GeoJSON FeatureCollection of LineStrings (origin to shelter, distance_km, estimated_time_min, status: `clear`|`warning`|`rerouted`)
    - `shelter_allocations`: List of `{ shelter_id, name, allocated_evacuees, remaining_capacity, status: "available"|"near_capacity"|"full" }`
    - `supply_routes`: GeoJSON FeatureCollection of LineStrings (warehouse to distribution point/shelter, distance_km, transit_time_min)
    - `inventory_status`: `{ total_water_litres, allocated_water_litres, total_food_rations, allocated_food_rations, total_medical_kits, allocated_medical_kits }`
    - `isolated_clusters`: List of `{ cluster_id, name, location: [lat, lon], trapped_population, requires_airlift: boolean }`

### 4. POST `/api/resources/allocate`
- **Request**: `{ shelter_or_point_id: string, supplies: { water_litres: number, food_rations: number, medical_kits: number } }`
- **Response**: `{ success: boolean, updated_inventory: object, allocation_details: object }`
