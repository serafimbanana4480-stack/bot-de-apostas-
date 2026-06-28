"""
Quick V1 model test - fixed prediction logic.
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.ml.models.football_poisson import FootballPoissonModel

df = pd.read_parquet(ROOT / "data" / "matches_football_real.parquet")
df["date"] = pd.to_datetime(df["date"])
train = df[df["date"] < "2023-08-01"]
test = df[df["date"] >= "2023-08-01"]

print(f"Train: {len(train)}, Test: {len(test)}")

model = FootballPoissonModel(use_dixon_coles=True)
model.fit(train, calibrate=True)
print(f"Is calibrated: {model.is_calibrated}")

result_map = {"H": "1", "D": "X", "A": "2"}
OUTCOME_KEYS = ["1", "X", "2"]
correct, total = 0, 0
edges_positive = 0
total_edge = 0.0

for _, row in test.head(200).iterrows():
    probs = model.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
    # Only use 1/X/2 keys for prediction
    outcome_probs = {k: probs[k] for k in OUTCOME_KEYS}
    actual = result_map.get(row["result"], "")
    predicted = max(outcome_probs, key=outcome_probs.get)

    if predicted == actual:
        correct += 1
    total += 1

    # Edge for predicted outcome
    if predicted == "1":
        odd = float(row.get("odd_home", 2.0))
    elif predicted == "X":
        odd = float(row.get("odd_draw", 3.5))
    else:
        odd = float(row.get("odd_away", 2.0))

    if odd > 0:
        edge = outcome_probs[predicted] - 1.0 / odd
        total_edge += edge
        if edge > 0:
            edges_positive += 1

    if total <= 10:
        xs = f"1={probs['1']:.2f} X={probs['X']:.2f} 2={probs['2']:.2f}"
        edge_str = f"{edge*100:+.1f}%" if odd > 0 else "N/A"
        print(f'{row["home_team"]:20s} vs {row["away_team"]:20s} | {xs} | Edge(pred): {edge_str} | Pred: {predicted} Act: {actual}')

print(f"\nAccuracy: {correct}/{total} = {correct/total*100:.1f}%")
print(f"Edges positive: {edges_positive}/{total} = {edges_positive/total*100:.1f}%")
print(f"Average edge: {total_edge/total*100:+.2f}%")
