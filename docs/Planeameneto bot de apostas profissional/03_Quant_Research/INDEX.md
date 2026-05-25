# 03_Quant_Research — INDEX

**ID:** `SEC-03` | **Fase:** #phase/1-6 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Esta secção contém o núcleo matemático do projeto. Toda a teoria de probabilidades, estatística de apostas, e metodologia científica que diferencia um sistema quantitativo credível de um sistema amador. **Nenhum modelo pode ser treinado sem que os conceitos desta secção estejam implementados.**

---

## 2. NOTAS FUNDAMENTAIS

- [[PROBABILIDADES_IMPLICITAS]] — De odds para probabilidades; overround; normalização
- [[CLV_CLOSED_LINE_VALUE]] — A única métrica que não pode ser manipulada; definição, cálculo, interpretação
- [[BRIER_SCORE]] — Medida de calibração de probabilidades; comparação com mercado
- [[ECE_MCE_CALIBRATION]] — Expected Calibration Error, Maximum Calibration Error; reliability diagrams
- [[MONTE_CARLO_SIMULATION]] — Simulação de bankroll, drawdowns, e regime changes
- [[BOOTSTRAP_BLOCK_RESAMPLING]] — Intervalos de confiança para ROI e CLV em séries temporais
- [[EDGE_DECAY_REGIME]] — Como o edge se degrada ao longo do tempo; deteção de regime changes
- [[VARIANCE_SHARPE_RATIO]] — Variância das apostas, Sharpe Ratio, Sortino Ratio
- [[STOCHASTIC_PROCESSES]] — Modelos de bankroll como processos estocásticos
- [[OVERROUND_VIG]] — Mecanismos matemáticos do overround e métodos de remoção

---

## 3. FRAMEWORK DE VALIDAÇÃO ESTATÍSTICA

Toda a afirmação de edge deve passar por este pipeline de validação:

```
1. BACKTEST RIGOROSO
   ├── Purged Walk-Forward CV com embargo ≥ 2 dias
   ├── Block bootstrap para intervalos de confiança
   ├── Multiple testing correction (Benjamini-Hochberg)
   └── Métricas: CLV, Brier, ECE, ROI, Sharpe

2. SHADOW MODE MULTI-CASA
   ├── True CLV em 3+ casas
   ├── Comparação de slippage real vs simulado
   └── Validação de liquidez

3. PAPER TRADING
   ├── Sinais gerados sem execução real
   ├── Tracking de odds obtidas vs simuladas
   └── Métricas operacionais (latência, uptime)

4. MICRO BANCA
   ├── 500-1000€ em execução real
   ├── Bootstrap de PnL real
   └── Teste de hipótese: H0: ROI ≤ 0 vs H1: ROI > 0

5. ESCALA CONTROLADA
   ├── Aumento gradual de stake
   ├── Monitorização de drawdown
   └── Reversão automática se métricas deteriorarem
```

---

## 4. MÉTRICAS QUANTITATIVAS OBRIGATÓRIAS

| Métrica | Fórmula | Target | Critical Threshold |
|---------|---------|--------|--------------------|
| CLV | `(odd_realizada / odd_fecho) - 1` | > 2% | < 0% = STOP |
| Brier Score | `(p - o)^2` onde o∈{0,1} | < Brier_mercado | > Brier_mercado = REVISÃO |
| ECE | `Σ |accuracy_i - confidence_i|` | < 0.05 | > 0.10 = RECALIBRAÇÃO |
| ROI | `PnL / turnover` | > 5% (backtest), > 3% (real) | < 0% após 50 apostas = PAUSA |
| Sharpe Ratio | `(ROI_avg - 0) / σ_ROI` | > 0.5 | < 0 = REVISÃO MODELO |
| Sortino | `(ROI_avg - 0) / σ_downside` | > 1.0 | < 0 = PAUSA |
| Risk of Ruin | fórmula de Gambler's Ruin | < 1% | > 5% = REDUÇÃO STAKE |
| Calmar Ratio | `ROI_anual / max_drawdown` | > 2.0 | < 1.0 = PAUSA |

---

## 5. BACKLOG DE PESQUISA

- [ ] Implementar purged k-fold CV com embargo automático
- [ ] Criar módulo de Monte Carlo para simulação de bankroll
- [ ] Implementar block bootstrap com block size ótimo (autocorrelação)
- [ ] Desenvolver teste de regime change (CUSUM, Chow test)
- [ ] Criar análise de edge decay por mercado e época
- [ ] Implementar decomposição de PnL (skill vs luck vs market movement)

---

## 6. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos preditivos
- [[06_Backtesting/INDEX]] → Validação temporal e overfitting
- [[08_Risk_Management/INDEX]] → Kelly, drawdown, bankroll theory
- [[32_Feature_Store/INDEX]] → Features de entrada para modelos
