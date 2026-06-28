#!/usr/bin/env python3
"""
Script de emergência: converte CSVs do football-data.co.uk para Parquet.
Executar uma vez para ter dados reais.

Uso:
    python scripts/convert_fdcouk_to_parquet.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("convert_fdcouk")

ROOT = Path(__file__).parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "fdcouk"
OUTPUT = ROOT / "data" / "matches_football_real.parquet"

# Mapa de ligas: prefixo → nome
LEAGUE_MAP = {
    "E0": "Premier League",
    "D1": "Bundesliga",
    "F1": "Ligue 1",
    "I1": "Serie A",
    "SP1": "La Liga",
    # Adicionar mais conforme necessário
}


def convert():
    files = sorted(CACHE_DIR.glob("*.csv"))
    if not files:
        logger.error("Nenhum CSV encontrado em %s", CACHE_DIR)
        logger.info("Download de https://www.football-data.co.uk/englandm.php manualmente primeiro.")
        sys.exit(1)

    all_dfs = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath, encoding="latin1")
        except Exception as e:
            logger.warning("Erro ao ler %s: %s", fpath.name, e)
            continue

        # Extrair época e liga do nome do ficheiro (ex: 2324_E0.csv)
        stem = fpath.stem  # "2324_E0"
        season_raw, league_code = stem.split("_")
        league_name = LEAGUE_MAP.get(league_code, f"League_{league_code}")

        # Determinar temporada
        season_start = int("20" + season_raw[:2])
        season_end = int("20" + season_raw[2:])
        season_label = f"{season_start}/{season_end}"

        # Colunas obrigatórias
        required = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
        if not all(c in df.columns for c in required):
            logger.warning("CSV %s não tem colunas obrigatórias. Skipping.", fpath.name)
            continue

        # Construir dataframe normalizado
        df_out = pd.DataFrame()
        df_out["date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        df_out["season"] = season_label
        df_out["league"] = league_name
        df_out["home_team"] = df["HomeTeam"].astype(str)
        df_out["away_team"] = df["AwayTeam"].astype(str)
        df_out["home_goals"] = pd.to_numeric(df["FTHG"], errors="coerce").fillna(0).astype(int)
        df_out["away_goals"] = pd.to_numeric(df["FTAG"], errors="coerce").fillna(0).astype(int)
        df_out["result"] = df["FTR"].fillna("X")

        # Mapear odds das várias casas para formato normalizado
        # Bookmakers no CSV: B365, BW, IW, PS, WH, VC
        odds_mapping = {
            "odd_home": "B365H",
            "odd_draw": "B365D",
            "odd_away": "B365A",
            "pin_close_home": "PSH",
            "pin_close_draw": "PSD",
            "pin_close_away": "PSA",
            "open_odd_home": "PSCH",  # Pinnacle closing (usamos como proxy)
            "open_odd_draw": "PSCD",
            "open_odd_away": "PSCA",
        }
        for new_col, csv_col in odds_mapping.items():
            if csv_col in df.columns:
                df_out[new_col] = pd.to_numeric(df[csv_col], errors="coerce").fillna(0.0)
            else:
                df_out[new_col] = 0.0

        # Calcular odds de fecho implícitas (max das odds das várias casas)
        for outcome, cols in [
            ("home", ["B365H", "BWH", "IWH", "PSH", "WHH", "VCH"]),
            ("draw", ["B365D", "BWD", "IWD", "PSD", "WHD", "VCD"]),
            ("away", ["B365A", "BWA", "IWA", "PSA", "WHA", "VCA"]),
        ]:
            valid_cols = [c for c in cols if c in df.columns]
            if valid_cols:
                df_out[f"max_{outcome}"] = df[valid_cols].max(axis=1)
                df_out[f"avg_{outcome}"] = df[valid_cols].mean(axis=1)
            else:
                df_out[f"max_{outcome}"] = df_out[f"odd_{outcome}"]
                df_out[f"avg_{outcome}"] = df_out[f"odd_{outcome}"]

        # Estimativa de opening odds (assumindo que Pinnacle fecho ≈ mercado)
        # Usamos PSCH/PSCD/PSCA como opening se disponíveis
        if "PSCH" in df.columns and "PSCH" in df.columns:
            df_out["open_home"] = pd.to_numeric(df["PSCH"], errors="coerce").fillna(0.0)
        else:
            df_out["open_home"] = df_out["odd_home"]
        if "PSCD" in df.columns:
            df_out["open_draw"] = pd.to_numeric(df["PSCD"], errors="coerce").fillna(0.0)
        else:
            df_out["open_draw"] = df_out["odd_draw"]
        if "PSCA" in df.columns:
            df_out["open_away"] = pd.to_numeric(df["PSCA"], errors="coerce").fillna(0.0)
        else:
            df_out["open_away"] = df_out["odd_away"]

        # Identificador único
        df_out["match_id"] = [f"{season_label}_{league_code}_{i}" for i in range(len(df_out))]

        all_dfs.append(df_out)
        logger.info("Convertido %s: %d jogos, liga=%s, época=%s",
                     fpath.name, len(df_out), league_name, season_label)

    if not all_dfs:
        logger.error("Nenhum dataframe convertido. Abortando.")
        sys.exit(1)

    final = pd.concat(all_dfs, ignore_index=True)
    final = final.sort_values("date").reset_index(drop=True)
    final = final.dropna(subset=["date"])

    # Remover jogos sem resultado
    final = final[final["result"].isin(["H", "D", "A"])].reset_index(drop=True)

    # Garantir que colunas numéricas estão corretas
    for col in final.columns:
        if col.endswith("_odds"):
            final[col] = pd.to_numeric(final[col], errors="coerce").fillna(0.0)
        if col.startswith("pin_") or col.startswith("open_") or col.startswith("odd_"):
            final[col] = pd.to_numeric(final[col], errors="coerce").fillna(0.0)

    # Guardar
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.to_parquet(OUTPUT, index=False)
    logger.info("✅ Dados salvos em %s", OUTPUT)
    logger.info("Total: %d jogos, %d ligas, %s a %s",
                 len(final), final["league"].nunique(),
                 final["date"].min().date(), final["date"].max().date())

    # Estatísticas
    home_win_pct = (final["result"] == "H").mean()
    draw_pct = (final["result"] == "D").mean()
    away_win_pct = (final["result"] == "A").mean()
    avg_goals = (final["home_goals"] + final["away_goals"]).mean()
    logger.info("Home win: %.1f%%, Draw: %.1f%%, Away: %.1f%%, Avg goals: %.2f",
                 home_win_pct * 100, draw_pct * 100, away_win_pct * 100, avg_goals)

    # Validação de colunas
    logger.info("Colunas disponíveis: %s", list(final.columns))
    return final


if __name__ == "__main__":
    convert()
