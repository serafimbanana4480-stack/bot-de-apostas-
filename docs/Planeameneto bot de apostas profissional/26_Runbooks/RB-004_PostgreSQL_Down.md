# RB-004 — PostgreSQL Down

**ID:** `RB-004` | **Severidade:** Critical | **Status:** #status/active

---

## 1. SINTOMAS

- Erro "connection refused" ao conectar PostgreSQL
- Aplicação não consegue ler/escrever dados
- Queries timeout

---

## 2. DIAGNÓSTICO DETALHADO

### 2.1 Verificar Status do Container (Docker)

```bash
# Verificar se container está running
docker ps | grep postgres

# Se não estiver, verificar estado
docker ps -a | grep postgres
docker logs --tail 50 postgres

# Verificar uso de recursos
docker stats postgres --no-stream
```

### 2.2 Diagnóstico Dentro do Container

```bash
# Entrar no container
docker exec -it postgres bash

# Verificar processo PostgreSQL
pg_isready -U vb_admin

# Verificar logs do PostgreSQL
tail -n 100 /var/log/postgresql/postgresql-15-main.log

# Verificar conexões ativas
psql -U vb_admin -d valuebetting -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Verificar locks
psql -U vb_admin -d valuebetting -c "SELECT pid, state, query_start, query FROM pg_stat_activity WHERE wait_event_type = 'Lock';"
```

### 2.3 Diagnóstico de Sistema Host

```bash
# Verificar espaço em disco
df -h

# Verificar memória
free -h

# Verificar se porta 5432 está em uso
ss -tlnp | grep 5432

# Verificar logs do sistema
journalctl -u postgresql --since "1 hour ago"
```

### 2.4 Matriz de Causas

| Sintoma | Causa Provável | Verificação |
|---------|---------------|-------------|
| Container exited | Out of memory | `docker logs postgres` procura "OOM" |
| Container restarting | Configuração inválida | `docker logs` procura "FATAL" |
| Conexão refused | Porta não mapeada / firewall | `ss -tlnp | grep 5432` |
| Queries timeout | Lock contention | `pg_stat_activity` com `wait_event_type = 'Lock'` |
| Disk full | Logs ou WAL cresceram | `df -h` |
| Corrupção de dados | Crash anterior / hardware | Logs com "PANIC" ou "corruption" |

---

## 3. RESOLUÇÃO PASSO A PASSO

### 3.1 Passo 1: Tentar Restart do Container

```bash
# Restart suave
docker compose restart postgres

# Aguardar 10 segundos
sleep 10

# Verificar se iniciou
docker ps | grep postgres
docker exec postgres pg_isready -U vb_admin
```

**Se funcionou:** Ir para Verificação (Passo 5).

### 3.2 Passo 2: Verificar e Liberar Espaço em Disco

```bash
# Verificar espaço
df -h | grep -E '(Filesystem|/dev/)'

# Se disco > 90%, identificar arquivos grandes
du -sh /var/lib/docker/volumes/* 2>/dev/null | sort -rh | head -10

# Limpar logs antigos do PostgreSQL (manter 7 dias)
find /var/log/postgresql -name "*.log" -mtime +7 -delete

# Limpar arquivos temporários
docker exec postgres rm -f /tmp/*.tmp

# Se WAL archives ocupam muito espaço, verificar política de retenção
```

**Nota:** Nunca apagar arquivos de dados do PostgreSQL diretamente.

### 3.3 Passo 3: Resolver Problemas de Memória

```bash
# Verificar OOM kills
dmesg | grep -i "killed process" | tail -5

# Se PostgreSQL foi morto por OOM:
# 1. Aumentar RAM do VPS (upgrade)
# 2. Ou reduzir shared_buffers no postgresql.conf
# 3. Ou reduzir max_connections

# Ajustar shared_buffers temporariamente
docker exec -it postgres sed -i 's/shared_buffers = 256MB/shared_buffers = 128MB/' /var/lib/postgresql/data/postgresql.conf
docker compose restart postgres
```

### 3.4 Passo 4: Restaurar de Backup (Corrução Severa)

```bash
# Parar o container
docker compose stop postgres

# Backup dos dados atuais (para investigação forense)
mv /var/lib/docker/volumes/botdeapostas_postgres_data/_data /var/lib/docker/volumes/botdeapostas_postgres_data/_data_corrupto

# Restaurar do backup mais recente
BACKUP_FILE=$(ls -t /backups/*.sql | head -1)
docker compose up -d postgres
sleep 10
docker exec -i postgres psql -U vb_admin -d valuebetting < $BACKUP_FILE

# Verificar integridade
pg_restore --list $BACKUP_FILE
```

**⚠️ Atenção:** Só restaurar backup se confirmação de corrupção. Perda de dados desde o último backup.

### 3.5 Passo 5: Escalar para VPS Provider (Hardware Issue)

Se:
- Disco está saudável
- Memória é suficiente
- Logs indicam erro de hardware (I/O error, disk failure)

**Ação:** Abrir ticket com provider de VPS incluindo:
- Logs de erro do PostgreSQL
- Output de `dmesg`
- Output de `smartctl` (se disponível)

---

## 4. PREVENÇÃO

### 4.1 Monitorização Proativa

```yaml
# prometheus.yml - alerta para PostgreSQL
rules:
  - alert: PostgreSQLDown
    expr: pg_up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "PostgreSQL está down"
      runbook_url: "https://wiki.internal/RB-004"

  - alert: PostgreSQLHighConnections
    expr: pg_stat_activity_count > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL com >80 conexões"
```

### 4.2 Manutenção Preventiva

- **Diária:** Verificar espaço em disco (`df -h`)
- **Semanal:** Verificar logs por warnings
- **Mensal:** Testar restore de backup
- **Trimestral:** Vacuum analyze em tabelas grandes

---

## 5. VERIFICAÇÃO PÓS-RESOLUÇÃO

```bash
# 1. PostgreSQL running
docker ps | grep postgres

# 2. Conexões funcionando
docker exec postgres pg_isready -U vb_admin

# 3. Queries executando
docker exec postgres psql -U vb_admin -d valuebetting -c "SELECT COUNT(*) FROM bets;"

# 4. API responde
curl -f http://localhost:8000/health || echo "API ainda down"

# 5. Sem erros críticos nos logs
docker logs --tail 20 postgres | grep -i "error\|fatal\|panic" || echo "Sem erros"
```

**Critérios de Passagem:**
- [ ] Container PostgreSQL em estado `Up`
- [ ] `pg_isready` retorna `accepting connections`
- [ ] Query de teste retorna resultado em < 1s
- [ ] API FastAPI responde com HTTP 200
- [ ] Logs não contêm erros FATAL/PANIC

---

## 6. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[15_Database/INDEX]] → Secção de database
- [[34_Security/POSTGRES_SEGURANCA]] → Segurança PostgreSQL
- [[34_Security/BACKUPS_ENCRIPTADOS]] → Procedimentos de backup
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Alertas de PostgreSQL
