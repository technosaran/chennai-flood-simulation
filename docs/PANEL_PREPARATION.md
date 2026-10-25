# Chennai Flood Lab — submission and panel preparation

Prepared 15 October 2026. This guide describes the implemented academic simulator.

## Project abstract

Chennai Flood Lab is a full-stack scenario simulation for examining flood response tradeoffs in Chennai. Users define a flood zone and conditions, inspect time-varying inundation and road accessibility, review capacity-constrained shelter assignments, and plan relief supplies against finite depot inventory. A portable Extra Trees model estimates demand with split-conformal intervals and rule fallbacks. The dashboard supports map playback, comparative experiments, allocation ledgers and exports. Data and hydrology are modeled; observed flood forecasting accuracy and operational rescue effectiveness have not been established.

## Modules and demo evidence

| Module | What to demonstrate | Evidence/limits |
|---|---|---|
| Scenario configuration | Preset, circle, polygon, rainfall/depth/spread/duration | Input validation and Chennai coordinate limits |
| Flood engine | Scrub timeline; compare extent and depth | Scenario geometry, not calibrated hydraulic prediction |
| Evacuation | Inspect paths, closed roads and unassigned population | Simplified graph, depth screening and shelter constraints |
| Relief logistics | Allocate from a depot; inspect remaining stock | Stock ledger, rollback and simulation ID checks |
| ML demand | Review live ML/rule counts and inventory demand intervals | 64-tree portable forest; synthetic training labels |
| Model evaluation (new) | Open Project Review | Verified model/dataset fingerprints and deployed runtime metrics |
| Advice | Open wards and English/Tamil bulletin | Rule-based final-hour snapshot, simulation-scoped refresh |
| Airlift analysis | Explain isolation and unavailable safe sites | No flooded fallback drop zone; no finite fleet scheduling |
| Impact | Click exposure chart and inspect hourly outcomes | Independent hourly assignments; no cumulative unique evacuees |
| Experiments | Run twice before visiting the notebook | Eight browser-local summaries/settings recorded across views |
| Exports | Download JSON, comparison CSV and panel guide | Full simulation export plus reproducible settings |
| API/testing | Open /docs; show test results | Regression tests, strict live integration and production build |

## Eight-minute demo

1. Explain the problem and distinguish scenario simulation from observed forecasting (one minute).
2. Run a preset; inspect hour 0 and peak exposure; toggle map layers and inspect a route (two minutes).
3. Inspect shelter constraints and allocate a small quantity from a depot (one minute).
4. Show final-hour scenario advice and Tamil sample bulletin (one minute).
5. Change rainfall/depth and rerun; open Experiments and export the comparison (one minute).
6. Open Project Review; explain MAE, baseline, conformal coverage and ML/rule counts (one minute).
7. Export results and state the limitations and next steps (one minute).

## Likely viva questions and grounded answers

### 1. What problem does your project solve?

It connects a hypothetical Chennai flood scenario to road accessibility, shelter assignments and relief-demand planning in one reproducible workflow. A reviewer can change conditions and compare the resulting response plans.

### 2. Which part is AI/ML, and which part is an algorithm?

A bundled 64-tree Extra Trees ensemble predicts per-person water, food and medical demand from rainfall, depth, density and vulnerability. Geometry models inundation. Graph algorithms compute routes; capacity constraints govern assignments. The advisory service uses explicit rules rather than an LLM.

### 3. Where does your dataset come from?

The 55,000 demand rows and labels are synthetic. Historical event names identify generated groups, not observed ground truth. Geography, populations and inventory are modeled inputs. This is an academic scenario simulator.

### 4. How do you prevent train/test leakage?

The complete synthetic 2023_Michaung group is held out (16,513 rows). The remaining rows are split into training (28,865) and conformal calibration (9,622). Event separation reduces row leakage, but a shared synthetic generator can still make evaluation optimistic.

### 5. Why Extra Trees instead of deep learning?

These are four tabular inputs. The shipped forest runs without heavy ML dependencies and can be inspected and reproduced. Legacy deep/XGBoost experiments exist, but the active model and evaluation must be identified from runtime metadata. Do not claim one model is universally superior.

### 6. How do you measure performance?

Use held-out mean absolute error in litres, rations and kits, compare with the rule baseline, and check interval coverage. MAE = sum of absolute prediction errors / number of rows. Report the deployed runtime including rounding and fallback, not a classification accuracy percentage.

### 7. What do the uncertainty intervals mean?

Split-conformal residuals on a separate calibration set produce nominal 90% intervals per resource. Held-out coverage measures the fraction of synthetic targets within each interval. Coverage on a different real event is not guaranteed; it is not a 90% confidence that a particular prediction is correct.

### 8. What happens when ML fails or inputs are outside training ranges?

The predictor rejects unsupported inputs and missing or invalid artifacts; planning rules supply demand instead. Per-run diagnostics report ML and rule counts. Per-person planning minimums and integer rounding apply to deployed predictions.

### 9. How do routes avoid floodwater?

At each snapshot, modeled road edges are screened for inundation. Evacuation roads close at 0.50m and truck roads at 0.30m. The simplified offline graph supplies candidate paths and congestion costs. These thresholds are project assumptions, not a guarantee of safe travel.

### 10. What if shelters are full or all roads are blocked?

Assignments obey shelter capacity and accessibility constraints. Unassigned affected people are reported as requiring rescue. Modeled amphibious/air options do not imply available vehicles. If every candidate drop zone is inundated, advice explicitly reports no safe drop zone.

### 11. How do you ensure supply inventory is correct?

Allocation is constrained by depot stock. Serialized mutations and rollback protect the ledger on failures. Manual allocation carries a simulation ID, so a replaced scenario is rejected. Earlier timeline snapshots retain their historical inventory.

### 12. Can hourly evacuee totals be added?

No. Each hour is an independent assignment plan, so the same person may appear repeatedly. Report hourly values or a clearly labeled peak. The current engine does not track individual movement or cumulative unique evacuations.

### 13. What is your contribution?

The integration of scenario controls, accessibility, shelter constraints, uncertainty-aware demand, inventory conservation and comparative experiments. Standard algorithms are reused; the project does not introduce a new flood-forecasting model or prove real-world emergency effectiveness.

### 14. How is the application tested?

Backend regression tests check geometry, routing, stock conservation, model integrity and API state. The strict live API suite exercises boundaries and combined scenarios. A production build checks frontend compilation; browser smoke checks cover the visible demo. These are different layers of evidence.

### 15. What are the main limitations and next steps?

Synthetic labels, approximate hydrology and roads, one active in-memory backend scenario, online map tiles, and no finite rescue fleet or dispatch integration. Next steps are observed-data calibration, independent real-event evaluation, persistent per-user scenarios and constrained fleet scheduling.

## Submission checklist

- Include the project abstract, problem statement, architecture and module/data-flow diagrams.
- Describe features, targets, data generation, event holdout and calibration split.
- Include MAE/baseline/coverage tables with the words **synthetic labels** in the caption.
- Include screenshots from a completed run, allocation, comparison and Project Review.
- Include reproducible installation/run commands and verification results.
- Identify your implementation work separately from third-party algorithms and libraries.
- Describe observed-data calibration, independent real-event evaluation, per-user persistence and constrained rescue-fleet scheduling as future work.

## Commands

From the project root:

```powershell
python -m pytest backend/tests -q
python -m pytest e2e -q --strict-live
python -m backend.ml_pipeline.evaluate_portable_model --save
```

The live API suite requires the backend on port 8000. Build the frontend with `npm run build` from `frontend/`, with the dev server stopped. Launch both services with `start_project.bat`; open http://localhost:3000.

## Known boundaries

One active backend scenario is shared between clients and lost on restart. Experiment settings and summary history are browser-local, not server backups. Online OSM tiles are needed for the street basemap. Rescue options are modeled, not dispatched or fleet-scheduled. The project has no citizen notification service. Do not present synthetic model scores as real flood accuracy.
