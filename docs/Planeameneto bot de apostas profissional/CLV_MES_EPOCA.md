# CLV_MES_EPOCA — Análise de Closing Line Value por Mês e Época

**ID:** `CLV-001` | **Área:** #area/quant | **Fase:** #phase/3+ | **Owner:** Principal Quant Engineer | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. PROPÓSITO

Monitorizar e decompor o **Closing Line Value (CLV)** ao longo do tempo — por mês, por época NBA, por regime de jogo e por mercado — para identificar:
1. Degradação do edge ao longo do tempo (decay)
2. Sazonalidade do edge (início vs fim de época)
3. Regimes onde o modelo tem mais ou menos vantagem
4. Necessidade de re-treino do modelo

---

## 2. DEFINIÇÃO DE CLV

```
CLV (%) = (odd_executada / odd_fecho) - 1

Onde:
  odd_executada = odd no momento da aposta (antes do jogo)
  odd_fecho     = odd na hora do início do jogo (closing line)

CLV > 0% → Apostámos melhor do que o mercado final → Edge real
CLV < 0% → Mercado moveu contra nós → Sinal de fraqueza
```

**Interpretação:**
- CLV > 2%: Edge consistente e significativo
- CLV 0-2%: Edge marginal, monitorizar
- CLV < 0%: Sem edge, parar apostas e investigar

---

## 3. ANÁLISE POR MÊS

### 3.1 Query SQL — CLV Mensal
```sql
SELECT
    DATE_TRUNC('month', bet_timestamp) AS mes,
    COUNT(*) AS n_apostas,
    ROUND(AVG((odd_executed / odd_close - 1) * 100), 2) AS clv_medio_pct,
    ROUND(STDDEV((odd_executed / odd_close - 1) * 100), 2) AS clv_std,
    ROUND(
        AVG((odd_executed / odd_close - 1) * 100) /
        NULLIF(STDDEV((odd_executed / odd_close - 1) * 100) / SQRT(COUNT(*)), 0),
        2
    ) AS t_stat,
    ROUND(SUM(pnl), 2) AS pnl_total_eur,
    ROUND(SUM(pnl) / SUM(stake) * 100, 2) AS roi_pct
FROM bets
WHERE
    status = 'settled'
    AND odd_close IS NOT NULL
GROUP BY 1
ORDER BY 1 DESC;
```

### 3.2 Tabela de Acompanhamento
| Mês | N Apostas | CLV Médio | t-stat | p-value | PnL (€) | ROI (%) | Estado |
|-----|-----------|-----------|--------|---------|---------|---------|--------|
| 2026-05 | — | — | — | — | — | — | ⏳ |
| 2026-06 | — | — | — | — | — | — | ⏳ |
| 2026-07 | — | — | — | — | — | — | ⏳ |

**Critério de saúde:** CLV > 2% com |t-stat| > 2.0 durante 2+ meses consecutivos.

---

## 4. ANÁLISE POR ÉPOCA NBA

### 4.1 Estrutura de uma Época NBA
```
Outubro–Novembro: Início de época (alta variância, modelos menos calibrados)
Dezembro–Fevereiro: Época regular consolidada (melhor edge)
Março: Fim de época regular (equipas em gestão de carga)
Abril: Playoffs fase 1 (amostra pequena, alta variância)
Maio–Junho: Playoffs finais (máxima atenção de mercado, menor edge esperado)
```

### 4.2 Query SQL — CLV por Fase de Época
```sql
SELECT
    CASE
        WHEN EXTRACT(MONTH FROM bet_timestamp) IN (10, 11) THEN 'Início Época'
        WHEN EXTRACT(MONTH FROM bet_timestamp) IN (12, 1, 2) THEN 'Época Consolidada'
        WHEN EXTRACT(MONTH FROM bet_timestamp) = 3 THEN 'Fim Época Regular'
        WHEN EXTRACT(MONTH FROM bet_timestamp) IN (4, 5, 6) THEN 'Playoffs'
    END AS fase_epoca,
    COUNT(*) AS n_apostas,
    ROUND(AVG((odd_executed / odd_close - 1) * 100), 2) AS clv_medio_pct,
    ROUND(SUM(pnl) / SUM(stake) * 100, 2) AS roi_pct
FROM bets
WHERE status = 'settled' AND odd_close IS NOT NULL
GROUP BY 1
ORDER BY MIN(bet_timestamp);
```

### 4.3 Hipóteses de Sazonalidade
| Fase | Edge Esperado | Razão |
|------|--------------|-------|
| Início Época | Baixo | Equipas novas, modelo não calibrado para nova época |
| Época Consolidada | Alto | Padrões estáveis, modelo bem calibrado |
| Fim Época Regular | Médio | Rotação de jogadores, gestão de carga |
| Playoffs | Baixo-Médio | Mercados mais eficientes, menos jogos |

---

## 5. ANÁLISE POR REGIME

### 5.1 CLV por Tipo de Jogo
```sql
SELECT
    CASE
        WHEN is_back_to_back = TRUE THEN 'Back-to-Back'
        WHEN rest_days <= 1 THEN 'Pouco Descanso'
        WHEN rest_days >= 4 THEN 'Muito Descanso'
        ELSE 'Normal'
    END AS regime,
    COUNT(*) AS n,
    ROUND(AVG((odd_executed / odd_close - 1) * 100), 2) AS clv_medio
FROM bets b
JOIN games g ON b.game_id = g.id
WHERE b.status = 'settled' AND b.odd_close IS NOT NULL
GROUP BY 1
ORDER BY clv_medio DESC;
```

### 5.2 CLV por Mercado
```sql
SELECT
    market_type,
    COUNT(*) AS n,
    ROUND(AVG((odd_executed / odd_close - 1) * 100), 2) AS clv_medio,
    ROUND(SUM(pnl) / SUM(stake) * 100, 2) AS roi_pct
FROM bets
WHERE status = 'settled' AND odd_close IS NOT NULL
GROUP BY 1;
```

---

## 6. DECOMPOSIÇÃO DO CLV

O CLV pode ser decomposto em:
```
CLV Total = CLV de Modelo + CLV de Timing + CLV de Execução

CLV de Modelo   = capacidade preditiva (probabilidade mais precisa que mercado)
CLV de Timing   = apostamos antes que o mercado corrija a ineficiência
CLV de Execução = slippage real vs teórico (negativo = pior execução)
```

### 6.1 Medir CLV de Timing
```python
def clv_timing_analysis(bets_df):
    """
    Compara CLV em diferentes janelas de antecedência:
    - 24h+ antes do jogo
    - 4-24h antes do jogo
    - <4h antes do jogo
    """
    bets_df['hours_before'] = (
        bets_df['game_start'] - bets_df['bet_timestamp']
    ).dt.total_seconds() / 3600

    bets_df['timing_bucket'] = pd.cut(
        bets_df['hours_before'],
        bins=[0, 4, 24, float('inf')],
        labels=['<4h', '4-24h', '>24h']
    )

    return bets_df.groupby('timing_bucket').agg(
        n=('clv', 'count'),
        clv_medio=('clv', 'mean'),
        clv_std=('clv', 'std')
    )
```

---

## 7. THRESHOLDS E CIRCUIT BREAKERS

| Condição | Ação |
|----------|------|
| CLV mensal < 0% durante 30 dias | Reduzir stakes para 50% |
| CLV mensal < -1% durante 60 dias | Pausar apostas, rever modelo |
| CLV médio 90d < 1% com p > 0.10 | Investigar degradação de edge |
| CLV de Playoffs < -2% em 2 épocas | Excluir Playoffs do sistema |

---

## 8. RELATÓRIO AUTOMÁTICO MENSAL

Script de geração automática (cron 1º de cada mês):
```python
def generate_monthly_clv_report(month: str) -> str:
    """
    Gera relatório Markdown com CLV do mês anterior.
    Enviado automaticamente para Telegram do operador.
    """
    # Calcular métricas
    # Comparar com mês anterior e média histórica
    # Detetar anomalias
    # Formatar relatório
    pass
```

---

## 9. BACKLOG

- [ ] Implementar queries SQL de CLV mensal após primeiras apostas reais
- [ ] Criar dashboard Grafana com gráfico de CLV rolling 30/60/90 dias
- [ ] Implementar script de relatório mensal automático
- [ ] Documentar primeiro mês de resultados reais (Fase 4)
- [ ] Analisar sazonalidade após primeira época completa

---

## 10. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] → Análise CLV detalhada e técnica
- [[03_Quant_Research/INDEX]] → Definições teóricas de CLV
- [[06_Backtesting/INDEX]] → CLV em backtests históricos
- [[47_Shadow_Betting/INDEX]] → CLV em shadow mode (pré-dinheiro real)
- [[36_KPIs/INDEX]] → CLV como KPI principal

---

**Data de Criação:** `2026-05-13`  
**Próxima Revisão:** Após primeiras 100 apostas reais (Fase 4)
