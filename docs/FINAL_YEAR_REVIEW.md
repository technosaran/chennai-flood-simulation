# Final-year project review — 9 October 2026

## Scope and contribution

Chennai Flood Lab is a reproducible academic flood-response scenario simulator. Its contribution is an integrated workflow linking hypothetical inundation, road accessibility, capacity-constrained shelter assignment, relief-demand estimation, stock conservation and interactive comparison. It is not an observed flood forecasting system or an emergency dispatch product.

The existing source and earlier improvements were retained. This review adds an experiment notebook, clearer hourly response analysis, backend consistency fixes, regression tests and this literature-to-design mapping. No private or locally supplied research papers were present in the project; the review below is a focused public-source review, not a systematic review of all flood literature.

## Literature-to-design mapping

| Source and access | Relevant finding | Application and limits |
|---|---|---|
| Paul et al. (2026), [Can aerosols improve urban flood forecasting? A case study of 2015 Chennai extreme event](https://nhess.copernicus.org/articles/26/3749/2026/), DOI 10.5194/nhess-26-3749-2026. Publisher full text accessible. | Couples weather simulation with hydrological and hydraulic modeling and checks modeled outcomes against observations. Rainfall errors propagate into inundation estimates. | Keep response simulation separate from forecasting claims. A future calibrated version requires observed rain, terrain, drainage, water levels and inundation evidence. The current geometric flood engine does not reproduce this paper. |
| [Feasibility study of urban flood mapping using traffic signs for route optimization](https://arxiv.org/abs/2109.11712) (2021). Abstract reviewed; preprint. | Uses estimated flood depths to construct an inundation map and calculate flood-free paths with A*. | Route planning must use spatially varying accessibility. This implementation screens modeled roads by depth and applies graph shortest paths; it does not estimate water levels from traffic signs. |
| [Exploration of a disrupted road network after a disaster with an online routing algorithm](https://link.springer.com/article/10.1007/s00291-020-00613-w) (published online 2020; OR Spectrum 43, 2021), DOI 10.1007/s00291-020-00613-w. Open-access publisher article reviewed. | Studies UAV exploration when initial information about road disruption is unavailable, updating exploration as information arrives. | Distinguish modeled accessibility from verified field accessibility. The app has a fixed offline graph, no drone reconnaissance and no live road observations. |

See [earlier research notes](RESEARCH_AND_IMPROVEMENTS.md) for the previous IEEE abstract review, demand-model construction and synthetic held-out evaluation. This review does not independently reproduce those papers or retrain that model.

## Implemented improvements

- **Experiment notebook:** the latest eight completed experiments are stored locally in the browser with scenario settings and compact outcome summaries. Restoring settings requires a fresh computation. CSV comparison supports report tables. Storage errors are visible; server state is not falsely restored from old results.
- **Response analysis:** selected-hour rescue need, shelter assignment capacity and relief routes supplement the existing map and interactive exposure plot. Each comparison column is an independent timeline maximum and may peak at a different hour.
- **Facility restrictions:** `warehouse_ids` now restricts automatic dispatch sources. An explicit empty shelter/warehouse list means no facilities; omitting it means all facilities. Unknown IDs fail validation before changing inventory. Manual dispatch can intentionally select a depot outside automatic-planning restrictions.
- **Consistent allocations:** manual dispatch updates the cached result, final timeline inventory, routes and ledger together. Exceptions roll inventory back. Earlier snapshots retain their historical values.
- **Reproducibility:** `/api/simulation/latest` exposes the current completed result; exports include effective scenario input. The resource-state endpoint identifies its simulation, and the browser rejects stock refreshes belonging to a different run.
- **Summary semantics:** peak affected population and its hour are explicit. The legacy final-hour affected count remains compatible. Hourly assignments must not be added to claim unique evacuations.

## Module status and honest boundaries

| Module | Implemented | Remaining scientific/product limits |
|---|---|---|
| Map and scenarios | OSM base map, presets, circles, polygons, layer controls | Online tiles required; presets are illustrative |
| Inundation | Time-varying depth/spread, terrain anchors, polygon geometry | No calibrated hydraulic PDE model; overlapping area double-counts |
| Evacuation | Flood-aware graph routing, shelter constraints, congestion, isolated clusters | Simplified modeled graph; independent hourly plans |
| Relief logistics | Mode selection, depot stocks, manual and automatic allocation, ledgers | No finite rescue fleet, scheduling or real dispatch; one source per destination per automatic step |
| Demand model | Portable ensemble, conformal intervals, rule fallback | Synthetic training/evaluation; real-event accuracy unknown |
| Dashboard | Responsive map workspace, playback, analysis, local notebook, JSON/CSV exports | Browser notebook stores summaries/settings, not full server restoration |
| Backend | Validation, serialized state changes, rollback, latest-result API | One in-memory active simulation shared by clients; no durable multi-user database |

The original request mentions actual Chennai road-network routing. The bundled simplified network does **not** fully meet that research-grade data requirement. Replacing it with a provenance-tracked OSM extract, validating facilities and acquiring observed hydrology remain explicit future work; they should not be described as already completed in the dissertation.

## Demonstration script

1. Start both services with `start_project.bat` and open `http://localhost:3000`.
2. Run the default scenario; explain the distinction between affected, assigned and stranded population.
3. Select an hour in the exposure chart. Inspect flood layers, evacuation routes and shelter capacity.
4. Change depth or rainfall and recompute. Compare the two notebook rows; export CSV for the report.
5. Restore the first experiment's settings and recompute to demonstrate repeatability.
6. Select a shelter/distribution point, allocate available supplies and inspect the final-hour inventory and exported ledger.
7. Expand the research-basis section and explain model assumptions, synthetic training data and missing observed validation.

## Evaluation plan

Separate software correctness from scientific validity. Regression tests check stock conservation, selection semantics, rollback and snapshot consistency. Live API tests check scenario behavior and geometry constraints. Production compilation checks the client contract. Browser interaction verifies the complete user workflow. Real scientific validation would require independent observed events and locations, baseline comparisons, inundation overlap/depth error and resource-demand calibration; current software tests do not establish these.
