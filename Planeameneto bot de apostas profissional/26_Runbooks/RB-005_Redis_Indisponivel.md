# RB-005 — Redis Indisponível

**ID:** `RB-005` | **Severidade:** High | **Status:** #status/active

---

## 1. SINTOMAS

- Erro ao conectar Redis
- Cache não funcionando
- Filas não processando

---

## 2. DIAGNÓSTICO DETALHADO

### 2.1 Verificar Container e Conectividade

```bash
# Verificar container
docker ps | grep redis
docker logs --tail 30 redis

# Testar conexão
docker exec redis redis-cli ping
# Esperado: PONG

# Verificar info
docker exec redis redis-cli INFO

# Verificar uso de memória
docker exec redis redis-cli INFO memory | grep -E "used_memory|maxmemory"
```

### 2.2 Diagnóstico de Memory

```bash
# Verificar se atingiu maxmemory
docker exec redis redis-cli INFO memory | grep used_memory_human

# Verificar política de evicção
docker exec redis redis-cli CONFIG GET maxmemory-policy

# Verificar keys (se muitas, pode estar em memory pressure)
docker exec redis redis-cli DBSIZE

# Verificar se há evicted keys
docker exec redis redis-cli INFO stats | grep evicted_keys
```

### 2.3 Diagnóstico de Persistência

```bash
# Verificar último save
docker exec redis redis-cli LASTSAVE

# Verificar estado de BGSAVE
docker exec redis redis-cli INFO persistence | grep -E "rdb_last_bgsave_status|aof_last_write_status"

# Verificar tamanho do RDB
ls -lh /var/lib/redis/dump.rdb
```

### 2.4 Matriz de Causas

| Sintoma | Causa Provável | Verificação |
|---------|---------------|-------------|
| `PING` timeout | Container parado | `docker ps` |
| `OOM command not allowed` | Memory full | `used_memory` ≈ `maxmemory` |
| Keys desaparecendo | Evicção ativa | `evicted_keys` > 0 |
| Dados não persistentes | AOF/RDB desativado | `INFO persistence` |
| Latência alta | Big keys / slow queries | `SLOWLOG GET 10` |

---

## 3. RESOLUÇÃO PASSO A PASSO

### 3.1 Passo 1: Restart do Container

```bash
docker compose restart redis
sleep 5
docker exec redis redis-cli ping
```

### 3.2 Passo 2: Resolver Memory Pressure

```bash
# Verificar uso atual
MEM_USAGE=$(docker exec redis redis-cli INFO memory | grep used_memory: | cut -d: -f2)
MAX_MEM=$(docker exec redis redis-cli INFO memory | grep maxmemory: | cut -d: -f2)

echo "Usado: $MEM_USAGE / Max: $MAX_MEM"

# Se > 90%, identificar keys grandes
docker exec redis redis-cli --bigkeys

# Limpar cache de features antigos (manter últimas 24h)
docker exec redis redis-cli EVAL "
  local keys = redis.call('keys', 'features:*')
  for i=1,#keys do redis.call('del', keys[i]) end
  return #keys
" 0

# Aumentar maxmemory temporariamente (se VPS tem RAM disponível)
docker exec redis redis-cli CONFIG SET maxmemory $((512 * 1024 * 1024))  # 512MB
```

### 3.3 Passo 3: Rebuild Cache

```bash
# Se cache está corrompido, limpar e deixar aplicação repopular
docker exec redis redis-cli FLUSHDB

# Reiniciar aplicação para repopular cache
docker compose restart api
```

**⚠️ Atenção:** `FLUSHDB` apaga TODOS os dados do Redis. Só usar se confirmar que os dados podem ser reconstruídos (cache, não dados persistentes).

### 3.4 Passo 4: Verificar Persistência

```bash
# Forçar snapshot manual
docker exec redis redis-cli BGSAVE

# Verificar se salvou corretamente
docker exec redis redis-cli INFO persistence | grep rdb_last_bgsave_status
```

---

## 4. PREVENÇÃO

```yaml
# docker-compose.yml - configuração recomendada
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  sysctls:
    - net.core.somaxconn=65535
  restart: unless-stopped
```

**Explicação:** `allkeys-lru` evita keys antigas automaticamente quando memory está cheia. Isto previne erros de "OOM command not allowed".

---

## 5. VERIFICAÇÃO PÓS-RESOLUÇÃO

```bash
# 1. Redis responde PONG
docker exec redis redis-cli ping

# 2. Memory saudável
USED=$(docker exec redis redis-cli INFO memory | grep used_memory_human | cut -d: -f2)
MAX=$(docker exec redis redis-cli INFO memory | grep maxmemory_human | cut -d: -f2)
echo "Redis: $USED / $MAX"

# 3. API consegue usar cache
curl -f http://localhost:8000/health/cache || echo "Cache API falhou"

# 4. Sem erros nos logs
docker logs --tail 20 redis | grep -i "error\|fatal" || echo "Sem erros"
```

**Critérios de Passagem:**
- [ ] `redis-cli ping` retorna `PONG`
- [ ] `used_memory` < `maxmemory` × 0.9
- [ ] API responde em < 500ms (cache funcional)
- [ ] Nenhum erro de evicção nos últimos 5 min

---

## 6. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[10_Monitoring/DASHBOARD_TECNICO]] → Dashboard Redis
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Alertas de Redis
