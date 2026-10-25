# Complete local simulation archive — 19 October 2026

The Experiments page now has a separate full-result library in addition to its eight-run browser comparison notebook. A manual named save captures the complete active simulation, not merely its peak summary or settings.

## Stored content

- Original simulation request, physical parameters, computed timestamp and result ID.
- Every flood/routing/assignment timeline snapshot and rescue fleet plan.
- Current final inventory ledger, manual allocation routes and hourly inventory states.
- Facility/population/map inputs and current depot/distribution-point stock.
- Evaluation evidence available at save time, including model and dataset fingerprints. Missing weather evidence remains marked unavailable.
- Derived display settings for opening the saved map and timeline.

Snapshots are immutable. Save again to retain changes after manual allocations. An explicit simulation ID prevents accidentally saving another browser's replacement scenario. Snapshot copying is protected by the simulation lock. Database writes use SQLite transactions; compressed payloads carry SHA-256 checksums. Connections close after every operation.

## Reopening and boundaries

Saved views are read-only. Opening one does not activate its stock ledger or replace the current server scenario. Allocation actions are blocked in the frontend until settings are rerun. Cached advisory content can be read; refresh does not query a different active scenario. Exported reports use the snapshot's archived evaluation and physical input units rather than current-model evidence. Current bundled reference basemap vectors may have been refreshed since saving; scenario overlay coordinates and saved facility inputs remain archived.

Reopening restores display settings, not the engine's internal graph objects. Custom API inputs with per-zone overrides remain preserved in the original request inside snapshot JSON; rerun through the API for exact replay of such options. Frontend-configured scenarios can be rerun through the loaded controls. A rerun computes fresh results under the currently installed model/data and may differ from the archived result.

## Local storage and backup

Default path: `backend/storage/simulations.sqlite3`. Override with `SIM_ARCHIVE_DB` before startup. The database is ignored by Git and is not uploaded or deployed. Stop the backend before copying the database for backup. The UI can also download individual snapshots as JSON and import those full exports. Active-state restoration remains outside this feature's scope. No snapshot deletion or automatic expiry is performed.

## Portable snapshot import

Download a snapshot with **Download snapshot JSON**. On the destination project, open Experiments, select the file under **Snapshot JSON file**, then choose **Import snapshot JSON**. The local backend must be running; internet is unnecessary. Each import creates a fresh local ID and save timestamp, even when importing the same file twice. The original result, timeline, inputs, fleet plans and evidence are preserved. Existing saved snapshots and the active simulation/stock ledger are unchanged. Open the imported entry to inspect it; rerun settings before making new allocations.

Only version 1 complete snapshot exports up to 10 MiB are accepted. The backend bounds streamed request bytes and checks required fields, finite numeric values, timeline ordering, map/GeoJSON coordinates, fleet data, display geometry and original scenario configuration. Malformed JSON, duplicate object keys, incompatible versions and incomplete telemetry/summary exports are rejected before writing to the archive. Checks establish format compatibility, not scientific validity or authenticity. Imported entries, opened views and report exports explicitly identify file-supplied evidence as not independently verified. SHA-256 protects the locally stored payload after import; it does not authenticate an external file.

## Validation

Tests cover exact full-result reopening through a newly constructed store, preserved fleet plans and source evidence, immutable before/after allocation snapshots, read-only behavior with a different active scenario, corruption detection, name validation, pagination and missing IDs.

Verification on 19 October 2026: 104 backend tests, 95 strict live integration tests, four report tests and the production frontend build passed. The five archive tests also passed after adding an explicit in-memory-result-loss check. In the browser, a named T. Nagar snapshot survived an actual backend restart and full page reload, reopened its map, timeline, inventory and fleet plan, blocked new allocations, and exported an HTML report with archived model evidence. The active-result endpoint remained 404 throughout reopening and export, confirming that viewing an archive did not activate a server simulation.

After adding portable import: 115 backend tests and five report tests passed, along with the production build. Import coverage includes exact result/map/evidence round trips, duplicate imports with independent IDs, preserved original records and active inventory, missing active state, malformed geometry/data, unsupported versions, non-finite numbers, duplicate keys, invalid encoding/JSON and the streamed size limit. Browser verification downloaded the original T. Nagar snapshot, selected and imported that file, opened the imported map/timeline and exported a report retaining fleet/model evidence plus the import notice. See `snapshot-import-verified.png` for the restored library view.
