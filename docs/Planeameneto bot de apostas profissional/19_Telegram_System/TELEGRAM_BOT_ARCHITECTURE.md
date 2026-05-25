---
ID: TEL-006
tags: #status/active #telegram #architecture #components #design
---

# Arquitetura do Bot Telegram

## Objetivo
Documentar a arquitetura técnica completa do bot Telegram do sistema de value betting NBA, especificando todos os componentes, suas responsabilidades, fluxos de dados, padrões de comunicação, e pontos de integração. Esta arquitetura deve suportar escalabilidade até 10.000 subscritores, garantir 99.9% de uptime, e permitir manutenção iterativa sem downtime.

## O que faz
- Define a arquitetura em camadas: (1) Camada de API Gateway (Webhook Handler), (2) Camada de Serviços (Business Logic), (3) Camada de Acesso a Dados (PostgreSQL + Redis), (4) Camada de Integração Externa (Signal Engine, Payment Gateway, Analytics).
- Especifica o fluxo de atualizações do Telegram: webhook → validação → rate limiting → router → handler → database → response.
- Define padrões de concorrência: async/await para handlers de comandos, filas para broadcasts, e locks para operações críticas.
- Estabelece contratos entre componentes: interfaces, formatos de mensagem, códigos de erro, e SLAs internos.

## Porque existe
- **Escalabilidade**: Uma arquitetura monolítica colapsa quando o número de subscritores ultrapassa 1.000. A separação em camadas e o uso de filas permitem escalar horizontalmente.
- **Manutenibilidade**: Com múltiplos desenvolvedores a trabalhar no sistema, uma arquitetura bem definida evita acoplamento excessivo e permite alterações localizadas sem efeitos colaterais.
- **Resiliência**: Se um componente falhar (ex: PostgreSQL), a arquitetura deve permitir fallback ou graceful degradation em vez de falha total do sistema.
- **Testabilidade**: Componentes isolados podem ser testados unitariamente; a arquitetura define pontos de injeção de dependências para mocks.

## Arquitetura em Camadas

### Camada 1: API Gateway (Webhook Handler)
**Responsabilidades:**
- Receber webhooks do Telegram API
- Validar secret token (anti-spoofing)
- Rate limiting inicial (IP-based)
- Parsing de updates (JSON → objetos)
- Encaminhamento para fila de processamento

**Componentes:**
```python
class WebhookHandler:
    """
    Ponto de entrada para todos os updates do Telegram.
    Executa validação rápida e encaminha para fila.
    """
    def __init__(self, webhook_secret, queue_service):
        self.webhook_secret = webhook_secret
        self.queue = queue_service
        self.metrics = MetricsCollector()

    def handle_webhook(self, request):
        # 1. Validar secret
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != self.webhook_secret:
            self.metrics.increment("webhook_invalid_secret")
            return {"status": "REJECTED", "code": "INVALID_SECRET"}

        # 2. Validar payload
        try:
            update = json.loads(request.body)
        except:
            self.metrics.increment("webhook_invalid_json")
            return {"status": "REJECTED", "code": "INVALID_JSON"}

        # 3. Rate limiting por IP
        if not self.check_ip_rate_limit(request.remote_addr):
            self.metrics.increment("webhook_rate_limited")
            return {"status": "REJECTED", "code": "RATE_LIMITED"}

        # 4. Enfileirar para processamento
        self.queue.enqueue("telegram_updates", update)
        self.metrics.increment("webhook_accepted")

        return {"status": "ACCEPTED", "update_id": update["update_id"]}
```

**SLAs:**
- Tempo de resposta: < 50ms (percentil 95)
- Throughput: 1000 updates/segundo
- Disponibilidade: 99.95%

---

### Camada 2: Serviços (Business Logic)
**Responsabilidades:**
- Processamento de comandos (/start, /status, etc.)
- Formatação e envio de sinais
- Gestão de subscrições
- Orquestração de workflows complexos

**Componentes:**

#### 2.1 Command Router
```python
class CommandRouter:
    """
    Despacha comandos para os handlers apropriados.
    Implementa middleware para logging, auth, e rate limiting.
    """
    def __init__(self, handlers, middleware_chain):
        self.handlers = handlers
        self.middleware = middleware_chain

    async def route(self, update):
        # Executar middleware chain
        for mw in self.middleware:
            result = await mw.process(update)
            if result["stop"]:
                return result

        # Determinar handler
        if "message" in update and update["message"]["text"].startswith("/"):
            command = update["message"]["text"].split()[0]
            handler = self.handlers.get(command, self.handlers["/unknown"])
            return await handler.execute(update)
        elif "callback_query" in update:
            handler = self.handlers["callback_query"]
            return await handler.execute(update)
        else:
            handler = self.handlers["message"]
            return await handler.execute(update)
```

#### 2.2 Signal Dispatcher
```python
class SignalDispatcher:
    """
    Responsável por distribuir sinais para subscritores.
    Implementa batching, rate limiting, e retry logic.
    """
    def __init__(self, db, telegram_client, queue):
        self.db = db
        self.telegram = telegram_client
        self.queue = queue

    async def dispatch_signal(self, signal):
        # 1. Obter subscritores elegíveis
        subscribers = await self.db.get_active_subscribers(signal["tier"])

        # 2. Dividir em batches
        batches = self._split_batches(subscribers, batch_size=100)

        # 3. Enviar com rate limiting
        for batch in batches:
            await self._send_batch(batch, signal)
            await asyncio.sleep(5)  # 5s delay entre batches

        # 4. Registrar estatísticas
        await self.db.record_signal_dispatch(signal["id"], len(subscribers))

    async def _send_batch(self, batch, signal):
        message = self._format_signal(signal)
        tasks = [self.telegram.send_message(s.chat_id, message) for s in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. Tratar falhas
        for sub, result in zip(batch, results):
            if isinstance(result, Exception):
                await self.queue.enqueue("retry_failed_send", {
                    "subscriber_id": sub.id,
                    "signal_id": signal["id"],
                    "error": str(result)
                })
```

#### 2.3 Subscription Manager
```python
class SubscriptionManager:
    """
    Gerencia o ciclo de vida de subscrições.
    Sincroniza com payment gateway e grupos Telegram.
    """
    def __init__(self, db, payment_gateway, telegram_groups):
        self.db = db
        self.payment = payment_gateway
        self.groups = telegram_groups

    async def activate_subscription(self, user_id, plan, payment_id):
        # 1. Validar pagamento
        payment = await self.payment.verify(payment_id)
        if not payment["success"]:
            raise InvalidPaymentError(payment["error"])

        # 2. Criar subscrição
        subscription = await self.db.create_subscription({
            "user_id": user_id,
            "plan": plan,
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=30),
            "payment_id": payment_id
        })

        # 3. Adicionar a grupos Telegram
        await self.groups.add_user_to_groups(user_id, plan)

        # 4. Enviar mensagem de boas-vindas
        await self.send_welcome_message(user_id, plan)

        return subscription

    async def expire_subscription(self, subscription_id):
        # 1. Marcar como expirada
        await self.db.update_subscription(subscription_id, {"status": "EXPIRED"})

        # 2. Remover de grupos Telegram
        user_id = await self.db.get_subscription_user(subscription_id)
        await self.groups.remove_user_from_groups(user_id)

        # 3. Enviar notificação
        await self.send_expiration_notice(user_id)
```

---

### Camada 3: Acesso a Dados
**Responsabilidades:**
- Persistência de dados estruturados (PostgreSQL)
- Cache de dados quentes (Redis)
- Queries otimizadas com índices
- Transações ACID

**Componentes:**

#### 3.1 PostgreSQL Repository
```python
class SubscriptionRepository:
    """
    Acesso a dados de subscrições.
    Implementa cache-aside pattern para queries frequentes.
    """
    def __init__(self, db_pool, redis):
        self.db = db_pool
        self.redis = redis
        self.cache_ttl = 300  # 5 minutos

    async def get_active_subscription(self, user_id):
        # 1. Tentar cache
        cache_key = f"subscription:{user_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. Query PostgreSQL
        query = """
            SELECT * FROM subscriptions
            WHERE user_id = $1 AND status = 'ACTIVE' AND end_date > NOW()
            ORDER BY end_date DESC LIMIT 1
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, user_id)

        if not row:
            return None

        # 3. Atualizar cache
        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(dict(row)))

        return dict(row)

    async def create_subscription(self, data):
        query = """
            INSERT INTO subscriptions (user_id, plan, start_date, end_date, payment_id, status)
            VALUES ($1, $2, $3, $4, $5, 'ACTIVE')
            RETURNING *
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                data["user_id"],
                data["plan"],
                data["start_date"],
                data["end_date"],
                data["payment_id"]
            )

        # Invalidar cache
        await self.redis.delete(f"subscription:{data['user_id']}")

        return dict(row)
```

#### 3.2 Redis Cache Manager
```python
class RedisCacheManager:
    """
    Gerenciador centralizado de cache Redis.
    Implementa patterns: cache-aside, write-through, TTL.
    """
    def __init__(self, redis_client):
        self.redis = redis_client

    async def get(self, key):
        return await self.redis.get(key)

    async def set(self, key, value, ttl=None):
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)

    async def delete(self, key):
        await self.redis.delete(key)

    async def increment(self, key, amount=1):
        return await self.redis.incrby(key, amount)

    async def get_rate_limit(self, identifier, window_seconds, max_requests):
        """
        Implementa rate limiting com sliding window.
        """
        key = f"ratelimit:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        # Remover entradas antigas
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Contar requests na janela
        count = await self.redis.zcard(key)

        if count >= max_requests:
            return {"allowed": False, "count": count}

        # Adicionar request atual
        await self.redis.zadd(key, {str(now): now})
        await self.redis.expire(key, window_seconds)

        return {"allowed": True, "count": count + 1}
```

---

### Camada 4: Integração Externa
**Responsabilidades:**
- Comunicação com Signal Engine
- Integração com Payment Gateway
- Envio de métricas para Analytics

**Componentes:**

#### 4.1 Signal Engine Client
```python
class SignalEngineClient:
    """
    Cliente HTTP para o motor de geração de sinais.
    Implementa retry logic e circuit breaker.
    """
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    async def get_pending_signals(self):
        """
        Obtém sinais pendentes de envio.
        """
        with self.circuit_breaker:
            response = await self._request("GET", "/api/v1/signals/pending")
            return response["signals"]

    async def mark_signal_sent(self, signal_id, timestamp):
        """
        Marca sinal como enviado para evitar duplicações.
        """
        with self.circuit_breaker:
            await self._request("POST", f"/api/v1/signals/{signal_id}/sent", {
                "sent_at": timestamp
            })

    async def _request(self, method, endpoint, data=None):
        """
        Implementa retry logic com exponential backoff.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method, url, json=data, headers=headers, timeout=10
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                if attempt == 2:
                    raise SignalEngineError(f"Failed after 3 attempts: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

#### 4.2 Payment Gateway Client
```python
class PaymentGatewayClient:
    """
    Cliente abstrato para gateways de pagamento (Stripe, PayPal).
    Implementa factory pattern para múltiplos providers.
    """
    def __init__(self, provider, config):
        self.provider = provider
        self.config = config
        self.client = self._create_client()

    def _create_client(self):
        if self.provider == "stripe":
            import stripe
            stripe.api_key = self.config["api_key"]
            return stripe
        elif self.provider == "paypal":
            # Implementar PayPal client
            pass

    async def create_payment_link(self, amount, currency, metadata):
        """
        Cria link de pagamento para subscrição.
        """
        if self.provider == "stripe":
            price = await self.client.Price.create(
                unit_amount=int(amount * 100),  # Stripe usa centavos
                currency=currency.lower(),
                recurring={"interval": "month"},
                product_data={"name": f"Subscrição {metadata['plan']}"}
            )

            session = await self.client.CheckoutSession.create(
                payment_method_types=["card"],
                line_items=[{"price": price.id, "quantity": 1}],
                mode="subscription",
                success_url=self.config["success_url"],
                cancel_url=self.config["cancel_url"],
                metadata=metadata
            )

            return {"payment_url": session.url, "payment_id": session.id}

    async def verify_payment(self, payment_id):
        """
        Verifica se um pagamento foi concluído com sucesso.
        """
        if self.provider == "stripe":
            session = await self.client.CheckoutSession.retrieve(payment_id)
            return {
                "success": session.payment_status == "paid",
                "amount": session.amount_total / 100,
                "currency": session.currency.upper()
            }
```

---

## Fluxo de Dados

### Fluxo 1: Receção e Processamento de Comando
```
1. Telegram API → Webhook (POST)
2. WebhookHandler → Valida secret + IP
3. WebhookHandler → Enfileira update
4. Worker → Desenfileira update
5. CommandRouter → Executa middleware
6. CommandRouter → Despacha para handler
7. Handler → Consulta PostgreSQL/Redis
8. Handler → Formata resposta
9. Telegram API → Envia mensagem
10. Handler → Registra metrics/logs
```

### Fluxo 2: Envio de Sinal
```
1. Signal Engine → Gera novo sinal
2. Signal Dispatcher → Consulta subscritores ativos
3. Signal Dispatcher → Formata mensagem
4. Signal Dispatcher → Divide em batches
5. Signal Dispatcher → Envia batch 1
6. Telegram API → Confirma envio
7. Signal Dispatcher → Aguarda 5s
8. Signal Dispatcher → Envia batch 2
9. ...
10. Signal Dispatcher → Marca sinal como enviado
```

### Fluxo 3: Ativação de Subscrição
```
1. Subscritor → Clica link pagamento
2. Payment Gateway → Processa pagamento
3. Webhook Payment Gateway → Notifica backend
4. Subscription Manager → Verifica pagamento
5. Subscription Manager → Cria subscrição
6. Subscription Manager → Adiciona a grupos Telegram
7. Subscription Manager → Envia boas-vindas
8. Analytics → Registra evento de conversão
```

---

## Thresholds e Tabelas

| Componente | Throughput | Latência P95 | Disponibilidade | Escalabilidade |
|------------|------------|--------------|-----------------|----------------|
| Webhook Handler | 1000 req/s | 50ms | 99.95% | Horizontal (N instances) |
| Command Router | 500 cmd/s | 200ms | 99.9% | Horizontal |
| Signal Dispatcher | 10 sinais/min | 5s/batch | 99.9% | Vertical (mais workers) |
| PostgreSQL | 1000 queries/s | 100ms | 99.95% | Vertical + read replicas |
| Redis | 10000 ops/s | 10ms | 99.99% | Cluster |

| Tipo de Operação | Prioridade | SLA | Retry Policy |
|------------------|------------|-----|--------------|
| Envio de sinal | Alta | < 30s para 100% subscritores | 3 tentativas, backoff exponencial |
| Comando de utilizador | Média | < 2s resposta | 1 tentativa |
| Ativação subscrição | Alta | < 10s | 3 tentativas |
| Broadcast admin | Baixa | Best effort | 5 tentativas |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Telegram API downtime | Média | Alto | Fallback para fila + alerta ops |
| PostgreSQL crash | Baixa | Crítico | Read replicas + backup hourly |
| Redis memory overflow | Baixa | Alto | Max memory policy + alerta |
| Payment webhook perdido | Baixa | Alto | Idempotency + reprocessamento |
| Rate limit Telegram | Média | Médio | Throttle adaptativo + múltiplos bots |

---

## Links Cruzados

- [[BOT_TELEGRAM_CONFIG]] → Configuração específica do bot
- [[COMANDOS_BOT]] → Especificação de comandos
- [[FORMATO_SINAIS]] → Templates de mensagens
- [[SEGURANCA_TELEGRAM]] → Camada de segurança
- [[13_Infrastructure/VPS_CONFIGURACAO]] → Infraestrutura de hosting