# DASHBOARD_KPIs — Indicadores Chave

**ID:** `KPI-001` | **Fase:** #phase/4-5 | **Owner:** Product Owner | **Status:** #status/pending

---

## 1. KPIs DE MODELO

| KPI | Formula | Target | Frequencia |
|-----|---------|--------|------------|
| CLV Medio | `AVG((odd_executed/odd_close)-1)` | > 2% | Diario |
| ROI | `SUM(pnl)/SUM(stake)` | > 3% (real), > 5% (backtest) | Semanal |
| Sharpe Ratio | `MEAN(roi)/STD(roi)` | > 0.5 | Mensal |
| Win Rate | `COUNT(win)/COUNT(*)` | > 50% | Semanal |
| Brier Score | `AVG((prob-outcome)^2)` | < mercado | Mensal |

---

## 2. KPIs DE NEGOCIO

| KPI | Formula | Target |
|-----|---------|--------|
| MRR | `SUM(subscription_value)` | Crescer 10%/mes |
| Churn | `SUBS_cancelados / SUBS_total` | < 10%/mes |
| CAC | `Custo_marketing / Novos_subs` | < 50 EUR |
| LTV | `MRR * 12 / Churn` | > 300 EUR |
| Break-even | `MRR > Custos` | Mes 5 |

---

## 3. KPIs OPERACIONAIS

| KPI | Target |
|-----|--------|
| Uptime sistema | > 99% |
| Latencia sinal -> execucao | < 2 min |
| Slippage medio | < 0.5% |
| Fill rate | > 80% |

---

## 4. BACKLOG

- [ ] Criar dashboard com todas as KPIs
- [ ] Automatizar calculo diario
- [ ] Configurar alertas quando KPI < target

---

## 5. LINKS CRUZADOS

- [[36_KPIs/INDEX]] ← Secao mae
- [[10_Monitoring/INDEX]] → Dashboards tecnicos
