# Offline atlas and reporting additions — 18 October 2026

## Delivered

1. **Offline map background.** Ward polygons were downloaded from the public Greater Chennai Corporation ArcGIS layer in EPSG:4326. All 200 wards are present. Rivers were downloaded as OpenStreetMap `waterway=river` ways in the Chennai bounding box via Overpass; 26 segments are bundled. The project road graph supplies 110 deduplicated modeled links. No raster tiles were bulk-downloaded. The map defaults to local vectors. Optional online street tiles have a tile-error fallback. Reference vectors use a separate Leaflet pane below scenario overlays.
2. **Ward Atlas.** Searches ward numbers and the names of included modeled population points. Point-in-polygon membership handles polygon holes and multipolygons. Population and risk categories remain modeled inputs, distinct from official boundary geometry. Unknown official population and vulnerable-group counts remain unknown. Three nearby modeled shelters are ranked by geodesic straight-line distance from a vertex-average ward reference point. Distances are not route lengths, and baseline spaces are not current operational availability.
3. **Scenario comparison.** Baseline/comparison selectors show signed changes and percentage changes. A zero baseline suppresses percentage calculation. Existing eight-run browser persistence is retained. Independent peak metrics cannot be interpreted as cumulative unique evacuees or causal intervention effects.
4. **Downloadable scenario report.** Self-contained HTML with local SVG vectors, the peak-exposure flood/routing snapshot, direct rainfall units, independent peak metrics, hourly rows, final destination deficits, available model evaluation, assumptions and source links. Browser Print → Save as PDF is supported through print CSS. Text is HTML-escaped and no executable scripts or remote image/font dependencies are embedded.

## Sources and provenance

- GCC Ward_Boundary layer: https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCPublic/GCC_AdminBoundary/MapServer/4
- OSM river geometry: https://www.openstreetmap.org/copyright (ODbL attribution included in map/report)
- GCC stormwater context: https://chennaicorporation.gov.in/gcc/department/storm-water/
- CAG 2017 flood-management audit: https://cag.gov.in/ag1/tamil-nadu/en/audit-report/details/45722

Acquisition metadata, exact query URLs and SHA-256 fingerprints are bundled in `frontend/public/data/reference_manifest.json`. The ward service does not supply an effective boundary date. Eight modeled cluster points fall within published GCC polygons. Tambaram/Mudichur and the project's Mylapore/Marina coastal point fall outside those polygons; they are listed separately instead of assigned to an invented ward. A point represents only its modeled catchment, not a full official ward population.

## Verification

- 91 backend tests pass, including all 200 unique ward IDs, full cluster accounting, polygon holes, missing population semantics, sorted shelter proximity, source hashes, static/API profile equality and the `/api/wards` endpoint.
- 95 strict live integration tests pass.
- Three report tests pass: HTML escaping and absence of executable/remote map dependencies; peak-snapshot/independent-plan semantics; rejection of empty completed timelines.
- Production build checks compilation, ESLint, TypeScript and static generation.
- Browser verification: offline vectors and attribution render; searching Velachery finds Ward 177 and its 37,000 modeled cluster population. Two completed Velachery scenarios (140 vs 50 mm/hour) show selectable comparison deltas. Downloading the report succeeds; the resulting HTML contains embedded vector paths, hourly results, shortages and model metrics. An example from that check is saved in `docs/reports/example-scenario.html`.

Refresh data explicitly with `python -m backend.app.data.build_reference_data`. It requires internet. Ordinary application startup and report rendering use bundled assets. Rebuild frontend and restart backend after changing reference inputs.
