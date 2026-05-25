# Getting Started — Bot de Apostas Quantitativo

## ⚠️ Aviso Legal
Este sistema é **estritamente para paper trading e investigação quantitativa**.  
A execução com dinheiro real requer licenciamento pela entidade reguladora do seu país (em Portugal: **SRIJ**).  
O **Betfair Exchange não opera legalmente em Portugal**. Utilize apenas operadores licenciados.

---

## Requisitos

- Python 3.11+
- uv (recomendado) ou Poetry
- Git

## Instalação Rápida

```bash
cd "Projeto de Apostas"
uv pip install -r requirements.txt  # ou: poetry install
```

## Configuração

Copie `.env.example` para `.env` e preencha as suas credenciais:

```bash
cp .env.example .env
```

**Importante**: Nunca comite o ficheiro `.env`. O sistema recusa-se a iniciar em produção se detetar passwords por defeito.

## Modo Paper Trading (Seguro)

O sistema inicia por defeito em modo paper trading (`PAPER_TRADING_ONLY=true`).  
Não altere esta configuração sem compreender os riscos legais e financeiros.

## Pipeline Diário

```bash
# 1. Ingerir dados gratuitos
uv run python scripts/ingest_free_data.py --sport football --source football-data-co-uk

# 2. Executar backtest honesto (verifica leakage temporal)
uv run python scripts/run_pipeline.py --sport football --mode backtest --start 2023-01-01 --end 2024-12-31 --check-leakage

# 3. Executar paper trading para o dia atual
uv run python scripts/run_pipeline.py --sport football --mode live --dry-run

# 4. Relatório CLV (Closing Line Value)
uv run python scripts/run_clv_report.py
```

## Testes

```bash
uv run python -m pytest tests/ -q
```

## Estrutura de Dados

```
data/
├── bronze/       # Dados brutos (parquet)
├── silver/       # Dados limpos
├── gold/         # Features e modelos
└── reports/      # Métricas e backtests
```

## Stack Tecnológica

- **Modelos**: XGBoost + Poisson Dixon-Coles
- **Calibração**: Isotonic Regression OOF temporal (sem leakage)
- **Validação**: Walk-Forward com purging/embargo
- **Risco**: Kelly fracionado + Circuit Breakers (6 níveis)
- **MLOps**: MLflow SQLite, serialização JSON (sem pickle)
- **Execução**: Paper trading por defeito; adapters para Betfair/Pinnacle apenas em jurisdições permitidas

## Métricas-Chave de Viabilidade

Antes de considerar dinheiro real, o backtest honesto deve demonstrar:

| Métrica | Mínimo Aceitável |
|---------|------------------|
| ROI | > 2% |
| Profit Factor | > 1.1 |
| Sortino Ratio | > 1.0 |
| CLV médio | > 2% |
| Risk of Ruin (50%) | < 10% |

**Resultado atual do backtest honesto (2023-2024):**
- ROI: **-10.9%** ❌
- Profit Factor: **0.85** ❌
- Sortino: **negativo** ❌
- Risk of Ruin: **91.2%** ❌
- CLV médio: **+4.0%** ✅ (edge de previsão existe, mas é consumido por comissões/overround)

## Próximos Passos

1. Não aposte dinheiro real com o modelo atual.
2. Investigue porque o CLV positivo não se traduz em lucro (overround, slippage, comissão).
3. Colete mais dados de odds reais (open/close Pinnacle) para refinar o edge.
4. Otimize a seleção de mercados e stakes com base no novo simulador Monte Carlo realista.
