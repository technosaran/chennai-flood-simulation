import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

def generate_synthetic_dataset(num_samples=10000):
    print("Generating synthetic historical Chennai flood dataset...")
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
    csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'chennai_historical_floods.csv')
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path}")
    return df

def train_model(df):
    print("Training Random Forest AI Model...")
    
    X = df[['Rainfall_mm_hr', 'Flood_Depth_m', 'Pop_Density_sqkm', 'Vulnerability_Score', 'Shelter_Occupancy']]
    y = df[['Target_Water_L', 'Target_Food_Rations', 'Target_MedKits']]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Using Random Forest for multi-output regression
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions, multioutput='raw_values')
    r2 = r2_score(y_test, predictions, multioutput='raw_values')
    
    print("\n=== AI Model Training Complete ===")
    print(f"Water Demand   - MAE: {mae[0]:.2f} L, R2 Score: {r2[0]:.4f}")
    print(f"Food Demand    - MAE: {mae[1]:.2f} pk, R2 Score: {r2[1]:.4f}")
    print(f"MedKit Demand  - MAE: {mae[2]:.2f} kt, R2 Score: {r2[2]:.4f}")
    
    # Save the trained model
    os.makedirs(os.path.join(os.path.dirname(__file__), 'models'), exist_ok=True)
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'resource_demand_model.joblib')
    joblib.dump(model, model_path)
    print(f"Trained model saved to {model_path}")

if __name__ == "__main__":
    dataset = generate_synthetic_dataset()
    train_model(dataset)
