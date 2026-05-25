# POSTGRES_CONFIG — Configuração do Banco de Dados

**ID:** `INF-003` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Configurar PostgreSQL 15 para performance otimizada em workloads analíticos, backup automático, e integridade de dados. PostgreSQL é a fonte de verdade do sistema.

---

## 2. INSTALAÇÃO

```bash
# Ubuntu 22.04
apt install postgresql-15 postgresql-contrib-15

# Criar utilizador e database
sudo -u postgres psql
CREATE USER valuebetting WITH PASSWORD 'senha_segura';
CREATE DATABASE valuebetting OWNER valuebetting;
GRANT ALL PRIVILEGES ON DATABASE valuebetting TO valuebetting;
\q
```

---

## 3. CONFIGURAÇÃO DE PRODUÇÃO

### 3.1 postgresql.conf

```conf
# CONEXÕES
max_connections = 100
superuser_reserved_connections = 3

# MEMÓRIA (ajustar para 8GB RAM VPS)
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 16MB

# WAL (Write Ahead Log)
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
checkpoint_completion_target = 0.9

# QUERY TUNING
random_page_cost = 1.1  # SSD
effective_io_concurrency = 200
default_statistics_target = 100

# LOGGING
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_duration = off

# OUTROS
timezone = 'UTC'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'
```

### 3.2 pg_hba.conf (Autenticação)

```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             postgres                                peer
local   all             valuebetting                             md5

# IPv4 local connections
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# Block external connections (security)
host    all             all             0.0.0.0/0               reject
```

---

## 4. VARIÁVEIS DE AMBIENTE

```bash
# .env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=valuebetting
POSTGRES_USER=valuebetting
POSTGRES_PASSWORD=senha_super_segura
DATABASE_URL=postgresql://valuebetting:senha_super_segura@127.0.0.1:5432/valuebetting
```

---

## 5. OTIMIZAÇÕES DE PERFORMANCE

### 5.1 Índices Críticos

```sql
-- Índices em tabelas principais
CREATE INDEX idx_games_game_date ON games(game_date);
CREATE INDEX idx_odds_game_id ON odds(game_id);
CREATE INDEX idx_odds_timestamp ON odds(timestamp);
CREATE INDEX idx_features_game_id ON features(game_id);
CREATE INDEX idx_bets_game_id ON bets(game_id);

-- Índices compostos para queries comuns
CREATE INDEX idx_odds_game_market ON odds(game_id, market);
CREATE INDEX idx_features_game_computed ON features(game_id, computed_at);
```

### 5.2 Partitioning (Futuro)

```sql
-- Partitioning de jogos por época (quando > 10.000 jogos)
CREATE TABLE games_2023_24 PARTITION OF games
    FOR VALUES FROM ('2023-10-01') TO ('2024-07-01');

CREATE TABLE games_2024_25 PARTITION OF games
    FOR VALUES FROM ('2024-10-01') TO ('2025-07-01');
```

### 5.3 VACUUM e ANALYZE Automático

```conf
# postgresql.conf
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
```

---

## 6. BACKUP AUTOMÁTICO

### 6.1 Script de Backup Diário

```bash
#!/bin/bash
# /opt/backup/postgres_backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30

# Criar diretório se não existir
mkdir -p $BACKUP_DIR

# Backup com pg_dump
pg_dump -U valuebetting -h 127.0.0.1 valuebetting | gzip > $BACKUP_DIR/valuebetting_$DATE.sql.gz

# Remover backups antigos
find $BACKUP_DIR -name "valuebetting_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Upload para S3 (opcional)
# aws s3 cp $BACKUP_DIR/valuebetting_$DATE.sql.gz s3://vb-backups/postgres/
```

### 6.2 Cron Job

```bash
# Backup diário às 02:00
0 2 * * * /opt/backup/postgres_backup.sh
```

### 6.3 Restore

```bash
# Parar aplicações
systemctl stop valuebetting-api

# Restore
gunzip < /backups/postgres/valuebetting_20260513.sql.gz | psql -U valuebetting -h 127.0.0.1 valuebetting

# Reiniciar aplicações
systemctl start valuebetting-api
```

---

## 7. MONITORIZAÇÃO

### 7.1 Métricas Importantes

```sql
-- Tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Conexões ativas
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Queries lentas
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Cache hit ratio (deve ser > 99%)
SELECT 
    sum(blks_hit) / (sum(blks_hit) + sum(blks_read)) AS cache_hit_ratio
FROM pg_stat_database;
```

### 7.2 Prometheus Exporter

```bash
# Instalar postgres_exporter
docker run -d \
  --name postgres_exporter \
  --network host \
  -e DATA_SOURCE_NAME="postgresql://valuebetting:senha@127.0.0.1:5432/valuebetting?sslmode=disable" \
  prometheuscommunity/postgres-exporter:latest
```

---

## 8. SEGURANÇA

- ✅ PostgreSQL nunca exposto para internet (127.0.0.1 only)
- ✅ Password forte (32+ caracteres)
- ✅ SSL desativado para conexões locais (performance)
- ✅ Firewall UFW bloqueia porta 5432 externamente
- ✅ Utilizador separado para aplicação (não postgres)
- ✅ Backup criptografado se enviado para S3

---

## 9. MANUTENÇÃO

### 9.1 Atualizações

```bash
# Atualizar PostgreSQL
sudo apt update
sudo apt upgrade postgresql-15

# Reiniciar serviço
sudo systemctl restart postgresql
```

### 9.2 Limpeza

```sql
-- VACUUM manual (se autovacuum não suficiente)
VACUUM ANALYZE games;

-- REINDEX se índices corrompidos
REINDEX TABLE games;
```

---

## 10. TROUBLESHOOTING

### Problema: Conexões recusadas
```bash
# Verificar status
sudo systemctl status postgresql

# Verificar logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Verificar conexões máximas
sudo -u postgres psql -c "SHOW max_connections;"
```

### Problema: Performance lenta
```sql
-- Verificar queries lentas
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 5;

-- Verificar se VACUUM está a correr
SELECT * FROM pg_stat_activity WHERE query LIKE '%VACUUM%';
```

### Problema: Disk space cheio
```bash
# Verificar tamanho do BD
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('valuebetting'));"

-- Limpar logs antigos
sudo rm /var/log/postgresql/*.gz
```

---

## 11. ESCALABILIDADE

### Quando escalar:
- Tamanho do BD > 500GB
- Queries > 10s consistentemente
- > 100 conexões simultâneas

### Opções:
1. **Vertical:** Upgrade VPS (mais RAM/CPU)
2. **Read Replicas:** Para queries analíticas
3. **Managed:** AWS RDS / Google Cloud SQL (futuro)
4. **Sharding:** Por época ou desporto (extremo)

---

## 12. LINKS CRUZADOS

- [[13_Infrastructure/INDEX]] ← Secção mãe
- [[15_Database/INDEX]] → Schema detalhado e design
- [[04_Data_Engineering/INDEX]] → Pipelines que usam PostgreSQL