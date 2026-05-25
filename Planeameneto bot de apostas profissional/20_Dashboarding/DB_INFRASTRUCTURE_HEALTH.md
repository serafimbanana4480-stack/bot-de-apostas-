---
ID: DB-006
tags: #status/active #dashboard #infrastructure #health #monitoring
---

# Dashboard de Saúde da Infraestrutura

## Objetivo
Monitorizar, visualizar e alertar sobre o estado de saúde de todos os componentes de infraestrutura que suportam o sistema de value betting NBA: servidores (VPS/bare metal/cloud), containers, bases de dados, caches, filas de processamento, armazenamento, rede, e dependências externas (APIs, CDNs, gateways de pagamento). O dashboard deve ser a fonte de verdade para a equipa de DevOps e infraestrutura.

## O que faz
- Apresenta métricas de hardware: CPU utilization (média e pico), RAM usage, disk I/O, disk space, network throughput, e load average.
- Monitoriza serviços de aplicação: PostgreSQL (connections, slow queries, replication lag, vacuum status), Redis (memory usage, hit rate, evicted keys, cluster health), Celery/RQ (queue depth, worker status, task failure rate).
- Rastreia dependências externas: latência e disponibilidade de feeds NBA, odds, injuries, Stripe, Telegram API, e serviços de e-mail.
- Visualiza tendências de 24h, 7d, e 30d para identificar padrões de degradação (ex: crescimento gradual de disco que antecede falha).
- Inclui mapa de dependências: qual serviço depende de qual, e qual o impacto de falha de cada nó.

## Porque existe
- **Prevenção de Falhas**: A maioria das falhas de infraestrutura não são súbitas; são precedidas por sinais de aviso (disco a encher, RAM a subir, queries a ficar lentas). O dashboard permite intervenção preventiva.
- **Custo**: Monitorização de recursos permite identificar over-provisioning (ex: VPS com CPU a 5% constante) e under-provisioning (ex: fila de tasks a crescer).
- **Troubleshooting**: Quando um serviço falha, o dashboard histórico permite correlacionar com eventos de infraestrutura (ex: "o feed de odds falhou exatamente quando o PostgreSQL atingiu 100% de CPU").
- **Capacity Planning**: Tendências de crescimento informam decisões de scaling — [[23_Scaling/EIXO_INFRA]].

## Implementação / Pseudocódigo
```python
class DashboardInfrastructureHealth:
    def __init__(self):
        self.componentes = {
            "vps_principal": {
                "tipo": "SERVIDOR",
                "metricas": ["cpu_percent", "ram_percent", "disk_percent", "load_1m", "network_in", "network_out"],
                "thresholds": {
                    "cpu_percent": {"alerta": 80, "critico": 95},
                    "ram_percent": {"alerta": 80, "critico": 95},
                    "disk_percent": {"alerta": 80, "critico": 90},
                    "load_1m": {"alerta": 4.0, "critico": 8.0}  # relativo a n_cores
                }
            },
            "postgresql": {
                "tipo": "BD",
                "metricas": ["connections_active", "connections_idle", "replication_lag_ms", "slow_queries_1m", "deadlocks", "cache_hit_ratio"],
                "thresholds": {
                    "connections_active": {"alerta": 80, "critico": 95},  # % de max_connections
                    "replication_lag_ms": {"alerta": 1000, "critico": 5000},
                    "slow_queries_1m": {"alerta": 10, "critico": 50},
                    "cache_hit_ratio": {"alerta": 0.95, "critico": 0.90}  # abaixo destes valores
                }
            },
            "redis": {
                "tipo": "CACHE",
                "metricas": ["memory_used_percent", "hit_rate", "evicted_keys_1m", "connected_clients", "rejected_connections"],
                "thresholds": {
                    "memory_used_percent": {"alerta": 80, "critico": 95},
                    "hit_rate": {"alerta": 0.85, "critico": 0.70},
                    "rejected_connections": {"alerta": 1, "critico": 10}
                }
            },
            "celery": {
                "tipo": "FILA",
                "metricas": ["queue_depth", "workers_active", "workers_idle", "task_failure_rate_1h", "task_latency_avg_ms"],
                "thresholds": {
                    "queue_depth": {"alerta": 1000, "critico": 5000},
                    "task_failure_rate_1h": {"alerta": 0.05, "critico": 0.10},
                    "task_latency_avg_ms": {"alerta": 5000, "critico": 30000}
                }
            },
            "feeds_externos": {
                "tipo": "DEPENDENCIA",
                "servicos": ["nba_stats", "odds_api", "injuries_api", "stripe", "telegram_api", "sendgrid"],
                "metricas": ["latencia_ms", "uptime_24h", "taxa_erro", "ultimo_sucesso"]
            }
        }
        self.frequencia_coleta_seg = 15

    def coletar_metricas(self):
        snapshot = {"timestamp": datetime.utcnow().isoformat(), "componentes": {}}
        
        for nome, config in self.componentes.items():
            if config["tipo"] == "SERVIDOR":
                snapshot["componentes"][nome] = self.coletar_metricas_servidor(nome)
            elif config["tipo"] == "BD":
                snapshot["componentes"][nome] = self.coletar_metricas_bd(nome)
            elif config["tipo"] == "CACHE":
                snapshot["componentes"][nome] = self.coletar_metricas_cache(nome)
            elif config["tipo"] == "FILA":
                snapshot["componentes"][nome] = self.coletar_metricas_fila(nome)
            elif config["tipo"] == "DEPENDENCIA":
                snapshot["componentes"][nome] = self.coletar_metricas_dependencias(config["servicos"])
        
        self.db.inserir("infra_snapshots", snapshot)
        return snapshot

    def coletar_metricas_servidor(self, nome):
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_1m": os.getloadavg()[0],
            "network_in": psutil.net_io_counters().bytes_recv,
            "network_out": psutil.net_io_counters().bytes_sent
        }

    def coletar_metricas_bd(self, nome):
        conn = self.db.get_raw_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        active = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'")
        idle = cursor.fetchone()[0]
        
        cursor.execute("SELECT extract(epoch from (now() - pg_last_xact_replay_timestamp()))")
        replication_lag = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT sum(seq_tup_read) / (sum(seq_tup_read) + sum(idx_tup_fetch)) FROM pg_stat_user_tables")
        cache_hit = cursor.fetchone()[0] or 0
        
        return {
            "connections_active": active,
            "connections_idle": idle,
            "replication_lag_ms": replication_lag * 1000,
            "slow_queries_1m": self.contar_slow_queries(),
            "deadlocks": self.contar_deadlocks(),
            "cache_hit_ratio": cache_hit
        }

    def avaliar_saude(self, snapshot):
        alertas = []
        for nome, metricas in snapshot["componentes"].items():
            config = self.componentes[nome]
            if "thresholds" not in config:
                continue
            for metrica, valor in metricas.items():
                if metrica in config["thresholds"]:
                    th = config["thresholds"][metrica]
                    if "critico" in th and self.acima_limite(valor, th["critico"], metrica):
                        alertas.append({"componente": nome, "metrica": metrica, "valor": valor, "nivel": "CRITICO", "threshold": th["critico"]})
                    elif "alerta" in th and self.acima_limite(valor, th["alerta"], metrica):
                        alertas.append({"componente": nome, "metrica": metrica, "valor": valor, "nivel": "ALERTA", "threshold": th["alerta"]})
        return alertas

    def acima_limite(self, valor, limite, metrica):
        # Para cache_hit_rate, abaixo do limite é mau
        if "ratio" in metrica or "hit_rate" in metrica:
            return valor < limite
        return valor > limite

    def gerar_dashboard(self):
        snapshot = self.coletar_metricas()
        alertas = self.avaliar_saude(snapshot)
        return {
            "timestamp": snapshot["timestamp"],
            "componentes": snapshot["componentes"],
            "alertas_ativos": alertas,
            "tendencias_24h": self.obter_tendencias(horas=24),
            "tendencias_7d": self.obter_tendencias(dias=7),
            "mapa_dependencias": self.gerar_mapa_dependencias()
        }
```

## Thresholds e Tabelas

| Componente | Métrica | Alerta | Crítico | Unidade | Frequência |
|-----------|---------|--------|---------|---------|------------|
| VPS Principal | CPU % | > 80% | > 95% | % | 15s |
| VPS Principal | RAM % | > 80% | > 95% | % | 15s |
| VPS Principal | Disk % | > 80% | > 90% | % | 60s |
| VPS Principal | Load 1m | > 4x cores | > 8x cores | ratio | 15s |
| PostgreSQL | Connections Active | > 80% max | > 95% max | % | 15s |
| PostgreSQL | Replication Lag | > 1000ms | > 5000ms | ms | 15s |
| PostgreSQL | Slow Queries | > 10/min | > 50/min | count | 60s |
| PostgreSQL | Cache Hit Ratio | < 95% | < 90% | ratio | 60s |
| Redis | Memory Used | > 80% | > 95% | % | 15s |
| Redis | Hit Rate | < 85% | < 70% | ratio | 60s |
| Redis | Rejected Conn. | > 1/min | > 10/min | count | 60s |
| Celery | Queue Depth | > 1000 | > 5000 | count | 15s |
| Celery | Task Failure Rate | > 5% | > 10% | % | 60s |
| Celery | Task Latency Avg | > 5000ms | > 30000ms | ms | 60s |

| Dependência Externa | Latência Alerta | Latência Crítico | Uptime Mínimo | Taxa Erro Máx |
|--------------------|----------------|------------------|---------------|---------------|
| NBA Stats API | > 5s | > 10s | 99% | 1% |
| Odds API | > 3s | > 5s | 99.5% | 0.5% |
| Injuries API | > 10s | > 30s | 98% | 2% |
| Stripe API | > 2s | > 5s | 99.9% | 0.1% |
| Telegram API | > 5s | > 10s | 99% | 1% |
| SendGrid / SES | > 3s | > 10s | 99% | 1% |

---

## Layout e Visualizações

### Linha 1: Recursos do VPS (Top Row)
**Layout**: 4 painéis de time series

1. **CPU Usage (Time Series)**
   - Visual: Gráfico de linha com múltiplas séries
   - Séries: CPU total (sólida), CPU por core (tracejadas)
   - Eixo Y: 0-100%
   - Linhas de threshold: 80% (amarelo), 95% (vermelho)
   - Área sombreada acima de 80%
   - Tooltip: Valor atual, média 5m, pico 1h
   - Cor: Verde (<50%), Amarelo (50-80%), Vermelho (>80%)

2. **Memory Usage (Time Series)**
   - Visual: Gráfico de linha com stacked area
   - Séries: RAM total, Swap
   - Eixo Y: 0-100%
   - Linhas de threshold: 85% (amarelo), 95% (vermelho)
   - Indicador: "Swap em uso: Sim/Não"
   - Tooltip: RAM usada, RAM disponível, Swap usado

3. **Disk Usage (Gauge + Time Series)**
   - Visual: Gauge radial (0-100%) + mini time series
   - Gauge: Percentagem atual com cores
   - Time series: Tendência de crescimento (últimos 7 dias)
   - Projeção: Linha tracejada estimando quando atingirá 90%
   - Tooltip: GB usados, GB livres, dias até 90%

4. **Load Average (Time Series)**
   - Visual: Gráfico de linha com 3 séries
   - Séries: Load 1m, Load 5m, Load 15m
   - Linha de referência: Número de cores (ex: 4 cores = linha a 4.0)
   - Tooltip: Load atual, cores disponíveis, ratio load/cores

### Linha 2: Banco de Dados (Middle Row 1)
**Layout**: 4 painéis

5. **PostgreSQL Connections (Gauge)**
   - Visual: Gauge linear (0-max_connections)
   - Valor: Conexões ativas / total
   - Séries: Ativas (verde), Idle (cinza)
   - Threshold: 80% de max (amarelo), 95% (vermelho)
   - Tooltip: Ativas, Idle, Total, Max configurado

6. **PostgreSQL Query Time (Time Series)**
   - Visual: Gráfico de linha
   - Séries: Tempo médio (sólida), P95 (tracejada), P99 (ponto)
   - Eixo Y: 0-500ms
   - Threshold: 100ms (amarelo), 200ms (vermelho)
   - Tooltip: Média, P50, P95, P99

7. **PostgreSQL Cache Hit Ratio (Gauge)**
   - Visual: Gauge radial (0.90-1.0 zoom)
   - Valor: Cache hit ratio
   - Cor: Verde (>0.98), Amarelo (0.95-0.98), Vermelho (<0.95)
   - Tooltip: Hit ratio, misses, total reads

8. **PostgreSQL Replication Lag (Time Series)**
   - Visual: Gráfico de linha
   - Eixo Y: 0-10s
   - Threshold: 1s (amarelo), 5s (vermelho)
   - Indicador: "Replicação: Ativa/Inativa"
   - Tooltip: Lag atual, lag máximo 1h

### Linha 3: Cache e Filas (Middle Row 2)
**Layout**: 4 painéis

9. **Redis Memory Usage (Gauge + Time Series)**
   - Visual: Gauge radial + time series
   - Gauge: Percentagem de maxmemory
   - Time series: Tendência de uso (últimas 24h)
   - Threshold: 80% (amarelo), 95% (vermelho)
   - Tooltip: MB usados, MB livres, fragmentation ratio

10. **Redis Hit Rate (Gauge)**
    - Visual: Gauge radial (0.70-1.0 zoom)
    - Valor: Cache hit ratio
    - Cor: Verde (>0.90), Amarelo (0.85-0.90), Vermelho (<0.85)
    - Tooltip: Hits, Misses, Ratio

11. **Celery Queue Depth (Gauge)**
    - Visual: Gauge vertical (0-10000)
    - Valor: Número de tasks na fila
    - Threshold: 1000 (amarelo), 5000 (vermelho)
    - Tooltip: Tasks pendentes, workers ativos, tasks/hora processadas

12. **Celery Task Failure Rate (Time Series)**
    - Visual: Gráfico de linha
    - Eixo Y: 0-20%
    - Threshold: 5% (amarelo), 10% (vermelho)
    - Tooltip: Taxa falha 1h, total falhas, total tasks

### Linha 4: Dependências Externas (Bottom Row)
**Layout**: Tabela de status + painéis auxiliares

13. **External Dependencies Status (Table)**
    - Colunas: Serviço, Status, Latência, Uptime 24h, Último Sucesso, Erros 1h
    - Linhas: NBA Stats API, Odds API, Injuries API, Stripe, Telegram, Sendgrid
    - Cores de status: Verde (OK), Amarelo (Degraded), Vermelho (DOWN)
    - Ordenação: Por status (DOWN primeiro)
    - Ação: Clicar para ver histórico de latência

14. **Network I/O (Time Series)**
    - Visual: Gráfico de linha com 2 séries
    - Séries: Receive (azul), Transmit (verde)
    - Eixo Y: Mbps
    - Tooltip: Rx atual, Tx atual, peak 1h

15. **Container Health (Table)**
    - Colunas: Container, Status, CPU%, RAM%, Restarts, Uptime
    - Linhas: FastAPI, Model API, Prefect, Telegram Bot, Prometheus, Grafana
    - Cores: Verde (running), Amarelo (restarting), Vermelho (stopped)
    - Ação: Clicar para ver logs

16. **System Uptime (Single Stat)**
    - Visual: Número grande com unidade
    - Valor: Uptime do VPS
    - Subtítulo: "Último reboot: DD/MM/YYYY HH:MM"
    - Cor: Verde (>99.9%), Amarelo (99.0-99.9%), Vermelho (<99.0%)

---

## Detalhes de Visualização

### Cores por Componente

**PostgreSQL**
- Cor primária: #336791 (azul PostgreSQL)
- Alerta: #F59E0B (amarelo)
- Crítico: #EF4444 (vermelho)

**Redis**
- Cor primária: #DC382D (vermelho Redis)
- Alerta: #F59E0B
- Crítico: #EF4444

**Celery**
- Cor primária: #38B2AC (turquesa)
- Alerta: #F59E0B
- Crítico: #EF4444

**APIs Externas**
- Cor primária: #8B5CF6 (roxo)
- Status OK: #10B981 (verde)
- Status Degraded: #F59E0B
- Status DOWN: #EF4444

### Anotações Automáticas

**Eventos de Sistema**
- "Deployment v1.2" - Marcador no timestamp do deployment
- "Database backup started" - Início de backup
- "VPS reboot" - Reinício do servidor
- "Config change" - Mudança de configuração

**Eventos de Aplicação**
- "Model retraining started" - Início de retreino
- "Circuit breaker activated" - Ativação de CB
- "Feed outage detected" - Detecção de outage

### Alertas Visuais

**Flash Animation**
- Painéis vermelhos piscam por 10 segundos quando threshold crítico é atingido
- Painéis amarelos têm borda amarela sólida quando threshold de alerta é atingido

**Sound Notifications** (opcional)
- Beep suave para alertas amarelos
- Beep repetitivo para alertas críticos
- Configurável por utilizador

## Riscos
- **Risco de Monitorização Excessiva**: Coletar métricas a cada 1 segundo em 50 componentes gera dados massivos que podem afetar a própria performance. Balancear granularidade com custo.
- **Risco de Falso Positivo**: Um pico de CPU a 100% por 10 segundos durante um deploy não é crítico. Alertas devem ter dampening (ex: CPU > 90% por mais de 5 minutos).
- **Risco de Cegueira em Cascata**: Se o PostgreSQL cair, o dashboard pode ficar cego porque os dados são armazenados no PostgreSQL. Necessário buffer local (ficheiro ou Redis) antes de persistir.
- **Risco de Dependência Circular**: O dashboard depende do Redis; se o Redis cair, o dashboard não mostra o estado do Redis. Health checks devem ser independentes.

## Checklist do Dashboard de Infraestrutura
- [ ] Todas as métricas coletadas automaticamente com frequência adequada; nenhuma coleta manual.
- [ ] Retenção de dados: métricas detalhadas por 30 dias; agregações horárias por 1 ano; agregações diárias por 3 anos.
- [ ] Mapa de dependências atualizado: se o feed de odds falha, o dashboard mostra que o pipeline de sinais está impactado.
- [ ] Alertas com dampening: nenhum alerta por picos < 5 minutos (salvo P1 explícito).
- [ ] Dashboard redundante: instância standby em servidor diferente; failover automático em 60 segundos.
- [ ] Acesso restrito a DevOps e gestor de operações; nenhum acesso de subscritores ou público.
- [ ] Capacidade de drill-down: clicar em "PostgreSQL connections" mostra lista de queries ativas e seus tempos.
- [ ] Revisão semanal de tendências: crescimento de disco, padrões de RAM, e eficiência de queries.

## Links Cruzados
- [[20_Dashboarding/DB_OPERATIONS_CENTER]] - NOC que integra dados de infraestrutura.
- [[13_Infrastructure]] - Pasta de infraestrutura com detalhes arquiteturais.
- [[12_DevOps]] - Pasta de DevOps com CI/CD e automação.
- [[34_Security/VPS_HARDENING]] - Segurança do servidor monitorizado.
- [[23_Scaling/EIXO_INFRA]] - Decisões de scaling baseadas em tendências.
