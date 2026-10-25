# Chennai Flood Lab — panel preparation

## What problem does your project solve?
It connects a hypothetical Chennai flood scenario to road accessibility, shelter assignments and relief-demand planning in one reproducible workflow. A reviewer can change conditions and compare the resulting response plans.

## Which part is AI/ML, and which part is an algorithm?
A 160-tree Extra Trees/Random Forest/Ridge blend predicts relief demand with split-conformal intervals, complemented by an offline multi-model XGBoost and PyTorch Deep Neural Network ensemble. A separate 250-tree regularized gradient-boosting classifier predicts next-day rainfall >= 10 mm/day from NASA POWER weather history. Geometry models inundation; graph algorithms route vehicles; capacity constraints govern assignments. The advisory service uses explicit rules.

## Where does your dataset come from?
The weather model uses 9,131 downloaded NASA POWER daily Chennai records from 2001–2025: gridded MERRA-2 reanalysis, not local station or flood observations. The separate 100,000-row relief-demand dataset covers all 15 Greater Chennai Corporation (GCC) zones and 8 critical flood micro-basins across 7 distinct disaster regimes with physical non-linear supply disruption calculations.

## How do you prevent train/test leakage?
The complete synthetic 2023_Michaung group is strictly held out (28,132 rows). The remaining 71,868 rows are split into fitting (53,901) and conformal calibration (17,967). Event separation using GroupKFold eliminates cross-event leakage during convex weight optimization.

## Why Extra Trees instead of deep learning?
These are four tabular inputs. The shipped forest runs without heavy ML dependencies and can be inspected and reproduced. Legacy deep/XGBoost experiments exist, but the active model and evaluation must be identified from runtime metadata. Do not claim one model is universally superior.

## How do you measure performance?
Relief regression uses held-out MAE and interval coverage against synthetic labels. The real-data rainfall classifier uses a chronological 2022–2025 holdout: 77.28% accuracy, 78.62% balanced accuracy, 80.36% recall and 31.11% precision. Compare majority and persistence baselines; raw accuracy alone hides rare wet days. Rainfall classification does not establish flood accuracy.

## What do the uncertainty intervals mean?
Split-conformal residuals on a separate calibration set produce nominal 90% intervals per resource. Held-out coverage measures the fraction of synthetic targets within each interval. Coverage on a different real event is not guaranteed; it is not a 90% confidence that a particular prediction is correct.

## What happens when ML fails or inputs are outside training ranges?
The predictor rejects unsupported inputs and missing or invalid artifacts; planning rules supply demand instead. Per-run diagnostics report ML and rule counts. Per-person planning minimums and integer rounding apply to deployed predictions.

## How do routes avoid floodwater?
At each snapshot, modeled road edges are screened for inundation. Evacuation roads close at 0.50m and truck roads at 0.30m. The simplified offline graph supplies candidate paths and congestion costs. These thresholds are project assumptions, not a guarantee of safe travel.

## What if shelters are full or all roads are blocked?
Assignments obey shelter capacity and accessibility constraints. Unassigned affected people are reported as requiring rescue. Modeled amphibious/air options do not imply available vehicles. If every candidate drop zone is inundated, advice explicitly reports no safe drop zone.

## How do you ensure supply inventory is correct?
Allocation is constrained by depot stock. Serialized mutations and rollback protect the ledger on failures. Manual allocation carries a simulation ID, so a replaced scenario is rejected. Earlier timeline snapshots retain their historical inventory.

## Can hourly evacuee totals be added?
No. Each hour is an independent assignment plan, so the same person may appear repeatedly. Report hourly values or a clearly labeled peak. The current engine does not track individual movement or cumulative unique evacuations.

## What is your contribution?
The integration of scenario controls, accessibility, shelter constraints, uncertainty-aware demand, inventory conservation and comparative experiments. Standard algorithms are reused; the project does not introduce a new flood-forecasting model or prove real-world emergency effectiveness.

## How is the application tested?
Backend regression tests check geometry, routing, stock conservation, model integrity and API state. The strict live API suite exercises boundaries and combined scenarios. A production build checks frontend compilation; browser smoke checks cover the visible demo. These are different layers of evidence.

## What are the main limitations and next steps?
Synthetic demand labels, approximate hydrology and roads, one active in-memory scenario, and unverified boat/air access remain limitations. Dedicated rescue fleet counts, seats, trip times, readiness and shelter space constrain provisional plans at each frozen snapshot. They do not execute dispatches or accumulate unique rescues. Next steps are observed-event validation, changing-flood route checks, persistent scenarios and verified multimodal access.

## Demo sequence
1. Run a preset and explain its rainfall, depth and duration inputs.
2. Inspect hour 0 and peak exposure; explain independent hourly plans.
3. Toggle flood, evacuation, supply and population layers; inspect a route.
4. Open Relief & Supplies and allocate a small quantity from an available depot.
5. Open scenario advice; inspect wards and the English/Tamil sample bulletin.
6. Change a condition and rerun; compare both runs in Experiments and export CSV.
7. Open Project Review; explain MAE, baseline, uncertainty, fallback and limitations.
8. Export the scenario JSON for reproducibility and include the test report in your submission.

## Verified model evaluation
{
  "model": {
    "name": "Event-CV blend: Extra Trees + Random Forest + Ridge / conformal",
    "model_sha256": "c34d5446eec133299d7427aa736cfa75bf3ea8f3753ff2b883dee40dfa5377ab",
    "artifact_name": "demand_ensemble_v2.json",
    "component_weights": [
      [
        0,
        0,
        1
      ],
      [
        0,
        0,
        1
      ],
      [
        0,
        0.7,
        0.3
      ]
    ],
    "components": [
      "Extra Trees",
      "Random Forest",
      "Ridge"
    ],
    "training_data": "synthetic",
    "validated_for_live_use": false,
    "features": [
      "Rainfall_mm_hr",
      "Flood_Depth_m",
      "Pop_Density_sqkm",
      "Vulnerability_Score"
    ],
    "tree_count": 128,
    "dataset_sha256": "7ac56260bfd57b636b48cd90457db008e508bd4bb98a040489765fd0a3a1b992",
    "load_error": null,
    "evaluation": {
      "holdout_event": "2023_Michaung",
      "training_rows": 28865,
      "calibration_rows": 9622,
      "test_rows": 16513,
      "source": "synthetic labels; no observed flood or relief ground truth",
      "selection": "Convex weights selected using GroupKFold out-of-event predictions on fitting rows only.",
      "cross_validation": [
        {
          "held_out_events": [
            "2015_Deluge"
          ],
          "rows": 10298
        },
        {
          "held_out_events": [
            "2020_Nivar"
          ],
          "rows": 6233
        },
        {
          "held_out_events": [
            "2021_Monsoon_Peak"
          ],
          "rows": 6190
        },
        {
          "held_out_events": [
            "Flash_Cloudburst"
          ],
          "rows": 6144
        }
      ],
      "component_weights": [
        [
          0,
          0,
          1
        ],
        [
          0,
          0,
          1
        ],
        [
          0,
          0.7,
          0.3
        ]
      ],
      "mae_units": {
        "water_litres": 122.43661563395709,
        "food_rations": 92.68714903890394,
        "medical_kits": 10.798392661195374
      },
      "r2": {
        "water_litres": 0.998536498293769,
        "food_rations": 0.9986536386987032,
        "medical_kits": 0.9686385886611961
      },
      "baseline_mae_units": {
        "water_litres": 3647.5320977412,
        "food_rations": 1843.6522291527895,
        "medical_kits": 92.03602737237328
      },
      "interval_coverage": {
        "water_litres": 0.8973536001937867,
        "food_rations": 0.9022588263792164,
        "medical_kits": 0.9309634833161752
      }
    }
  },
  "evaluation": {
    "generated_at": "2026-10-18T14:12:15.242362+00:00",
    "model_sha256": "c34d5446eec133299d7427aa736cfa75bf3ea8f3753ff2b883dee40dfa5377ab",
    "artifact_name": "demand_ensemble_v2.json",
    "dataset_sha256": "7ac56260bfd57b636b48cd90457db008e508bd4bb98a040489765fd0a3a1b992",
    "source": "synthetic held-out labels; not real-world accuracy",
    "holdout_event": "2023_Michaung",
    "rows": 16513,
    "tree_count": 128,
    "ml_rows": 16513,
    "rule_fallback_rows": 0,
    "runtime_mae_units": {
      "water_litres": 122.4377078665291,
      "food_rations": 92.68843214437118,
      "medical_kits": 10.896768606552392
    },
    "runtime_baseline_mae_units": {
      "water_litres": 3647.5320977412,
      "food_rations": 1843.6522291527895,
      "medical_kits": 91.53947556470672
    },
    "interval_coverage_ml_rows": {
      "water_litres": 0.8981408587173741,
      "food_rations": 0.9029249682068673,
      "medical_kits": 0.9390177435959547
    },
    "evaluation_seconds": 6.946183000000019,
    "repeated_conditions_inference": {
      "uncached": {
        "median_ms": 0.31089999993128004,
        "p95_ms": 0.37750000001324224
      },
      "cached": {
        "median_ms": 0.0059000003602704965,
        "p95_ms": 0.006499999926745659
      }
    }
  },
  "evaluation_status": "verified",
  "reproduce_command": "python -m backend.ml_pipeline.evaluate_portable_model --save",
  "limitations": [
    "Training and evaluation labels are synthetic.",
    "Relief demand is predicted; flood extent and depth use scenario calculations.",
    "Held-out synthetic errors do not establish accuracy on observed floods.",
    "Coverage is marginal per resource, not a guarantee for a new event."
  ]
}

## Current run diagnostics
{
  "compute_time_ms": 484.9,
  "time_steps": 5,
  "demand_model": {
    "name": "Event-CV blend: Extra Trees + Random Forest + Ridge / conformal",
    "model_sha256": "c34d5446eec133299d7427aa736cfa75bf3ea8f3753ff2b883dee40dfa5377ab",
    "artifact_name": "demand_ensemble_v2.json",
    "component_weights": [
      [
        0,
        0,
        1
      ],
      [
        0,
        0,
        1
      ],
      [
        0,
        0.7,
        0.3
      ]
    ],
    "components": [
      "Extra Trees",
      "Random Forest",
      "Ridge"
    ],
    "training_data": "synthetic",
    "validated_for_live_use": false,
    "features": [
      "Rainfall_mm_hr",
      "Flood_Depth_m",
      "Pop_Density_sqkm",
      "Vulnerability_Score"
    ],
    "tree_count": 128,
    "dataset_sha256": "7ac56260bfd57b636b48cd90457db008e508bd4bb98a040489765fd0a3a1b992",
    "load_error": null,
    "evaluation": {
      "holdout_event": "2023_Michaung",
      "training_rows": 28865,
      "calibration_rows": 9622,
      "test_rows": 16513,
      "source": "synthetic labels; no observed flood or relief ground truth",
      "selection": "Convex weights selected using GroupKFold out-of-event predictions on fitting rows only.",
      "cross_validation": [
        {
          "held_out_events": [
            "2015_Deluge"
          ],
          "rows": 10298
        },
        {
          "held_out_events": [
            "2020_Nivar"
          ],
          "rows": 6233
        },
        {
          "held_out_events": [
            "2021_Monsoon_Peak"
          ],
          "rows": 6190
        },
        {
          "held_out_events": [
            "Flash_Cloudburst"
          ],
          "rows": 6144
        }
      ],
      "component_weights": [
        [
          0,
          0,
          1
        ],
        [
          0,
          0,
          1
        ],
        [
          0,
          0.7,
          0.3
        ]
      ],
      "mae_units": {
        "water_litres": 122.43661563395709,
        "food_rations": 92.68714903890394,
        "medical_kits": 10.798392661195374
      },
      "r2": {
        "water_litres": 0.998536498293769,
        "food_rations": 0.9986536386987032,
        "medical_kits": 0.9686385886611961
      },
      "baseline_mae_units": {
        "water_litres": 3647.5320977412,
        "food_rations": 1843.6522291527895,
        "medical_kits": 92.03602737237328
      },
      "interval_coverage": {
        "water_litres": 0.8973536001937867,
        "food_rations": 0.9022588263792164,
        "medical_kits": 0.9309634833161752
      }
    }
  },
  "ml_predictions": 17,
  "rule_predictions": 43
}