# REDIS_CONFIG — Configuração do Cache e Filas

**ID:** `INF-002` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Configurar Redis para cache de odds em memória, filas de tarefas assíncronas, e rate limiting. Redis é crítico para latência baixa e processamento concorrente.

---

## 2. INSTALAÇÃO

```bash
# Ubuntu/Debian
apt install redis-server

# Configuração básica
vim /etc/redis/redis.conf
```

---

## 3. CONFIGURAÇÃO DE PRODUÇÃO

### 3.1 redis.conf

```conf
# Networking
bind 127.0.0.1
port 6379
protected-mode yes

# Persistência (RDB + AOF para segurança)
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Memória
maxmemory 2gb
maxmemory-policy allkeys-lru

# Segurança
requirepass ${REDIS_PASSWORD}
rename-command FLUSHDB ""
rename-command FLUSHALL ""

# Logging
loglevel notice
logfile /var/log/redis/redis.log
```

### 3.2 Variáveis de Ambiente

```bash
# .env
REDIS_PASSWORD=senha_super_segura_aleatoria
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
```

---

## 4. USOS NO SISTEMA

### 4.1 Cache de Odds em Memória

```python
import redis
import json

r = redis.Redis(host='127.0.0.1', port=6379, password=REDIS_PASSWORD)

# Guardar odd com TTL de 5 minutos
def cache_odd(game_id: str, market: str, odd: float, timestamp: int):
    key = f"odd:{game_id}:{market}"
    value = json.dumps({"odd": odd, "timestamp": timestamp})
    r.setex(key, 300, value)  # 5 minutos TTL

# Recuperar odd
def get_cached_odd(game_id: str, market: str) -> dict:
    key = f"odd:{game_id}:{market}"
    value = r.get(key)
    return json.loads(value) if value else None
```

### 4.2 Fila de Tarefas (Sinais)

```python
# Producer: Motor de value
def publish_signal(signal: dict):
    r.lpush("signals:queue", json.dumps(signal))

# Consumer: Telegram bot
def consume_signal():
    signal = r.brpop("signals:queue", timeout=30)
    if signal:
        return json.loads(signal[1])
    return None
```

### 4.3 Rate Limiting

```python
# Limitar requisições à API por IP
def check_rate_limit(ip: str, limit: int = 100, window: int = 60):
    key = f"ratelimit:{ip}"
    current = r.incr(key)
    if current == 1:
        r.expire(key, window)
    return current <= limit
```

### 4.4 Locking Distribuído

```python
# Evitar processamento duplicado
def acquire_lock(lock_name: str, timeout: int = 10):
    key = f"lock:{lock_name}"
    return r.set(key, "1", nx=True, ex=timeout)

def release_lock(lock_name: str):
    key = f"lock:{lock_name}"
    r.delete(key)
```

---

## 5. MONITORIZAÇÃO

### 5.1 Métricas Importantes

```bash
# Memória usada
redis-cli INFO memory | used_memory_human

# Conexões ativas
redis-cli INFO clients | connected_clients

# Comandos por segundo
redis-cli INFO stats | instantaneous_ops_per_sec

# Taxa de hits/misses do cache
redis-cli INFO stats | keyspace_hits
redis-cli INFO stats | keyspace_misses
```

### 5.2 Alertas Prometheus

```yaml
# prometheus.yml
- job_name: 'redis'
  static_configs:
    - targets: ['localhost:9121']  # redis_exporter
```

---

## 6. BACKUP E RESTORE

### 6.1 Backup Manual

```bash
# Snapshot RDB
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backups/redis_$(date +%Y%m%d).rdb

# Backup AOF
cp /var/lib/redis/appendonly.aof /backups/redis_aof_$(date +%Y%m%d).aof
```

### 6.2 Restore

```bash
# Parar Redis
systemctl stop redis

# Restaurar
cp /backups/redis_20260513.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# Iniciar Redis
systemctl start redis
```

---

## 7. SEGURANÇA

- ✅ Redis nunca exposto para internet (127.0.0.1 only)
- ✅ Password forte (32+ caracteres, aleatório)
- ✅ Comandos perigosos desativados (FLUSHDB, FLUSHALL)
- ✅ TLS para conexões remotas (se necessário no futuro)
- ✅ Firewall UFW bloqueia porta 6379 externamente

---

## 8. ESCALABILIDADE

### Quando escalar:
- Memória > 80% consistentemente
- Latência > 10ms para operações GET
- > 10.000 operações/segundo

### Opções de escala:
1. **Vertical:** Upgrade VPS para mais RAM
2. **Horizontal:** Redis Cluster (múltiplas instâncias)
3. **Managed:** Redis Cloud / AWS ElastiCache (futuro)

---

## 9. TROUBLESHOOTING

### Problema: Redis out of memory
```bash
# Verificar memória
redis-cli INFO memory

# Limpar chaves expiradas
redis-cli --scan --pattern "temp:*" | xargs redis-cli DEL
```

### Problema: Conexões recusadas
```bash
# Verificar se está a correr
systemctl status redis

# Verificar logs
tail -f /var/log/redis/redis.log

# Verificar firewall
ufw status
```

---

## 10. LINKS CRUZADOS

- [[13_Infrastructure/INDEX]] ← Secção mãe
- [[VPS_CONFIGURACAO]] → Configuração do servidor base
- [[15_Database/INDEX]] → PostgreSQL (BD principal)