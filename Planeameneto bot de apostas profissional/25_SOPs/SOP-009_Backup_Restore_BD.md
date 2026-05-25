# SOP-009 — Backup e Restore de Base de Dados

**ID:** `SOP-009` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Procedimento para backup e restore da base de dados PostgreSQL.

---

## 2. CHECKLIST DE BACKUP
- [ ] Verificar espaço em disco
- [ ] Executar pg_dump
- [ ] Comprimir backup
- [ ] Transferir para local seguro
- [ ] Verificar integridade
- [ ] Documentar backup

---

## 3. CHECKLIST DE RESTORE
- [ ] Identificar backup a restaurar
- [ ] Parar aplicação
- [ ] Drop database existente
- [ ] Criar database novo
- [ ] Restore do backup
- [ ] Verificar integridade
- [ ] Reiniciar aplicação
- [ ] Testar funcionalidades

---

## 4. PROCEDIMENTO DETALHADO

### 4.1 Backup Manual

```bash
# Verificar espaço em disco
df -h /opt/backups

# Criar backup completo
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U vb_admin -F c -b -v -f /tmp/backup_$DATE.dump valuebetting

# Copiar do container para host
docker cp vb-postgres:/tmp/backup_$DATE.dump /opt/backups/

# Comprimir
gzip /opt/backups/backup_$DATE.dump

# Verificar integridade
pg_restore --list /opt/backups/backup_$DATE.dump.gz > /dev/null && echo "OK" || echo "CORRUPT"

# Limpar ficheiro temporário do container
docker compose exec -T postgres rm /tmp/backup_$DATE.dump
```

**Critério de passagem:** Ficheiro `.dump.gz` criado, `pg_restore --list` retorna 0.

### 4.2 Restore Completo

```bash
# PARAR A APLICAÇÃO PRIMEIRO
docker compose down api

# Criar database novo (ou drop + recreate)
docker compose exec -T postgres psql -U vb_admin -c "DROP DATABASE IF EXISTS valuebetting_new;"
docker compose exec -T postgres psql -U vb_admin -c "CREATE DATABASE valuebetting_new;"

# Restaurar
docker compose exec -T postgres pg_restore -U vb_admin -d valuebetting_new -v /opt/backups/backup_YYYYMMDD_HHMMSS.dump.gz

# Verificar tabelas principais
docker compose exec -T postgres psql -U vb_admin -d valuebetting_new -c "SELECT COUNT(*) FROM bronze.raw_odds;"
docker compose exec -T postgres psql -U vb_admin -d valuebetting_new -c "SELECT COUNT(*) FROM gold.features;"

# Se tudo OK: renomear
docker compose exec -T postgres psql -U vb_admin -c "DROP DATABASE IF EXISTS valuebetting_old;"
docker compose exec -T postgres psql -U vb_admin -c "ALTER DATABASE valuebetting RENAME TO valuebetting_old;"
docker compose exec -T postgres psql -U vb_admin -c "ALTER DATABASE valuebetting_new RENAME TO valuebetting;"

# Reiniciar aplicação
docker compose up -d api
```

**Critério de passagem:** Aplicação arranca, queries retornam resultados consistentes com backup.

### 4.3 Restore de Tabela Específica

```bash
# Restaurar apenas uma tabela
docker compose exec -T postgres pg_restore -U vb_admin -d valuebetting --table=raw_odds --data-only /opt/backups/backup_YYYYMMDD_HHMMSS.dump.gz
```

### 4.4 Backup Automático (já configurado)

O backup automático corre diariamente às 03:00 via cron. Verificar:
```bash
ls -lht /opt/backups/ | head -5
```

---

## 5. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[15_Database/BACKUP_STRATEGY]] → Estratégia de backup
