"""High-fidelity disaster dataset generator for Chennai relief demand modeling.

Generates 100,000+ realistic disaster simulation records across all 15 Greater
Chennai Corporation (GCC) zones plus 8 critical flood basin micro-zones and
multiple historical/synthetic disaster regimes.
"""
import time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATASET_CSV = ROOT / "dataset" / "chennai_historical_2015_2023.csv"


def generate_disaster_dataset(num_samples: int = 100000, random_seed: int = 42) -> pd.DataFrame:
    print(f"[*] Generating {num_samples:,} high-fidelity disaster simulation records (seed={random_seed})...")
    t0 = time.perf_counter()
    np.random.seed(random_seed)

    # 8 disaster event regimes with distinctive hydrological profiles
    events = [
        {"name": "2015_Deluge", "p": 0.20, "rain_mean": 360, "rain_std": 75, "depth_mean": 2.8, "depth_std": 0.65, "disease_mult": 2.2},
        {"name": "2016_Vardah_Surge", "p": 0.10, "rain_mean": 190, "rain_std": 50, "depth_mean": 1.4, "depth_std": 0.45, "disease_mult": 1.5},
        {"name": "2020_Nivar", "p": 0.12, "rain_mean": 165, "rain_std": 45, "depth_mean": 1.25, "depth_std": 0.40, "disease_mult": 1.3},
        {"name": "2021_Monsoon_Peak", "p": 0.12, "rain_mean": 225, "rain_std": 55, "depth_mean": 1.75, "depth_std": 0.45, "disease_mult": 1.6},
        {"name": "2023_Michaung", "p": 0.28, "rain_mean": 420, "rain_std": 85, "depth_mean": 2.35, "depth_std": 0.55, "disease_mult": 2.0},
        {"name": "Flash_Cloudburst", "p": 0.10, "rain_mean": 290, "rain_std": 65, "depth_mean": 1.55, "depth_std": 0.45, "disease_mult": 1.4},
        {"name": "Northeast_Monsoon_Depression", "p": 0.08, "rain_mean": 260, "rain_std": 60, "depth_mean": 1.65, "depth_std": 0.50, "disease_mult": 1.7},
    ]

    # All 15 GCC Zones + 8 vulnerable flood basin micro-zones
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
        {"name": "Micro_Pallikaranai_Marsh", "density": 16000, "vuln": 0.98},
        {"name": "Micro_Ennore_Creek_Basin", "density": 14000, "vuln": 0.91},
        {"name": "Micro_Madipakkam_Lakebed", "density": 25000, "vuln": 0.93},
        {"name": "Micro_Perumbakkam_IT", "density": 18000, "vuln": 0.89},
        {"name": "Micro_Ambattur_Lake", "density": 21000, "vuln": 0.87},
        {"name": "Micro_Porur_Basin", "density": 23000, "vuln": 0.90},
    ]

    event_probs = [e["p"] for e in events]
    records = []

    for _ in range(num_samples):
        ev = np.random.choice(events, p=event_probs)
        zn = np.random.choice(zones)

        # Environmental & rainfall parameters
        rain = np.clip(np.random.normal(ev["rain_mean"], ev["rain_std"]), 15.0, 500.0)
        base_depth = np.clip(np.random.normal(ev["depth_mean"], ev["depth_std"]), 0.10, 4.50)
        depth = np.clip(base_depth * (zn["vuln"] * 1.15), 0.10, 4.50)

        # Population density variation (+- 15%)
        density = int(np.clip(zn["density"] * np.random.uniform(0.85, 1.15), 5000, 45000))
        vuln = float(np.clip(zn["vuln"] * np.random.uniform(0.95, 1.05), 0.15, 0.99))

        # Evacuation & shelter occupancy calculation
        evac_fraction = np.clip(
            (depth / 4.0) * 0.18 * vuln * np.random.uniform(0.85, 1.25),
            0.02,
            0.28
        )
        shelter_occupancy = int(density * evac_fraction)
        if shelter_occupancy < 5:
            shelter_occupancy = 5

        # Sphere standard and non-linear relief demand calculations:
        # 1. Clean Water (L): Base 3.0L + tap water contamination + heat/humidity stress factor
        water_per_person = 3.0 + (depth * 0.45) + (rain / 200.0 * 0.30) + (vuln * 0.25)
        water_noise = np.random.normal(0, 0.06)
        water_total = shelter_occupancy * np.maximum(3.0, water_per_person + water_noise)

        # 2. Food (Rations): Base 3.0 rations + supply chain disruption & kitchen submergence
        food_per_person = 3.0 + (depth * 0.28) + (vuln * 0.35)
        food_noise = np.random.normal(0, 0.05)
        food_total = shelter_occupancy * np.maximum(3.0, food_per_person + food_noise)

        # 3. Medical Kits: Base 0.02 (1 per 50 people) + disease surge multiplier from stagnant water
        med_per_person = 0.02 * ev["disease_mult"] * (1.0 + depth * 0.50) * (vuln ** 1.5)
        med_noise = np.random.normal(0, 0.0015)
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
    print(f"[+] Generated {len(df):,} records across {df['Ward'].nunique()} zones in {elapsed:.2f}s")
    return df


def save_dataset(df: pd.DataFrame, path: Path = DATASET_CSV) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[+] Saved high-resolution dataset to {path} ({path.stat().st_size / 1024 / 1024:.2f} MB)")
    return path


if __name__ == "__main__":
    dataset = generate_disaster_dataset(num_samples=100000)
    save_dataset(dataset)
