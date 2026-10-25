# Training and measured results — 18 October 2026

The application has two distinct ML tasks. Real weather data cannot establish relief-demand accuracy, and synthetic relief labels cannot establish flood accuracy.

## Chennai rainfall classification

Source: [NASA POWER daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), latitude 13.0827, longitude 80.2707, UTC. Downloaded 9,131 consecutive days from 2001-01-01 through 2025-12-31. Parameters: corrected precipitation, temperature, relative humidity, wind speed and surface pressure. The raw JSON and normalized CSV are in `backend/ml_pipeline/dataset/`; `weather_manifest.json` records the request, units, returned coordinates, retrieval date and hashes. Missing/sentinel/nonfinite values cause acquisition to fail instead of being fabricated.

NASA describes meteorological values as grid averages from MERRA-2 assimilation/reanalysis: [methodology](https://power.larc.nasa.gov/docs/methodology/meteorology/). They are real sourced environmental data with modeled components, not direct observations from a Chennai rain gauge.

Target: next-day corrected rainfall >= 10 mm/day. This threshold belongs to the project, not an official flood warning category. Features use the preceding seven completed daily records: current precipitation, temperature, humidity, wind and pressure; precipitation lags; three/seven-day means; seven-day maximum; target-date cyclic seasonality. No target-day weather enters features.

Training: 6,567 target days, 2001-01-08 to 2018-12-31. Validation: 1,096 days, 2019–2021. Test: 1,461 days, 2022–2025. Chronological boundaries follow target dates. Two gradient-boosting configurations and a random forest were compared on validation only. Thresholds were selected on validation balanced accuracy. The selected model is 180 gradient-boosted depth-two trees with learning rate 0.04; no refit on validation changes its threshold relationship. [Algorithm documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingClassifier.html).

| Test metric | Selected model | Always low rainfall | Previous-day persistence |
|---|---:|---:|---:|
| Accuracy | 77.28% | 88.50% | 88.30% |
| Balanced accuracy | 78.62% | 50.00% | 71.38% |
| Precision | 31.11% | 0.00% | 49.11% |
| Recall | 80.36% | 0.00% | 49.40% |
| F1 | 44.85% | 0.00% | 49.26% |
| ROC AUC | 0.8712 | 0.5000 | 0.7138 |

Confusion matrix (rows actual low/elevated, columns predicted low/elevated): `[[994,299],[33,135]]`. There are 168 elevated-rainfall days. The model improves balanced accuracy and recall over persistence but sacrifices precision, F1 and raw accuracy. It is an academic hindcast with uncalibrated probabilities, substantial false alarms, one spatial grid point and unmodeled data-publication latency. It does not predict flood extent or depth and is not validated for operational emergency use.

Portable inference is checked against scikit-learn probabilities on every held-out day with maximum absolute tolerance 1e-10. Dataset/model/report hashes must match before the API serves weather results. API inference uses standard-library JSON tree traversal; there is no runtime scikit-learn dependency or download.

## Relief-demand ensemble

The existing 55,000-row synthetic relief dataset is retained and explicitly labeled. The complete synthetic `2023_Michaung` group (16,513 rows) is held out. The remaining data is split into fitting (28,865) and conformal calibration (9,622) rows. GroupKFold on fitting rows holds out each of four synthetic event groups for blend selection. Calibration and final test rows are excluded from selection.

64 Extra Trees, 64 Random Forest trees and scaled Ridge regression predict per-person water, food and medical-kit demand. Per-resource convex weights are chosen on a 0.1 grid using out-of-event total-unit MAE. The fitted model is exported as JSON trees and unscaled linear coefficients. Split-conformal absolute residual quantiles use separate calibration rows, nominal 90% per resource. Planning floors and integer rounding apply in the deployed runtime. The present selection uses Ridge for water/food and a 70% forest / 30% Ridge blend for medical kits.

| Runtime held-out metric | Water litres | Food rations | Medical kits |
|---|---:|---:|---:|
| MAE | 122.44 | 92.69 | 10.90 |
| Planning-rule MAE | 3,647.53 | 1,843.65 | 91.54 |
| ML interval coverage | 89.81% | 90.29% | 93.90% |

All held-out rows use ML with the current artifact. These errors are measured against synthetic labels. They do not prove real relief-demand accuracy. Regression has no classification accuracy percentage; use MAE and interval coverage. The runtime report now fingerprints the actual active `demand_ensemble_v2.json`, fixing the previous association with the older forest filename.

## Reproduce

Run `train_models.bat` from the project directory, or install `backend/requirements-training.txt` and run:

```powershell
python -m backend.ml_pipeline.download_weather
python -m backend.ml_pipeline.train_weather_model
python -m backend.ml_pipeline.train_demand_ensemble
python -m backend.ml_pipeline.evaluate_portable_model --save
```

The downloader reuses the bundled raw response. To intentionally refresh source revisions, archive that response before downloading again, then retrain and regenerate all evidence. Historical source revisions can change results. Restart the API after retraining. Treat test years as final evaluation; further tuning requires a new untouched test period.

Use `start_project.bat` for normal startup, open Project Review for metrics and historical replay, and inspect `/docs` for typed endpoints. The weather module informs the research/demo workflow; it does not automatically replace the scenario's user-chosen rainfall or hydrology assumptions.

## Verification evidence

- Backend suite: 87 passed. Includes source/model/report provenance, chronological boundaries, rejection of invalid input histories, and recomputation of all 1,461 portable test predictions against the saved confusion matrix.
- Strict live API integration suite: 95 passed against the running backend.
- Production frontend build: passed compilation, ESLint, TypeScript and static page generation.
- Production dashboard browser check: System Evaluation displays both verified model reports. Replaying conditions through 2023-12-03 gives 80.50% estimated next-day rainfall probability and 141.1 mm/day subsequent reanalysis. Changing the date to 2025-10-01 and submitting the form displays the 2025-10-02 prediction and 6.92 mm/day subsequent reanalysis. The Next.js proxy endpoints return verified evidence successfully.

The existing FastAPI/Starlette test client emits a dependency deprecation warning; it did not cause failures. No deployment or operational flood validation is claimed.
