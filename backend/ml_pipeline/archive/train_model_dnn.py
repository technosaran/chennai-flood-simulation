import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

class SupplyDemandDNN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(SupplyDemandDNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.2),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.net(x)

def generate_synthetic_dataset(num_samples=10000):
    print("Generating synthetic historical Chennai flood dataset for DNN...")
    np.random.seed(42)
    
    # Features
    rainfall_intensity = np.random.uniform(20, 250, num_samples) # mm/hr
    flood_depth = np.random.uniform(0.1, 3.5, num_samples) # meters
    population_density = np.random.uniform(5000, 35000, num_samples) # per sq km
    ward_vulnerability = np.random.uniform(0.1, 1.0, num_samples) # 0 to 1
    shelter_occupancy = np.random.uniform(100, 5000, num_samples) # people
    
    # Target Variables (Complex non-linear relationships with some noise)
    water_demand = (shelter_occupancy * 3.5) + (rainfall_intensity * 10) + (flood_depth * 500) * ward_vulnerability + np.random.normal(0, 100, num_samples)
    food_demand = (shelter_occupancy * 2.0) + (flood_depth * 300) * ward_vulnerability + np.random.normal(0, 50, num_samples)
    medkit_demand = (shelter_occupancy * 0.1) + (flood_depth * 100) * (ward_vulnerability ** 2) + np.random.normal(0, 10, num_samples)
    
    # Ensure no negative values
    water_demand = np.maximum(0, water_demand)
    food_demand = np.maximum(0, food_demand)
    medkit_demand = np.maximum(0, medkit_demand)
    
    df = pd.DataFrame({
        'Rainfall_mm_hr': rainfall_intensity,
        'Flood_Depth_m': flood_depth,
        'Pop_Density_sqkm': population_density,
        'Vulnerability_Score': ward_vulnerability,
        'Shelter_Occupancy': shelter_occupancy,
        'Target_Water_L': water_demand,
        'Target_Food_Rations': food_demand,
        'Target_MedKits': medkit_demand
    })
    
    os.makedirs(os.path.join(os.path.dirname(__file__), 'dataset'), exist_ok=True)
    csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'chennai_historical_floods_dnn.csv')
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path}")
    return df

def train_model(df):
    print("Training PyTorch Deep Neural Network AI Model...")
    
    features = ['Rainfall_mm_hr', 'Flood_Depth_m', 'Pop_Density_sqkm', 'Vulnerability_Score', 'Shelter_Occupancy']
    targets = ['Target_Water_L', 'Target_Food_Rations', 'Target_MedKits']
    
    X = df[features].values
    y = df[targets].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler for inference
    os.makedirs(os.path.join(os.path.dirname(__file__), 'models'), exist_ok=True)
    scaler_path = os.path.join(os.path.dirname(__file__), 'models', 'dnn_scaler.joblib')
    joblib.dump(scaler, scaler_path)
    
    # Convert to PyTorch tensors
    X_train_t = torch.FloatTensor(X_train_scaled)
    y_train_t = torch.FloatTensor(y_train)
    X_test_t = torch.FloatTensor(X_test_scaled)
    y_test_t = torch.FloatTensor(y_test)
    
    # Create DataLoader
    train_dataset = torch.utils.data.TensorDataset(X_train_t, y_train_t)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True)
    
    # Initialize Model
    model = SupplyDemandDNN(input_dim=len(features), output_dim=len(targets))
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    
    epochs = 150
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        if (epoch+1) % 50 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(train_loader):.4f}")
            
    # Evaluation
    model.eval()
    with torch.no_grad():
        predictions = model(X_test_t)
        mae = torch.mean(torch.abs(predictions - y_test_t), dim=0)
        
    print("\n=== PyTorch DNN Training Complete ===")
    print(f"Water Demand   - MAE: {mae[0]:.2f} L")
    print(f"Food Demand    - MAE: {mae[1]:.2f} pk")
    print(f"MedKit Demand  - MAE: {mae[2]:.2f} kt")
    
    # Save the trained model
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'dnn_model.pt')
    torch.save(model.state_dict(), model_path)
    print(f"Trained PyTorch model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")

if __name__ == "__main__":
    dataset = generate_synthetic_dataset()
    train_model(dataset)
