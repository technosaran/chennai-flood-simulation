import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import joblib
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score

# ==========================================
# 1. Historical Dataset Generation (2015-2023)
# ==========================================
def generate_historical_dataset(num_samples=15000):
    print("Generating SYNTHETIC event-inspired Chennai data; this is not observed historical ground truth...")
    np.random.seed(42)
    
    # Define historical events to sample from
    events = [
        {"name": "2015_Deluge", "rain_mean": 350, "rain_std": 100, "depth_mean": 2.5, "depth_std": 0.8},
        {"name": "2020_Nivar", "rain_mean": 150, "rain_std": 50, "depth_mean": 1.0, "depth_std": 0.5},
        {"name": "2023_Michaung", "rain_mean": 400, "rain_std": 80, "depth_mean": 2.0, "depth_std": 0.6},
        {"name": "Monsoon_Baseline", "rain_mean": 50, "rain_std": 20, "depth_mean": 0.2, "depth_std": 0.1},
    ]
    
    # Wards data (vulnerability & density)
    wards = [
        {"name": "Velachery", "density": 25000, "vuln": 0.95},
        {"name": "T_Nagar", "density": 32000, "vuln": 0.85},
        {"name": "Adyar", "density": 18000, "vuln": 0.70},
        {"name": "Tambaram", "density": 20000, "vuln": 0.80},
        {"name": "Mylapore", "density": 28000, "vuln": 0.60},
    ]

    data = []
    for _ in range(num_samples):
        event = np.random.choice(events, p=[0.3, 0.2, 0.3, 0.2])
        ward = np.random.choice(wards)
        
        rain = max(0, np.random.normal(event["rain_mean"], event["rain_std"]))
        depth = max(0, np.random.normal(event["depth_mean"], event["depth_std"]))
        
        # Adjust depth based on vulnerability (low lying areas flood more)
        depth = depth * ward["vuln"]
        
        # People seeking shelter (5% to 15% of density depending on depth)
        shelter_pct = np.clip(depth * 0.05 * np.random.uniform(0.8, 1.2), 0, 0.20)
        shelter_occupancy = int(ward["density"] * shelter_pct)
        
        # Synthetic demand targets derived from planning rules and random stress factors.
        # 1. Water: Baseline 3L + 1L extra for high temp/humidity + contamination factor
        water = shelter_occupancy * (3.0 + (depth * 0.5)) + np.random.normal(0, shelter_occupancy * 0.1)
        # 2. Food: 3 Rations + spoilage factor in deep floods
        food = shelter_occupancy * (3.0 + (depth * 0.2)) + np.random.normal(0, shelter_occupancy * 0.05)
        # 3. Medical: Baseline + waterborne disease surge in 2015 & 2023
        disease_factor = 2.0 if event["name"] in ["2015_Deluge", "2023_Michaung"] else 1.0
        meds = shelter_occupancy * (0.02 * disease_factor * ward["vuln"]) + np.random.normal(0, 5)
        
        data.append({
            'Year': event["name"],
            'Ward': ward["name"],
            'Rainfall_mm_hr': rain,
            'Flood_Depth_m': depth,
            'Pop_Density_sqkm': ward["density"],
            'Vulnerability_Score': ward["vuln"],
            'Shelter_Occupancy': max(0, shelter_occupancy),
            'Target_Water_L': max(0, water),
            'Target_Food_Rations': max(0, food),
            'Target_MedKits': max(0, meds)
        })
        
    df = pd.DataFrame(data)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'dataset'), exist_ok=True)
    csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'chennai_historical_2015_2023.csv')
    df.to_csv(csv_path, index=False)
    print(f"Synthetic Dataset saved to {csv_path}")
    return df

# ==========================================
# 2. PyTorch DNN Model
# ==========================================
class SupplyDemandDNN(nn.Module):
    def __init__(self, input_dim, output_dim):
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

# ==========================================
# 3. Train Advanced Ensemble (DNN, XGBoost, RF)
# ==========================================
def train_ensemble(df):
    print("Training Advanced AI Ensemble Models (XGBoost, Random Forest, PyTorch DNN)...")
    
    features = ['Rainfall_mm_hr', 'Flood_Depth_m', 'Pop_Density_sqkm', 'Vulnerability_Score', 'Shelter_Occupancy']
    targets = ['Target_Water_L', 'Target_Food_Rations', 'Target_MedKits']
    
    X = df[features].values
    y = df[targets].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(scaler, os.path.join(model_dir, 'ensemble_scaler.joblib'))
    
    # 3.1 Train XGBoost
    print("Training XGBoost MultiOutput Regressor...")
    xgb_model = xgb.XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.05, n_jobs=-1, random_state=42)
    xgb_model.fit(X_train_scaled, y_train)
    xgb_preds = xgb_model.predict(X_test_scaled)
    joblib.dump(xgb_model, os.path.join(model_dir, 'xgb_model.joblib'))
    
    # 3.2 Train Random Forest
    print("Training Random Forest...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_train_scaled, y_train)
    rf_preds = rf_model.predict(X_test_scaled)
    joblib.dump(rf_model, os.path.join(model_dir, 'rf_model.joblib'))
    
    # 3.3 Train PyTorch DNN
    print("Training PyTorch Deep Neural Network...")
    X_train_t = torch.FloatTensor(X_train_scaled)
    y_train_t = torch.FloatTensor(y_train)
    X_test_t = torch.FloatTensor(X_test_scaled)
    
    train_dataset = torch.utils.data.TensorDataset(X_train_t, y_train_t)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    dnn_model = SupplyDemandDNN(input_dim=len(features), output_dim=len(targets))
    criterion = nn.HuberLoss() # Better for outliers in disaster data
    optimizer = optim.AdamW(dnn_model.parameters(), lr=0.005, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=10, factor=0.5)
    
    epochs = 200
    for epoch in range(epochs):
        dnn_model.train()
        epoch_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = dnn_model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        scheduler.step(epoch_loss)
        
    dnn_model.eval()
    with torch.no_grad():
        dnn_preds = dnn_model(X_test_t).numpy()
    
    torch.save(dnn_model.state_dict(), os.path.join(model_dir, 'dnn_advanced.pt'))
    
    # 3.4 Ensemble Stacking (Average predictions)
    print("\n=== Ensemble Evaluation (Test Set) ===")
    ensemble_preds = (xgb_preds + rf_preds + dnn_preds) / 3.0
    
    mae_water = mean_absolute_error(y_test[:, 0], ensemble_preds[:, 0])
    mae_food = mean_absolute_error(y_test[:, 1], ensemble_preds[:, 1])
    mae_meds = mean_absolute_error(y_test[:, 2], ensemble_preds[:, 2])
    
    r2_water = r2_score(y_test[:, 0], ensemble_preds[:, 0])
    r2_food = r2_score(y_test[:, 1], ensemble_preds[:, 1])
    r2_meds = r2_score(y_test[:, 2], ensemble_preds[:, 2])
    
    print(f"Water Demand  | MAE: {mae_water:.2f} L | R2: {r2_water:.4f}")
    print(f"Food Demand   | MAE: {mae_food:.2f} pkt | R2: {r2_food:.4f}")
    print(f"MedKit Demand | MAE: {mae_meds:.2f} kit | R2: {r2_meds:.4f}")
    print("\nAll models and ensemble weights saved successfully!")

if __name__ == "__main__":
    df = generate_historical_dataset()
    train_ensemble(df)
