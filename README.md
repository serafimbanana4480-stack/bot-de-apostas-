# 🎲 VBQ-UNIFIED — Bot de Apostas Quantitativo (0€)

> **Sistema profissional de value betting** (Futebol, UFC, NBA) com **custo operacional mínimo**: treino local, dados gratuitos, MLflow SQLite, Parquet em disco.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/Poetry-📦-blueviolet.svg)](https://python-poetry.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![MLflow](https://img.shields.io/badge/MLflow-📊-orange.svg)](https://mlflow.org/)

---

## 🎯 Visão Geral

O **VBQ-UNIFIED** é um sistema de **apostas quantitativas** que:

1. **Gera** dados gratuitos (mock ou fontes abertas)
2. **Treina** modelos preditivos (Poisson, xG, mercado)
3. **Avalia** value bets com calibração OOF (Out-Of-Fold)
4. **Executa** backtesting rigoroso (walk-forward)
5. **Comprova** edge com CLV (Closing Line Value)
6. **Deteta** leakage (Overfitting)
7. **Opera** a 0€ (sem APIs pagas)

---

## ✨ Funcionalidades Principais

| Funcionalidade | Descrição | Estado |
|----------------|-------------|--------|
| **Zero Cost Mode** | Dados locais (Parquet), sem APIs pagas | ✅ Ativo |
| **Multi-Sport** | Futebol, UFC, NBA | ✅ Ativo |
| **Poisson Model** | Modelo base para futebol | ✅ Ativo |
| **Calibração OOF** | Validação cruzada (Over-Of-Fold) | ✅ Ativo |
| **Walk-Forward** | Backtesting temporal (nunca random split) | ✅ Ativo |
| **CLV Report** | Prova de edge vs. closing line | ✅ Ativo |
| **Leakage Detection** | Deteta overfitting | ✅ Ativo |
| **MLflow Tracking** | Experimentos locais (SQLite) | ✅ Ativo |
| **Parquet Storage** | Eficiência (LocalDataStore) | ✅ Ativo |
| **Tier B Pipeline** | Sharp + Dynamic EV | ✅ Ativo |

---

## 🏗️ Arquitetura

```
bot de apostas/
├── app/                      # Código-fonte principal
│   ├── src/                # Módulos core
│   │   ├── models/        # Modelos preditivos
│   │   ├── pipeline/      # Pipelines de treino
│   │   ├── data/          # DataStore (Parquet)
│   │   └── utils/         # Utilitários
│   ├── scripts/           # Scripts de execução
│   │   ├── ingest_free_data.py
│   │   ├── train_bot.py
│   │   ├── run_clv_report.py
│   │   ├── backtest_season.py
│   │   └── ...
│   └── tests/            # Testes unitários
├── docs/                     # Documentação
├── models/                   # Modelos treinados (.pkl)
├── data/                     # Dados Parquet
├── mlruns/                  # MLflow experiments
├── AGENTS.md                # Instruções para agentes
└── README.md                # Este ficheiro
```

---

## 🚀 Quick Start (0€ — sem APIs pagas)

### 1. Setup

```powershell
# 1. Entrar na pasta
cd "C:\Users\rodri\Desktop\bot de apostas\app"

# 2. Instalar dependências (Poetry)
poetry install

# 3. Ativar ambiente
poetry shell
```

### 2. Gerar Dados Gratuitos

```powershell
# Dados mock (Futebol)
poetry run python scripts/ingest_free_data.py --sport football --source mock

# Dados reais gratuitos (Football-Data.co.uk)
poetry run python scripts/ingest_free_data.py --sport football --source football-data-co-uk
```

### 3. Treinar Modelo

```powershell
# Treino Futebol (Poisson + calibração OOF)
poetry run python scripts/train_bot.py football --source mock --calibrate

# Treino com dados reais + walk-forward
poetry run python scripts/train_bot.py football --source football_real_odds --walk-forward
```

### 4. Backtesting Rigoroso

```powershell
# Walk-forward + métricas (Sortino, Calmar, profit factor)
poetry run python scripts/train_bot.py football --source mock --walk-forward

# Backtest completo (temporada inteira)
poetry run python scripts/backtest_season.py --sport football --start 2023-01-01 --end 2024-12-31 --check-leakage
```

### 5. Prova de Edge (CLV)

```powershell
# Relatório CLV (prova de edge vs closing line)
poetry run python scripts/run_clv_report.py
```

**Objetivo:** CLV > 1% (prova que o modelo tem edge real)

### 6. Pipeline Unificado (Tier B)

```powershell
# Live (produção)
py -3 scripts/run_pipeline.py --sport football --mode live

# Backtest (validação)
py -3 scripts/run_pipeline.py --sport football --mode backtest --start 2023-01-01 --end 2024-12-31 --check-leakage

# Settlement (fechamento de apostas)
py -3 scripts/settle_yesterday.py --sport football

# Relatório diário
py -3 scripts/daily_report.py
```

---

## 📖 Guias Importantes

### ⚠️ Leakage (Overfitting)

**Obrigatório:** Executar `LeakageDetector` **antes** de todo treino.

```powershell
poetry run python scripts/train_bot.py football --check-leakage
```

Se leakage detetado:
- Reduzir features
- Aumentar regularização
- Usar walk-forward (nunca random split)

### 📊 CLV (Closing Line Value)

**Prova de edge:** Comparar odds iniciais vs. odds de fechamento.

```powershell
poetry run python scripts/run_clv_report.py
```

**Interpretação:**
- CLV > 0%: Modelo tem edge
- CLV > 1%: Edge significativo
- CLV < 0%: Modelo não tem edge (overfitted)

### 🔄 Walk-Forward (Nunca Random Split!)

**Errado:**
```python
# NUNCA FAZER ISTO!
train_test_split(random_state=42)  # ❌ Data leakage!
```

**Correto:**
```powershell
# Walk-forward temporal
poetry run python scripts/train_bot.py football --walk-forward
```

---

## 🗂️ Fontes de Dados Gratuitas

| Fonte | Custo | Uso |
|--------|-------|-----|
| **Mock Data** | 0€ | Desenvolvimento e testes |
| **Football-Data.co.uk** | 0€ | Odds históricas (futebol) |
| **NBA API** | 0€ | Estatísticas NBA |
| **UFC Stats** | 0€ | Resultados UFC |
| **Local Parquet** | 0€ | Eficiência (LocalDataStore) |

---

## ⚙️ Configuração (`.env`)

```bash
# Zero Cost Mode (obrigatório)
ZERO_COST_MODE=true

# MLflow (local)
MLFLOW_TRACKING_URI=./mlruns

# Data Store (Parquet local)
DATA_STORE_TYPE=local
DATA_STORE_PATH=./data

# Logging
LOG_LEVEL=INFO
```

---

## 🧪 Testes

```powershell
# Testes unitários (obrigatórios após mudanças)
poetry run pytest tests/ -q

# Lint
poetry run ruff check src scripts

# Type check
poetry run mypy src/
```

---

## 📂 Estrutura do Projeto

```
bot de apostas/
├── app/              # Código-fonte principal (API, modelos, pipelines)
├── docs/             # Documentação, planeamento e análises
├── models/           # Modelos treinados (.pkl)
├── data/             # Dados Parquet (gratuitos)
├── mlruns/          # MLflow experiments (SQLite)
├── logs/             # Ficheiros de log
├── .gitignore        # Ficheiros ignorados (dados, logs, secrets)
├── AGENTS.md         # Instruções para agentes Cursor
└── README.md         # Este ficheiro
```

---

## 🔍 Troubleshooting

### Leakage Detetado

**Causa:** Overfitting (modelo memorizou dados de treino).

**Solução:**
1. Reduzir complexidade do modelo
2. Aumentar regularização
3. Usar walk-forward validação

### CLV Negativo

**Causa:** Modelo não tem edge real (overfitted).

**Solução:**
1. Rever features (remover leakage)
2. Melhorar preprocessamento
3. Coletar mais dados

### MLflow não grava

**Causa:** Permissões ou caminho incorreto.

**Solução:**
```powershell
# Verificar se MLFLOW_TRACKING_URI está correto
echo %MLFLOW_TRACKING_URI%

# Ou usar default (./mlruns)
unset MLFLOW_TRACKING_URI
```

---

## 📝 Licença

MIT — usar com responsabilidade.

⚠️ **Aviso Legal:** Este sistema é para **pesquisa académica** e **uso pessoal**. Cumprir sempre os termos das fontes de dados.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fazer fork do repositório
2. Criar uma branch de funcionalidade
3. Fazer as tuas alterações
4. Submeter um Pull Request

---

## 📞 Suporte

Para problemas e questões:

- Consultar a seção de troubleshooting
- Rever logs em `logs/bot.log`
- Abrir uma issue no GitHub

---

## 🙏 Agradecimentos

- **Poisson Model:** https://en.wikipedia.org/wiki/Poisson_regression
- **Value Betting:** https://www.pinnacle.com/en/betting-articles/value-betting/what-is-value-betting/
- **CLV:** https://www.pinnacle.com/en/betting-articles/closing-line-value/what-is-closing-line-value/
- **MLflow:** https://mlflow.org/
- **Poetry:** https://python-poetry.org/

---

## 📈 Estatísticas do Projeto

- **Última atualização:** 2026-06-28
- **Branch:** `master`
- **Total de ficheiros:** ~50 (código fonte)
- **Módulos Python:** 20+
- **Cobertura de testes:** 85%+
- **Modelos Disponíveis:** Poisson, xG, Mercado

---

**Feito com ❤️ em Portugal** 🇵🇹
