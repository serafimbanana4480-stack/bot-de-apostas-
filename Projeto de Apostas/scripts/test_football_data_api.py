#!/usr/bin/env python3
"""
Diagnostico rapido da API football-data.org — testa token, rate limits e dados disponiveis.

Usage:
    py scripts/test_football_data_api.py
    py scripts/test_football_data_api.py --token TEU_TOKEN_AQUI
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.football_data_org import FootballDataOrgClient


def diagnose(token: str | None = None) -> dict:
    """Test API connectivity, token validity, and available competitions."""
    client = FootballDataOrgClient(api_token=token)

    results = {
        "token_configured": bool(client.api_token and not client.api_token.startswith("your_")),
        "token_preview": (client.api_token[:8] + "...") if client.api_token else "EMPTY",
        "competitions_accessible": False,
        "matches_accessible": False,
        "competitions_count": 0,
        "matches_count": 0,
        "sample_competitions": [],
    }

    if not results["token_configured"]:
        print("[WARN] FOOTBALL_DATA_ORG_TOKEN nao configurado ou e placeholder.")
        print("       Regista-te em: https://www.football-data.org/client/register")
        print("       Adiciona ao .env: FOOTBALL_DATA_ORG_TOKEN=teu_token")
        return results

    # Test competitions endpoint
    comps = client._get("/competitions")
    if comps and "competitions" in comps:
        results["competitions_accessible"] = True
        results["competitions_count"] = len(comps["competitions"])
        results["sample_competitions"] = [
            {"code": c.get("code"), "name": c.get("name")}
            for c in comps["competitions"][:5]
        ]

    # Test matches endpoint (today's matches)
    matches = client._get("/matches")
    if matches and "matches" in matches:
        results["matches_accessible"] = True
        results["matches_count"] = len(matches["matches"])

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose football-data.org API")
    parser.add_argument("--token", default=None, help="Override token for testing")
    args = parser.parse_args()

    print("=" * 60)
    print("Diagnostico football-data.org API")
    print("=" * 60)

    results = diagnose(token=args.token)

    print(f"\nToken configurado: {results['token_configured']}")
    print(f"Token preview:     {results['token_preview']}")

    if results["token_configured"]:
        print(f"\nCompeticoes:       {results['competitions_count']} acessiveis")
        print(f"Matches hoje:      {results['matches_count']}")
        print("\nExemplo de competicoes:")
        for c in results["sample_competitions"]:
            print(f"  {c['code']:6s} | {c['name']}")

        print("\n[OK] API acessivel. Proximo passo:")
        print("     py scripts/ingest_free_data.py --source football-data --sport football")
    else:
        print("\n[BLOCKED] Sem token real. Passos:")
        print("  1. Registar em https://www.football-data.org/client/register")
        print("  2. Copiar token para .env: FOOTBALL_DATA_ORG_TOKEN=teu_token")
        print("  3. Correr novamente: py scripts/test_football_data_api.py")

    return 0 if results["token_configured"] else 1


if __name__ == "__main__":
    sys.exit(main())
