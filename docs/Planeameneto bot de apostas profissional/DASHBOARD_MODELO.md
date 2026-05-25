# DASHBOARD_MODELO — Especificação de Dashboards Operacionais

**ID:** `DB-MOD-001` | **Fase:** #phase/4+ | **Owner:** MLOps Engineer + Operations Lead | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. PROPÓSITO

Este documento define o modelo canónico de todos os dashboards do sistema de value betting. Serve como referência para a criação de painéis Grafana, páginas web operacionais e relatórios Telegram.

---

## 2. HIERARQUIA DE DASHBOARDS

```
NÍVEL 1 — Executive Summary (gestão, 1 página)
    └── NÍVEL 2 — Business Dashboard (PnL, ROI, CLV, subscritores)
        └── NÍVEL 3 — Operations Center (sinais, apostas, regime)
            └── NÍVEL 4 — Quant Performance (modelo, calibração, drift)
                └── NÍVEL 5 — Infrastructure Health (sistema, BD, APIs)
```

**Referências completas em:** [[20_Dashboarding/INDEX]]

---

## 3. MODELO CANÓNICO DE PAINEL

Cada dashboard segue esta estrutura:

| Secção | Conteúdo | Refresh |
|--------|----------|---------|
| Header | Fase ativa, data/hora, alertas críticos | 1 min |
| KPIs de topo | 4-6 métricas chave com trend | 5 min |
| Gráfico principal | Série temporal da métrica principal | 5 min |
| Breakdown | Segmentação por regime/mercado/equipa | 15 min |
| Tabela de detalhe | Top 10 apostas / anomalias | 15 min |
| Alertas ativos | Lista de alertas não resolvidos | 1 min |

---

## 4. PALETA DE CORES E ALERTAS

| Estado | Cor | Threshold |
|--------|-----|-----------|
| OK / Verde | `#00C853` | Métrica dentro do target |
| Warning / Amarelo | `#FFD600` | Métrica 10-20% fora do target |
| Critical / Vermelho | `#D50000` | Métrica >20% fora do target ou circuit breaker ativo |
| Info / Azul | `#2196F3` | Informação operacional |
| Shadow / Cinza | `#757575` | Shadow mode (sem dinheiro real) |

---

## 5. MÉTRICAS POR DASHBOARD

### 5.1 Executive Summary
- ROI acumulado (%) desde início
- PnL total (€) e por fase
- CLV médio (%) rolling 30 dias
- Número de apostas ativas
- Estado do sistema (OK / Warning / Critical)
- Subscritores Telegram ativos

### 5.2 Business Dashboard
- PnL diário/semanal/mensal (gráfico de barras)
- ROI por mercado (Moneyline vs Spread)
- CLV por regime (home/away, B2B, favorites/underdogs)
- Bankroll evolution (curva acumulada)
- Drawdown atual e máximo histórico
- MRR tipster (€/mês)

### 5.3 Operations Center
- Sinais gerados hoje / confirmados / executados
- Apostas abertas (pendentes de resultado)
- Apostas settledadas hoje (win/loss/void)
- Odd média executada vs sinalizada (slippage)
- Tempo médio execução (manual ou automática)
- Disponibilidade das casas de apostas

### 5.4 Quant Performance
- Brier Score rolling (vs mercado baseline)
- ECE (Expected Calibration Error) por regime
- Feature importance top 10 (atual vs anterior)
- Precision/Recall por threshold de edge
- Distribuição de probabilidades previstas
- Walk-forward CV results (Sharpe, ROI, CLV)

### 5.5 Infrastructure Health
- CPU / RAM / Disk (VPS)
- PostgreSQL: conexões, query time, replication lag
- Redis: hit rate, memória, operações/seg
- FastAPI: request rate, latência p50/p99, error rate
- APIs externas: Betfair latência, NBA API status
- Último backup: data e tamanho

---

## 6. ALERTAS INTEGRADOS

| Alerta | Threshold | Ação | Canal |
|--------|-----------|------|-------|
| Drawdown > 15% | ROI 7d < -15% | Pausar apostas | Telegram + Email |
| CLV caindo | CLV 30d < 1% | Rever modelo | Telegram |
| Brier Score pior que mercado | BS > 0.25 | Investigar calibração | Telegram |
| Pipeline falhou | Dados > 30 min atraso | Verificar ingestão | Telegram |
| Sistema offline | Uptime < 99% | Investigar VPS | SMS + Telegram |
| Aposta não confirmada | > 10 min após sinal | Alertar operador | Telegram |

---

## 7. IMPLEMENTAÇÃO TÉCNICA

### 7.1 Stack
- **Grafana** (dashboards técnicos e de negócio)
- **Prometheus** (métricas de infraestrutura e modelo)
- **PostgreSQL + queries SQL** (métricas de apostas/PnL)
- **Telegram Bot** (alertas e resumos diários automáticos)
- **FastAPI** (endpoint `/metrics` para Prometheus scraping)

### 7.2 Exportação de Métricas (FastAPI)
```python
from prometheus_client import Counter, Gauge, Histogram

bets_total = Counter('bets_total', 'Total bets placed', ['market', 'result'])
clv_gauge = Gauge('clv_current', 'Current CLV rolling 30d')
roi_gauge = Gauge('roi_current', 'Current ROI all-time')
model_brier = Gauge('model_brier_score', 'Current Brier Score')
```

---

## 8. BACKLOG

- [ ] Criar dashboards Grafana para cada nível
- [ ] Implementar endpoint `/metrics` na FastAPI
- [ ] Configurar alertas Prometheus → Alertmanager → Telegram
- [ ] Criar script de resumo diário automático (cron 08:00)
- [ ] Documentar queries SQL para cada métrica

---

## 9. LINKS CRUZADOS

- [[20_Dashboarding/INDEX]] → Dashboards detalhados
- [[10_Monitoring/INDEX]] → Prometheus/Grafana setup
- [[33_Alerting/INDEX]] → Regras de alertas
- [[36_KPIs/INDEX]] → KPIs de negócio
- [[37_CLV_Analytics/INDEX]] → Análise CLV detalhada

---

**Data de Criação:** `2026-05-13`  
**Próxima Revisão:** `2026-06-13`
