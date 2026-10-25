# Verification — 5 October 2026

Chennai Flood Lab was verified locally using the deterministic demand model (`ENABLE_ML=0`, now the default).

- Backend: **39 passed**. Includes the existing 35 tests plus invalid-geometry and resource-state / stale-scenario checks. One dependency deprecation warning from Starlette/httpx remains.
- Live API integration: **95 passed**, with `--strict-live`; none skipped. Feature, boundary, interaction and historical-inspired scenarios were exercised. Existing tests were not weakened or removed.
- Frontend: production build, ESLint and TypeScript checks passed.
- Browser: checked desktop and 390 px mobile layouts, OpenStreetMap tile loading, simulation request/results, timeline steps/playback, allocation success, a custom three-point polygon run, and error overlays. New allocation updates depot stock, final-step inventory and delivery routes. The mobile layout showed no horizontal overflow; no browser errors were reported.
- Launcher: `start_project.ps1` successfully detected running services and displayed the dashboard/API addresses.

The simulation uses the assumptions documented in the main README. These tests validate software behavior, not real-world flood prediction accuracy. Optional ML mode was not part of this verification.

Detailed test output is saved alongside this report.

Screenshots: [desktop](desktop.png), [mobile](mobile.png).
