# 26_Runbooks — INDEX

**ID:** `SEC-26` | **Fase:** Todas | **Owner:** Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Documentar runbooks para incidentes específicos. Runbooks são guias passo-a-passo para diagnosticar e resolver problemas conhecidos. Diferente de SOPs (procedimentos rotineiros), runbooks são para situações anormais.

---

## 2. NOTAS FUNDAMENTAIS

- [[RUNBOOK-001_API_DOWN]] — API não responde
- [[RUNBOOK-002_DATABASE_DOWN]] — PostgreSQL não conecta
- [[RUNBOOK-003_REDIS_DOWN]] — Redis não responde
- [[RUNBOOK-004_DATA_NOT_UPDATING]] — Dados não atualizando
- [[RUNBOOK-005_HIGH_CPU]] — CPU > 80% sustained
- [[RUNBOOK-006_HIGH_MEMORY]] — Memory pressure, OOM kills
- [[RUNBOOK-007_DISK_FULL]] — Disco > 90%
- [[RUNBOOK-008_TELEGRAM_BOT_DOWN]] — Telegram Bot offline
- [[RUNBOOK-009_MODEL_PERFORMANCE_DROP]] — CLV cai abruptamente
- [[RUNBOOK-010_ODDS_FEED_FAILURE]] — Feed de odds falha

---

## 3. RUNBOOKS CRÍTICOS (PRIORIDADE ALTA)

### RUNBOOK-001: API Não Responde
**Severidade:** CRITICAL
**Tempo estimado:** 10-30 minutos
**Owner:** On-call Engineer

**Sintomas:**
- Health check `/health` retorna 503 ou timeout
- Dashboards mostram API error rate > 5%
- Telegram bot não consegue enviar sinais

**Diagnóstico:**
```bash
# 1. Verificar se API container está running
docker ps | grep vb-api

# 2. Verificar logs da API
docker compose logs -f api

# 3. Verificar se API está em crash loop
docker compose ps api
# Se Restart Count > 5, container está em crash loop

# 4. Verificar recursos (CPU/Memory)
docker stats vb-api

# 5. Verificar se dependências estão healthy
docker compose ps postgres redis
```

**Causas Comuns:**
1. **Container crash:** Bug no código causou exceção não tratada
2. **Out of memory:** API container excedeu limite de RAM
3. **Database connection:** PostgreSQL não responde
4. **Port conflict:** Porta 8000 já em uso

**Resolução:**

**Caso 1: Container crash**
```bash
# Ver logs para identificar erro
docker compose logs api --tail 100

# Se for bug temporário, reiniciar
docker compose restart api

# Se for bug persistente, fazer rollback
docker compose down
docker compose up -d api
# Considerar rollback para versão anterior
```

**Caso 2: Out of memory**
```bash
# Ver memory usage
docker stats vb-api

# Se OOM, aumentar limite no docker-compose.yml
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Reiniciar
docker compose restart api
```

**Caso 3: Database connection**
```bash
# Verificar PostgreSQL
docker compose ps postgres
docker compose logs postgres

# Se PostgreSQL down, seguir RUNBOOK-002
```

**Caso 4: Port conflict**
```bash
# Verificar o que está usando porta 8000
netstat -tulpn | grep 8000

# Matar processo se necessário
kill -9 <PID>

# Reiniciar API
docker compose restart api
```

**Verificação:**
```bash
# Testar health check
curl -f http://localhost:8000/health
# Deve retornar 200

# Ver logs
docker compose logs api --tail 20
# Deve mostrar "Application startup complete"
```

**Prevenção:**
- Adicionar health checks ao docker-compose.yml
- Configurar auto-restart policy
- Monitorizar memory usage e alertar se > 80%

---

### RUNBOOK-002: PostgreSQL Não Conecta
**Severidade:** CRITICAL
**Tempo estimado:** 15-45 minutos
**Owner:** On-call Engineer + DBA

**Sintomas:**
- API logs mostram "connection refused" ou timeout ao conectar PostgreSQL
- `docker compose exec postgres pg_isready` falha
- Dashboards mostram PostgreSQL error rate > 5%

**Diagnóstico:**
```bash
# 1. Verificar se PostgreSQL container está running
docker ps | grep vb-postgres

# 2. Verificar logs do PostgreSQL
docker compose logs postgres

# 3. Verificar se PostgreSQL está aceitando conexões
docker compose exec postgres pg_isready -U vb_admin

# 4. Verificar recursos (CPU/Memory/Disk)
docker stats vb-postgres
df -h  # Verificar espaço em disco

# 5. Verificar número de conexões
docker compose exec postgres psql -U vb_admin -d valuebetting -c "SELECT count(*) FROM pg_stat_activity;"
```

**Causas Comuns:**
1. **Container crash:** PostgreSQL crashou
2. **Disk full:** Disco do PostgreSQL está 100%
3. **Connection limit:** Muitas conexões simultâneas
4. **Corruption:** Database corruption (raro mas crítico)

**Resolução:**

**Caso 1: Container crash**
```bash
# Ver logs para identificar crash
docker compose logs postgres --tail 100

# Reiniciar PostgreSQL
docker compose restart postgres

# Se não iniciar, verificar logs novamente
docker compose logs postgres
```

**Caso 2: Disk full**
```bash
# Verificar uso de disco
df -h

# Se /var/lib/postgresql/data está 100%:
# 1. Limpar logs antigos
docker compose exec postgres psql -U vb_admin -d valuebetting -c "VACUUM FULL;"

# 2. Limpar backups antigos
cd /opt/backups
find . -name "backup_*.tar.gz" -mtime +30 -delete

# 3. Se ainda assim, expandir disco (VPS provider)
```

**Caso 3: Connection limit**
```bash
# Verificar max_connections
docker compose exec postgres psql -U vb_admin -d valuebetting -c "SHOW max_connections;"

# Verificar conexões atuais
docker compose exec postgres psql -U vb_admin -d valuebetting -c "SELECT count(*) FROM pg_stat_activity;"

# Se próximo do limite, aumentar max_connections
# Editar postgresql.conf ou docker-compose.yml
# command: postgres -c max_connections=200

# Reiniciar PostgreSQL
docker compose restart postgres
```

**Caso 4: Database corruption**
```bash
# ATENÇÃO: Caso crítico, pode requerer restore de backup

# Tentar recovery
docker compose exec postgres psql -U vb_admin -d valuebetting -c "REINDEX DATABASE valuebetting;"

# Se falhar, restaurar backup
docker compose down
cd /opt/backups
tar xzf backup_YYYYMMDD_HHMMSS.tar.gz
docker compose up -d postgres
docker exec -i vb-postgres psql -U vb_admin valuebetting < db_YYYYMMDD_HHMMSS.sql
docker compose up -d
```

**Verificação:**
```bash
# Testar conexão
docker compose exec postgres pg_isready -U vb_admin
# Deve retornar "vb-postgres:5432 - accepting connections"

# Testar queries
docker compose exec postgres psql -U vb_admin -d valuebetting -c "SELECT 1;"
# Deve retornar "1"
```

**Prevenção:**
- Monitorizar disco usage (alertar se > 85%)
- Configurar auto-vacuum agressivo
- Backups diários automatizados
- Testar restore mensalmente

---

### RUNBOOK-003: Redis Não Responde
**Severidade:** HIGH
**Tempo estimado:** 10-20 minutos
**Owner:** On-call Engineer

**Sintomas:**
- API logs mostram "Redis connection error"
- `docker compose exec redis redis-cli ping` falha
- Cache não está funcionando (API lento)

**Diagnóstico:**
```bash
# 1. Verificar se Redis container está running
docker ps | grep vb-redis

# 2. Verificar logs do Redis
docker compose logs redis

# 3. Verificar se Redis responde
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping
# Deve retornar PONG

# 4. Verificar recursos
docker stats vb-redis
```

**Causas Comuns:**
1. **Container crash:** Redis crashou
2. **Memory full:** Redis excedeu limite de RAM
3. **Password error:** Password incorreta

**Resolução:**

**Caso 1: Container crash**
```bash
# Ver logs
docker compose logs redis --tail 100

# Reiniciar
docker compose restart redis
```

**Caso 2: Memory full**
```bash
# Ver memory usage
docker stats vb-redis

# Se OOM, aumentar limite ou configurar maxmemory
# Editar redis.conf ou comando no docker-compose.yml
# command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru

# Reiniciar
docker compose restart redis
```

**Caso 3: Password error**
```bash
# Verificar password no .env
cat .env | grep REDIS_PASSWORD

# Verificar se password está correto
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping

# Se password errado, corrigir no .env e reiniciar
docker compose restart redis
```

**Verificação:**
```bash
# Testar ping
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping
# Deve retornar PONG

# Testar set/get
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} SET test "hello"
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} GET test
# Deve retornar "hello"
```

**Prevenção:**
- Configurar maxmemory e eviction policy
- Monitorizar memory usage
- Backups diários do Redis dump

---

### RUNBOOK-004: Dados Não Atualizando
**Severidade:** HIGH
**Tempo estimado:** 15-30 minutos
**Owner:** Data Engineer

**Sintomas:**
- Última ingestão de dados NBA > 24h
- Odds não atualizadas (> 30min)
- Dashboard mostra "Data stale"

**Diagnóstico:**
```bash
# 1. Verificar último update
docker compose exec api python -c "from app.db import Session; from app.models import Game; print(Session().query(Game).order_by(Game.game_date.desc()).first().game_date)"

# 2. Verificar logs de ingestão
docker compose logs api | grep "ingest"

# 3. Verificar se Prefect flows estão rodando
# Acessar Prefect UI em http://localhost:4200
# Verificar status dos flows de ingestão

# 4. Verificar se APIs externas estão respondendo
curl -I https://api.nba.com/...
curl -I https://www.basketball-reference.com/...
```

**Causas Comuns:**
1. **API rate limit:** NBA API bloqueou por excesso de requests
2. **Prefect flow falhou:** Flow de ingestão crashou
3. **Network issue:** VPS não consegue alcançar APIs externas
4. **Code bug:** Bug no código de ingestão

**Resolução:**

**Caso 1: API rate limit**
```bash
# Verificar logs para ver se há erro 429
docker compose logs api | grep "429"

# Se rate limit, reduzir frequência de ingestão
# Editar Prefect flow schedule para 4h em vez de 2h

# Reiniciar flow com nova frequência
```

**Caso 2: Prefect flow falhou**
```bash
# Acessar Prefect UI
# Verificar logs do flow failed
# Identificar erro

# Se for bug temporário, re-run manualmente
# Se for bug persistente, corrigir código e re-deploy
```

**Caso 3: Network issue**
```bash
# Testar conectividade
ping api.nba.com
ping basketball-reference.com

# Se DNS issue, verificar /etc/resolv.conf
# Se firewall issue, verificar UFW rules

# Se VPS issue, contactar provider
```

**Caso 4: Code bug**
```bash
# Ver logs detalhados
docker compose logs api --tail 200 | grep "ERROR"

# Identificar linha de código com erro
# Corrigir bug
# Re-deploy
docker compose down
docker compose up -d
```

**Verificação:**
```bash
# Verificar que dados foram atualizados
docker compose exec api python -c "from app.db import Session; from app.models import Game; print(Session().query(Game).order_by(Game.game_date.desc()).first().game_date)"
# Deve mostrar data de hoje

# Verificar logs de ingestão bem-sucedidos
docker compose logs api | grep "ingest" | tail 10
# Deve mostrar "Ingestion complete"
```

**Prevenção:**
- Alertas se dados > 2h sem update
- Rate limiting próprio no código de ingestão
- Fallback para fontes alternativas
- Monitorizar status de Prefect flows

---

## 4. BACKLOG DE RUNBOOKS

- [ ] RUNBOOK-005: High CPU (> 80% sustained)
- [ ] RUNBOOK-006: High Memory (OOM kills)
- [ ] RUNBOOK-007: Disk Full (> 90%)
- [ ] RUNBOOK-008: Telegram Bot Down
- [ ] RUNBOOK-009: Model Performance Drop (CLV cai)
- [ ] RUNBOOK-010: Odds Feed Failure

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[25_SOPs/INDEX]] → Procedimentos rotineiros
- [[27_Postmortems/INDEX]] → Análise pós-incidente
- [[10_Monitoring/INDEX]] → Monitorização e alertas
