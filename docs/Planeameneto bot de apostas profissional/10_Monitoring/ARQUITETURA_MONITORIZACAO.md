# Arquitetura de Monitorização

**ID:** `MON-100` | **Fase:** #phase/1 | **Owner:** MLOps Engineer | **Status:** #status/draft

---

## 1. VISÃO GERAL

A arquitetura de monitorização do sistema de value betting NBA é baseada numa abordagem de **observabilidade completa**, combinando três pilares fundamentais: **métricas**, **logs** e **tracing**. Esta arquitetura permite à equipa de operações detetar, diagnosticar e resolver problemas antes que afetem a performance financeira ou a experiência dos subscritores.

### Pilares de Observabilidade

1. **Métricas (Prometheus)**: Dados numéricos time-series que quantificam o comportamento do sistema ao longo do tempo. Métricas são agregadas, eficientes de armazenar e ideais para alertas.
2. **Logs (Loki/JSON)**: Registros estruturados de eventos discretos com contexto rico (correlation IDs, timestamps, user IDs). Logs são essenciais para debugging e audit trail.
3. **Tracing (OpenTelemetry)**: Rastreamento de requests através de múltiplos serviços, permitindo identificar gargalos de latência e dependências entre componentes.

---

## 2. ARQUITETURA DE COLETA DE MÉTRICAS

### 2.1 Camada de Instrumentação

A coleta de métricas começa no código da aplicação através de instrumentação. Cada serviço expõe métricas num endpoint `/metrics` no formato Prometheus:

```
Serviço                    Endpoint /metrics       Porta
─────────────────────────────────────────────────────────
FastAPI (API Principal)   /metrics                 8000
Model API (Inferência)    /metrics                 8001
Data Pipeline (Prefect)   /metrics                 8002
Telegram Bot              /metrics                 8003
Node Exporter (VPS)       /metrics                 9100
PostgreSQL Exporter       /metrics                 9187
Redis Exporter            /metrics                 9121
```

### 2.2 Tipos de Métricas Prometheus

**Counter**: Métrica que só aumenta (monotonicamente). Usada para contagem de eventos.

Exemplos:
- `fastapi_requests_total`: Total de requests recebidos
- `bets_placed_total`: Total de apostas executadas
- `model_predictions_total`: Total de inferências realizadas

**Gauge**: Métrica que pode subir ou descer. Usada para valores atuais.

Exemplos:
- `fastapi_requests_in_flight`: Requests atualmente em processamento
- `vps_cpu_usage_percent`: Percentagem de CPU atual
- `queue_depth`: Número de itens na fila Redis

**Histogram**: Métrica que conta observações em buckets configuráveis. Usada para distribuições como latência.

Exemplos:
- `fastapi_request_duration_seconds_bucket`: Distribuição de latência de requests
- `stake_distribution_eur_bucket`: Distribuição de valores de stake
- `slippage_points_bucket`: Distribuição de slippage

**Summary**: Similar ao histogram mas calcula quantis no lado do cliente. Menos eficiente que histogram para sistemas de alta escala.

### 2.3 Pipeline de Coleta

```
┌─────────────┐     Scrape (15s)      ┌─────────────┐
│  Aplicação  │ ───────────────────>  │ Prometheus  │
│  /metrics   │                        │  (TSDB)     │
└─────────────┘                        └──────┬──────┘
                                              │
                                              │ Query (PromQL)
                                              ↓
┌─────────────┐     Alert Evaluation   ┌─────────────┐
│  Grafana    │ <────────────────────  │ Alertmanager│
│  Dashboards │                        │  Routing    │
└─────────────┘                        └──────┬──────┘
                                              │
                                              │ Notifications
                                              ↓
                                      ┌──────────────┐
                                      │   Telegram   │
                                      │     Email    │
                                      └──────────────┘
```

**Frequência de Scrape**: 15 segundos para infraestrutura, 30 segundos para aplicações, 60 segundos para métricas de negócio (menos voláteis).

**Retenção de Dados**: 15 dias de resolução alta (raw), 90 dias de resolução reduzida (5m), 1 ano de resolução baixa (1h).

---

## 3. MÉTRICAS DE SISTEMA VS MÉTRICAS DE NEGÓCIO

### 3.1 Métricas de Sistema (Infraestrutura)

Métricas que monitorizam a saúde técnica dos componentes. São **leading indicators** — problemas aqui causam problemas no negócio.

**CPU (Processamento)**
- `cpu_usage_percent`: Percentagem de CPU utilizada
- `cpu_load_1m/5m/15m`: Load average do sistema
- `cpu_iowait`: Tempo de CPU à espera de I/O (indica bottleneck de disco)

**Memória**
- `memory_usage_percent`: Percentagem de RAM utilizada
- `memory_available_bytes`: RAM disponível
- `memory_swap_usage_percent`: Uso de swap (indica pressão de memória)

**Disco**
- `disk_usage_percent`: Percentagem de espaço em disco utilizado
- `disk_io_read_bytes_sec`: Taxa de leitura de disco
- `disk_io_write_bytes_sec`: Taxa de escrita de disco
- `disk_io_time_sec`: Tempo de I/O (indica saturação)

**Rede**
- `network_receive_bytes_sec`: Taxa de receção de rede
- `network_transmit_bytes_sec`: Taxa de transmissão de rede
- `network_errors_total`: Erros de rede

**PostgreSQL**
- `pg_stat_activity_count`: Número de conexões ativas
- `pg_stat_database_blks_hit`: Cache hit ratio (eficiência de cache)
- `pg_stat_statements_mean_time`: Tempo médio de queries
- `pg_replication_lag_seconds`: Lag de replicação (se aplicável)

**Redis**
- `redis_memory_used_bytes`: Memória utilizada
- `redis_memory_fragmentation_ratio`: Fragmentação de memória
- `redis_keyspace_hits_total`: Cache hits
- `redis_keyspace_misses_total`: Cache misses
- `redis_connected_clients`: Clientes conectados

### 3.2 Métricas de Negócio (Financeiro/Operacional)

Métricas que quantificam a performance financeira e operacional do sistema. São **lagging indicators** — refletem o resultado das decisões e execuções.

**Performance Financeira**
- `pnl_daily_eur`: Lucro/prejuízo diário
- `pnl_monthly_eur`: Lucro/prejuízo mensal
- `roi_percent`: Return on Investment (PnL / Stake)
- `yield_percent`: Yield (PnL / Turnover)
- `drawdown_current_percent`: Drawdown atual
- `sharpe_ratio`: Retorno ajustado ao risco
- `bankroll_available_eur`: Bankroll disponível

**Performance do Modelo**
- `clv_mean_percent`: CLV (Closing Line Value) médio
- `clv_realized_percent`: CLV realizado (odd obtida vs odd fechada)
- `win_rate_percent`: Taxa de acerto
- `edge_mean_percent`: Edge médio das apostas
- `brier_score`: Calibração de probabilidades
- `auc_roc`: Área sob a curva ROC
- `model_drift_score`: Score de drift do modelo

**Operacional**
- `signals_generated_total`: Total de sinais gerados
- `signals_executed_total`: Total de sinais executados
- `fill_rate_percent`: Percentagem de sinais executados
- `slippage_mean_points`: Slippage médio
- `execution_latency_seconds`: Latência de execução (sinal → aposta)
- `feed_uptime_percent`: Uptime dos feeds de dados
- `telegram_delivery_success_rate`: Taxa de entrega Telegram

**Qualidade de Dados**
- `data_freshness_minutes`: Idade dos dados mais recentes
- `missing_games_count`: Jogos em falta vs esperados
- `null_features_percent`: Percentagem de features nulas
- `schema_violations_total`: Violações de schema
- `duplicate_records_total`: Registros duplicados

### 3.3 Diferenças Chave

| Característica | Métricas de Sistema | Métricas de Negócio |
|---------------|--------------------|---------------------|
| **Objetivo** | Saúde técnica | Performance financeira |
| **Volatilidade** | Alta (segundos) | Baixa (dias/semanas) |
| **Ação Típica** | Escalar, reiniciar, debug | Ajustar stakes, pausar mercado |
| **Proprietário** | DevOps | Operations / Risk Manager |
| **Alertas** | Imediatos (minutos) | Diários/semanais |
| **Retenção** | Curta (dias) | Longa (anos) |

---

## 4. ESTRATÉGIA DE COLETA DE DADOS

### 4.1 Push vs Pull

**Prometheus usa Pull**: O servidor Prometheus faz scrape dos endpoints `/metrics` periodicamente. Isto tem vantagens:

- **Simplicidade**: Não há necessidade de configurar autenticação complexa em cada serviço
- **Descoberta de Serviços**: Prometheus pode descobrir automaticamente novos serviços via DNS ou Kubernetes service discovery
- **Fiabilidade**: Se o serviço cair, o scrape falha e Prometheus deteta a falha
- **Performance**: O serviço não precisa de manter buffers de métricas para push

**Pull é preferido para**: Infraestrutura, APIs internas, serviços stateless

**Push pode ser necessário para**: Jobs batch, serviços que não podem ser expostos (firewall), métricas de negócio que requerem agregação complexa

### 4.2 Cardinalidade e Labeling

**Labels** são pares chave-valor que permitem filtrar e agregar métricas. Exemplo:

```
fastapi_requests_total{endpoint="/predict", method="POST", status="200"}
```

**Regra de Ouro**: Evitar cardinalidade alta. Labels com muitos valores únicos (ex: `user_id`, `bet_id`) causam explosão de séries temporais.

**Boas Práticas de Labeling**:
- Usar labels de baixa cardinalidade: `endpoint`, `method`, `status`, `market`, `bookmaker`
- Evitar labels de alta cardinalidade: `user_id`, `bet_id`, `timestamp` (use isso no nome da métrica)
- Limitar a 10-15 labels por métrica
- Usar labels consistentes em todas as métricas (ex: sempre `market`, nunca `market_name`)

### 4.3 Agregação e Downsampling

Métricas são coletadas em alta resolução (15s) mas agregadas para reduzir custos de armazenamento:

```
Resolução Original (15s) ──→ 15 dias
         ↓
Resolução Reduzida (5m) ──→ 90 dias
         ↓
Resolução Baixa (1h) ────→ 1 ano
```

**Funções de Agregação**:
- `rate()`: Taxa de mudança por segundo (para counters)
- `avg()`: Média (para gauges)
- `sum()`: Soma (para contagens)
- `max()`/`min()`: Valores extremos

### 4.4 Exemplo: Métrica CLV

**Definição**: CLV = (Odd Fechada / Odd Obtida) - 1

**Instrumentação**:
```python
from prometheus_client import Histogram, Gauge

# Histogram para distribuição de CLV
clv_histogram = Histogram(
    'clv_distribution_percent',
    'Distribuição de CLV das apostas',
    buckets=[-0.05, -0.03, -0.01, 0, 0.01, 0.03, 0.05, 0.07, 0.10]
)

# Gauge para CLV médio rolling
clv_mean_gauge = Gauge(
    'clv_mean_rolling_percent',
    'CLV médio (últimas 50 apostas)'
)

clv_histogram.observe(clv_value)
clv_mean_gauge.set(clv_mean_rolling)
```

**Labels Recomendadas**:
- `market`: spread, total, moneyline
- `bookmaker`: bet365, betway, william_hill
- `regime`: home, away, favorite, underdog

**Labels a Evitar**:
- `game_id`: Cardinalidade muito alta (milhares de jogos)
- `bet_id`: Cardinalidade extrema (milhões de apostas)

---

## 5. INTEGRAÇÃO COM GRAFANA

### 5.1 Data Sources

Grafana suporta múltiplas fontes de dados. Para este sistema:

| Fonte de Dados | Uso | Configuração |
|----------------|-----|--------------|
| Prometheus | Métricas de sistema e negócio | URL: http://localhost:9090 |
| PostgreSQL | Queries de negócio complexas | Host: localhost, DB: nba_betting |
| Loki | Logs estruturados (opcional) | URL: http://localhost:3100 |

### 5.2 Variáveis de Dashboard

Variáveis permitem dashboards dinâmicos que podem ser filtrados:

```
$market: spread, total, moneyline, player_props
$bookmaker: bet365, betway, william_hill, unibet
$time_range: 1h, 6h, 24h, 7d, 30d, 90d
$model_version: v1.0, v1.1, v1.2, current
```

### 5.3 Refresh Rates

- **Dashboards de Infraestrutura**: 15-30 segundos (tempo real)
- **Dashboards de Operações**: 1-5 minutos (quase real-time)
- **Dashboards de Negócio**: 15-60 minutos (não crítico)
- **Dashboards Executivos**: 1-4 horas (tendência)

---

## 6. RISCOS E MITIGAÇÃO

### 6.1 Risco: Explosão de Cardinalidade

**Problema**: Labels com muitos valores únicos causam consumo excessivo de memória e CPU no Prometheus.

**Mitigação**:
- Revisar todas as métricas antes de produção
- Limitar cardinalidade a < 100.000 séries por servidor
- Usar relabeling para remover labels desnecessários
- Monitorizar `prometheus_tsdb_series_count`

### 6.2 Risco: Latência de Alertas

**Problema**: Alertas críticos podem demorar minutos a ser processados se o Prometheus estiver sobrecarregado.

**Mitigação**:
- Separar Prometheus de alertas (Alertmanager) de Prometheus de retenção longa
- Usar regras de alerta otimizadas (evitar queries complexas)
- Configurar `evaluation_interval` apropriado (15s para críticos, 1m para normais)

### 6.3 Risco: Perda de Dados

**Problema**: Se o Prometheus cair, dados de scrape são perdidos permanentemente.

**Mitigação**:
- Configurar backup regular do TSDB
- Usar Prometheus HA (dois instâncias com configuração idêntica)
- Para dados críticos de negócio, armazenar em PostgreSQL como fonte de verdade

### 6.4 Risco: Alert Fatigue

**Problema**: Demasiados alertas causam desensibilização e alertas críticos são ignorados.

**Mitigação**:
- Thresholds conservadores (evitar falsos positivos)
- Agrupamento de alertas correlacionados
- Silêncio programado para janelas de manutenção
- Revisão trimestral de regras de alerta

---

## 7. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Instalar Prometheus via Docker Compose
- [ ] Configurar Node Exporter no VPS
- [ ] Configurar PostgreSQL Exporter
- [ ] Configurar Redis Exporter
- [ ] Instrumentar FastAPI com prometheus_client
- [ ] Criar endpoint `/metrics` em todos os serviços
- [ ] Configurar scrape targets no Prometheus
- [ ] Definir labels padrão para todas as métricas
- [ ] Implementar cardinalidade limits
- [ ] Configurar retenção de dados
- [ ] Instalar Grafana e configurar datasource Prometheus
- [ ] Criar dashboards base de infraestrutura
- [ ] Implementar métricas de negócio (CLV, PnL, ROI)
- [ ] Testar pipeline end-to-end
- [ ] Documentar todas as métricas em catálogo interno

---

## 8. LINKS CRUZADOS

- [[10_Monitoring/INDEX]] ← Seção mãe
- [[20_Dashboarding/INDEX]] → Visualização de métricas
- [[33_Alerting/INDEX]] → Alertas baseados em métricas
- [[13_Infrastructure/INDEX]] → Infraestrutura que suporta monitorização