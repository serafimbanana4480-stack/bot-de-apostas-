# Métricas Detalhadas — Definições e Interpretação

**ID:** `MON-101` | **Fase:** #phase/1 | **Owner:** MLOps Engineer | **Status:** #status/draft

---

## 1. INTRODUÇÃO

Este documento define formalmente todas as métricas monitorizadas no sistema de value betting NBA, incluindo fórmulas de cálculo, interpretação de valores, thresholds de alerta, e ações recomendadas. Métricas são classificadas em quatro categorias: **Financeiro**, **Modelo**, **Operacional**, e **Infraestrutura**.

---

## 2. MÉTRICAS FINANCEIRAS

### 2.1 PnL (Profit and Loss)

**Definição**: Lucro ou prejuízo acumulado num período.

**Fórmula**:
```
PnL = Σ(stake × (odd - 1)) para apostas vencedoras
    - Σ(stake) para apostas perdedoras
```

**Granularidades**:
- `pnl_daily_eur`: PnL diário
- `pnl_weekly_eur`: PnL semanal
- `pnl_monthly_eur`: PnL mensal
- `pnl_cumulative_eur`: PnL acumulado desde o início

**Interpretação**:
- Positivo: Sistema lucrativo no período
- Negativo: Sistema em prejuízo no período
- Tendência: Sequência de dias negativos indica degradação

**Thresholds**:
- Alerta: PnL diário < -€1.000
- Crítico: PnL semanal < -€5.000
- Crítico: PnL mensal < -€10.000

**Ação Recomendada**:
- Investigar causas: drawdown natural, degradação de modelo, ou mudança de mercado
- Se drawdown > limite, ativar circuit breaker
- Revisar stakes e exposição

### 2.2 ROI (Return on Investment)

**Definição**: Retorno sobre o investimento, expresso como percentagem do stake total.

**Fórmula**:
```
ROI = (PnL / Stake Total) × 100
```

**Granularidades**:
- `roi_daily_percent`: ROI diário
- `roi_7d_percent`: ROI dos últimos 7 dias
- `roi_30d_percent`: ROI dos últimos 30 dias
- `roi_90d_percent`: ROI dos últimos 90 dias

**Interpretação**:
- > 5%: Excelente (edge forte)
- 2-5%: Bom (edge moderado)
- 0-2%: Fraco (edge marginal)
- < 0%: Negativo (sem edge ou degradado)

**Thresholds**:
- Alerta: ROI 7d < 0%
- Crítico: ROI 30d < -2%
- Crítico: ROI 90d < -5%

**Ação Recomendada**:
- ROI 7d < 0%: Investigar curto prazo (pode ser variação normal)
- ROI 30d < -2%: Revisar modelo, possível degradação
- ROI 90d < -5%: Pausar operações, retreinar modelo

### 2.3 Yield

**Definição**: Similar ao ROI mas calculado sobre turnover (total apostado), não sobre bankroll. É mais estável que ROI para comparação entre períodos.

**Fórmula**:
```
Yield = (PnL / Turnover) × 100
```

**Granularidades**:
- `yield_7d_percent`: Yield dos últimos 7 dias
- `yield_30d_percent`: Yield dos últimos 30 dias
- `yield_90d_percent`: Yield dos últimos 90 dias

**Interpretação**:
- > 5%: Excelente
- 2-5%: Bom
- 0-2%: Marginal
- < 0%: Negativo

**Thresholds**:
- Alerta: Yield 30d < 2%
- Crítico: Yield 90d < 0%

**Ação Recomendada**:
- Comparar com backtest yield esperado
- Se yield real << yield esperado, investigar slippage e execução

### 2.4 Drawdown

**Definição**: Queda desde o pico máximo (peak) em termos percentuais. Mede a severidade de perdas.

**Fórmula**:
```
Drawdown = (Peak - Current) / Peak × 100
```

**Tipos**:
- `drawdown_current_percent`: Drawdown atual
- `drawdown_max_percent`: Drawdown máximo histórico
- `drawdown_avg_percent`: Drawdown médio (média de todos os drawdowns)

**Interpretação**:
- < 10%: Normal (variação esperada)
- 10-20%: Moderado (atenção)
- 20-30%: Alto (risco significativo)
- > 30%: Crítico (ameaça à banca)

**Thresholds**:
- Alerta: Drawdown > 10%
- Alto: Drawdown > 15%
- Crítico: Drawdown > 20%
- Emergência: Drawdown > 30%

**Ação Recomendada**:
- 10-15%: Monitorizar, reduzir stakes se tendência continuar
- 15-20%: Reduzir stakes 50%, investigar causa
- 20-30%: Pausar novas apostas, revisar modelo completamente
- > 30%: Parar operações, análise profunda necessária

### 2.5 Sharpe Ratio

**Definição**: Retorno ajustado ao risco. Mede o retorno por unidade de risco (desvio padrão).

**Fórmula**:
```
Sharpe Ratio = (Retorno Médio - Risk Free Rate) / Desvio Padrão
```

**Granularidades**:
- `sharpe_ratio_30d`: Sharpe dos últimos 30 dias
- `sharpe_ratio_90d`: Sharpe dos últimos 90 dias

**Interpretação**:
- > 2.0: Excelente
- 1.0-2.0: Bom
- 0.5-1.0: Aceitável
- < 0.5: Fraco
- < 0: Retorno negativo ajustado ao risco

**Thresholds**:
- Alerta: Sharpe 90d < 0.5
- Crítico: Sharpe 90d < 0

**Ação Recomendada**:
- Sharpe baixo com retorno alto: Volatilidade excessiva (riscos ocultos)
- Sharpe baixo com retorno baixo: Sistema ineficiente
- Ajustar estratégias para reduzir volatilidade sem sacrificar retorno

### 2.6 Bankroll

**Definição**: Capital total disponível para apostas.

**Componentes**:
- `bankroll_total_eur`: Bankroll total (todas as bookmakers + caixa)
- `bankroll_available_eur`: Bankroll disponível (não comprometido)
- `bankroll_committed_eur`: Bankroll comprometido (em apostas pendentes)

**Interpretação**:
- Bankroll disponível deve ser sempre > 20% do total (liquidez)
- Bankroll comprometido > 80% indica sobre-exposição

**Thresholds**:
- Alerta: Bankroll disponível < 30%
- Crítico: Bankroll disponível < 20%
- Emergência: Bankroll disponível < 10%

**Ação Recomendada**:
- Reduzir stakes se disponibilidade < 30%
- Pausar novas apostas se disponibilidade < 20%
- Transferir fundos entre bookmakers se desequilibrado

---

## 3. MÉTRICAS DE MODELO

### 3.1 CLV (Closing Line Value)

**Definição**: Diferença entre a odd obtida e a odd de fechamento (closing line), expressa como percentagem. É a métrica mais importante para validar edge.

**Fórmula**:
```
CLV = ((Odd Fechada / Odd Obtida) - 1) × 100
```

**Tipos**:
- `clv_mean_percent`: CLV médio (todas as apostas)
- `clv_mean_50b_percent`: CLV médio das últimas 50 apostas
- `clv_mean_100b_percent`: CLV médio das últimas 100 apostas
- `clv_mean_500b_percent`: CLV médio das últimas 500 apostas

**Interpretação**:
- > 3%: Excelente edge
- 1-3%: Bom edge
- 0-1%: Edge marginal
- < 0%: No edge (modelo a perder para o mercado)

**Thresholds**:
- Alerta: CLV 50b < 0%
- Alto: CLV 100b < 0%
- Crítico: CLV 3d < 0%

**Ação Recomendada**:
- CLV 50b < 0%: Variação normal, monitorizar
- CLV 100b < 0%: Possível degradação, investigar
- CLV 3d < 0%: Modelo degradado, retreinar necessário

### 3.2 CLV Realizado

**Definição**: CLV calculado com a odd realmente obtida pelo subscritor, não a odd recomendada. Mede slippage.

**Fórmula**:
```
CLV Realizado = ((Odd Fechada / Odd Obtida Real) - 1) × 100
Slippage = CLV Esperado - CLV Realizado
```

**Interpretação**:
- CLV realizado << CLV esperado: Slippage excessivo
- Slippage > 2%: Problema de execução ou bookmaker com limites

**Thresholds**:
- Alerta: Slippage médio > 2%
- Crítico: Slippage médio > 5%

**Ação Recomendada**:
- Investigar bookmakers com slippage alto
- Ajustar recomendações (odds mais conservadoras)
- Treinar subscritores em timing de entrada

### 3.3 Win Rate (Taxa de Acerto)

**Definição**: Percentagem de apostas vencedoras sobre o total.

**Fórmula**:
```
Win Rate = (Apostas Vencedoras / Total Apostas) × 100
```

**Granularidades**:
- `win_rate_7d_percent`: Win rate dos últimos 7 dias
- `win_rate_30d_percent`: Win rate dos últimos 30 dias
- `win_rate_90d_percent`: Win rate dos últimos 90 dias

**Interpretação**:
- > 55%: Excelente
- 52-55%: Bom
- 50-52%: Marginal
- < 50%: Abaixo do aleatório (modelo pior que random)

**Thresholds**:
- Alerta: Win rate 30d < 52%
- Crítico: Win rate 90d < 50%

**Ação Recomendada**:
- Win rate baixo com CLV alto: Variação normal, edge existe
- Win rate baixo com CLV baixo: Modelo degradado
- Investigar se mudança de mercado ou regime

### 3.4 Edge

**Definição**: Vantagem matemática esperada da aposta, calculada como diferença entre probabilidade do modelo e probabilidade implícita da odd.

**Fórmula**:
```
Edge = (Probabilidade Modelo - Probabilidade Implícita Odd) × 100
Probabilidade Implícita = 1 / Odd
```

**Granularidades**:
- `edge_mean_percent`: Edge médio
- `edge_distribution_percent`: Distribuição de edge (histograma)

**Interpretação**:
- > 5%: Excelente
- 2-5%: Bom
- 1-2%: Marginal
- < 1%: Apenas apostar se volume alto

**Thresholds**:
- Alerta: Edge médio < 2%
- Crítico: Edge médio < 1%

**Ação Recomendada**:
- Edge baixo: Modelo não encontra valor
- Ajustar threshold mínimo de edge para gerar sinais
- Possível saturação de mercado

### 3.5 Brier Score

**Definição**: Métrica de calibração de probabilidades. Mede a diferença quadrática média entre probabilidades previstas e resultados reais.

**Fórmula**:
```
Brier Score = (1/N) × Σ(p_i - o_i)²
Onde p_i = probabilidade prevista, o_i = resultado (0 ou 1)
```

**Interpretação**:
- 0.0-0.15: Excelente calibração
- 0.15-0.25: Boa calibração
- 0.25-0.35: Calibração fraca
- > 0.35: Calibração muito fraca

**Thresholds**:
- Alerta: Brier Score > 0.25
- Crítico: Brier Score > 0.30

**Ação Recomendada**:
- Brier score alto: Probabilidades não calibradas
- Aplicar calibração isotónica ou Platt scaling
- Retreinar modelo com mais dados recentes

### 3.6 AUC-ROC (Area Under Curve - ROC)

**Definição**: Capacidade do modelo de distinguir entre resultados positivos e negativos.

**Fórmula**: Calculado via curva ROC (taxa de verdadeiros positivos vs falsos positivos)

**Interpretação**:
- > 0.70: Excelente
- 0.60-0.70: Bom
- 0.55-0.60: Marginal
- 0.50-0.55: Fraco (pouco melhor que random)
- 0.50: Aleatório

**Thresholds**:
- Alerta: AUC-ROC < 0.55
- Crítico: AUC-ROC < 0.53

**Ação Recomendada**:
- AUC baixo: Modelo não tem poder preditivo
- Investigar features, feature engineering, ou arquitetura do modelo
- Considerar mudança de algoritmo

### 3.7 Calibration Error (ECE)

**Definição**: Expected Calibration Error. Mede a diferença média entre confiança do modelo e accuracy real em bins de probabilidade.

**Fórmula**:
```
ECE = Σ (n_m / N) × |acc(m) - conf(m)|
Onde m = bin de probabilidade, n_m = amostras no bin
```

**Interpretação**:
- < 0.05: Excelente calibração
- 0.05-0.10: Boa calibração
- 0.10-0.15: Calibração fraca
- > 0.15: Calibração muito fraca

**Thresholds**:
- Alerta: ECE > 0.10
- Crítico: ECE > 0.15

**Ação Recomendada**:
- ECE alto: Modelo sobre-confiante ou sub-confiante
- Aplicar calibração (isotónica, Platt)
- Retreinar com balanced dataset

### 3.8 Model Drift

**Definição**: Mudança na distribuição de features ou performance do modelo ao longo do tempo.

**Tipos**:
- **Feature Drift**: Mudança na distribuição de features (KS test, PSI)
- **Performance Drift**: Degradação de métricas de performance (AUC, Brier)
- **Concept Drift**: Mudança na relação entre features e target

**Métricas**:
- `drift_ks_statistic`: Kolmogorov-Smirnov statistic por feature
- `drift_psi`: Population Stability Index por feature
- `drift_features_count`: Número de features com drift detetado

**Interpretação**:
- KS > 0.1 ou PSI > 0.2: Drift detetado
- > 3 features com drift: Drift significativo

**Thresholds**:
- Alerta: 1-2 features com drift
- Crítico: > 3 features com drift

**Ação Recomendada**:
- Investigar causa: mudança de regras NBA, nova temporada, etc.
- Retreinar modelo com dados recentes
- Ajustar features para capturar novo regime

---

## 4. MÉTRICAS OPERACIONAIS

### 4.1 Fill Rate

**Definição**: Percentagem de sinais que foram executados como apostas.

**Fórmula**:
```
Fill Rate = (Apostas Executadas / Sinais Gerados) × 100
```

**Interpretação**:
- > 90%: Excelente execução
- 80-90%: Boa execução
- 70-80%: Execução aceitável
- < 70%: Execução fraca

**Thresholds**:
- Alerta: Fill rate < 80%
- Crítico: Fill rate < 70%

**Ação Recomendada**:
- Investigar causas: odds desapareceram, subscritores não executaram, delays
- Ajustar janela de validade de sinais
- Melhorar comunicação com subscritores

### 4.2 Slippage

**Definição**: Diferença entre a odd recomendada e a odd obtida.

**Fórmula**:
```
Slippage = Odd Recomendada - Odd Obtida
Slippage % = ((Odd Recomendada - Odd Obtida) / Odd Recomendada) × 100
```

**Interpretação**:
- < 2%: Excelente
- 2-5%: Aceitável
- 5-10%: Alto
- > 10%: Muito alto

**Thresholds**:
- Alerta: Slippage médio > 5%
- Crítico: Slippage médio > 10%

**Ação Recomendada**:
- Investigar bookmakers com slippage alto
- Ajustar recomendações (odds conservadoras)
- Treinar subscritores em execução rápida

### 4.3 Execution Latency

**Definição**: Tempo entre geração do sinal e execução da aposta.

**Fórmula**:
```
Latência = Timestamp Execução - Timestamp Sinal
```

**Granularidades**:
- `execution_latency_p50_seconds`: Mediana
- `execution_latency_p95_seconds`: Percentil 95
- `execution_latency_p99_seconds`: Percentil 99

**Interpretação**:
- < 30s: Excelente
- 30-60s: Bom
- 60-120s: Aceitável
- > 120s: Alto

**Thresholds**:
- Alerta: P95 > 120s
- Crítico: P95 > 300s

**Ação Recomendada**:
- Latência alta: Investigar pipeline de notificação
- Melhorar integração Telegram → Subscritor
- Considerar automação de execução

### 4.4 Feed Uptime

**Definição**: Percentagem de tempo que os feeds de dados estão operacionais.

**Fórmula**:
```
Uptime = (Tempo Operacional / Tempo Total) × 100
```

**Feeds Monitorizados**:
- NBA Stats API
- Odds API
- Injuries API
- Line Movements

**Interpretação**:
- > 99.5%: Excelente
- 99.0-99.5%: Bom
- 98.0-99.0%: Aceitável
- < 98.0%: Fraco

**Thresholds**:
- Alerta: Feed offline > 5 min
- Crítico: Feed offline > 10 min
- Crítico: Uptime diário < 99%

**Ação Recomendada**:
- Feed offline: Investigar API, verificar rate limits
- Uptime baixo: Considerar provider alternativo ou caching agressivo

### 4.5 Data Freshness

**Definição**: Idade dos dados mais recentes em relação ao tempo atual.

**Fórmula**:
```
Freshness = Tempo Atual - Timestamp Último Dado
```

**Interpretação**:
- < 1 min: Excelente (real-time)
- 1-5 min: Bom
- 5-15 min: Aceitável
- > 15 min: Fraco

**Thresholds**:
- Alerta: Dados > 5 min
- Crítico: Dados > 15 min

**Ação Recomendada**:
- Freshness alta: Investigar pipeline ETL
- Verificar schedulers e jobs de ingestão
- Considerar caching ou streaming

### 4.6 Signal Generation Rate

**Definição**: Número de sinais gerados por unidade de tempo.

**Fórmula**:
```
Rate = Sinais Gerados / Período
```

**Granularidades**:
- `signals_per_hour`: Sinais por hora
- `signals_per_day`: Sinais por dia

**Interpretação**:
- Depende de estratégia (não há "bom" absoluto)
- Mudanças bruscas indicam problemas

**Thresholds**:
- Alerta: Taxa de sinais cai > 50% vs média 7d
- Alerta: Taxa de sinais sobe > 200% vs média 7d

**Ação Recomendada**:
- Queda: Investigar threshold de edge, dados de entrada
- Aumento: Investigar se modelo a gerar sinais de baixa qualidade

---

## 5. MÉTRICAS DE INFRAESTRUTURA

### 5.1 CPU Usage

**Definição**: Percentagem de CPU utilizada pelo sistema.

**Interpretação**:
- < 50%: Saudável (headroom disponível)
- 50-80%: Aceitável
- 80-90%: Alto (atenção)
- > 90%: Crítico (saturação)

**Thresholds**:
- Alerta: CPU > 80% por 5 min
- Crítico: CPU > 95% por 2 min

**Ação Recomendada**:
- CPU alto: Identificar processo consumidor
- Escalar VPS ou otimizar código
- Verificar se há loops infinitos ou memory leaks

### 5.2 Memory Usage

**Definição**: Percentagem de RAM utilizada.

**Interpretação**:
- < 70%: Saudável
- 70-85%: Aceitável
- 85-95%: Alto
- > 95%: Crítico (risk de OOM)

**Thresholds**:
- Alerta: RAM > 85%
- Crítico: RAM > 95%

**Ação Recomendada**:
- RAM alto: Identificar leak de memória
- Aumentar RAM do VPS
- Otimizar queries ou algoritmos

### 5.3 Disk Usage

**Definição**: Percentagem de espaço em disco utilizado.

**Interpretação**:
- < 70%: Saudável
- 70-85%: Aceitável
- 85-90%: Alto
- > 90%: Crítico (sem espaço para logs/DB)

**Thresholds**:
- Alerta: Disco > 85%
- Crítico: Disco > 90%

**Ação Recomendada**:
- Limpar logs antigos
- Arquivar dados históricos
- Aumentar disco

### 5.4 Database Performance

**Métricas Chave**:
- `pg_connections_active`: Conexões ativas
- `pg_query_time_avg`: Tempo médio de queries
- `pg_cache_hit_ratio`: Cache hit ratio
- `pg_replication_lag`: Lag de replicação

**Thresholds**:
- Alerta: Conexões > 80% de max
- Alerta: Query time avg > 100ms
- Alerta: Cache hit ratio < 95%
- Crítico: Replication lag > 5s

**Ação Recomendada**:
- Otimizar queries lentas (EXPLAIN ANALYZE)
- Adicionar índices
- Aumentar connection pool

---

## 6. LINKS CRUZADOS

- [[10_Monitoring/INDEX]] ← Seção mãe
- [[10_Monitoring/ARQUITETURA_MONITORIZACAO]] → Arquitetura de coleta
- [[20_Dashboarding/INDEX]] → Visualização destas métricas
- [[33_Alerting/INDEX]] → Alertas baseados nestes thresholds