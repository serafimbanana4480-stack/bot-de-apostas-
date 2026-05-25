# TEMPLATE_DASHBOARD — Template de Dashboard

**ID:** `DB-001` | **Fase:** #phase/3 | **Owner:** Data Analyst | **Status:** #status/active

---

## 1. OBJETIVO

Definir template padrão para dashboards de monitorização.

---

## 2. ESTRUTURA DO DASHBOARD

```
┌─────────────────────────────────────┐
│  Header: Nome do Dashboard          │
│  Filtros: Data, Mercado, Regime     │
├─────────────────────────────────────┤
│  KPI Cards (4-6 métricas principais)│
├─────────────────────────────────────┤
│  Gráficos de tendência (time series) │
├─────────────────────────────────────┤
│  Tabelas detalhadas                 │
└─────────────────────────────────────┘
```

---

## 3. KPI CARDS

| KPI | Formato | Atualização |
|-----|---------|-------------|
| ROI | Percentagem | Diário |
| CLV | Percentagem | Diário |
| N Apostas | Contador | Diário |
| Bankroll | Moeda | Diário |

---

## 4. GRÁFICOS PADRÃO

- **PnL acumulado** (line chart)
- **ROI por dia** (bar chart)
- **CLV por regime** (grouped bar)
- **Volume de apostas** (line chart)

---

## 5. CRITÉRIOS

- **Atualização diária** dos dados
- **Filtros interativos** (data, mercado)
- **Exportação para CSV/Excel**

---

## 6. LINKS CRUZADOS

- [[09_Monitoring/INDEX]]
- [[TABLEAU_DASHBOARDS]]
