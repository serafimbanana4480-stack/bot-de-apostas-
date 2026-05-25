# BACKUP_STRATEGY — Estratégia de Backup e Disaster Recovery

**ID:** `DB-003` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégia completa de backup, retention policies, procedimentos de restore, e plano de disaster recovery para garantir continuidade de negócio e proteção de dados críticos.

---

## 2. POLÍTICA DE BACKUP

### 2.1 Estratégia 3-2-1

**Regra 3-2-1:**
- **3** cópias dos dados (produção + 2 backups)
- **2** tipos diferentes de mídia (local + cloud)
- **1** cópia off-site (cloud storage)

### 2.2 Tipos de Backup

| Tipo | Frequência | Retenção | RPO | RTO |
|------|------------|----------|-----|-----|
| Full (Base Backup) | Diário (2 AM) | 7 dias | 24h | 1h |
| Incremental (WAL) | Contínuo | 7 dias | < 5min | 1h |
| Weekly Full | Semanal (Domingo) | 4 semanas | 7 dias | 2h |
| Monthly Full | Mensal (1º dia) | 12 meses | 30 dias | 4h |
| Annual Full | Anual (1º Jan) | 7 anos | 365 dias | 1 dia |

### 2.3 RPO/RTO Targets

| Sistema | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) |
|---------|-------------------------------|-------------------------------|
| PostgreSQL (Dados) | 5 minutos | 1 hora |
| PostgreSQL (Config) | 24 horas | 30 minutos |
| Redis (Cache) | 24 horas | 30 minutos |
| ML Models | 24 horas | 1 hora |
| Código (Git) | 0 minutos | 15 minutos |

---

## 3. BACKUP POSTGRESQL

### 3.1 pg_dump (Backup Lógico)

**Uso:** Backups pequenos, portabilidade entre versões

```bash
# Backup completo do database
pg_dump -h localhost -U vb_admin -d valuebetting \
    -F c -f /backups/valuebetting_$(date +%Y%m%d).dump

# Backup com compressão
pg_dump -h localhost -U vb_admin -d valuebetting \
    -F c -Z 9 -f /backups/valuebetting_$(date +%Y%m%d).dump

# Backup apenas schema (sem dados)
pg_dump -h localhost -U vb_admin -d valuebetting \
    --schema-only -f /backups/schema_$(date +%Y%m%d).sql

# Backup apenas dados específicos
pg_dump -h localhost -U vb_admin -d valuebetting \
    -t silver.clean_games -t gold.signals \
    -F c -f /backups/critical_tables_$(date +%Y%m%d).dump

# Backup com paralelismo (para databases grandes)
pg_dump -h localhost -U vb_admin -d valuebetting \
    -F c -j 4 -f /backups/valuebetting_$(date +%Y%m%d).dump
```

### 3.2 pg_basebackup (Backup Físico)

**Uso:** Backups grandes, Point-in-Time Recovery (PITR)

```bash
# Backup físico completo
pg_basebackup -h localhost -U vb_admin \
    -D /backups/base_$(date +%Y%m%d) \
    -Fp -Xs -P -R

# Backup com compressão
pg_basebackup -h localhost -U vb_admin \
    -D /backups/base_$(date +%Y%m%d) \
    -Ft -z -P -R

# Backup incremental (base + WAL)
pg_basebackup -h localhost -U vb_admin \
    -D /backups/base_$(date +%Y%m%d) \
    -Fp -X stream -P -R
```

### 3.3 Configuração de Archiving WAL

**postgresql.conf:**
```ini
# Habilitar WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
archive_timeout = 300  # 5 minutos

# Configuração para compressão de WAL
archive_command = 'gzip < %p > /backups/wal/%f.gz'
```

**restore_command:**
```ini
restore_command = 'gunzip < /backups/wal/%f.gz > %p'
```

### 3.4 Script de Backup Automatizado

```bash
#!/bin/bash
# /usr/local/bin/backup_postgres.sh

set -e

# Configurações
DB_NAME="valuebetting"
DB_USER="vb_admin"
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório
mkdir -p $BACKUP_DIR/daily
mkdir -p $BACKUP_DIR/wal

# Backup full com pg_dump
echo "Iniciando backup full..."
pg_dump -h localhost -U $DB_USER -d $DB_NAME \
    -F c -Z 6 \
    -f $BACKUP_DIR/daily/valuebetting_$DATE.dump

# Comprimir backup
gzip -f $BACKUP_DIR/daily/valuebetting_$DATE.dump

# Limpar backups antigos
echo "Limpando backups antigos..."
find $BACKUP_DIR/daily -name "valuebetting_*.dump.gz" -mtime +$RETENTION_DAYS -delete

# Limpar WAL antigos (manter 7 dias)
find $BACKUP_DIR/wal -name "*.gz" -mtime +$RETENTION_DAYS -delete

# Enviar para S3 (opcional)
echo "Enviando para S3..."
aws s3 sync $BACKUP_DIR/daily s3://valuebetting-backups/postgres/daily/
aws s3 sync $BACKUP_DIR/wal s3://valuebetting-backups/postgres/wal/

echo "Backup concluído com sucesso!"
```

**Cron Job:**
```bash
# Backup diário às 2 AM
0 2 * * * /usr/local/bin/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
```

---

## 4. BACKUP OFF-SITE (CLOUD)

### 4.1 AWS S3

```bash
# Instalar AWS CLI
pip install awscli

# Configurar credenciais
aws configure

# Upload de backup para S3
aws s3 cp /backups/valuebetting_20231115.dump.gz \
    s3://valuebetting-backups/postgres/daily/valuebetting_20231115.dump.gz

# Upload com lifecycle policy (retention automática)
aws s3api put-bucket-lifecycle-configuration \
    --bucket valuebetting-backups \
    --lifecycle-configuration file://lifecycle.json
```

**lifecycle.json:**
```json
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Prefix": "postgres/daily/",
      "Expiration": {
        "Days": 30
      }
    },
    {
      "Id": "TransitionToGlacier",
      "Status": "Enabled",
      "Prefix": "postgres/monthly/",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### 4.2 Backblaze B2 (Alternativa Econômica)

```bash
# Instalar B2 CLI
pip install b2

# Autorizar
b2 authorize-account

# Upload
b2 upload-file valuebetting-backups \
    /backups/valuebetting_20231115.dump.gz \
    postgres/daily/valuebetting_20231115.dump.gz
```

### 4.3 Rclone (Multi-Cloud)

```bash
# Configurar rclone
rclone config

# Sync para multiple providers
rclone sync /backups/postgres/ s3:valuebetting-backups/postgres/
rclone sync /backups/postgres/ b2:valuebetting-backups/postgres/
rclone sync /backups/postgres/ dropbox:valuebetting-backups/postgres/
```

---

## 5. RESTORE

### 5.1 Restore de pg_dump

```bash
# Restore completo
pg_restore -h localhost -U vb_admin -d valuebetting \
    -v /backups/valuebetting_20231115.dump

# Restore para database novo
pg_restore -h localhost -U vb_admin -d valuebetting_restore \
    -v /backups/valuebetting_20231115.dump

# Restore apenas schema
pg_restore -h localhost -U vb_admin -d valuebetting \
    --schema-only -v /backups/valuebetting_20231115.dump

# Restore apenas dados específicos
pg_restore -h localhost -U vb_admin -d valuebetting \
    -t silver.clean_games -t gold.signals \
    -v /backups/valuebetting_20231115.dump

# Restore com clean (drop existing objects)
pg_restore -h localhost -U vb_admin -d valuebetting \
    --clean --if-exists \
    -v /backups/valuebetting_20231115.dump
```

### 5.2 Point-in-Time Recovery (PITR)

**Uso:** Recuperar database para um momento específico no tempo

```bash
# 1. Parar PostgreSQL
sudo systemctl stop postgresql

# 2. Limpar data directory
sudo rm -rf /var/lib/postgresql/15/main/*

# 3. Restore base backup
pg_basebackup -h localhost -U vb_admin \
    -D /var/lib/postgresql/15/main \
    -Fp -Xs -P

# 4. Configurar recovery
# postgresql.conf:
restore_command = 'cp /backups/wal/%f %p'
recovery_target_time = '2023-11-15 14:30:00'

# 5. Criar arquivo recovery.signal
touch /var/lib/postgresql/15/main/recovery.signal

# 6. Iniciar PostgreSQL
sudo systemctl start postgresql

# 7. PostgreSQL vai recuperar até o tempo especificado
# e então criar standby.signal automaticamente
```

### 5.3 Script de Restore Automatizado

```bash
#!/bin/bash
# /usr/local/bin/restore_postgres.sh

set -e

DB_NAME="valuebetting"
DB_USER="vb_admin"
BACKUP_FILE=$1
RESTORE_DB="${DB_NAME}_restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: $0 <backup_file>"
    exit 1
fi

echo "Iniciando restore..."

# Criar database de restore
dropdb -h localhost -U $DB_USER $RESTORE_DB 2>/dev/null || true
createdb -h localhost -U $DB_USER $RESTORE_DB

# Restore
pg_restore -h localhost -U $DB_USER -d $RESTORE_DB \
    -v $BACKUP_FILE

echo "Restore concluído: $RESTORE_DB"
echo "Para substituir database de produção:"
echo "  dropdb $DB_NAME"
echo "  ALTER DATABASE $RESTORE_DB RENAME TO $DB_NAME"
```

---

## 6. DISASTER RECOVERY

### 6.1 Plano de Disaster Recovery

**Cenário 1: Corrupção de Database**
1. Identificar momento da corrupção
2. Parar PostgreSQL
3. Restore do backup mais recente antes da corrupção
4. Aplicar WAL logs até momento antes da corrupção
5. Validar integridade dos dados
6. RTO: 1-2 horas

**Cenário 2: Falha de Hardware (Servidor)**
1. Provisionar novo servidor
2. Instalar PostgreSQL (mesma versão)
3. Restore do backup base mais recente
4. Aplicar WAL logs
5. Atualizar DNS/IP
6. RTO: 2-4 horas

**Cenário 3: Desastre Completo (Data Center)**
1. Ativar DR site (ou cloud)
2. Restore de backup off-site
3. Configurar DNS failover
4. Validar sistemas
5. RTO: 4-8 horas

### 6.2 Standby Server (Streaming Replication)

**Primary (postgresql.conf):**
```ini
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB
```

**Primary (pg_hba.conf):**
```ini
host    replication     replicator      192.168.1.0/24     md5
```

**Standby (recovery.conf / postgresql.auto.conf):**
```ini
standby_mode = on
primary_conninfo = 'host=primary-ip port=5432 user=replicator'
restore_command = 'cp /backups/wal/%f %p'
```

### 6.3 Failover Automático

Usar **Patroni** ou **repmgr** para failover automático:

```bash
# Instalar repmgr
apt install repmgr

# Configurar cluster
repmgr -f /etc/repmgr.conf primary register

# Adicionar standby
repmgr -f /etc/repmgr.conf standby clone
repmgr -f /etc/repmgr.conf standby register

# Promover standby (failover manual)
repmgr -f /etc/repmgr.conf standby promote
```

---

## 7. MONITORING DE BACKUP

### 7.1 Verificação de Backups

```sql
-- Tabela para tracking de backups
CREATE TABLE meta.backup_history (
    backup_id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) NOT NULL,  -- 'full', 'incremental'
    backup_path VARCHAR(255) NOT NULL,
    backup_size_bytes BIGINT,
    backup_start_time TIMESTAMPTZ NOT NULL,
    backup_end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Verificar último backup bem-sucedido
SELECT 
    backup_type,
    MAX(backup_end_time) as last_backup,
    backup_size_bytes
FROM meta.backup_history
WHERE status = 'success'
GROUP BY backup_type;
```

### 7.2 Alertas

**Alertas configurar:**
- Backup falhou nas últimas 24 horas
- Backup não iniciou no horário esperado
- Espaço em disco < 20%
- WAL archiving falhou
- Replication lag > 5 minutos

---

## 8. TESTING DE RESTORE

### 8.1 Teste Mensal Obrigatório

**Procedimento:**
1. Selecionar backup aleatório do mês anterior
2. Restore em ambiente de staging
3. Validar integridade dos dados
4. Verificar que todas as tabelas estão presentes
5. Executar queries de validação
6. Documentar resultado do teste

### 8.2 Script de Validação

```sql
-- Validação pós-restore
DO $$
DECLARE
    table_count INT;
    row_count INT;
BEGIN
    -- Verificar número de tabelas
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema IN ('bronze', 'silver', 'gold', 'meta', 'audit');
    
    IF table_count < 20 THEN
        RAISE EXCEPTION 'Número de tabelas insuficiente: %', table_count;
    END IF;
    
    -- Verificar jogos recentes
    SELECT COUNT(*) INTO row_count
    FROM silver.clean_games
    WHERE game_date >= CURRENT_DATE - INTERVAL '7 days';
    
    IF row_count = 0 THEN
        RAISE EXCEPTION 'Não há jogos recentes nos últimos 7 dias';
    END IF;
    
    RAISE NOTICE 'Validação concluída com sucesso';
END $$;
```

---

## 9. DOCUMENTAÇÃO E RUNBOOKS

### 9.1 Runbook: Restore Completo

**Pré-requisitos:**
- Acesso ao servidor
- Credenciais de banco
- Backup file disponível

**Passos:**
1. Notificar stakeholders do downtime
2. Parar aplicações
3. Parar PostgreSQL
4. Backup do data directory atual (precaução)
5. Limpar data directory
6. Restore do backup
7. Iniciar PostgreSQL
8. Validar integridade
9. Iniciar aplicações
10. Notificar stakeholders de conclusão

### 9.2 Runbook: Failover para Standby

**Pré-requisitos:**
- Standby server configurado
- Replication funcionando
- Acesso DNS

**Passos:**
1. Verificar lag de replicação
2. Promover standby a primary
3. Atualizar DNS/IP
4. Validar aplicações
5. Reconfigurar antigo primary como standby
6. Documentar incidente

---

## 10. SECURITY DE BACKUP

### 10.1 Encryption

```bash
# Encrypt backup com GPG
gpg --symmetric --cipher-algo AES256 \
    /backups/valuebetting_20231115.dump

# Decrypt
gpg --decrypt /backups/valuebetting_20231115.dump.gpg \
    > /backups/valuebetting_20231115.dump

# Encrypt durante upload para S3
aws s3 cp /backups/valuebetting_20231115.dump \
    s3://valuebetting-backups/postgres/ \
    --server-side-encryption AES256
```

### 10.2 Access Control

```bash
# Permissões de diretório
chmod 700 /backups
chmod 600 /backups/*

# Ownership
chown -R postgres:postgres /backups

# S3 Bucket Policy (restrito)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::valuebetting-backups/*",
      "Condition": {
        "NotIpAddress": {
          "aws:SourceIp": ["192.168.1.0/24"]
        }
      }
    }
  ]
}
```

---

## 11. CHECKLIST DE BACKUP

### 11.1 Diário
- [ ] Verificar se backup diário foi executado
- [ ] Verificar tamanho do backup
- [ ] Verificar upload para cloud
- [ ] Verificar espaço em disco

### 11.2 Semanal
- [ ] Testar restore de backup aleatório
- [ ] Verificar integridade de backup off-site
- [ ] Review logs de backup
- [ ] Verificar replication lag (se aplicável)

### 11.3 Mensal
- [ ] Teste completo de disaster recovery
- [ ] Review e atualizar documentação
- [ ] Verificar custos de storage cloud
- [ ] Update retention policies se necessário

---

## 12. LINKS CRUZADOS

- [[15_Database/INDEX]] ← Secao mae
- [[15_Database/SCHEMA_POSTGRESQL]] → Schema completo
- [[15_Database/PERFORMANCE_TUNING]] → Otimização de performance
- [[13_Infrastructure/DISASTER_RECOVERY]] → Disaster recovery geral
- [[13_Infrastructure/POSTGRES_CONFIG]] → Configuração PostgreSQL