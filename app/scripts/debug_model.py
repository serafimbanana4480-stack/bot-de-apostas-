"""
Debug: verificar porque edges são todos negativos.
Compara probabilidades do modelo vs. implícitas do mercado.
"""
import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.ml.models.football_poisson_v2 import FootballPoissonModelV2

df = pd.read_parquet(ROOT / "data" / "matches_football_real.parquet")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

# Use a SMALL subset for training (e.g. 2022-2023 premier league)
train = df[(df["date"] >= "2022-08-01") & (df["date"] <= "2023-05-31")]
test = df[(df["date"] >= "2023-08-01") & (df["date"] <= "2024-05-31")]

print(f"Train: {len(train)} matches")
print(f"Test: {len(test)} matches")

model = FootballPoissonModelV2(use_dixon_coles=True, reg_lambda=0.15, time_decay_halflife_days=90)
model.fit(train, calibrate=True)

print(f"\nHome advantage: {model.home_advantage:.3f}")
print(f"Rho: {model.rho:.3f}")

# Test a few matches
result_map = {"H": "1", "D": "X", "A": "2"}
total = 0
correct = 0
correct_market = 0
for _, row in test.head(50).iterrows():
    probs = model.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
    actual = result_map.get(row["result"], "")
    predicted = max(probs, key=probs.get) if isinstance(probs, dict) else "X"
    
    # Compare model prob vs implied prob (Pinnacle)
    odd_h = row.get("odd_home", 2.0)
    implied_h = 1.0 / odd_h
    
    model_h = probs.get("1", 0.33)
    edge = model_h - implied_h
    
    total += 1
    if predicted == actual:
        correct += 1
    if max(probs.values()) > implied_h:
        correct_market += 1

    result_str = "OK" if predicted == actual else "NO"
    print(f"{row['home_team']:20s} vs {row['away_team']:20s} | "
          f"Model: 1={probs['1']:.3f} X={probs['X']:.3f} 2={probs['2']:.3f} | "
          f"Mkt: {implied_h:.3f} | Edge: {edge*100:+.2f}% | "
          f"Actual: {actual} Pred: {predicted} [{result_str}]")

print(f"\nAccuracy: {correct}/{total} = {correct/total*100:.1f}%")
print(f"Beat market: {correct_market}/{total} = {correct_market/total*100:.1f}%")

# Validação rápida com V1
print("\n--- V1 Model Comparison ---")
from src.ml.models.football_poisson import FootballPoissonModel
model_v1 = FootballPoissonModel(use_dixon_coles=True)
model_v1.fit(train, calibrate=True)

v1_correct = 0
for _, row in test.head(50).iterrows():
    probs = model_v1.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
    actual = result_map.get(row["result"], "")
    predicted = max(probs, key=probs.get)
    if predicted == actual:
        v1_correct += 1
