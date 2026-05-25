# Agent instructions — Bot de Apostas

## Repositório canónico

Trabalha sempre em **`Projeto de Apostas/`** salvo pedido explícito.

## Modo zero custo (default)

- `ZERO_COST_MODE=true` — dados em `data/` Parquet, sem cloud
- Treino: `scripts/train_bot.py`, `scripts/ingest_free_data.py`, `scripts/run_clv_report.py`
- Não exigir OddsAPI/Betfair pagos para treinar
- MLflow: `MLFLOW_TRACKING_URI=./mlruns`

## Prioridades de implementação

1. Dados reais/gratuitos → `LocalDataStore` + `football_data_org.py`
2. Prova de edge → `run_clv_report.py` com CLV > 1%
3. Leakage → `LeakageDetector` antes de todo treino
4. Walk-forward → `WalkForwardValidator` (nunca random split em odds)
5. Execução live só após CLV validado

## Não duplicar

`project_quant_betting/` — fundir módulos úteis (parquet store, leakage) em vez de manter dois bots.

## Skills Cursor úteis

| Skill | Quando |
|-------|--------|
| automate | Criar/ajustar automação diária |
| create-rule | Regras persistentes `.cursor/rules/` |
| playwright | Scraping odds históricas (cuidado legal/ToS) |

## Testes obrigatórios após mudanças

```bash
poetry run pytest tests/ -q
poetry run ruff check src scripts
```

## Documentação

- `Projeto de Apostas/docs/ZERO_COST_STACK.md`
- `Planeameneto bot de apostas profissional/04_Data_Engineering/FONTES_GRATUITAS.md`
