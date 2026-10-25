"""Train advanced multi-model ensemble (XGBoost + Random Forest + Deep Neural Network).

Trains:
1. MultiOutput XGBoost Regressor
2. Random Forest Regressor
3. PyTorch Deep Neural Network (SupplyDemandDNN) with BatchNorm & LeakyReLU
4. StandardScaler for feature normalization

Saves artifacts for MLPredictor (backend/app/services/ml_predictor.py).
"""
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import xgboost as xgb
import torch
import torch.nn as nn
import torch.optim as optim

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "dataset" / "chennai_historical_2015_2023.csv"
MODELS_DIR = ROOT / "models"

FEATURES_5D = ["Rainfall_mm_hr", "Flood_Depth_m", "Pop_Density_sqkm", "Vulnerability_Score", "Shelter_Occupancy"]
TARGETS = ["Target_Water_L", "Target_Food_Rations", "Target_MedKits"]


class SupplyDemandDNN(nn.Module):
    def __init__(self, input_dim=5, output_dim=3):
        super(SupplyDemandDNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.LeakyReLU(0.1),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 256),
            nn.LeakyReLU(0.1),
            nn.BatchNorm1d(256),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.LeakyReLU(0.1),
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.net(x)


def train_advanced():
    t_start = time.perf_counter()
    print("=" * 70)
    print("[*] TRAINING ADVANCED MULTI-MODEL ENSEMBLE (XGB + RF + PYTORCH DNN)")
    print("=" * 70)

    print(f"[*] Loading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    print(f"[+] Loaded {len(df):,} records.")

    # Chronological / Event split: Hold out 2023_Michaung for strict testing
    test_mask = df["Year"] == "2023_Michaung"
    train_mask = ~test_mask

    x_train_raw = df.loc[train_mask, FEATURES_5D].values
    y_train = df.loc[train_mask, TARGETS].values

    x_test_raw = df.loc[test_mask, FEATURES_5D].values
    y_test = df.loc[test_mask, TARGETS].values

    print(f"[*] Training samples: {len(x_train_raw):,} | Test samples (2023_Michaung): {len(x_test_raw):,}")

    # Step 1: Feature Scaling
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_raw)
    x_test_scaled = scaler.transform(x_test_raw)

    # Step 2: Train XGBoost Multi-Output
    print("\n[*] [1/3] Training XGBoost Multi-Output Regressor...")
    t0 = time.perf_counter()
    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(x_train_scaled, y_train)
    xgb_time = time.perf_counter() - t0
    xgb_preds = np.maximum(0, xgb_model.predict(x_test_scaled))
    xgb_mae = mean_absolute_error(y_test, xgb_preds, multioutput="raw_values")
    xgb_r2 = r2_score(y_test, xgb_preds, multioutput="raw_values")
    print(f"[+] XGBoost fit in {xgb_time:.2f}s | Test MAE: Water={xgb_mae[0]:.2f}L, Food={xgb_mae[1]:.2f}pk, Meds={xgb_mae[2]:.2f}kt")

    # Step 3: Train Random Forest
    print("\n[*] [2/3] Training Random Forest Regressor...")
    t0 = time.perf_counter()
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=8,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(x_train_scaled, y_train)
    rf_time = time.perf_counter() - t0
    rf_preds = np.maximum(0, rf_model.predict(x_test_scaled))
    rf_mae = mean_absolute_error(y_test, rf_preds, multioutput="raw_values")
    rf_r2 = r2_score(y_test, rf_preds, multioutput="raw_values")
    print(f"[+] Random Forest fit in {rf_time:.2f}s | Test MAE: Water={rf_mae[0]:.2f}L, Food={rf_mae[1]:.2f}pk, Meds={rf_mae[2]:.2f}kt")

    # Step 4: Train PyTorch Deep Neural Network (SupplyDemandDNN)
    print("\n[*] [3/3] Training PyTorch Deep Neural Network (SupplyDemandDNN)...")
    t0 = time.perf_counter()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"    Target compute device: {device}")

    dnn_model = SupplyDemandDNN(input_dim=5, output_dim=3).to(device)
    criterion = nn.HuberLoss(delta=1.0)
    optimizer = optim.AdamW(dnn_model.parameters(), lr=0.005, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30, eta_min=1e-5)

    dataset_tensor = torch.utils.data.TensorDataset(
        torch.FloatTensor(x_train_scaled),
        torch.FloatTensor(y_train)
    )
    dataloader = torch.utils.data.DataLoader(dataset_tensor, batch_size=512, shuffle=True)

    dnn_model.train()
    epochs = 30
    for ep in range(epochs):
        for bx, by in dataloader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            pred = dnn_model(bx)
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()
        scheduler.step()

    dnn_time = time.perf_counter() - t0
    dnn_model.eval()
    with torch.no_grad():
        test_t = torch.FloatTensor(x_test_scaled).to(device)
        dnn_preds = np.maximum(0, dnn_model(test_t).cpu().numpy())
    dnn_mae = mean_absolute_error(y_test, dnn_preds, multioutput="raw_values")
    dnn_r2 = r2_score(y_test, dnn_preds, multioutput="raw_values")
    print(f"[+] PyTorch DNN trained in {dnn_time:.2f}s ({epochs} epochs) | Test MAE: Water={dnn_mae[0]:.2f}L, Food={dnn_mae[1]:.2f}pk, Meds={dnn_mae[2]:.2f}kt")

    # Step 5: Ensemble Evaluation
    print("\n[*] Evaluating Blended Multi-Model Ensemble on 2023_Michaung...")
    ensemble_preds = (xgb_preds + rf_preds + dnn_preds) / 3.0
    ensemble_mae = mean_absolute_error(y_test, ensemble_preds, multioutput="raw_values")
    ensemble_r2 = r2_score(y_test, ensemble_preds, multioutput="raw_values")

    print("\n" + "=" * 70)
    print("--- MODEL COMPARISON ON HELD-OUT 2023 MICHAUNG TEST SET (28,132 rows) ---")
    print(f"{'Model':25} | {'Water MAE':10} | {'Food MAE':10} | {'Meds MAE':10} | {'Mean R2':8}")
    print("-" * 70)
    print(f"{'XGBoost':25} | {xgb_mae[0]:8.2f} L | {xgb_mae[1]:8.2f} pk | {xgb_mae[2]:8.2f} kt | {np.mean(xgb_r2):.4f}")
    print(f"{'Random Forest':25} | {rf_mae[0]:8.2f} L | {rf_mae[1]:8.2f} pk | {rf_mae[2]:8.2f} kt | {np.mean(rf_r2):.4f}")
    print(f"{'Deep PyTorch DNN':25} | {dnn_mae[0]:8.2f} L | {dnn_mae[1]:8.2f} pk | {dnn_mae[2]:8.2f} kt | {np.mean(dnn_r2):.4f}")
    print(f"{'Stacked 3-Way Ensemble':25} | {ensemble_mae[0]:8.2f} L | {ensemble_mae[1]:8.2f} pk | {ensemble_mae[2]:8.2f} kt | {np.mean(ensemble_r2):.4f}")
    print("=" * 70)

    # Step 6: Save production model weights
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, MODELS_DIR / "ensemble_scaler.joblib")
    joblib.dump(xgb_model, MODELS_DIR / "xgb_model.joblib")
    joblib.dump(rf_model, MODELS_DIR / "rf_model.joblib")
    torch.save(dnn_model.state_dict(), MODELS_DIR / "dnn_advanced.pt")
    print("[+] All model weights and scaler serialized successfully to ml_pipeline/models/")

    total_time = time.perf_counter() - t_start
    print(f"[SUCCESS] Advanced training complete in {total_time:.2f}s (~{total_time/60:.2f} min).")


if __name__ == "__main__":
    train_advanced()
