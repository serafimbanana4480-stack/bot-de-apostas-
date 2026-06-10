# VBQ-UNIFIED — Requisitos para Apostas Reais (Dinheiro Real)

> **AVISO LEGAL**: Este documento descreve requisitos técnicos. O utilizador é inteiramente responsável por cumprir a legislação do seu país/jurisdição relativamente a apostas desportivas online. O autor não se responsabiliza por perdas financeiras.

---

## Checklist Obrigatória (TODOS devem estar verdes)

### 1. Dados
- [ ] **Nenhum dado mock presente** — `data/bronze/matches_football_mock.parquet` NÃO deve existir
- [ ] **Dados reais históricos** — mínimo 3 épocas (6 temporadas) de football-data.co.uk
- [ ] **Odds reais com Pinnacle closing** — necessário para CLV validation
- [ ] **Mínimo 5000 jogos** no dataset de treino (preferencialmente 10000+)

### 2. Modelo
- [ ] **ECE < 0.05** em validação out-of-sample (teste temporal)
- [ ] **Brier Score < 0.22** para resultados 1X2
- [ ] **Rho fixo por liga** ativado (`rho_fixed_by_league=True`)
- [ ] **Halflife ótimo** confirmado por grid search (tipicamente 60-90 dias)
- [ ] **Regularização ótima** confirmada por CV temporal
- [ ] **Overfit diagnostic** passou (gap train/val < 15%)

### 3. Backtest
- [ ] **ROI > +2%** em 3000+ apostas
- [ ] **p-value < 0.05** (ROI estatisticamente significativo)
- [ ] **Risk of Ruin < 10%** (Monte Carlo, 10k simulações)
- [ ] **Sortino > 1.0**
- [ ] **Max Drawdown < 20%**
- [ ] **Walk-forward validation** obrigatório (não aceitar simples train/test split)

### 4. Meta-Labeling
- [ ] **Features de mercado reais** (The Odds API ou histórico próprio)
- [ ] **Subset filtrado tem ROI > ROI total**
- [ ] **Redução de 30-60%** no número de apostas
- [ ] **Threshold >= 0.60**

### 5. Risco & Staking
- [ ] **Kelly fractional dinâmico** (0.10x inicial, max 0.25x)
- [ ] **Kelly sanity check** ativo (rejeita se Kelly full > 15%)
- [ ] **Max stake 1% do bankroll** por aposta individual
- [ ] **Max daily exposure 5%** do bankroll
- [ ] **Circuit breaker**: pausa automática após drawdown > 20% ou 5 apostas perdidas consecutivas
- [ ] **Bankroll separado** — nunca usar dinheiro de necessidades básicas

### 6. Execução
- [ ] **Paper trading 3000+ apostas** com ROI positivo
- [ ] **PAPER_TRADING_ONLY=False** apenas após aprovação manual
- [ ] **Betfair sandbox testado** (se usar Betfair)
- [ ] **Slippage model** calibrado para mercados reais

### 7. Infraestrutura
- [ ] **Secrets configurados** (JWT, DB, Redis) — nenhum default
- [ ] **MLflow em PostgreSQL** (não SQLite)
- [ ] **Model serialization** via joblib + SHA-256 (não pickle raw)
- [ ] **Health checks** ativos nos serviços Docker
- [ ] **Logging estruturado** (JSON) com audit trail completo

### 8. Compliance
- [ ] **Conta verificada** na exchange (Betfair/Pinnacle)
- [ ] **Limites de depósito** configurados
- [ ] **Self-exclusion** opções conhecidas
- [ ] **Registo de apostas** para fins fiscais (IRS/Finanças)

---

## Sequência Correta de Ativação

```
1. Ingest dados reais
   → scripts/ingest_real_data.py --seasons 2122 2223 2324

2. Treina modelo
   → scripts/train_bot.py football --source football-data-co-uk --walk-forward

3. Diagnóstico completo
   → scripts/run_model_diagnostic.py

4. Backtest otimizado
   → scripts/run_optimized_backtest.py --halflife 60 --reg-lambda 0.20

5. Paper trading (mínimo 3000 apostas)
   → scripts/run_pipeline.py --mode live --dry-run

6. Pre-flight check
   → scripts/pre_flight_check.py --report models/optimized/backtest_report.json

7. SÓ ENTÃO: Ativar dinheiro real
   → export PAPER_TRADING_ONLY=false
   → scripts/go_live_check.py --report models/optimized/backtest_report.json --paper-log data/paper_log.parquet
```

---

## Comandos Úteis

```bash
# Verificar se há dados mock
ls data/bronze/*mock* data/bronze/*backtest* 2>/dev/null && echo "MOCK FOUND" || echo "CLEAN"

# Verificar ECE do modelo
python -c "import json; d=json.load(open('models/optimized/backtest_report.json')); print('ECE:', d.get('model_ece', 'N/A'))"

# Verificar se paper trading está ativo
python -c "from src.core.config import settings; print('PAPER:', settings.PAPER_TRADING_ONLY)"
```

---

## Ligações Recomendadas (Less Efficient = Higher Edge)

| Liga | Código | Eficiência | Prioridade |
|------|--------|-----------|------------|
| Championship | E1 | Baixa | ALTA |
| Bundesliga 2 | D2 | Baixa | ALTA |
| Ligue 2 | F2 | Baixa | ALTA |
| Serie B | I2 | Baixa | ALTA |
| Primeira Liga | P1 | Média | ALTA |
| Eredivisie | N1 | Média | ALTA |
| Premier League | E0 | Alta | BAIXA (referência) |
| La Liga | SP1 | Alta | BAIXA |
| Bundesliga | D1 | Alta | BAIXA |
| Serie A | I1 | Alta | BAIXA |
| Ligue 1 | F1 | Alta | BAIXA |

---

## Contacto & Suporte

Para questões técnicas: abrir issue no repositório.
Para questões de risco: rever este documento e o `src/risk/go_live_validator.py`.
