# Repair and verification — 14 October 2026

Scope: run a scenario from the dashboard, inspect hourly maps and shelter assignments, review advice, allocate relief, and export results. Existing uncommitted project work was preserved.

## Changes

- Playback now runs at dashboard level instead of stopping when the map view unmounts.
- Keyboard shortcuts respect dialogs, editable fields, buttons, links and modifier keys. Mobile navigation traps focus and closes with Escape.
- Fixed shelter occupancy calculations to include assigned evacuees in both the summary and directory. The summary no longer describes compromised/full shelters as available.
- Prevent stale results from being exported after scenario edits; clear obsolete advice and route dialogs on a new run/reset.
- Removed duplicate preset controls, promotional cards, decorative glow/pulses, and verbose navigation labels. Logistics starts collapsed; layers expand on demand. The map appears ahead of controls on narrower screens, with readable mobile metric labels.
- Replaced fake reroute/vehicle changes and cellular-tower dispatch success messages. Route inspection shows computed distance, time, mode and cargo. Advice supports session-local review, English/Tamil text downloads, clipboard copy with error feedback and device-local speech preview.
- Corrected Extreme vulnerability to 0.99 instead of the generic 0.8 default. Rule-based demand no longer requests medical stock for zero occupants.
- Added bounded caching for per-person forest inference, preserving independent headcount scaling and fresh uncertainty objects.
- Validate calibration, ranges and tree structure at load time so malformed artifacts fall back instead of crashing/hanging at inference.
- Preserve the portable model if optional legacy model initialization fails. Correct advice metadata that previously claimed a deep ensemble and active SHAP explanations for the portable model.
- Corrected README provenance: shipped artifact contains 64 trees.

## Checks

| Boundary | Result | Evidence |
|---|---|---|
| Backend behavior | Pass | 76 tests, including corrupt model artifacts, cache/headcount integrity, Extreme vulnerability and empty shelter demand |
| Production frontend | Pass | `npm run build`, including TypeScript and ESLint |
| Live API integration | Pass | `python -m pytest e2e -q --strict-live`; 95 cases |
| Browser → proxy → API → results | Pass | Default six-hour scenario returned seven snapshots and rendered routes and metrics |
| Playback outside map | Pass | Started playback at hour 0, switched to Impact, observed advancement to hour 6 |
| Advice | Pass | Recommendations and Tamil bulletin rendered; Escape closed dialog; no browser console errors in checked flow |
| Responsive UI | Pass | Tested 390 × 844 viewport; mobile navigation and dialogs worked, document width 375 px including scrollbar, map width about 342 px, no horizontal page overflow |
| Desktop map | Pass | Map width increased from about 349 px to 661 px at the tested desktop viewport after fixing layout conflict |

The live API suite includes allocation, inventory conservation, boundary conditions, route safety and historical-inspired scenarios. Browser coverage is a smoke check, not an exhaustive automated UI suite. Test tooling emits a Starlette/httpx deprecation warning; tests pass.

## Exact shipped model evaluation

Command: `python -m backend.ml_pipeline.evaluate_portable_model`.
This standard-library evaluator checks dataset SHA-256 provenance and evaluates the exact deployed tree traversal, range checks, integer rounding and rule fallback behavior.

16,513 held-out synthetic 2023-event rows: all used ML, none required fallback.

| Resource | Runtime mean absolute error | Rule baseline mean absolute error | Interval coverage |
|---|---:|---:|---:|
| Water (litres) | 128.55 | 3,647.53 | 89.67% |
| Food (rations) | 98.13 | 1,843.65 | 90.21% |
| Medicine (kits) | 13.08 | 91.54 | 90.23% |

These reproduce the existing model's synthetic evaluation; the model was not retrained in this repair. They do not measure accuracy on observed floods. Real accuracy improvement requires observed demand/outcome data and independent event validation. The demand model does not predict flood extent or depth.

For 1,000 calls with repeated conditions and changing occupancy, local median inference was 0.208 ms without caching and 0.0069 ms with caching (about 30× faster for this workload). Unique conditions still traverse the forest. This is not a 30× whole-simulation speedup.

The engine benchmark now includes the shipped predictor. Three 12-hour circle runs took 0.628/0.385/0.355 seconds; polygon runs took 0.183/0.257/0.375 seconds. These engine measurements exclude browser rendering, tile downloads and HTTP transfer.

## Running locally

The verification frontend uses http://localhost:3001 because port 3000 was already occupied. Backend: http://127.0.0.1:8000. Normal project launch scripts retain their configured ports.

Remaining limitations: synthetic hydrology/geography and labels; no live flood feed or dispatch integration; one active backend scenario shared between clients; results lost on backend restart. No claim is made that every possible UI interaction or model condition has been exhaustively validated.
