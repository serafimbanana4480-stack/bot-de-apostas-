# TEMPLATE_DASHBOARD — Especificação de Dashboard

**ID:** TPL-011 | **Versão:** v1.0 | **Data:** YYYY-MM-DD  
**Tags:** #type/dashboard #status/[draft|active|deprecated]

---

## 1. INFORMAÇÕES DO DASHBOARD

| Campo | Valor |
|-------|-------|
| **ID** | *DB-XXX* |
| **Nome** | *Nome do dashboard* |
| **Ferramenta** | *[Grafana|Tableau|Custom]* |
| **Público-Alvo** | *[Quant|Operações|Negócio|Executivo|Técnico]* |
| **Frequência de Atualização** | *[Real-time|5min|15min|1h|Diária]* |
| **Owner** | *Nome* |

---

## 2. PROPÓSITO

### 2.1 Objetivo
*Qual a decisão ou insight que este dashboard deve fornecer?*

### 2.2 Questões que Responde

1. *Pergunta 1?*
2. *Pergunta 2?*
3. *Pergunta 3?*

---

## 3. ARQUITETURA DE DADOS

### 3.1 Fontes de Dados

| Fonte | Tabela/Endpoint | Frequência | Campos Utilizados |
|-------|-----------------|------------|-------------------|
| *PostgreSQL* | *gold.metrics* | *15min* | *roi, clv* |
| *Prometheus* | *api_requests* | *Real-time* | *latency, status* |

### 3.2 Queries Principais

```sql
-- Query para KPI principal
SELECT 
    date_trunc('day', created_at) as day,
    avg(clv) as avg_clv,
    sum(pnl) as total_pnl
FROM gold.bets
WHERE created_at >= now() - interval '30 days'
GROUP BY 1
ORDER BY 1;
```

---

## 4. LAYOUT E VISUALIZAÇÕES

### 4.1 Estrutura de Painéis

```
┌─────────────────────────────────────────────────────────────┐
│  PAINEL 1: KPIs PRINCIPAIS (Row 1)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   CLV    │ │   ROI    │ │  Sharpe  │ │ # Bets   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  PAINEL 2: TENDÊNCIAS (Row 2)                               │
│  ┌──────────────────────┐ ┌──────────────────────┐       │
│  │   Gráfico CLV        │ │   Gráfico PnL        │       │
│  └──────────────────────┘ └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Painéis Detalhados

#### Painel 1.1: CLV Médio
- **Tipo:** Stat
- **Query:** `avg(clv) FROM gold.bets`
- **Thresholds:** < 0% Vermelho, 0-2% Amarelo, > 2% Verde

#### Painel 1.2: ROI Acumulado
- **Tipo:** Stat com sparkline
- **Query:** `sum(pnl) / sum(stake)`

#### Painel 2.1: Evolução CLV
- **Tipo:** Time series
- **Query:** CLV rolling 30 dias

---

## 5. ALERTAS

| Condição | Threshold | Ação |
|----------|-----------|------|
| CLV < 0% | 3 dias | Notificar @quant-team |
| ROI < -5% | 7 dias | Circuit breaker Gamma |
| API down | 2 min | Página on-call |

---

## 6. PERMISSÕES E ACESSO

| Papel | Acesso | Editar | Comentar |
|-------|--------|--------|----------|
| Admin | Total | Sim | Sim |
| Quant | Ler | Não | Sim |
| Operações | Ler | Não | Sim |

---

## 7. IMPLEMENTAÇÃO

### 7.1 Checklist

- [ ] Queries testadas e otimizadas
- [ ] Dashboard criado
- [ ] Alertas configurados
- [ ] Permissões aplicadas
- [ ] Documentação atualizada

### 7.2 URL de Acesso

- **Produção:** `https://grafana.vbq.duckdns.org/d/db-xxx`

---

## 8. LINKS CRUZADOS

- [[20_Dashboarding/INDEX]] ← Secção de dashboards
- [[36_KPIs/INDEX]] → KPIs definidos

---

**Fim do Template de Dashboard**
