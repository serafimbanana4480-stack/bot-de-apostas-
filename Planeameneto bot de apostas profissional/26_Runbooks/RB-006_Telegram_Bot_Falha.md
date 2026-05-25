# RB-006 — Telegram Bot Falha

**ID:** `RB-006` | **Severidade:** Medium | **Status:** #status/active

---

## 1. SINTOMAS

- Bot não responde a comandos
- Alertas não são enviados
- Timeout ao enviar mensagens

---

## 2. DIAGNÓSTICO DETALHADO

### 2.1 Verificar Container e Logs

```bash
# Verificar se container do bot está running
docker ps | grep telegram-bot

# Verificar logs recentes
docker logs --tail 50 telegram-bot

# Verificar estado do processo Python
ps aux | grep telegram
```

### 2.2 Testar API do Telegram

```bash
# Testar token (substituir <TOKEN> pelo token real)
TOKEN=$TELEGRAM_BOT_TOKEN
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" | python3 -m json.tool

# Resposta esperada:
# {
#   "ok": true,
#   "result": {
#     "id": 123456789,
#     "is_bot": true,
#     "first_name": "VBQ Bot",
#     "username": "vbq_bot"
#   }
# }

# Se "Unauthorized", o token é inválido
# Se "Too Many Requests", há rate limiting
```

### 2.3 Verificar Webhook (se usar webhook)

```bash
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | python3 -m json.tool

# Verificar se webhook URL está correto
# Verificar se há pending updates (> 100 pode indicar backlog)
```

### 2.4 Verificar Rede e Conectividade

```bash
# Testar DNS
dig api.telegram.org

# Testar conectividade HTTPS
curl -v https://api.telegram.org/bot${TOKEN}/getMe 2>&1 | grep -E "(Connected|SSL|HTTP)"

# Verificar se IP foi bloqueado (HTTP 429 = rate limit)
curl -s -o /dev/null -w "%{http_code}" "https://api.telegram.org/bot${TOKEN}/getMe"
```

### 2.5 Matriz de Causas

| Sintoma | Código HTTP | Causa |
|---------|------------|-------|
| `Unauthorized` | 401 | Token inválido ou revogado |
| `Too Many Requests` | 429 | Rate limit excedido |
| `Bad Gateway` | 502 | Problema na infraestrutura Telegram |
| Timeout | — | Firewall / DNS / rede local |
| `Webhook not set` | — | URL de webhook inválida ou HTTPS inválido |

---

## 3. RESOLUÇÃO PASSO A PASSO

### 3.1 Passo 1: Verificar e Renovar Token

```bash
# Verificar se token está configurado
echo $TELEGRAM_BOT_TOKEN | wc -c
# Deve retornar ~50 caracteres (formato: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)

# Se token vazio ou inválido, obter novo:
# 1. Ir a @BotFather no Telegram
# 2. /revoke <bot_name>
# 3. Copiar novo token
# 4. Atualizar .env
# 5. Reiniciar container
```

### 3.2 Passo 2: Resolver Rate Limiting (429)

```python
# Implementar exponential backoff no código do bot
import time
from functools import wraps

def rate_limit_backoff(max_retries=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except telegram.error.RetryAfter as e:
                    wait = e.retry_after
                    logger.warning(f"Rate limit. Aguardando {wait}s")
                    time.sleep(wait)
                except telegram.error.TimedOut:
                    wait = 2 ** attempt
                    logger.warning(f"Timeout. Retry {attempt+1}/{max_retries} em {wait}s")
                    time.sleep(wait)
            raise Exception("Max retries excedido")
        return wrapper
    return decorator
```

**Medida preventiva:** Limitar a 30 mensagens/segundo por chat. Para broadcasts, usar batch com delays.

### 3.3 Passo 3: Reconfigurar Webhook

```bash
# Deletar webhook antigo
curl -s "https://api.telegram.org/bot${TOKEN}/deleteWebhook"

# Setar novo webhook (exige HTTPS com certificado válido)
WEBHOOK_URL="https://api.seudominio.com/webhook"
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}"

# Verificar
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
```

**Alternativa:** Se não têm HTTPS válido, usar polling mode em vez de webhook:
```python
# No código do bot
updater.start_polling(drop_pending_updates=True)
```

### 3.4 Passo 4: Verificar Firewall e Rede

```bash
# Verificar se porta 443 está aberta para saída
nc -zv api.telegram.org 443

# Verificar regras de firewall
iptables -L -n | grep 443

# Se estiver atrás de proxy corporativo, configurar:
export HTTPS_PROXY=http://proxy.company.com:8080
```

---

## 4. PREVENÇÃO

### 4.1 Monitorização

```python
# Health check para o bot
def health_check() -> dict:
    try:
        me = bot.get_me()
        return {"status": "healthy", "bot_id": me.id, "username": me.username}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Endpoint FastAPI
@app.get("/health/telegram")
async def telegram_health():
    return health_check()
```

### 4.2 Configuração Recomendada

- **Mode:** Polling para desenvolvimento; Webhook para produção (menos latência)
- **Timeout:** 30s para conexão, 10s para leitura
- **Retries:** 3 tentativas com backoff exponencial
- **Queue:** Usar Redis como fila para envio de mensagens (evita rate limit)

---

## 5. VERIFICAÇÃO PÓS-RESOLUÇÃO

```bash
# 1. Bot responde a getMe
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" | grep '"ok": true'

# 2. Enviar mensagem de teste
CHAT_ID="<ID_DO_CHAT_TESTE>"
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=Teste pós-recuperação ✅"

# 3. Health check da API
curl -f http://localhost:8000/health/telegram || echo "Health check falhou"
```

**Critérios de Passagem:**
- [ ] `getMe` retorna `"ok": true`
- [ ] Mensagem de teste entregue em < 5s
- [ ] Health check retorna status `healthy`
- [ ] Logs não mostram erros de conexão nos últimos 5 min

---

## 6. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[19_Telegram_System/INDEX]] → Sistema Telegram
- [[19_Telegram_System/COMANDOS_BOT]] → Comandos do bot
- [[33_Alerting/ALERTAS_TELEGRAM]] → Sistema de alertas
