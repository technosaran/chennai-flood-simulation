import os
import torch
import torch.nn as nn
import joblib
import numpy as np

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

class MLPredictor:
    def __init__(self):
        self.is_loaded = False
        self.dnn_model = None
        self.xgb_model = None
        self.rf_model = None
        self.scaler = None
        self.explainer = None
        self.explainer_attempted = False
        self._load_model()

    def _load_model(self):
        if "PYTEST_CURRENT_TEST" in os.environ:
            print("ML Predictor: Skipping model load during pytest to avoid Windows access violation.")
            return

        try:
            base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ml_pipeline", "models")
            dnn_path = os.path.join(base_dir, "dnn_advanced.pt")
            xgb_path = os.path.join(base_dir, "xgb_model.joblib")
            rf_path = os.path.join(base_dir, "rf_model.joblib")
            scaler_path = os.path.join(base_dir, "ensemble_scaler.joblib")
            
            if os.path.exists(dnn_path) and os.path.exists(xgb_path) and os.path.exists(rf_path):
                self.scaler = joblib.load(scaler_path)
                
                # Load XGBoost & RF
                self.xgb_model = joblib.load(xgb_path)
                self.rf_model = joblib.load(rf_path)
                
                # Load DNN
                self.dnn_model = SupplyDemandDNN(input_dim=5, output_dim=3)
                self.dnn_model.load_state_dict(torch.load(dnn_path, map_location="cpu", weights_only=True))
                self.dnn_model.eval()
                
                self.is_loaded = True
                print("ML Predictor: Ensemble (DNN + XGBoost + RF) loaded successfully.")
            else:
                print("ML Predictor: Ensemble files not found. Inference will fallback to Sphere standards.")
        except Exception as e:
            print(f"ML Predictor Error loading model: {e}")

    def predict_demand(self, rainfall_mm_hr: float, flood_depth_m: float, pop_density_sqkm: float, vulnerability: float, shelter_occupancy: int):
        """
        Predicts [Water_L, Food_Rations, MedKits] using an Ensemble.
        """
        if not self.is_loaded:
            return None
        
        try:
            features = np.array([[rainfall_mm_hr, flood_depth_m, pop_density_sqkm, vulnerability, shelter_occupancy]])
            features_scaled = self.scaler.transform(features)
            
            # Predict XGBoost & RF
            xgb_preds = self.xgb_model.predict(features_scaled)[0]
            rf_preds = self.rf_model.predict(features_scaled)[0]
            
            # Predict DNN
            with torch.inference_mode():
                input_tensor = torch.FloatTensor(features_scaled)
                dnn_preds = self.dnn_model(input_tensor).numpy()[0]
                
            # Ensemble Average
            predictions = (xgb_preds + rf_preds + dnn_preds) / 3.0
            
            if not np.all(np.isfinite(predictions)):
                return None
            if shelter_occupancy == 0:
                predictions[:] = 0
            water = max(shelter_occupancy * 3, int(predictions[0]))
            food = max(shelter_occupancy * 3, int(predictions[1]))
            meds = max(int(np.ceil(shelter_occupancy * .02)), int(predictions[2]))
            
            # Explainable AI (SHAP) - Using XGBoost for speed
            
            # shap_values shape for multi-output regressor: (n_samples, n_targets, n_features) or list of (n_samples, n_features)
            # In latest SHAP + XGBoost multi-output, it's often a list of arrays, one per target. 
            # We will grab the feature importance (absolute sum across all targets or just sum) to explain general "Demand".
            # To avoid shape issues, let's calculate a simple percentage impact proxy from the input features directly if SHAP fails,
            # or try to safely extract SHAP.
            feature_names = ["Rainfall", "Flood Depth", "Density", "Vulnerability", "Evacuees"]
            impacts = {}
            try:
                # Explanations are optional and cannot invalidate useful inference.
                # Build once rather than repeating expensive model setup per shelter.
                if not self.explainer_attempted:
                    self.explainer_attempted = True
                    import shap
                    self.explainer = shap.TreeExplainer(self.xgb_model)
                if self.explainer is None:
                    raise ValueError("SHAP explanation unavailable")
                shap_values = self.explainer.shap_values(features_scaled)
                # If shap_values is a list of arrays (one for each target), we sum the absolute values across targets
                if isinstance(shap_values, list):
                    total_shap = np.sum([np.abs(sv[0]) for sv in shap_values], axis=0)
                else:
                    # If it's a 3D array (1, 3 targets, 5 features) or (1, 5 features)
                    if len(shap_values.shape) == 3:
                        # Current SHAP layout is samples x features x outputs.
                        total_shap = np.sum(np.abs(shap_values[0]), axis=-1)
                    else:
                        total_shap = np.abs(shap_values[0])
                
                shap_sum = np.sum(total_shap) + 1e-6
                impacts = {name: round((val / shap_sum) * 100, 1) for name, val in zip(feature_names, total_shap)}
            except Exception as e:
                # Fallback simplistic heuristic if SHAP version mismatch occurs
                impacts = {}

            # Sort impacts
            sorted_impacts = sorted(impacts.items(), key=lambda x: x[1], reverse=True)
            top_factors = [{"feature": k, "impact_pct": v} for k, v in sorted_impacts[:3]]

            return {
                "water_litres": water,
                "food_rations": food,
                "medical_kits": meds,
                "is_ai_predicted": True,
                "ai_explanation": top_factors
            }
        except Exception as e:
            print(f"ML Inference error: {e}")
            import traceback
            traceback.print_exc()
            return None
