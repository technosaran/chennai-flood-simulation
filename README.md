# Chennai Flood Lab

An academic Chennai flood-response simulation built with Next.js, Leaflet and a Python/FastAPI engine. Define a flood zone, configure conditions, then explore estimated flood progression, evacuation assignments and relief logistics on a map.

This is a **scenario simulation**, with estimated population and hydrology. It does not monitor live floods, notify citizens, or dispatch emergency services. No authentication or paid API key is required. After installation/build, the dashboard, bundled reference map and trained models work without internet. Online street tiles are an optional map control; initial dependencies/fonts and reference-data refreshes need internet.

## Start on Windows

Prerequisites: Node.js 20+ and Python 3.10+.

1. Run `setup_project.bat` once to create a Python virtual environment and install the core/backend and frontend dependencies.
2. Run `start_project.bat` to start both services in the background. Startup logs are in `logs/`.
3. Open [the dashboard](http://localhost:3000). [API documentation](http://localhost:8000/docs) is also available.

For terminal logs, run `start_backend.bat` and `start_frontend.bat` in separate terminals. The launchers never kill unrelated services occupying a port.

## Real-time data switch and offline presentations

The header's **Real-time OFF / ON** switch is off whenever the dashboard starts. Off uses the local simulator and reads the last saved weather/notice snapshot from this computer without refreshing external sources. On downloads Chennai weather model estimates from [Open-Meteo](https://open-meteo.com/en/docs) and recent Chennai/Tamil Nadu text matches from [NDMA SACHET RSS](https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml), refreshing every five minutes. No API key is required. Internet is required for downloads; the Python backend is still required for local simulation.

Each provider shows download/model/issue times in IST and independent unavailable, cached or stale states. Failures retain the last successful download in `backend/storage/realtime_cache.json`. A fresh weather source can remain usable when the alert feed fails. RSS notices are issued within 24 hours and may already have expired; they are not asserted to be active Chennai warnings or complete geographic coverage. Weather is model data, not a rain-gauge or flood-sensor feed.

**Use hourly rainfall in scenario** explicitly applies the latest preceding-hour precipitation as a constant mm/hour scenario setting. It pauses automatic reruns and requires review/run. It never changes flood depth, spread, vehicles or active results automatically. Exact low readings such as 1–5 mm/hour retain physical units rather than becoming legacy preset levels. Stale data and offline mode cannot apply online rainfall.

For college: enable On while connected to download a snapshot, then turn Off and use local scenarios. Saved data keeps its original timestamps. Turning Off cancels browser polling; an already-started server request may finish. Reloading returns to Off. The optional online map-tile control remains separate; **Load online street tiles / Use offline map** controls basemap access.

API: `GET /api/realtime/cache` reads only local cache; `POST /api/realtime/refresh` requests provider updates (five-minute rate limit per provider). Normal startup performs no weather/alert download. TLS certificate and hostname verification remain enabled, using native system roots through `truststore` when available.

## Use the simulation

The light-theme dashboard guides you through **Choose a scenario → Review and run → Understand results**. Start with one of six example cards, choose rainfall and duration, then review and run. Advanced settings contain custom zone drawing, flood depth/spread, rescue vehicles, and optional automatic reruns (off by default). The map is a compact preview; use **Map & routes → Expand map** for detailed mapping.

Results open at peak modeled exposure. **Summary** explains the selected hour and provides an hourly chart. **Shelters & supplies** distinguishes hourly shelter plans from accumulated inventory. **Save analysis** opens the existing local snapshot library; **Download report** exports the existing self-contained report. Edited settings preserve previous results with an outdated warning and disable allocations/saving/export until rerun. Saved snapshots remain read-only. Navigation: **New analysis**, **Saved analyses**, **Models & datasets**, and **More tools** (Ward Atlas, detailed analysis, reservoirs, scenario advice). Keyboard shortcuts: 1 new analysis, 2 saved analyses, 3 models, R review before running, arrows/Space timeline controls, ? help with shortcuts.

## Accuracy and fleet route update (24 October 2026)

The Kaggle classifier now selects its cutoff and model using **validation accuracy** by default. The held-out 2021-2022 benchmark is **90.27% accuracy (501/555 days)**, 69.39% balanced accuracy, 57.78% precision and 42.62% recall. The always-low-rainfall baseline has 89.01% accuracy. This is next-day rainfall classification, not 90% flood/rescue accuracy. The higher accuracy setting misses 35 of 61 elevated-rainfall days. Use `train_kaggle_weather.bat --objective balanced_accuracy` for the alternative selection objective. No missing rainfall values are filled in and test rows are excluded from selection.

Unused rescue vehicles now show why no trip was allocated (pickup depth, screened road access, shelter space, readiness, or travel/handling time). “Ready” only describes vehicle availability at window end. Increasing the window or moving the base closer may permit trips; flooded truck access is still rejected. Planned rescue trips now appear on Map & routes with the Evacuation & rescue layer enabled. Truck lines follow the screened road geometry; boat and air lines are provisional direct-distance proxies. Rerun old analyses to populate the new geometry and diagnostics.

## Kaggle Chennai dataset and automatic training

Run `train_kaggle_weather.bat` to download the [Kaggle Indian cities weather archive](https://www.kaggle.com/datasets/vanvalkenberg/historicalweatherdataforindiancities), extract Chennai records, compare Gradient Boosting, Random Forest and Extra Trees, select a model on validation years, evaluate on held-out years and export portable inference. Add `--refresh` to download again. No Kaggle credential is required for this public archive. Cached data supports offline retraining after dependencies are installed.

The dataset has daily average temperature and rainfall; incomplete seven-day windows and missing target rainfall are excluded. Training ends in 2015, validation uses 2016–2020, and testing uses 2021 onward, with eight-day gaps between splits. The wider validation interval is necessary because this archive is sparse in those years. The target is next-day rainfall ≥10 mm/day, not flood depth or relief demand. Uploader station provenance has not been independently audited. View actual selected-model metrics, excluded-window counts, candidate comparisons and historical replay in **Models & datasets**. API endpoints: `/api/weather/kaggle/evaluation` and `/api/weather/kaggle/prediction?as_of=2021-11-06`. Model and dataset fingerprints are verified before evidence is served; restart the backend after training.

`train_models.bat` now includes this portable Kaggle workflow. The legacy `train_advanced_models` experiment requires extra PyTorch/XGBoost dependencies and is no longer invoked by the core training launcher.

- Choose a preset or create a custom circle / polygon. Click at least three map points and choose **Finish zone** for a polygon.
- Adjust rainfall level, peak depth, spread rate and duration (1–12 hours), then choose **Run simulation**.
- Use the timeline slider, hour buttons, playback and speed controls to inspect each hour. Toggle individual map layers. Click a route for computed distance, travel time, transport mode and cargo/person count.
- Select a shelter or distribution point to allocate supplies. The dialog shows the selected depot's remaining stock. Manual allocations apply to the final simulation hour and add their routes to the map.
- Export the results as JSON for a project report, or reset to start a fresh scenario. Scenario changes require another run before allocation/export.
- On mobile, switch between **Map**, **Scenario**, and **Resources**.

## Complete saved simulations

Open **Experiments → Saved simulations**, enter a snapshot name and choose **Save complete simulation** after running the scenario. Saving captures the active engine result, including any manual allocations already recorded, the complete timeline, fleet plans, facility/map inputs and model evaluation evidence. Each save creates an immutable snapshot; later allocations do not modify earlier saves.

Choose **Open saved view** to reopen the map and timeline after restarting, or **Download snapshot JSON** for a portable backup. Reopened views are explicitly read-only and do not replace the engine's active inventory. Rerun the loaded settings to make new allocations. The HTML report uses the archived physical parameters and evaluation evidence when exporting a saved view. Background reference vectors come from the locally bundled map data.

To restore a downloaded full snapshot, select it under **Snapshot JSON file** and choose **Import snapshot JSON**. Files up to 10 MB are validated and stored as new read-only copies; existing snapshots and active inventory are preserved. Imported views and reports identify file-supplied evidence as not independently verified. Summary/telemetry exports are not full snapshot backups.

Snapshots are stored in `backend/storage/simulations.sqlite3`, using SQLite transactions, gzip compression and SHA-256 integrity checks. This directory is ignored by Git. Back up the database while the backend is stopped; keep it with the project to retain saved runs. Set `SIM_ARCHIVE_DB` before starting the backend to select another local database path. Browser comparison summaries and full database snapshots are separate features. Internet is not required; the local backend must be running to access saved snapshots.

API: `POST /api/simulations/saved` with `simulation_id` and `name`; `GET /api/simulations/saved?offset=0&limit=20`; `GET /api/simulations/saved/{snapshot_id}`. Saving a scenario replaced on the engine returns 409. Opening a corrupt snapshot reports an error without changing the active scenario.

Import API: `POST /api/simulations/saved/import` with the full snapshot JSON as the request body. Invalid/incomplete snapshots return 422; files exceeding 10 MB return 413. A successful import returns the new local snapshot ID.

## Continuing rescue allocation

New dashboard analyses enable **Advanced settings → Limited rescue fleet → Continue rescues across hours**. Each run owns one rescue schedule: vehicles keep their busy/return times, passengers committed to a journey are excluded from later ground/rescue assignment, and shelter seats remain reserved. Arrivals count as **simulated shelter arrivals** only after final unloading. The panel separates cumulative arrivals, committed passengers not yet arrived, new assignments and remaining unassigned demand. Readiness delays apply from run start, not again each hour.

New departures are booked only before the next timeline step and must deliver within the configured lookahead window. At the final timestamp no new departures are added; journeys already scheduled may remain pending beyond the displayed scenario. Existing journeys retain their departure-time routes and travel times. A shelter that later becomes compromised shows a warning; future route safety and relocation are not simulated. Ground assignments are still recomputed each hour, with rescue commitments and shelter reservations deducted. Completed rescue arrivals increase shelter occupancy and relief demand.

Vehicle coordinates/activity describe the selected simulation timestamp. Trip times and rescue playback use absolute minutes from run start; selecting a later hour starts replay at that hour rather than at zero. Reports label cumulative values and list each new handoff journey once. Historical snapshots without this mode remain independent plans. To compare the old behavior, turn the checkbox off. API callers opt in with `rescue_fleet.continue_across_hours=true`; omission preserves legacy independent planning.

## Boat-to-truck transfers, fleet advice and playback

Rescue fleet settings now enable coordinated boat → truck journeys by default. The planner samples dry roadside nodes near flooded pickups, screens each truck leg and its endpoint connectors, reserves both vehicles, waits until the boat has unloaded before loading the truck, and reserves dry shelter space. People count once at final shelter unloading; a paired journey has two vehicle trips. Boat launch/landing access and dry staging are assumptions, not verified facilities. Each hourly plan remains independent.

Choose **Advanced settings → Limited rescue fleet → Rescue destination** to restrict rescue arrivals to one shelter, or leave all dry shelters available. Ground evacuation destinations remain independent. Results show transfer-point coordinates, vehicle-leg schedules, the number of people planned through handoffs, and recommendations for planning time, shelter capacity and fleet capacity. Additional vehicle counts are rough throughput extrapolations and can exceed the simulator's 30-vehicle limit; they are not promised outcomes.

Under **Map & routes**, enable **Evacuation & rescue**, then use **Play rescue replay**, the speed selector or the rescue-minute slider. Colored vehicle dots follow scheduled loading, travel, handoff waiting, unloading and return phases. The replay starts paused, includes returns beyond the planning window, and is separate from the hourly flood timeline. Old snapshots keep their routes and omit animation when phase data is absent. HTML scenario reports include rescue geometry, paired journeys and recommendations.

For a handoff demonstration, keep **Velachery 2015**, select **Jawaharlal Nehru Stadium** as the rescue destination, set the window to **240 minutes**, boats to **8 km/h** with **5-minute** handling, trucks to **30 km/h** with **5-minute** handling, and helicopters to **0**. Keep the default six 24-seat trucks and four 12-seat boats. With independent snapshot mode and the bundled planning road graph, this plans **48 people via four boat → truck journeys (eight vehicle trips)** per snapshot. With continuation enabled, those journeys persist and later hours show their arrivals and subsequent vehicle reuse. These are demonstration assumptions, not calibrated operating speeds or resource availability.

## Rescue fleet configuration

Open **Scenario → Limited rescue fleet** to configure dedicated trucks, boats and helicopters: counts, seats, planning speed, loading/unloading time, readiness delay, a shared base and a 15–240-minute planning window. Defaults are six 24-seat trucks, four 12-seat boats and one six-seat helicopter; these are project assumptions, not real available vehicles. A maximum of 30 vehicles is supported. Set all counts to zero to test unavailable rescue support.

Run the scenario, choose a timeline hour, then open **Relief & Supplies** or **Impact & Analytics** for **Rescue fleet availability**. The panel reports demand, provisionally served people, remaining support need, vehicle readiness, individual trip schedules and reasons for unserved demand. Vehicles return to base before another trip. Destinations need dry residual shelter space after ground assignments. Trucks need a screened road path; boats require modeled water depth of at least 0.30 m at pickup. Boat/air travel uses direct-distance proxies with unverified access conditions.

Each hour starts an independent plan under frozen flood conditions; vehicle activity is not carried between snapshots. Fleet reservations do not execute rescues, change ground-assignment totals, allocate relief stock or constrain the separate cargo fleet. Reports export fleet outcomes/configuration. Experiments save and restore fleet settings and compare independent peak fleet metrics. The API accepts optional `rescue_fleet` on `POST /api/simulation/run`; omitting it retains ground-only planning and returns no fleet plan.

## Offline atlas and reporting

- The map loads OpenStreetMap street tiles with an automatic offline fallback: 200 GCC wards, 37,138 OSM main-street segments and bundled rivers. Routes use a separate imported street graph, including residential roads and footpaths (178,798 junctions/endpoints, 449,548 directed edges). Route geometry follows OSM curves. See [road data and limitations](docs/ROAD_NETWORK.md).
- **Ward Atlas** searches all 200 ward numbers and modeled locality names. Profiles show included modeled population points, three nearby planning shelters, baseline spaces, amenities, an inclusive planning checklist and cited sources. Population totals, vulnerable-group counts and ward-specific flood histories are unavailable unless explicitly provided; missing coverage is not zero risk. Shelter distances are straight-line proximity, not safe route distances. Eight wards contain the project's population-cluster points; two modeled points fall outside the published GCC polygons.
- **Experiments → Baseline → comparison** selects two saved runs and shows signed differences and percentage changes in peak exposure, assignments, rescue need and maximum flood area. Changing geography or duration affects interpretation. Peaks may occur at different hours. Eight summaries/settings persist in this browser; full results are not stored there.
- **Experiments → Download scenario report** exports a self-contained HTML document with an embedded SVG map, scenario inputs, hourly results, final resource shortages, model evidence and sources. It opens offline. Use your browser's **Print → Save as PDF** for submission. Run changed settings again before exporting. Model evidence is marked unavailable when its API cannot be reached; the current run still exports.

Reference sources: [GCC ward-boundary service](https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCPublic/GCC_AdminBoundary/MapServer/4), [OpenStreetMap attribution](https://www.openstreetmap.org/copyright), [CAG Chennai flood audit](https://cag.gov.in/ag1/tamil-nadu/en/audit-report/details/45722). Download metadata and file hashes are in `frontend/public/data/reference_manifest.json`. Refresh references with `python -m backend.app.data.build_reference_data`; this also rebuilds offline ward profiles. The source does not supply an effective ward-boundary date.

## Final-year review

Open **Project Review** in the dashboard for verified deployed-model evaluation, current-run ML/rule counts, 15 searchable viva questions and a downloadable panel guide. Complete runs are recorded by the experiment notebook even while another view is open. See [the submission and demo guide](docs/PANEL_PREPARATION.md).

To regenerate the dashboard's evaluation evidence, run `python -m backend.ml_pipeline.evaluate_portable_model --save`. The API checks model and dataset SHA-256 fingerprints before displaying metrics. If either artifact changes, stale evaluation is withheld. This evaluates synthetic relief demand, not real flood prediction accuracy.

## Model assumptions

- Presets are inspired by historical events; they are not calibrated reconstructions. The road graph uses a bundled OpenStreetMap snapshot, not a live road or traffic feed. Population figures and facility stock/capacity are modeled inputs. The Mylapore/Marina cluster represents coastal settlements.
- Flood depth begins at 10% of configured peak, reaches peak at 60% of the duration, and spreads according to rainfall and spread rate. Circular zones use approximate terrain anchors; drawn polygons use a conservative interior depth. Overlapping flood envelopes are counted separately in the estimated area.
- Each timeline step computes an independent shelter-assignment plan for that hour. People assigned at one hour are not permanently removed from the population in later snapshots. The supply ledger accumulates allocations across the run and resets when a new simulation starts.
- Roads close at modeled depth of 0.50 m for evacuation and 0.30 m for trucks. Unreachable destinations use modeled amphibious or air delivery options. Ground-level access and elevated road clearance are checked separately.
- Top-level API summary corridors are screened against the entire timeline. A dry route suffix may be returned with `requires_rescue_transfer`, `pickup_location`, and `planned_at_hour`; it represents onward ground travel after rescue to a safe pickup. Use `timeline` for complete plans at a particular hour.
- The backend holds one active scenario in memory. Restarting clears that state. Allocate against a simulation ID to detect a scenario replaced in another browser.

## Configuration

The frontend sends requests to its own `/api` endpoint, which proxies to `http://127.0.0.1:8000`. This also works when opening the dashboard from another device. Set `BACKEND_API_URL` in `frontend/.env.local` to change the proxy destination, then restart/rebuild. `NEXT_PUBLIC_API_URL` remains an optional override for direct browser-to-API access.

The default demand model is a bundled **128-tree Extra Trees / Random Forest / Ridge blend**, with event-based cross-validation, split-conformal uncertainty estimates and per-person planning minimums. Inference uses Python's standard library; PyTorch, XGBoost, SHAP and scikit-learn are unnecessary to run the app. Missing models or inputs outside the training feature ranges fall back to planning rules. The health endpoint and each simulation's `diagnostics` report model provenance and ML/rule prediction counts.

Training data and labels are **synthetic**, even where legacy filenames say historical. ML estimates relief demand; flood geometry and route closures remain scenario calculations. This model has not been validated against observed Chennai floods. Interval coverage is nominal per resource, not a guarantee under a new event or real conditions. Prediction metadata and bounds appear in the exported inventory ledger.

To retrain the advanced demand ensemble, install `backend/requirements-training.txt`, then run `python -m backend.ml_pipeline.train_demand_ensemble` followed by `python -m backend.ml_pipeline.evaluate_portable_model --save`. It reserves the entire synthetic 2023 event for evaluation and uses separate training/calibration splits. Convex blending weights are selected with leave-event-out cross-validation on fitting rows only. `train_portable_model` remains a standalone older forest experiment; the advanced artifact takes priority at runtime. For the legacy heavyweight ensemble, install `backend/requirements.txt` and set `ENABLE_ML=1`.

## Real weather dataset and trained rainfall model

**Project Review → Real-data rainfall model** displays a separately trained gradient-boosted classifier and historical replay. Its dataset contains **9,131 daily Chennai records (2001–2025)** downloaded from [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/). These are gridded MERRA-2 weather reanalysis values, not station measurements, observed flood labels, or real relief demand.

The target is next-day rainfall **≥ 10 mm/day**, a project-defined threshold. Inputs use the completed preceding seven days and seasonality. Training uses target dates through 2018; model and threshold selection use 2019–2021; final testing uses 2022–2025. The selected 180-tree gradient-boosting model achieves **77.28% accuracy, 78.62% balanced accuracy, 80.36% recall, 31.11% precision and 0.871 ROC AUC** on 1,461 test days. The majority baseline has 88.50% accuracy and zero recall; persistence has 71.38% balanced accuracy. Model selection favors balanced accuracy, with a substantial false-positive tradeoff. These metrics do not measure flood forecasting accuracy.

Run `train_models.bat` to install training dependencies, reproduce both models and refresh evaluation evidence. Raw source JSON, the normalized CSV, acquisition metadata, SHA-256 fingerprints, portable models and evaluation reports are bundled. Ordinary startup needs no training or weather API access.

New API endpoints:

- `GET /api/weather/evaluation`: verified test metrics, validation comparisons and limitations.
- `GET /api/weather/prediction?as_of=2023-12-03`: historical next-day prediction with subsequent reanalysis rainfall for comparison.
- `POST /api/weather/predict`: supply exactly seven ordered consecutive daily records (`date`, `PRECTOTCORR`, `T2M`, `RH2M`, `WS10M`, `PS`). Units are mm/day, °C, %, m/s and kPa. Out-of-training-range features are flagged.

This weather module is an offline hindcast. It assumes previous-day weather is available, does not account for publication latency, and does not issue live warnings. See [training and evaluation details](docs/TRAINING_AND_RESULTS.md).

See [the research and implementation notes](docs/RESEARCH_AND_IMPROVEMENTS.md) for IEEE references, model evaluation and measured performance. Click the exposure chart to select a timeline hour; completed runs open at peak modeled population exposure. Connection status refreshes automatically.

## Verification

Run `run_all_tests.bat` with the backend running and the frontend dev server stopped. It runs backend tests, live API integration tests with `--strict-live` (so an offline engine cannot produce a false pass), and a production build.

Manual commands from the project root:

```powershell
python -m pytest backend/tests -q
python -m pytest e2e -q --strict-live
cd frontend
npm run build
npm start
```

Avoid running `npm run build` at the same time as `npm run dev`: both write to `.next`. A production build must finish before `npm start`.

The dashboard requires the Python backend to compute results. When it is unavailable, baseline map data remains visible and simulation errors explain how to restore the connection.

Runtime evaluation (including range checks, rounding and rule fallbacks): `python -m backend.ml_pipeline.evaluate_portable_model`. Repeated conditions share a bounded inference cache; outputs still scale independently with headcount.
