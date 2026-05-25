# RB-001 — Feed de Dados Offline

**ID:** `RB-001` | **Severidade:** Critical | **Status:** #status/active

---

## 1. SINTOMAS

- API de odds retorna erros 5xx
- Timeout ao conectar com API
- Sem dados novos por > 30min

---

## 2. DIAGNÓSTICO DETALHADO

### 2.1 Verificar API Externa

```bash
# Testar Betfair API (Exchange)
curl -s "https://api.betfair.com/exchange/betting/json-rpc/v1" \
  -H "X-Application: ${BETFAIR_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEventTypes", "params": {}, "id": 1}'

# Testar The Odds API
curl -s "https://api.the-odds-api.com/v4/sports/?apiKey=${ODDS_API_KEY}"

# Verificar status de saúde da API (se disponível)
curl -s "https://status.betfair.com/api/v2/status.json"
```

### 2.2 Verificar Serviço Interno

```bash
# Verificar se container do feed está running
docker ps | grep odds-feed

# Verificar logs do feed
docker logs --tail 50 odds-feed

# Verificar se processo está ativo
ps aux | grep odds_ingestion

# Verificar conectividade de rede do container
docker exec odds-feed curl -s https://api.betfair.com
```

### 2.3 Verificar Banco de Dados

```bash
# Última ingestão de odds
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    source,
    MAX(ingested_at) as last_ingestion,
    NOW() - MAX(ingested_at) as time_since
FROM raw_odds
GROUP BY source;
"

# Verificar se há jogos hoje sem odds
SELECT g.game_id, g.game_date
FROM games g
LEFT JOIN raw_odds o ON g.game_id = o.game_id
WHERE g.game_date = CURRENT_DATE
AND o.odds_id IS NULL;
```

### 2.4 Matriz de Causas

| Sintoma | Causa Provável | Verificação |
|---------|---------------|-------------|
| HTTP 401/403 | Credenciais inválidas | Verificar BETFAIR_APP_KEY |
| HTTP 429 | Rate limit excedido | Verificar headers de rate limit |
| Timeout | Firewall / DNS / rede | `curl` de dentro do container |
| Sem dados mas API OK | Erro no parser | Logs do feed |
| Container parado | Crash / OOM | `docker ps` e `docker logs` |

---

## 3. RESOLUÇÃO PASSO A PASSO

### 3.1 Passo 1: Verificar Credenciais

```bash
# Verificar se APP_KEY está configurada
echo $BETFAIR_APP_KEY | wc -c
# Deve retornar ~30 caracteres

# Verificar se session token é válido
curl -s "https://identitysso.betfair.com/api/login" \
  -H "X-Application: ${BETFAIR_APP_KEY}" \
  -d "username=${BETFAIR_USERNAME}&password=${BETFAIR_PASSWORD}"

# Se falhar, renovar credenciais na Betfair Developer Portal
```

### 3.2 Passo 2: Resolver Rate Limiting

```bash
# Verificar headers de rate limit
curl -s -I "https://api.betfair.com/exchange/betting/json-rpc/v1" \
  -H "X-Application: ${BETFAIR_APP_KEY}"

# Se X-RateLimit-Remaining ≈ 0, aguardar cooldown
# Betfair: 20 req/seg para dados de mercado
```

**Implementar backoff no código:**
```python
import time
from functools import wraps

def rate_limit_backoff(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except BetfairAPIError as e:
                    if e.status_code == 429:
                        wait = 2 ** attempt
                        logger.warning(f"Rate limit, aguardando {wait}s")
                        time.sleep(wait)
                    else:
                        raise
            raise Exception("Max retries excedido")
        return wrapper
    return decorator
```

### 3.3 Passo 3: Restart do Serviço

```bash
# Restart suave
docker compose restart odds-feed

# Se persistir, restart completo
docker compose stop odds-feed
docker compose rm -f odds-feed
docker compose up -d odds-feed

# Verificar se iniciou corretamente
sleep 10
docker logs --tail 20 odds-feed
```

### 3.4 Passo 4: Fallback para Outra Fonte

Se Betfair está indisponível:
1. Ativar feed secundário (The Odds API / Pinnacle)
2. Ajustar configuração: `PRIMARY_FEED=odds_api`
3. Reduzir frequência de polling para não exceder rate limits

```bash
# Configurar feed secundário
export PRIMARY_FEED=odds_api
export ODDS_API_KEY=<sua_chave>
docker compose restart odds-feed
```

---

## 4. VERIFICAÇÃO PÓS-RESOLUÇÃO

```bash
# 1. Feed está running
docker ps | grep odds-feed

# 2. Última ingestão < 15 minutos
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT NOW() - MAX(ingested_at) as minutes_since
FROM raw_odds;
"
# Esperado: < 15 min

# 3. Sem erros nos logs
docker logs --tail 20 odds-feed | grep -i "error\|fail" || echo "Sem erros"

# 4. Jogos de hoje têm odds
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT COUNT(*) as jogos_com_odds
FROM games g
JOIN raw_odds o ON g.game_id = o.game_id
WHERE g.game_date = CURRENT_DATE;
"
# Esperado: > 0
```

**Critérios de Passagem:**
- [ ] Container odds-feed em estado `Up`
- [ ] Última ingestão < 15 minutos
- [ ] Sem erros de API nos logs
- [ ] Jogos do dia têm odds associadas

---

## 5. PREVENÇÃO

### 5.1 Monitorização Proativa

```yaml
# prometheus.yml
rules:
  - alert: OddsFeedStalled
    expr: time() - odds_last_ingestion_timestamp > 1800
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Odds feed stalled for 30+ minutes"
      runbook_url: "https://wiki.internal/RB-001"

  - alert: OddsFeedRateLimit
    expr: rate(api_rate_limit_hits_total[5m]) > 0
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "API rate limit being hit"
```

### 5.2 Redundância

- Configurar feed primário (Betfair) + secundário (The Odds API)
- Se primário falha, sistema automaticamente usa secundário
- Rate limits diferentes permitem maior resiliência

---

## 6. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[04_Data_Engineering/INGESTAO_ODDS]] → Ingestão de odds
- [[14_APIs/BETFAIR_API]] → API Betfair
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Thresholds de alertas
