# PERFORMANCE_TUNING — Otimização de Performance PostgreSQL

**ID:** `DB-002` | **Fase:** #phase/2 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias de otimização de performance para PostgreSQL 15, incluindo índices, partitioning, query optimization, e configurações de tuning para garantir performance adequada para workload analítico e transacional.

---

## 2. ARQUITETURA DE PERFORMANCE

### 2.1 Workload Analysis

**Tipos de Queries:**

| Tipo | Frequência | Latência Alvo | Tabela Principal |
|------|------------|---------------|------------------|
| Ingestão (INSERT) | Alto (batch) | < 1s | bronze.* |
| Feature Engineering | Médio (diário) | < 5min | gold.* |
| Treino de Modelo | Baixo (semanal) | < 10min | gold.* |
| API Reads | Alto (real-time) | < 100ms | silver.*, gold.* |
| Reporting | Médio (diário) | < 30s | Todas |

### 2.2 SLAs de Performance

| Operação | SLA | Métrica |
|----------|-----|---------|
| Ingestão de dados | < 1000 jogos/min | Throughput |
| Query de features | < 100ms | Latência P95 |
| Treino de modelo | < 10min | Tempo total |
| Backup diário | < 30min | Tempo total |
| Recovery | < 1h | RTO |

---

## 3. ÍNDICES

### 3.1 Estratégia de Indexação

**Princípios:**
- Índices em colunas frequentemente usadas em WHERE, JOIN, ORDER BY
- Índices compostos para queries multi-coluna
- Índices parciais para filtros específicos
- Evitar over-indexing (custo em INSERT/UPDATE)

### 3.2 Índices B-Tree (Padrão)

```sql
-- Índice simples
CREATE INDEX idx_clean_games_date 
ON silver.clean_games(game_date);

-- Índice composto (ordem importa!)
CREATE INDEX idx_clean_odds_game_market 
ON silver.clean_odds(game_id, market, bookmaker);

-- Índice com ordenação descendente
CREATE INDEX idx_bets_executed_desc 
ON gold.bets(executed_at DESC);

-- Índice com expressão
CREATE INDEX idx_games_year 
ON silver.clean_games(EXTRACT(YEAR FROM game_date));
```

### 3.3 Índices Parciais (Partial Indexes)

```sql
-- Apenas jogos finalizados (reduz tamanho do índice)
CREATE INDEX idx_clean_games_finalized 
ON silver.clean_games(game_date, season)
WHERE status = 'Final';

-- Apenas sinais não executados
CREATE INDEX idx_signals_pending 
ON gold.signals(created_at)
WHERE is_executed = FALSE;

-- Apenas apostas reais (não shadow/paper)
CREATE INDEX idx_bets_real 
ON gold.bets(executed_at, outcome)
WHERE bet_type = 'real';
```

### 3.4 Índices BRIN para Dados de Séries Temporais

```sql
-- BRIN é eficiente para dados ordenados por tempo
CREATE INDEX idx_raw_odds_timestamp_brin 
ON bronze.raw_odds_betfair USING BRIN(timestamp);

CREATE INDEX idx_api_access_timestamp_brin 
ON audit.api_access_log USING BRIN(timestamp);
```

### 3.5 Índices GIN para JSONB

```sql
-- Para busca em campos JSONB
CREATE INDEX idx_raw_nba_games_json 
ON bronze.raw_nba_games USING GIN(raw_json);

-- Índice GIN com jsonb_path_ops (mais eficiente para operações @>)
CREATE INDEX idx_raw_nba_games_json_path 
ON bronze.raw_nba_games USING GIN(raw_json jsonb_path_ops);
```

### 3.6 Índices Hash para Igualdade Exata

```sql
-- Para queries de igualdade (mais compacto que B-Tree)
CREATE INDEX idx_teams_abbr_hash 
ON silver.teams USING HASH(team_abbr);
```

### 3.7 Manutenção de Índices

```sql
-- Analisar uso de índices
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Identificar índices não utilizados
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Reindexar índices fragmentados
REINDEX INDEX CONCURRENTLY idx_clean_games_date;

-- REINDEX TABLE (todos os índices)
REINDEX TABLE CONCURRENTLY silver.clean_games;
```

---

## 4. PARTITIONING

### 4.1 Estratégia de Partitioning

**Tabelas Candidatas a Partitioning:**
- `silver.clean_games` (por mês/ano)
- `silver.clean_odds` (por mês)
- `bronze.raw_odds_betfair` (por dia)
- `audit.api_access_log` (por mês)

### 4.2 Range Partitioning por Data

```sql
-- Tabela principal (partitioned)
CREATE TABLE silver.clean_games (
    game_id VARCHAR(20) NOT NULL,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    home_score INT,
    away_score INT,
    winner_team_id INT,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (game_id, game_date)
) PARTITION BY RANGE (game_date);

-- Criar partições mensais
CREATE TABLE silver.clean_games_2023_10 
PARTITION OF silver.clean_games
FOR VALUES FROM ('2023-10-01') TO ('2023-11-01');

CREATE TABLE silver.clean_games_2023_11 
PARTITION OF silver.clean_games
FOR VALUES FROM ('2023-11-01') TO ('2023-12-01');

CREATE TABLE silver.clean_games_2023_12 
PARTITION OF silver.clean_games
FOR VALUES FROM ('2023-12-01') TO ('2024-01-01');

-- Partition default (para dados fora do range esperado)
CREATE TABLE silver.clean_games_default 
PARTITION OF silver.clean_games
DEFAULT;
```

### 4.3 List Partitioning por Categoria

```sql
-- Partitioning por status
CREATE TABLE silver.clean_games_status (
    game_id VARCHAR(20) NOT NULL,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    -- ... outras colunas
) PARTITION BY LIST (status);

CREATE TABLE silver.clean_games_scheduled 
PARTITION OF silver.clean_games_status
FOR VALUES IN ('scheduled');

CREATE TABLE silver.clean_games_in_progress 
PARTITION OF silver.clean_games_status
FOR VALUES IN ('in_progress');

CREATE TABLE silver.clean_games_final 
PARTITION OF silver.clean_games_status
FOR VALUES IN ('final', 'cancelled');
```

### 4.4 Hash Partitioning

```sql
-- Distribuir dados uniformemente por N partições
CREATE TABLE bronze.raw_nba_games_hash (
    raw_id BIGSERIAL,
    game_id VARCHAR(20),
    -- ... outras colunas
) PARTITION BY HASH (raw_id);

CREATE TABLE bronze.raw_nba_games_hash_0 
PARTITION OF bronze.raw_nba_games_hash
FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE bronze.raw_nba_games_hash_1 
PARTITION OF bronze.raw_nba_games_hash
FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE bronze.raw_nba_games_hash_2 
PARTITION OF bronze.raw_nba_games_hash
FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE bronze.raw_nba_games_hash_3 
PARTITION OF bronze.raw_nba_games_hash
FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### 4.5 Declarative Partitioning com Partman

Usar extensão `pg_partman` para gestão automática de partições:

```sql
-- Instalar extensão
CREATE EXTENSION pg_partman;

-- Criar tabela com partição automática
SELECT partman.create_parent(
    'silver.clean_odds',
    'recorded_at',
    'native',
    'monthly'
);

-- Configurar retenção (manter apenas 24 meses)
UPDATE partman.part_config
SET retention = '24 months',
    retention_keep_table = false
WHERE parent_table = 'silver.clean_odds';
```

### 4.6 Pruning de Partições

PostgreSQL automaticamente elimina partições irrelevantes:

```sql
-- Query usa apenas partições relevantes
EXPLAIN ANALYZE
SELECT * FROM silver.clean_games
WHERE game_date BETWEEN '2023-11-01' AND '2023-11-30';

-- Verificar se partition pruning está ativo
-- Output deve mostrar "Partition Pruning: true"
```

---

## 5. QUERY OPTIMIZATION

### 5.1 ANALYZE e Statistics

```sql
-- Atualizar estatísticas da tabela
ANALYZE silver.clean_games;

-- Atualizar estatísticas com amostragem mais detalhada
ANALYZE VERBOSE silver.clean_games;

-- Configurar nível de detalhe de estatísticas
ALTER TABLE silver.clean_games 
ALTER COLUMN game_date SET STATISTICS 1000;

-- Verificar estatísticas atuais
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE tablename = 'clean_games'
ORDER BY attname;
```

### 5.2 EXPLAIN ANALYZE

```sql
-- Analisar plano de execução
EXPLAIN ANALYZE
SELECT g.game_id, g.game_date, o.odd
FROM silver.clean_games g
JOIN silver.clean_odds o ON g.game_id = o.game_id
WHERE g.game_date >= '2023-11-01'
AND o.market = 'moneyline_home'
ORDER BY g.game_date;

-- Verificar se está usando índices corretos
-- Procurar por "Index Scan" ou "Bitmap Index Scan"
-- Evitar "Seq Scan" em tabelas grandes
```

### 5.3 Otimização de JOINs

```sql
-- Forçar uso de hash join (geralmente mais rápido para grandes datasets)
SET enable_hashjoin = on;
SET enable_mergejoin = off;
SET enable_nestloop = off;

-- JOIN com condições explícitas
SELECT g.*, o.odd
FROM silver.clean_games g
INNER JOIN silver.clean_odds o 
    ON g.game_id = o.game_id 
    AND o.market = 'moneyline_home'
WHERE g.game_date >= '2023-11-01';

-- Usar CTEs para queries complexas
WITH recent_games AS (
    SELECT game_id, game_date
    FROM silver.clean_games
    WHERE game_date >= CURRENT_DATE - INTERVAL '30 days'
),
latest_odds AS (
    SELECT DISTINCT ON (game_id, market) game_id, market, odd
    FROM silver.clean_odds
    ORDER BY game_id, market, recorded_at DESC
)
SELECT rg.game_id, rg.game_date, lo.market, lo.odd
FROM recent_games rg
JOIN latest_odds lo ON rg.game_id = lo.game_id;
```

### 5.4 Otimização de Aggregations

```sql
-- Usar materialized views para aggregations frequentes
CREATE MATERIALIZED VIEW mv_monthly_bet_performance AS
SELECT 
    DATE_TRUNC('month', executed_at) AS month,
    bet_type,
    COUNT(*) AS total_bets,
    SUM(CASE WHEN outcome = 1 THEN 1 ELSE 0 END) AS wins,
    SUM(stake) AS total_staked,
    SUM(pnl) AS total_pnl
FROM gold.bets
WHERE outcome IN (-1, 1)
GROUP BY DATE_TRUNC('month', executed_at), bet_type;

-- Criar índice unique na materialized view
CREATE UNIQUE INDEX idx_mv_monthly_bet_performance 
ON mv_monthly_bet_performance (month, bet_type);

-- Refresh materialized view
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_bet_performance;

-- Agendamento (via cron ou pg_cron)
SELECT cron.schedule(
    'refresh-mv-monthly-performance',
    '0 2 * * *',  -- Diariamente às 2 AM
    'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_bet_performance'
);
```

### 5.5 Query Rewriting

```sql
-- Evitar SELECT *
-- Ruim:
SELECT * FROM silver.clean_games WHERE game_date = '2023-11-15';

-- Bom:
SELECT game_id, home_team_id, away_team_id, home_score, away_score
FROM silver.clean_games 
WHERE game_date = '2023-11-15';

-- Usar LIMIT quando apropriado
SELECT game_id, game_date
FROM silver.clean_games
WHERE game_date >= '2023-11-01'
ORDER BY game_date
LIMIT 100;

-- Usar EXISTS em vez de IN para subqueries
-- Ruim:
SELECT * FROM silver.clean_games g
WHERE g.game_id IN (SELECT game_id FROM silver.clean_odds WHERE odd > 2.0);

-- Bom:
SELECT * FROM silver.clean_games g
WHERE EXISTS (
    SELECT 1 FROM silver.clean_odds o 
    WHERE o.game_id = g.game_id AND o.odd > 2.0
);
```

---

## 6. CONFIGURAÇÃO POSTGRESQL

### 6.1 postgresql.conf - Configurações de Performance

```ini
# Conexões
max_connections = 100
superuser_reserved_connections = 3

# Memória
shared_buffers = 4GB              # 25% da RAM total
effective_cache_size = 12GB       # 75% da RAM total
work_mem = 64MB                   # Por operação de sort/hash
maintenance_work_mem = 512MB      # Para VACUUM, CREATE INDEX

# WAL (Write-Ahead Log)
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# Query Planning
random_page_cost = 1.1            # Para SSD
effective_io_concurrency = 200    # Para SSD
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# Autovacuum
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.2
autovacuum_analyze_scale_factor = 0.1

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

### 6.2 Configuração Específica por Workload

**Workload OLTP (Transacional):**
```ini
shared_buffers = 2GB
work_mem = 16MB
max_wal_size = 2GB
checkpoint_completion_target = 0.7
synchronous_commit = on
```

**Workload OLAP (Analítico):**
```ini
shared_buffers = 8GB
work_mem = 128MB
max_wal_size = 8GB
checkpoint_completion_target = 0.9
synchronous_commit = off  # Para bulk loads
maintenance_work_mem = 1GB
```

---

## 7. MONITORING DE PERFORMANCE

### 7.1 pg_stat_statements

```sql
-- Habilitar extensão
CREATE EXTENSION pg_stat_statements;

-- Queries mais lentas
SELECT 
    query,
    calls,
    total_exec_time / 1000 / 60 as total_minutes,
    mean_exec_time as avg_ms,
    max_exec_time as max_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Queries mais frequentes
SELECT 
    query,
    calls,
    total_exec_time / 1000 / 60 as total_minutes
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;
```

### 7.2 pg_stat_activity

```sql
-- Queries em execução atualmente
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Matar query bloqueada
SELECT pg_cancel_backend(pid);
-- Ou matar conexão
SELECT pg_terminate_backend(pid);
```

### 7.3 pg_stat_user_tables

```sql
-- Tabelas com mais sequências/updates
SELECT 
    schemaname,
    tablename,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    vacuum_count,
    autovacuum_count
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

---

## 8. VACUUM E MAINTENANCE

### 8.1 VACUUM Manual

```sql
-- VACUUM padrão (reclama espaço, mantém tabela disponível)
VACUUM silver.clean_games;

-- VACUUM FULL (reclama mais espaço, mas bloqueia tabela)
VACUUM FULL silver.clean_games;

-- VACUUM ANALYZE (reclama espaço + atualiza estatísticas)
VACUUM ANALYZE silver.clean_games;

-- VACUUM em tabela específica com opções
VACUUM (VERBOSE, ANALYZE, INDEX_CLEANUP ON) silver.clean_games;
```

### 8.2 Autovacuum Tuning por Tabela

```sql
-- Configurar autovacuum agressivo para tabelas com alto churn
ALTER TABLE silver.clean_odds SET (
    autovacuum_vacuum_threshold = 1000,
    autovacuum_analyze_threshold = 500,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Desabilitar autovacuum para tabelas estáticas (read-only)
ALTER TABLE meta.model_registry SET (
    autovacuum_enabled = false
);
```

### 8.3 REINDEX

```sql
-- Reindexar índice específico (bloqueia writes)
REINDEX INDEX idx_clean_games_date;

-- Reindexar sem bloqueio (CONCURRENTLY)
REINDEX INDEX CONCURRENTLY idx_clean_games_date;

-- Reindexar toda a tabela
REINDEX TABLE CONCURRENTLY silver.clean_games;
```

---

## 9. CACHING

### 9.1 PostgreSQL Query Cache

PostgreSQL não tem query cache explícito, mas usa shared_buffers:

```sql
-- Verificar hit ratio do cache
SELECT 
    sum(blks_hit) / (sum(blks_hit) + sum(blks_read)) * 100 as cache_hit_ratio
FROM pg_stat_database;

-- Target: > 99%
```

### 9.2 Redis como Cache Externo

```python
# Exemplo de caching com Redis
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_key(query, params):
    """Gera chave única para cache"""
    key_string = f"{query}_{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_games_with_cache(team_id, season):
    """Obtém jogos com cache Redis"""
    cache_key = f"games:{team_id}:{season}"
    
    # Tentar obter do cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Se não está no cache, consultar DB
    games = query_db(team_id, season)
    
    # Guardar no cache (TTL 1 hora)
    redis_client.setex(cache_key, 3600, json.dumps(games))
    
    return games
```

---

## 10. CHECKLIST DE PERFORMANCE

### 10.1 Diário
- [ ] Verificar pg_stat_statements para queries lentas
- [ ] Verificar cache hit ratio (> 99%)
- [ ] Verificar autovacuum rodando corretamente
- [ ] Verificar espaço em disco

### 10.11 Semanal
- [ ] Analisar tamanho de tabelas e índices
- [ ] Identificar índices não utilizados
- [ ] Verificar fragmentação de tabelas
- [ ] Review de logs de queries lentas

### 10.3 Mensal
- [ ] Reindexar índices fragmentados
- [ ] Review e ajustar configurações de autovacuum
- [ ] Analisar crescimento de dados e planejar capacity
- [ ] Review de partitioning (criar/remover partições)

---

## 11. LINKS CRUZADOS

- [[15_Database/INDEX]] ← Secao mae
- [[15_Database/SCHEMA_POSTGRESQL]] → Schema completo
- [[15_Database/BACKUP_STRATEGY]] → Backup e recovery
- [[13_Infrastructure/POSTGRES_CONFIG]] → Configuração PostgreSQL
- [[10_Monitoring/METRICAS_DETALHADAS]] → Métricas de monitoring