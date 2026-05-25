# Setup football-data.org — Token Real (0€)

## Obter token gratuito

1. Registar em: https://www.football-data.org/client/register
2. Free tier: 10 requests/minuto, ligas europeias principais
3. Copiar o token para `.env`:

```env
FOOTBALL_DATA_ORG_TOKEN=seu_token_aqui
```

## Comandos de teste

```powershell
cd "Projeto de Apostas"

# 1. Ingerir dados reais (PL, PD, SA, BL1, FL1)
py scripts/ingest_free_data.py --source football-data --sport football --leagues PL,PD,SA

# 2. Verificar dados ingeridos
py -c "from src.data.local_store import LocalDataStore; s=LocalDataStore('data'); print(s.load_matches('football_fdo').shape)"

# 3. Treinar com dados reais
py scripts/train_bot.py football --source football-data --walk-forward

# 4. Gerar CLV report
py scripts/run_clv_report.py

# 5. Backtest completo
py scripts/backtest_season.py --sport football --season 2024 --check-leakage --compare-tier-b
```

## O que esperar

- Dados reais têm menos matches que mock (apenas jogos das ligas escolhidas)
- O mock serve só como smoke test; não deve ser tratado como prova de edge
- `football_real_odds` é a fonte correta para medir CLV real com Pinnacle closing lines
- Break-even para viabilidade: CLV > 2.565%
- Se CLV real < 1%, o modelo precisa de mais features ou calibracao

## Restricoes

- Nao usar OddsAPI pago ate CLV > 2.6% em dados reais
- Manter ZERO_COST_MODE=true e PAPER_TRADING_ONLY=true
- Validar pelo menos 500 bets antes de considerar live trading
