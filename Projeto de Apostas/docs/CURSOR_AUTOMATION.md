# Cursor Automation — Treino diário do bot (0€)

Configura uma **Cursor Automation** para re-treinar e validar o bot sem custo de cloud.

## Criar no Cursor

1. Abre **Cursor Settings → Automations → New Automation**
2. Nome: `VBQ Daily Train (Zero Cost)`
3. **Trigger:** Schedule — `0 6 * * *` (06:00 diário) ou Manual
4. **Working directory:** `Projeto de Apostas`
5. **Prompt** (copiar abaixo)
6. **Tools:** Terminal, Read, Write (sem MCP pago)
7. **Approval:** Required na primeira vez; depois auto se confiares

## Prompt da automação

```
Executa o pipeline ZERO-COST do bot de apostas em "Projeto de Apostas":

1. poetry install (se necessário)
2. poetry run python scripts/ingest_free_data.py --sport football --source football-data-co-uk
   (se falhar, usa --source football-data ou --source mock)
3. poetry run python scripts/train_bot.py football --source football_real_odds --walk-forward
4. poetry run python scripts/run_clv_report.py
5. Lê data/reports/clv_report.json e resume: mean_clv_pct, edge_proven, bets_analyzed
6. Se edge_proven=false, lista 3 melhorias concretas no código (máx 1 ficheiro cada)
7. poetry run pytest tests/test_validation.py tests/test_leakage_and_store.py -q

Não usar APIs pagas. Não commitar .env.
```

## Ficheiro de referência

Ver também `.cursor/automations/vbq-daily-train.json` (metadados para import manual).

## Skills recomendadas no Agent

- **automate** — criar/ajustar esta automação
- **playwright** — só se precisares scrape SBR (último recurso)
- **Temporal** — não necessário para este projeto (Prefect/local basta)

## Alertas gratuitos

- Telegram: `TELEGRAM_BOT_TOKEN` + `send_signal_alert` após CLV report
- Ou ler `data/reports/clv_report.json` no Obsidian vault
