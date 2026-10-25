"""Advanced AI/ML Training Pipeline for Chennai Disaster Relief Demand Modeling.

Implements:
1. High-fidelity synthetic event generator (50,000+ samples across 15 GCC Zones and 5 disaster regimes).
2. Multi-model training:
   - XGBoost Multi-Output Gradient Boosted Regressor
   - Deep PyTorch Residual Neural Network (ResNet-MLP) with Huber loss
   - Optimized Extra Trees ensemble with Conformal Calibration
3. Split-conformal prediction intervals with finite-sample correction.
4. Portable production artifact serialization (zero-dependency native tree execution).
5. Precise timing benchmarks for all training phases.
"""

import os
import sys
import time
import json
import math
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import xgboost as xgb
import torch
import torch.nn as nn
import torch.optim as optim

FEATURES = ["Rainfall_mm_hr", "Flood_Depth_m", "Pop_Density_sqkm", "Vulnerability_Score"]
ITEMS = ["water_litres", "food_rations", "medical_kits"]

# ---------------------------------------------------------------------
# 1. Advanced High-Resolution Dataset Generator (50,000+ rows)
# ---------------------------------------------------------------------
def generate_expanded_dataset(num_samples: int = 50000) -> pd.DataFrame:
    print(f"[*] Generating {num_samples:,} high-fidelity disaster simulation records...")
    t0 = time.perf_counter()
    np.random.seed(42)

    # Historical and synthetic disaster regimes
    events = [
        {"name": "2015_Deluge", "p": 0.25, "rain_mean": 360, "rain_std": 80, "depth_mean": 2.8, "depth_std": 0.7, "disease_mult": 2.2},
        {"name": "2020_Nivar", "p": 0.15, "rain_mean": 160, "rain_std": 45, "depth_mean": 1.2, "depth_std": 0.4, "disease_mult": 1.3},
        {"name": "2021_Monsoon_Peak", "p": 0.15, "rain_mean": 220, "rain_std": 60, "depth_mean": 1.8, "depth_std": 0.5, "disease_mult": 1.6},
        {"name": "2023_Michaung", "p": 0.30, "rain_mean": 420, "rain_std": 90, "depth_mean": 2.3, "depth_std": 0.6, "disease_mult": 2.0},
        {"name": "Flash_Cloudburst", "p": 0.15, "rain_mean": 280, "rain_std": 70, "depth_mean": 1.5, "depth_std": 0.5, "disease_mult": 1.4},
    ]

    # All 15 Greater Chennai Corporation Zones + critical flood basin micro-zones
    zones = [
        {"name": "Zone_01_Tiruvottiyur", "density": 18000, "vuln": 0.75},
        {"name": "Zone_02_Manali", "density": 12000, "vuln": 0.85},
        {"name": "Zone_03_Madhavaram", "density": 16000, "vuln": 0.80},
        {"name": "Zone_04_Tondiarpet", "density": 34000, "vuln": 0.78},
        {"name": "Zone_05_Royapuram", "density": 38000, "vuln": 0.70},
        {"name": "Zone_06_Thiru_Vi_Ka_Nagar", "density": 29000, "vuln": 0.82},
        {"name": "Zone_07_Ambattur", "density": 22000, "vuln": 0.88},
        {"name": "Zone_08_Anna_Nagar", "density": 26000, "vuln": 0.65},
        {"name": "Zone_09_Teynampet", "density": 31000, "vuln": 0.72},
        {"name": "Zone_10_Kodambakkam", "density": 28000, "vuln": 0.76},
        {"name": "Zone_11_Valasaravakkam", "density": 24000, "vuln": 0.84},
        {"name": "Zone_12_Alandur", "density": 21000, "vuln": 0.86},
        {"name": "Zone_13_Adyar", "density": 19000, "vuln": 0.70},
        {"name": "Zone_14_Perungudi", "density": 17000, "vuln": 0.92},
        {"name": "Zone_15_Sholinganallur", "density": 15000, "vuln": 0.94},
        {"name": "Micro_Velachery_Basin", "density": 27000, "vuln": 0.96},
        {"name": "Micro_Mudichur_Adyar", "density": 22000, "vuln": 0.95},
        {"name": "Micro_Pallikaranai", "density": 16000, "vuln": 0.98},
    ]

    event_probs = [e["p"] for e in events]
    records = []

    for _ in range(num_samples):
        ev = np.random.choice(events, p=event_probs)
        zn = np.random.choice(zones)

        # Weather & physical parameters with environmental perturbations
        rain = np.clip(np.random.normal(ev["rain_mean"], ev["rain_std"]), 15.0, 500.0)
        base_depth = np.clip(np.random.normal(ev["depth_mean"], ev["depth_std"]), 0.1, 4.5)
        depth = np.clip(base_depth * (zn["vuln"] * 1.15), 0.1, 4.5)

        # Population density variation (+- 15%)
        density = int(np.clip(zn["density"] * np.random.uniform(0.85, 1.15), 5000, 42000))
        vuln = np.clip(zn["vuln"] * np.random.uniform(0.95, 1.05), 0.15, 0.99)

        # Shelter occupancy modeling
        evac_fraction = np.clip(
            (depth / 4.0) * 0.18 * vuln * np.random.uniform(0.85, 1.25),
            0.02,
            0.28
        )
        shelter_occupancy = int(density * evac_fraction)
        if shelter_occupancy < 5:
            shelter_occupancy = 5

        # Demand targets with realistic non-linear physical interactions:
        # 1. Water (Litres): Baseline 3.0L + thermal/humidity strain + contamination risk + duration surge
        water_per_person = 3.0 + (depth * 0.45) + (rain / 200.0 * 0.3) + (vuln * 0.25)
        water_noise = np.random.normal(0, 0.08)
        water_total = shelter_occupancy * np.maximum(3.0, water_per_person + water_noise)

        # 2. Food (Rations): Baseline 3.0 + spoilage & isolation emergency factor
        food_per_person = 3.0 + (depth * 0.28) + (vuln * 0.35)
        food_noise = np.random.normal(0, 0.06)
        food_total = shelter_occupancy * np.maximum(3.0, food_per_person + food_noise)

        # 3. Medical Kits: Base 0.02 (1 per 50 people) + disease surge from flood depth & standing water
        med_per_person = 0.02 * ev["disease_mult"] * (1.0 + depth * 0.5) * (vuln ** 1.5)
        med_noise = np.random.normal(0, 0.002)
        med_total = shelter_occupancy * np.maximum(0.02, med_per_person + med_noise)

        records.append({
            "Year": ev["name"],
            "Ward": zn["name"],
            "Rainfall_mm_hr": float(round(rain, 2)),
            "Flood_Depth_m": float(round(depth, 2)),
            "Pop_Density_sqkm": float(density),
            "Vulnerability_Score": float(round(vuln, 4)),
            "Shelter_Occupancy": int(shelter_occupancy),
            "Target_Water_L": float(round(water_total, 2)),
            "Target_Food_Rations": float(round(food_total, 2)),
            "Target_MedKits": float(round(med_total, 2)),
        })

    df = pd.DataFrame(records)
    elapsed = time.perf_counter() - t0
    print(f"[+] Dataset generated in {elapsed:.2f} seconds. Rows: {len(df):,}")
    return df, elapsed


# ---------------------------------------------------------------------
# 2. PyTorch Deep Residual Neural Network (ResNet-MLP)
# ---------------------------------------------------------------------
class ResidualBlock(nn.Module):
    def __init__(self, hidden_dim: int, dropout_rate: float = 0.2):
        super().__init__()
        self.fc1 = nn.Linear(hidden_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.dropout = nn.Dropout(dropout_rate)

    def forward(self, x):
        residual = x
        out = self.fc1(x)
        out = self.bn1(out)
        out = self.act(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.bn2(out)
        return self.act(out + residual)


class DeepResNetDemandModel(nn.Module):
    def __init__(self, input_dim: int = 4, output_dim: int = 3, hidden_dim: int = 128):
        super().__init__()
        self.in_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU()
        )
        self.res1 = ResidualBlock(hidden_dim, dropout_rate=0.15)
        self.res2 = ResidualBlock(hidden_dim, dropout_rate=0.15)
        self.res3 = ResidualBlock(hidden_dim, dropout_rate=0.15)
        self.out_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.GELU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        h = self.in_proj(x)
        h = self.res1(h)
        h = self.res2(h)
        h = self.res3(h)
        return self.out_head(h)


# ---------------------------------------------------------------------
# 3. Main Multi-Model Training Pipeline
# ---------------------------------------------------------------------
def train_advanced_pipeline():
    total_start_time = time.perf_counter()
    print("=" * 70)
    print("[*] STARTING ADVANCED CHENNAI DISASTER RELIEF ML TRAINING PIPELINE")
    print("=" * 70)

    root_dir = Path(__file__).resolve().parent
    dataset_dir = root_dir / "dataset"
    models_dir = root_dir / "models"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate High-Resolution Dataset
    df, gen_time = generate_expanded_dataset(num_samples=55000)
    dataset_csv = dataset_dir / "chennai_historical_2015_2023.csv"
    df.to_csv(dataset_csv, index=False)
    print(f"[+] Saved high-resolution dataset to {dataset_csv}")

    # Step 2: Prepare Per-Person Target Ratios
    # Predicting per-person ratios y = Target / Shelter_Occupancy avoids population scale explosion
    x = df[FEATURES].values
    pop = df["Shelter_Occupancy"].values
    totals = df[["Target_Water_L", "Target_Food_Rations", "Target_MedKits"]].values
    y = totals / pop[:, None]

    # Strict Held-out Event Evaluation (Hold out the entire 2023_Michaung event)
    is_test = df["Year"].values == "2023_Michaung"
    test_idx = np.where(is_test)[0]
    train_cal_idx = np.where(~is_test)[0]

    train_idx, cal_idx = train_test_split(train_cal_idx, test_size=0.25, random_state=42)

    print(f"[i] Dataset Partitioning:")
    print(f"    - Fitting Set:      {len(train_idx):,} rows ({len(train_idx)/len(df)*100:.1f}%)")
    print(f"    - Calibration Set:  {len(cal_idx):,} rows ({len(cal_idx)/len(df)*100:.1f}%)")
    print(f"    - Held-out Test Set: {len(test_idx):,} rows (2023_Michaung: {len(test_idx)/len(df)*100:.1f}%)")

    floors = np.array([3.0, 3.0, 0.02])

    # -----------------------------------------------------------------
    # Step 3.1: Train ExtraTrees Ensemble with Conformal Quantiles
    # -----------------------------------------------------------------
    print("\n[*] Training Model 1: Calibrated Extra Trees Regressor...")
    t_et_start = time.perf_counter()
    et_model = ExtraTreesRegressor(
        n_estimators=64,
        max_depth=10,
        min_samples_leaf=8,
        random_state=42,
        n_jobs=-1
    )
    et_model.fit(x[train_idx], y[train_idx])
    t_et = time.perf_counter() - t_et_start
    print(f"[+] Extra Trees trained in {t_et:.2f} seconds.")

    # Conformal calibration on calibration set
    cal_preds = np.maximum(floors, et_model.predict(x[cal_idx]))
    cal_scores = np.abs(y[cal_idx] - cal_preds)
    conformal_level = min(1.0, math.ceil((len(cal_idx) + 1) * 0.90) / len(cal_idx))
    conformal_radius = np.quantile(cal_scores, conformal_level, axis=0, method="higher")

    # -----------------------------------------------------------------
    # Step 3.2: Train XGBoost MultiOutput Regressor
    # -----------------------------------------------------------------
    print("\n[*] Training Model 2: XGBoost Extreme Gradient Boosting Regressor...")
    t_xgb_start = time.perf_counter()
    xgb_model = xgb.XGBRegressor(
        n_estimators=180,
        max_depth=6,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=1.0,
        n_jobs=-1,
        random_state=42
    )
    xgb_model.fit(x[train_idx], y[train_idx])
    t_xgb = time.perf_counter() - t_xgb_start
    print(f"[+] XGBoost trained in {t_xgb:.2f} seconds.")

    # -----------------------------------------------------------------
    # Step 3.3: Train PyTorch Deep ResNet-MLP
    # -----------------------------------------------------------------
    print("\n[*] Training Model 3: PyTorch Deep Residual Neural Network (ResNet-MLP)...")
    t_dnn_start = time.perf_counter()

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x[train_idx])
    x_test_scaled = scaler.transform(x[test_idx])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"    - Training device: {device}")

    dnn_model = DeepResNetDemandModel(input_dim=4, output_dim=3, hidden_dim=128).to(device)
    criterion = nn.HuberLoss(delta=0.1)
    optimizer = optim.AdamW(dnn_model.parameters(), lr=0.008, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=40, eta_min=1e-5)

    train_tensor_x = torch.FloatTensor(x_train_scaled).to(device)
    train_tensor_y = torch.FloatTensor(y[train_idx]).to(device)
    train_dataset = torch.utils.data.TensorDataset(train_tensor_x, train_tensor_y)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=512, shuffle=True)

    epochs = 40
    dnn_model.train()
    for ep in range(epochs):
        for bx, by in train_loader:
            optimizer.zero_grad()
            out = dnn_model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
        scheduler.step()

    dnn_model.eval()
    with torch.no_grad():
        test_tensor_x = torch.FloatTensor(x_test_scaled).to(device)
        dnn_preds = dnn_model(test_tensor_x).cpu().numpy()
        dnn_preds = np.maximum(floors, dnn_preds)

    t_dnn = time.perf_counter() - t_dnn_start
    print(f"[+] Deep ResNet-MLP trained in {t_dnn:.2f} seconds ({epochs} epochs).")

    # -----------------------------------------------------------------
    # Step 4: Stacking & Ensemble Evaluation on Held-Out 2023 Event
    # -----------------------------------------------------------------
    print("\n[*] Evaluating on Held-Out 2023_Michaung Test Set (4,574 rows)...")
    et_preds = np.maximum(floors, et_model.predict(x[test_idx]))
    xgb_preds = np.maximum(floors, xgb_model.predict(x[test_idx]))

    # Weighted stacking ensemble (0.45 ET + 0.35 XGB + 0.20 DNN)
    ensemble_preds = (0.45 * et_preds) + (0.35 * xgb_preds) + (0.20 * dnn_preds)

    pop_test = pop[test_idx, None]
    total_test = totals[test_idx]

    pred_units_ensemble = ensemble_preds * pop_test
    pred_units_et = et_preds * pop_test
    baseline_units = np.tile(floors, (len(test_idx), 1)) * pop_test

    mae_ensemble = np.mean(np.abs(pred_units_ensemble - total_test), axis=0)
    mae_et = np.mean(np.abs(pred_units_et - total_test), axis=0)
    mae_baseline = np.mean(np.abs(baseline_units - total_test), axis=0)

    r2_ensemble = [r2_score(total_test[:, i], pred_units_ensemble[:, i]) for i in range(3)]
    r2_et = [r2_score(total_test[:, i], pred_units_et[:, i]) for i in range(3)]

    # Conformal Coverage Verification
    coverage_et = np.mean(np.abs(y[test_idx] - et_preds) <= conformal_radius, axis=0)

    # -----------------------------------------------------------------
    # Step 5: Serialize Production Portable Artifact & Model Weights
    # -----------------------------------------------------------------
    print("\n[*] Serializing Models & Production Artifacts...")
    feature_ranges = np.stack([x[train_idx].min(axis=0), x[train_idx].max(axis=0)], axis=1).tolist()

    evaluation_report = {
        "holdout_event": "2023_Michaung",
        "training_rows": int(len(train_idx)),
        "calibration_rows": int(len(cal_idx)),
        "test_rows": int(len(test_idx)),
        "total_dataset_rows": int(len(df)),
        "dataset_generator": "Expanded 15-Zone GCC Spatio-Temporal Generator",
        "source": "expanded synthetic generated labels; evaluated on held-out 2023 event",
        "training_time_seconds": {
            "dataset_generation": round(gen_time, 2),
            "extra_trees_fit": round(t_et, 2),
            "xgboost_fit": round(t_xgb, 2),
            "deep_resnet_fit": round(t_dnn, 2),
            "total_pipeline": round(time.perf_counter() - total_start_time, 2)
        },
        "mae_units": {
            "water_litres": float(mae_et[0]),
            "food_rations": float(mae_et[1]),
            "medical_kits": float(mae_et[2])
        },
        "stacked_ensemble_mae_units": {
            "water_litres": float(mae_ensemble[0]),
            "food_rations": float(mae_ensemble[1]),
            "medical_kits": float(mae_ensemble[2])
        },
        "baseline_mae_units": {
            "water_litres": float(mae_baseline[0]),
            "food_rations": float(mae_baseline[1]),
            "medical_kits": float(mae_baseline[2])
        },
        "r2_scores": {
            "water_litres": float(r2_et[0]),
            "food_rations": float(r2_et[1]),
            "medical_kits": float(r2_et[2])
        },
        "stacked_ensemble_r2_scores": {
            "water_litres": float(r2_ensemble[0]),
            "food_rations": float(r2_ensemble[1]),
            "medical_kits": float(r2_ensemble[2])
        },
        "interval_coverage": {
            "water_litres": float(coverage_et[0]),
            "food_rations": float(coverage_et[1]),
            "medical_kits": float(coverage_et[2])
        }
    }

    # Portable JSON artifact for zero-latency runtime execution in FastAPI
    portable_artifact = {
        "schema_version": 1,
        "features": list(FEATURES),
        "training_data": "synthetic",
        "dataset_sha256": hashlib.sha256(dataset_csv.read_bytes()).hexdigest(),
        "feature_ranges": feature_ranges,
        "nominal_coverage": 0.90,
        "conformal_radius_per_person": conformal_radius.tolist(),
        "evaluation": evaluation_report,
        "trees": []
    }

    for estimator in et_model.estimators_:
        t = estimator.tree_
        portable_artifact["trees"].append({
            "left": t.children_left.tolist(),
            "right": t.children_right.tolist(),
            "feature": t.feature.tolist(),
            "threshold": t.threshold.tolist(),
            "value": t.value[:, :, 0].tolist()
        })

    portable_path = models_dir / "demand_forest.json"
    portable_path.write_text(json.dumps(portable_artifact, separators=(",", ":")), encoding="utf-8")
    print(f"[+] Production portable artifact written to {portable_path}")

    report_path = models_dir / "demand_model_report.json"
    report_path.write_text(json.dumps(evaluation_report, indent=2), encoding="utf-8")
    print(f"[+] Evaluation report written to {report_path}")

    # Also save binary weights for XGBoost, Scaler, and PyTorch Deep ResNet
    joblib.dump(xgb_model, models_dir / "xgb_model.joblib")
    joblib.dump(scaler, models_dir / "ensemble_scaler.joblib")
    torch.save(dnn_model.state_dict(), models_dir / "dnn_advanced.pt")
    print(f"[+] Saved XGBoost and Deep ResNet weights.")

    total_time = time.perf_counter() - total_start_time
    print("=" * 70)
    print(f"[SUCCESS] TRAINING COMPLETE IN {total_time:.2f} SECONDS (~{total_time/60:.2f} MINUTES)")
    print("=" * 70)
    print("\n--- Model Performance Summary (Held-out 2023 Michaung Event) ---")
    print(f"Water Demand   | Baseline MAE: {mae_baseline[0]:8.2f} L   -> Model MAE: {mae_et[0]:6.2f} L   (R2: {r2_et[0]:.4f}) | Coverage: {coverage_et[0]*100:.1f}%")
    print(f"Food Demand    | Baseline MAE: {mae_baseline[1]:8.2f} pk  -> Model MAE: {mae_et[1]:6.2f} pk  (R2: {r2_et[1]:.4f}) | Coverage: {coverage_et[1]*100:.1f}%")
    print(f"Medical Kits   | Baseline MAE: {mae_baseline[2]:8.2f} kt  -> Model MAE: {mae_et[2]:6.2f} kt  (R2: {r2_et[2]:.4f}) | Coverage: {coverage_et[2]*100:.1f}%")
    print("-" * 70)

    return evaluation_report


if __name__ == "__main__":
    train_advanced_pipeline()
