# BACKUPS_ENCRIPTADOS — Backups Encriptados

**ID:** `SEC-006` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar o processo de criação e gestão de backups encriptados.

---

## 2. ESTRATÉGIA DE ENCRIPTAÇÃO

### 2.1 Encriptação em Repouso
- **PostgreSQL:** Ativar TDE (Transparent Data Encryption) ou encriptar volume
- **Backups:** GPG encriptação com chave assimétrica
- **Secrets:** HashiCorp Vault ou arquivo `.env` encriptado com AES-256

### 2.2 Encriptação em Trânsito
- TLS 1.3 para todas as APIs
- VPN para acesso ao VPS ( WireGuard recomendado)
- SCP/SFTP para transferência de backups

### 2.3 Script de Backup Encriptado
```bash
#!/bin/bash
# backup_encrypted.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
GPG_RECIPIENT="backup@seudominio.com"

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U vb_admin -F c valuebetting | \
  gpg --encrypt --recipient $GPG_RECIPIENT --trust-model always \
  > $BACKUP_DIR/backup_$DATE.dump.gpg

# Verificar integridade
gpg --decrypt $BACKUP_DIR/backup_$DATE.dump.gpg | pg_restore --list > /dev/null && echo "OK"
```

### 2.4 Rotação de Backups
- Diários: 7 dias
- Semanais: 4 semanas
- Mensais: 12 meses
- Anuais: 5 anos (obrigatório fiscal)

## 3. PROCEDIMENTOS DE BACKUP

### 3.1 Backup Diário Automatizado

```bash
#!/bin/bash
# /opt/scripts/backup_daily.sh
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
GPG_RECIPIENT="backup@valuebetting.pt"
RETENTION_DAYS=7

# Criar diretório se não existir
mkdir -p $BACKUP_DIR

# Backup PostgreSQL (custom format, compressão + encriptação)
echo "[$(date)] Iniciando backup PostgreSQL..."
docker compose exec -T postgres pg_dump \
    -U vb_admin \
    -h localhost \
    -F c \
    -Z 9 \
    valuebetting | \
    gpg --encrypt \
        --recipient $GPG_RECIPIENT \
        --trust-model always \
        --compress-algo 2 \
        > $BACKUP_DIR/postgres_${DATE}.dump.gpg

# Backup Redis (RDB)
echo "[$(date)] Iniciando backup Redis..."
docker compose exec redis redis-cli BGSAVE
sleep 5  # Aguardar snapshot

# Copiar RDB e encriptar
docker cp redis:/data/dump.rdb /tmp/redis_${DATE}.rdb
gpg --encrypt \
    --recipient $GPG_RECIPIENT \
    --trust-model always \
    < /tmp/redis_${DATE}.rdb \
    > $BACKUP_DIR/redis_${DATE}.rdb.gpg
rm -f /tmp/redis_${DATE}.rdb

# Backup de configurações
echo "[$(date)] Backup de configurações..."
tar czf - \
    docker-compose.yml \
    .env.example \
    config/ \
    2>/dev/null | \
    gpg --encrypt \
        --recipient $GPG_RECIPIENT \
        --trust-model always \
        > $BACKUP_DIR/config_${DATE}.tar.gz.gpg

# Verificar integridade dos backups
echo "[$(date)] Verificando integridade..."
for file in $BACKUP_DIR/*_${DATE}.*; do
    if gpg --list-packets "$file" > /dev/null 2>&1; then
        echo "✓ $file - OK"
    else
        echo "✗ $file - CORROMPIDO"
        exit 1
    fi
done

# Rotação: apagar backups mais antigos que RETENTION_DAYS
find $BACKUP_DIR -name "*.gpg" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz.gpg" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup concluído."
```

### 3.2 Restore de Backup

```bash
#!/bin/bash
# /opt/scripts/restore.sh
set -euo pipefail

BACKUP_FILE=$1
RESTORE_TYPE=$2  # 'postgres', 'redis', 'config'

echo "Restaurando de: $BACKUP_FILE"

case $RESTORE_TYPE in
    postgres)
        # Parar aplicações
        docker compose stop api
        
        # Decriptar e restaurar
        gpg --decrypt $BACKUP_FILE | docker exec -i postgres pg_restore \
            -U vb_admin \
            -d valuebetting \
            --clean \
            --if-exists \
            --verbose
        
        # Reiniciar aplicações
        docker compose start api
        ;;
    
    redis)
        # Parar Redis
        docker compose stop redis
        
        # Decriptar
        gpg --decrypt $BACKUP_FILE > /tmp/dump.rdb
        
        # Copiar para container
        docker cp /tmp/dump.rdb redis:/data/dump.rdb
        rm -f /tmp/dump.rdb
        
        # Reiniciar Redis
        docker compose start redis
        ;;
    
    config)
        # Decriptar
        gpg --decrypt $BACKUP_FILE | tar xzf - -C /tmp/restore_config/
        
        echo "Configurações restauradas em /tmp/restore_config/"
        echo "Revisar e copiar manualmente para o diretório correto"
        ;;
    
    *)
        echo "Tipo desconhecido: $RESTORE_TYPE"
        exit 1
        ;;
esac

echo "Restore concluído."
```

---

## 4. TESTES DE RESTORE

### 4.1 Teste Mensal de Restore

```bash
#!/bin/bash
# /opt/scripts/test_restore.sh
set -euo pipefail

# Obter backup mais recente
LATEST_BACKUP=$(ls -t /opt/backups/postgres_*.dump.gpg | head -1)

echo "Testando restore de: $LATEST_BACKUP"

# Criar base de dados de teste
docker exec postgres psql -U vb_admin -c "CREATE DATABASE test_restore;"

# Decriptar e restaurar
gpg --decrypt $LATEST_BACKUP | docker exec -i postgres pg_restore \
    -U vb_admin \
    -d test_restore \
    --verbose

# Verificar se dados estão consistentes
ROW_COUNT=$(docker exec postgres psql -U vb_admin -d test_restore -t -c "SELECT COUNT(*) FROM bets;")
echo "Apostas restauradas: $ROW_COUNT"

# Limpar base de teste
docker exec postgres psql -U vb_admin -c "DROP DATABASE test_restore;"

echo "Teste de restore concluído com sucesso."
```

**Frequência:** Executar no primeiro domingo de cada mês.

---

## 5. BACKLOG

- [x] Definir estratégia de encriptação
- [x] Implementar script de backup diário automatizado
- [x] Implementar script de restore
- [x] Definir rotação de backups
- [x] Documentar teste mensal de restore
- [ ] Configurar cron para execução automática diária
- [ ] Configurar notificação de sucesso/falha de backup
- [ ] Testar restore completo end-to-end (Fase 3+)

---

## 6. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secção mãe
- [[34_Security/POSTGRES_SEGURANCA]] → Segurança PostgreSQL
- [[15_Database/BACKUP_STRATEGY]] → Estratégia de backup geral
- [[15_Database/SCHEMA_EVOLUTION]] → Schema e migrações
