# 36_KPIs — INDEX

**ID:** `SEC-36` | **Fase:** #phase/3-10 | **Owner:** Product Owner + Financeiro | **Status:** #status/active

---

## 1. OBJETIVO

Definir e monitorizar KPIs (Key Performance Indicators) para medir o sucesso do sistema em múltiplas dimensões: modelo, negócio, operação, e infraestrutura. KPIs permitem tomar decisões baseadas em dados e identificar áreas de melhoria.

---

## 2. PILARES DE KPIs

```
┌─────────────────────────────────────────────────────────────┐
│                    PILAR 1: MODELO                             │
│  CLV, ROI, Sharpe, Win Rate, Calibração, Drift              │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 2: NEGÓCIO                           │
│  MRR, ARPU, Churn, CAC, LTV, Subscritores, Conversão      │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 3: OPERAÇÃO                           │
│  Uptime, Latência, Fill Rate, Slippage, Alert Response    │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 4: INFRAESTRUTURA                    │
│  CPU, Memory, Disk, Network, Costs, Scalability             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. KPIs DE MODELO

### 3.1 CLV (Closed Line Value)

**Definição:** Edge médio de todas as apostas

**Fórmula:**
```
CLV = (Probabilidade × Odd) - 1
CLV_médio = Média de CLV de todas as apostas
```

**Target:** > 2.0%

**Frequência:** Rolling 100 apostas

**Alerta:** Se CLV 3d < 0% (HIGH)

---

### 3.2 ROI (Return on Investment)

**Definição:** PnL total / Stake total

**Fórmula:**
```
ROI = (PnL / Stake) × 100
```

**Target:** > 5%

**Frequência:** Mensal

**Alerta:** Se ROI 7d < 0% (HIGH)

---

### 3.3 Sharpe Ratio

**Definição:** ROI médio / Desvio padrão de ROI

**Fórmula:**
```
Sharpe = (Média_ROI / Desvio_Padrão_ROI) × √252 (anualizado)
```

**Target:** > 0.5

**Frequência:** Rolling 100 apostas

**Alerta:** Se Sharpe < 0.3 (MEDIUM)

---

### 3.4 Win Rate

**Definição:** % de apostas vencedas

**Fórmula:**
```
Win Rate = (Apostas Vencidas / Total Apostas) × 100
```

**Target:** > 52%

**Frequência:** Rolling 100 apostas

**Alerta:** Se Win Rate < 48% (MEDIUM)

---

### 3.5 Brier Score

**Definição:** Erro quadrático médio de calibração

**Fórmula:**
```
Brier = (1/N) × Σ(Probabilidade - Outcome)²
```

**Target:** < Brier_mercado

**Frequência:** Mensal

**Alerta:** Se Brier > Brier_mercado + 0.05 (HIGH)

---

### 3.6 ECE (Expected Calibration Error)

**Definição:** Erro médio absoluto de calibração

**Fórmula:**
```
ECE = (1/N) × Σ|Probabilidade_Preditos - Probabilidade_Real|
```

**Target:** < 0.05

**Frequência:** Mensal

**Alerta:** Se ECE > 0.10 (HIGH)

---

### 3.7 Model Drift

**Definição:** Mudança na distribuição de features

**Fórmula:**
```
Drift = KS test entre features atuais e features de treino
```

**Target:** < 0.20

**Frequência:** Semanal

**Alerta:** Se Drift > 0.20 (HIGH)

---

## 4. KPIs DE NEGÓCIO

### 4.1 MRR (Monthly Recurring Revenue)

**Definição:** Receita recorrente mensal de subscrições

**Fórmula:**
```
MRR = Σ(Subscrições Ativas × Preço)
```

**Target:** > 1.450€ (50 subscritores × 29€)

**Frequência:** Mensal

**Alerta:** Se MRR < 1.000€ (MEDIUM)

---

### 4.2 ARPU (Average Revenue Per User)

**Definição:** Receita média por subscritor

**Fórmula:**
```
ARPU = MRR / Número de Subscritores
```

**Target:** > 29€

**Frequência:** Mensal

**Alerta:** Se ARPU < 25€ (MEDIUM)

---

### 4.3 Churn Rate

**Definição:** Taxa de cancelamento mensal

**Fórmula:**
```
Churn Rate = (Cancelamentos no Mês / Subscritores no Início do Mês) × 100
```

**Target:** < 5%

**Frequência:** Mensal

**Alerta:** Se Churn > 10% (HIGH)

---

### 4.4 CAC (Customer Acquisition Cost)

**Definição:** Custo médio de aquisição de subscritor

**Fórmula:**
```
CAC = (Marketing + Vendas) / Novos Subscritores
```

**Target:** < 50€

**Frequência:** Trimestral

**Alerta:** Se CAC > 100€ (MEDIUM)

---

### 4.5 LTV (Lifetime Value)

**Definição:** Valor total do subscritor durante sua vida

**Fórmula:**
```
LTV = ARPU × (1 / Churn Rate)
```

**Target:** > 100€

**Frequência:** Trimestral

**Alerta:** Se LTV < CAC (HIGH)

---

### 4.6 Número de Subscritores

**Definição:** Número total de subscritores ativos

**Target:** 50 (Fase 6), 100 (Fase 12)

**Frequência:** Mensal

**Alerta:** Se Subscritores < 30 (MEDIUM)

---

## 5. KPIs DE OPERAÇÃO

### 5.1 Uptime

**Definição:** % de tempo que sistema está disponível

**Fórmula:**
```
Uptime = (Tempo Online / Tempo Total) × 100
```

**Target:** > 99.5%

**Frequência:** Mensal

**Alerta:** Se Uptime < 99% (CRITICAL)

---

### 5.2 Latência de API

**Definição:** Tempo médio de resposta da API

**Fórmula:**
```
Latência p50 = Mediana de tempo de resposta
Latência p95 = 95º percentil de tempo de resposta
```

**Target:** p50 < 100ms, p95 < 200ms

**Frequência:** Semanal

**Alerta:** Se p95 > 500ms (HIGH)

---

### 5.3 Fill Rate

**Definição:** % de sinais que resultaram em apostas executadas

**Fórmula:**
```
Fill Rate = (Apostas Executadas / Sinais Gerados) × 100
```

**Target:** > 80%

**Frequência:** Diária

**Alerta:** Se Fill Rate < 70% (HIGH)

---

### 5.4 Slippage Médio

**Definição:** Diferença média entre odd esperada e odd executada

**Fórmula:**
```
Slippage = |Odd_Executada - Odd_Esperada| / Odd_Esperada
```

**Target:** < 2%

**Frequência:** Diária

**Alerta:** Se Slippage > 3% (HIGH)

---

### 5.5 Tempo de Resposta a Alertas

**Definição:** Tempo médio para responder a alertas críticos

**Fórmula:**
```
Tempo Resposta = Tempo entre alerta e acknowledge
```

**Target:** < 5 min (CRITICAL), < 30 min (HIGH)

**Frequência:** Mensal

**Alerta:** Se Tempo > 10 min (CRITICAL)

---

## 6. KPIs DE INFRAESTRUTURA

### 6.1 CPU Usage

**Definição:** % de utilização de CPU

**Target:** < 70% (média), < 90% (pico)

**Frequência:** Contínua

**Alerta:** Se CPU > 90% por 10 min (HIGH)

---

### 6.2 Memory Usage

**Definição:** % de utilização de RAM

**Target:** < 70% (média), < 85% (pico)

**Frequência:** Contínua

**Alerta:** Se Memory > 85% por 10 min (HIGH)

---

### 6.3 Disk Usage

**Definição:** % de utilização de disco

**Target:** < 85%

**Frequência:** Diária

**Alerta:** Se Disk > 90% (HIGH)

---

### 6.4 Network Latency

**Definição:** Latência de rede entre serviços

**Target:** < 10ms (local), < 50ms (externo)

**Frequência:** Semanal

**Alerta:** Se Latência > 100ms (MEDIUM)

---

### 6.5 Custos

**Definição:** Custo mensal total de infraestrutura

**Target:** < 30€ (Fase 1-6), < 100€ (Fase 7-12)

**Frequência:** Mensal

**Alerta:** Se Custos > 50% do orçamento (HIGH)

---

## 7. DASHBOARDS DE KPIs

### 7.1 Dashboard de Modelo

**Gráficos:**
- CLV rolling (últimos 100 apostas)
- ROI mensal (últimos 12 meses)
- Sharpe Ratio rolling (últimos 100 apostas)
- Win Rate rolling (últimos 100 apostas)
- Brier Score mensal
- ECE mensal
- Model Drift (KS test)

### 7.2 Dashboard de Negócio

**Gráficos:**
- MRR ao longo do tempo
- ARPU ao longo do tempo
- Churn rate mensal
- Número de subscritores ao longo do tempo
- CAC vs LTV
- Funnel de conversão (visitantes → trial → pagos)

### 7.3 Dashboard de Operação

**Gráficos:**
- Uptime (últimos 30 dias)
- Latência de API (p50, p95)
- Fill rate diário
- Slippage médio diário
- Tempo de resposta a alertas
- Número de incidentes

### 7.4 Dashboard de Infraestrutura

**Gráficos:**
- CPU usage (últimos 7 dias)
- Memory usage (últimos 7 dias)
- Disk usage
- Network latency
- Custos mensais
- Número de containers

---

## 8. ALERTAS DE KPIs

### 8.1 Configuração de Alertas

```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: model_kpis
    rules:
      - alert: CLVNegative
        expr: clv_rolling_3d < 0
        for: 5m
        labels:
          severity: high
          team: business
        annotations:
          summary: "CLV negativo nos últimos 3 dias"
      
      - alert: ModelDriftHigh
        expr: drift_score > 0.20
        for: 1h
        labels:
          severity: high
          team: data
        annotations:
          summary: "Model drift detectado"
  
  - name: business_kpis
    rules:
      - alert: ChurnHigh
        expr: churn_rate > 0.10
        for: 1d
        labels:
          severity: high
          team: business
        annotations:
          summary: "Churn rate > 10%"
      
      - alert: SubscribersLow
        expr: n_subscribers < 30
        for: 1d
        labels:
          severity: medium
          team: business
        annotations:
          summary: "Número de subscritores abaixo de 30"
  
  - name: operations_kpis
    rules:
      - alert: FillRateLow
        expr: fill_rate < 0.70
        for: 1h
        labels:
          severity: high
          team: operations
        annotations:
          summary: "Fill rate < 70%"
      
      - alert: UptimeLow
        expr: uptime < 0.99
        for: 5m
        labels:
          severity: critical
          team: operations
        annotations:
          summary: "Uptime < 99%"
  
  - name: infrastructure_kpis
    rules:
      - alert: CPUHigh
        expr: cpu_usage > 0.90
        for: 10m
        labels:
          severity: high
          team: devops
        annotations:
          summary: "CPU > 90%"
      
      - alert: DiskFull
        expr: disk_usage > 0.90
        for: 5m
        labels:
          severity: high
          team: devops
        annotations:
          summary: "Disk > 90%"
```

---

## 9. REPORTING DE KPIs

### 9.1 Relatório Semanal

**Conteúdo:**
- Resumo executivo
- KPIs de modelo (CLV, ROI, Sharpe)
- KPIs de negócio (MRR, Churn)
- KPIs de operação (Uptime, Fill Rate)
- Análise de tendências
- Recomendações

**Distribuição:**
- Email para equipa (segunda-feira 09:00)
- Disponível no dashboard

### 9.2 Relatório Mensal

**Conteúdo:**
- Resumo executivo
- Todos os KPIs (modelo, negócio, operação, infra)
- Comparação com targets
- Análise de tendências
- Recomendações estratégicas
- Planos de ação

**Distribuição:**
- Email para stakeholders (dia 1 de cada mês)
- Disponível no dashboard
- Apresentação em reunião mensal

---

## 10. BACKLOG DE KPIs

- [ ] Definir todos os KPIs
- [ ] Implementar coleta de dados para KPIs
- [ ] Configurar dashboards Grafana para cada pilar
- [ ] Configurar alertas Prometheus para todos os KPIs
- [ ] Implementar relatório semanal
- [ ] Implementar relatório mensal
- [ ] Configurar automação de relatórios
- [ ] Definir processo de revisão de KPIs
- [ ] Documentar targets e justificações
- [ ] Implementar sistema de alerta de KPIs

---

## 11. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[10_Monitoring/INDEX]] → Monitorização e alertas
- [[35_Financial_Tracking/INDEX]] → Tracking financeiro
- [[37_CLV_Analytics/INDEX]] → Análise de CLV
- [[02_Business_Model/INDEX]] → Modelo de negócio
