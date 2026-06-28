"""
Train football Poisson V2 model with real data from parquet.
"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_football")

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "matches_football_real.parquet"
MODEL_PATH = ROOT / "data" / "models" / "football_v2_mle.json"

# Add project to sys.path
sys.path.insert(0, str(ROOT))


def main():
    logger.info("Carregando dados de %s", DATA_PATH)
    df = pd.read_parquet(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    logger.info("Total: %d jogos, %s a %s", len(df), df["date"].min().date(), df["date"].max().date())
    logger.info("Ligas: %s", list(df["league"].unique()))

    # Split temporal: 2023-2024 para validação
    train = df[df["date"] < "2023-08-01"]
    val = df[df["date"] >= "2023-08-01"]

    logger.info("Treino: %d jogos | Validação: %d jogos", len(train), len(val))

    from src.ml.models.football_poisson_v2 import FootballPoissonModelV2

    model = FootballPoissonModelV2(
        use_dixon_coles=True,
        reg_lambda=0.15,
        time_decay_halflife_days=90.0,
    )

    logger.info("A treinar modelo Poisson V2 com MLE...")
    model.fit(train, calibrate=True)

    logger.info("Home advantage: %.3f", model.home_advantage)
    logger.info("Rho: %.3f", model.rho)
    logger.info("Equipas no modelo: %d", len(model.attack))

    # Validação
    from src.ml.models.football_poisson_v2 import _fold_brier_score, _fold_log_likelihood

    val_ll = _fold_log_likelihood(model, val)
    val_bs = _fold_brier_score(model, val)
    logger.info("Log-Likelihood (validação): %.4f", val_ll)
    logger.info("Brier Score (validação): %.4f", val_bs)

    # Brier score de referência: 0.22 é bom, < 0.20 é excelente
    naive_bs = 0.22  # baseline (prever sempre o resultado mais comum)
    if val_bs < naive_bs:
        logger.info("✅ Brier %.4f < %.2f (baseline) — modelo tem capacidade preditiva", val_bs, naive_bs)
    else:
        logger.warning("⚠️ Brier %.4f >= %.2f — modelo precisa de melhorias", val_bs, naive_bs)

    # Guardar modelo
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))
    logger.info("✅ Modelo salvo em %s", MODEL_PATH)

    # Backup para o caminho do champion
    champion_path = ROOT / "data" / "models" / "champion" / "football_poisson_champion.pkl"
    champion_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(champion_path))
    logger.info("✅ Backup salvo em %s", champion_path)

    return model


if __name__ == "__main__":
    main()
