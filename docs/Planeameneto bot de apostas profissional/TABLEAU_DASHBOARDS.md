# TABLEAU_DASHBOARDS — Dashboards Tableau

**ID:** `DB-002` | **Fase:** #phase/3 | **Owner:** Data Analyst | **Status:** #status/active

---

## 1. OBJETIVO

Definir dashboards Tableau para visualização interativa de métricas de negócio, operações e performance do modelo, permitindo análise em tempo real e tomada de decisão informada.

---

## 2. ARQUITETURA DE DASHBOARDS

### 2.1 Hierarquia de Dashboards

```
Tableau Server / Tableau Cloud
│
├── 01_Executive_Overview (Nível Executivo)
│   ├── KPIs principais
│   ├── Tendências de alto nível
│   └── Alertas críticos
│
├── 02_Operational_Monitoring (Nível Operacional)
│   ├── Volume de apostas
│   ├── Status de execução
│   └── Reconciliação
│
├── 03_Model_Performance (Nível Técnico)
│   ├── Métricas de ML
│   ├── Feature importance
│   └── Drift detection
│
├── 04_Financial_Analysis (Nível Financeiro)
│   ├── PnL detalhado
│   ├── ROI por segmento
│   └── Análise de drawdown
│
└── 05_Risk_Management (Nível de Risco)
    ├── Exposição atual
    ├── Limites de risco
    └── Circuit breakers
```

---

## 3. DASHBOARD EXECUTIVO (01_Executive_Overview)

### 3.1 KPIs Principais

| KPI | Fórmula | Target | Alerta |
|-----|---------|--------|--------|
| ROI YTD | PnL total / Stake total | > 5% | < 0% |
| CLV Médio | Média de CLV | > 2% | < 1% |
| Bankroll Atual | Soma disponível | > €10,000 | < €5,000 |
| Sharpe Ratio | (ROI - Rf) / Std(ROI) | > 0.5 | < 0 |
| Win Rate | Apostas ganhas / Total | > 55% | < 50% |
| Max Drawdown | Max queda acumulada | < 20% | > 30% |

### 3.2 Visualizações

**Gráfico Principal - PnL Acumulado:**
- Line chart mostrando PnL ao longo do tempo
- Filtros: Período (7D, 30D, 90D, YTD), Desporto, Liga
- Linha de referência: Break-even (€0)
- Highlight: PnL dos últimos 30 dias

**Gráfico Secundário - ROI por Mês:**
- Bar chart comparativo mensal
- Cores: Verde (positivo), Vermelho (negativo)
- Meta: Linha de target (5%)

**KPI Cards:**
- 6 cards no topo com KPIs principais
- Indicadores de tendência (↑ ↓)
- Comparação com período anterior

**Alertas Panel:**
- Lista de alertas ativos
- Severidade: Crítico (vermelho), Alto (laranja), Médio (amarelo)
- Link para dashboard detalhado

### 3.3 Filtros

- **Período:** Últimos 7 dias, 30 dias, 90 dias, YTD, Custom
- **Desporto:** Todos, NBA, NFL, Tênis, etc.
- **Liga:** Todas as ligas do desporto selecionado
- **Tipo de aposta:** Todos, Moneyline, Spread, Totals
- **Modelo:** Todos, Modelo A, Modelo B, Ensemble

---

## 4. DASHBOARD OPERACIONAL (02_Operational_Monitoring)

### 4.1 Volume de Apostas

**Métricas:**
- Apostas por dia (count)
- Volume monetário (stake total)
- Apostas por hora (heatmap)
- Taxa de preenchimento (fill rate)

**Visualizações:**
- Line chart: Apostas por dia (últimos 30 dias)
- Bar chart: Volume por tipo de aposta
- Heatmap: Distribuição horária (hora vs dia da semana)
- Gauge: Fill rate atual (target > 85%)

### 4.2 Status de Execução

**Métricas:**
- Taxa de sucesso de execução
- Tempo médio de execução
- Erros por tipo
- Latência por API

**Visualizações:**
- Gauge: Taxa de sucesso (target > 95%)
- Line chart: Tempo médio de execução
- Pie chart: Distribuição de erros
- Bar chart: Latência por API (Betfair, Pinnacle, etc.)

### 4.3 Reconciliação

**Métricas:**
- Apostas reconciliadas vs pendentes
- Discrepâncias por tipo
- Tempo de reconciliação
- Status por bookmaker

**Visualizações:**
- Stacked bar: Apostas por status (Reconciliada, Pendente, Discrepante)
- Line chart: Discrepâncias ao longo do tempo
- Table: Lista de apostas pendentes (> 24h)

### 4.4 Alertas Operacionais

**Tipos de Alertas:**
- Sistema offline
- API indisponível
- Taxa de erro alta
- Latência excessiva

**Visualização:**
- Timeline de alertas
- Contagem por severidade
- Tempo médio de resolução

---

## 5. DASHBOARD DE MODELO (03_Model_Performance)

### 5.1 Métricas de ML

**Métricas:**
- Accuracy, Precision, Recall, F1
- ROC AUC
- Log Loss
- Brier Score
- ECE (Expected Calibration Error)

**Visualizações:**
- Line chart: Métricas ao longo do tempo (rolling 7D)
- Bar chart: Comparação com baseline
- Table: Valores atuais vs targets

### 5.2 Feature Importance

**Visualizações:**
- Horizontal bar chart: Top 20 features
- Treemap: Importance por categoria (Forma, Mercado, Contexto)
- Line chart: Importância ao longo do tempo (últimos 30 dias)
- Heatmap: Correlação entre features

**Filtros:**
- Modelo
- Período
- Tipo de feature

### 5.3 Calibração

**Visualizações:**
- Reliability diagram: Probabilidade predita vs frequência observada
- Histograma de probabilidades
- Calibration slope e intercept
- Brier score por bin de probabilidade

**Análise:**
- Overconfident: Slope < 1
- Underconfident: Slope > 1
- Well-calibrated: Slope ≈ 1, Intercept ≈ 0

### 5.4 Performance por Regime

**Regimes:**
- Favorito (prob > 0.65)
- Equilibrado (0.35 ≤ prob ≤ 0.65)
- Underdog (prob < 0.35)
- Alta volatilidade
- Baixa volatilidade

**Visualizações:**
- Bar chart: ROI por regime
- Line chart: Performance ao longo do tempo por regime
- Table: Estatísticas detalhadas por regime

### 5.5 Drift Detection

**Métricas:**
- PSI (Population Stability Index) por feature
- KS Test p-value
- Delta em distribuições

**Visualizações:**
- Heatmap: PSI por feature ao longo do tempo
- Bar chart: Features com drift mais alto (PSI > 0.2)
- Line chart: PSI agregado ao longo do tempo
- Alert panel: Features com drift detetado

---

## 6. DASHBOARD FINANCEIRO (04_Financial_Analysis)

### 6.1 PnL Detalhado

**Visualizações:**
- Line chart: PnL diário com média móvel (7D)
- Bar chart: PnL por tipo de aposta
- Area chart: PnL acumulado por desporto
- Waterfall chart: Decomposição de PnL (ganhos, perdas, comissões)

**Filtros:**
- Período
- Desporto
- Liga
- Tipo de aposta
- Range de odds

### 6.2 ROI por Segmento

**Segmentos:**
- Por desporto
- Por liga
- Por tipo de aposta
- Por range de odds
- Por dia da semana
- Por hora do dia

**Visualizações:**
- Treemap: ROI por segmento (tamanho = volume)
- Bar chart: Top 10 segmentos por ROI
- Heatmap: ROI por (desporto x tipo de aposta)
- Scatter plot: ROI vs Volume por segmento

### 6.3 Análise de Drawdown

**Métricas:**
- Max drawdown atual
- Duração do drawdown atual
- Número de drawdowns > 10%
- Tempo de recuperação médio

**Visualizações:**
- Line chart: PnL com drawdowns destacados (área vermelha)
- Bar chart: Magnitude dos drawdowns históricos
- Line chart: Duração dos drawdowns
- Gauge: Drawdown atual (vermelho > 20%, amarelo > 10%, verde < 10%)

### 6.4 Análise de CLV

**Visualizações:**
- Histograma: Distribuição de CLV
- Line chart: CLV médio ao longo do tempo
- Scatter plot: CLV vs Odds
- Box plot: CLV por tipo de aposta
- Table: Top 10 apostas por CLV (positivo e negativo)

---

## 7. DASHBOARD DE RISCO (05_Risk_Management)

### 7.1 Exposição Atual

**Métricas:**
- Stake total em aberto
- Exposição por desporto
- Exposição por liga
- Exposição por tipo de aposta
- Exposição vs limite (%)

**Visualizações:**
- Gauge: Exposição total vs limite
- Bar chart: Exposição por desporto
- Pie chart: Exposição por tipo de aposta
- Heatmap: Exposição por (desporto x liga)
- Table: Apostas em aberto detalhadas

### 7.2 Limites de Risco

**Limites:**
- Stake máximo por aposta
- Stake máximo diário
- Exposição máxima por desporto
- Exposição máxima por liga
- Drawdown máximo

**Visualizações:**
- Gauge: Cada limite com % utilizado
- Bar chart: Utilização de cada limite
- Timeline: Violações de limites históricas
- Alert panel: Limites próximos de ser excedidos (> 80%)

### 7.3 Circuit Breakers

**Status:**
- Circuit breakers ativos
- Motivo de ativação
- Duração
- Ações tomadas

**Visualizações:**
- Table: Circuit breakers ativos
- Timeline: Histórico de ativações
- Pie chart: Circuit breakers por motivo
- Line chart: Taxa de ativação ao longo do tempo

---

## 8. DATA SOURCES

### 8.1 PostgreSQL (Principal)

**Tabelas:**
- `bets`: Todas as apostas executadas
- `predictions`: Todas as predições do modelo
- `model_metrics`: Métricas de performance
- `feature_importance`: Importância de features
- `drift_detection`: Métricas de drift
- `financial_summary`: Agregações financeiras

**Refresh:**
- Incremental: A cada hora
- Full: Diariamente às 02:00 UTC

### 8.2 Redis (Cache)

**Dados:**
- Métricas em tempo real
- Status de sistema
- Alertas ativos

**Refresh:**
- A cada 5 minutos

### 8.3 Arquivos Flat (Histórico)

**Dados:**
- Logs de sistema
- Arquivos de backup

**Refresh:**
- Diariamente

---

## 9. ATUALIZAÇÃO E PERFORMANCE

### 9.1 Schedule de Refresh

| Dashboard | Frequência | Horário | Método |
|-----------|-----------|---------|--------|
| Executive Overview | A cada hora | :00 | Incremental |
| Operational | A cada 15 min | :00, :15, :30, :45 | Incremental |
| Model Performance | Diário | 03:00 | Full |
| Financial Analysis | Diário | 04:00 | Full |
| Risk Management | A cada 5 min | Contínuo | Incremental |

### 9.2 Performance Targets

| Métrica | Target | SLO |
|---------|--------|-----|
| Tempo de carregamento | < 5s | < 10s |
| Tempo de refresh | < 2min | < 5min |
| Queries por segundo | > 50 | > 20 |
| Concorrência de usuários | > 20 | > 10 |

---

## 10. ACESSO E SEGURANÇA

### 10.1 Níveis de Acesso

| Nível | Dashboards | Permissões |
|-------|------------|------------|
| Executivo | Executive Overview | View only |
| Operações | Operational, Executive | View, export |
| Técnico | Model Performance, Operational | View, export, drill-down |
| Financeiro | Financial, Executive | View, export |
| Risco | Risk Management, Executive | View, export |
| Admin | Todos | Full access |

### 10.2 Autenticação

- **SSO** via Google/Microsoft
- **MFA** obrigatório para admin
- **Sessão:** 8 horas timeout
- **IP whitelisting:** Opcional para admin

---

## 11. EXPORTAÇÃO E DISTRIBUIÇÃO

### 11.1 Formatos de Exportação

- **PDF:** Para relatórios executivos
- **Excel:** Para análise adicional
- **Image (PNG):** Para apresentações
- **CSV:** Para integração com outros sistemas

### 11.2 Assinaturas Automáticas

- **Relatório diário executivo:** PDF por email às 08:00
- **Relatório semanal financeiro:** PDF por email segunda-feira às 09:00
- **Alertas críticos:** Instantâneo via Slack/Telegram

---

## 12. MELHORIAS FUTURAS

- [ ] Integrar com MLflow para tracking de experimentos
- [ ] Adicionar dashboards mobile (Tableau Mobile)
- [ ] Implementar data storytelling automático
- [ ] Adicionar análise de sentimento de mercado
- [ ] Criar dashboards de benchmarking vs concorrência
- [ ] Implementar alertas inteligentes (ML-based)

---

## 13. LINKS CRUZADOS

- [[09_Monitoring/INDEX]] ← Secção mãe
- [[TEMPLATE_DASHBOARD]] → Template para novos dashboards
- [[10_Monitoring/METRICAS_DETALHADAS]] → Definição de métricas
- [[16_Data_Analytics/INDEX]] → Análise de dados avançada
