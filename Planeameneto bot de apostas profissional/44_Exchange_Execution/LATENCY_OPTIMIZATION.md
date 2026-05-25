# LATENCY_OPTIMIZATION — Otimização de Latência e Proximity

**ID:** `EXE-002` | **Fase:** #phase/7-12 | **Owner:** DevOps Lead + Network Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Minimizar latência de ponta a ponta (sinal → execução) para maximizar edge em mercados rápidos. Latência é o inimigo de CLV - cada milissegundo conta.

**Target:** < 500ms de latência média de execução (sinal → confirmação Betfair)

---

## 2. ANATOMIA DA LATÊNCIA

### 2.1 Breakdown de Latência

```
┌─────────────────────────────────────────────────────────────────┐
│ SINAL → EXECUÇÃO: ANATOMIA DA LATÊNCIA                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1. GERAÇÃO DE SINAL (50-100ms)                                   │
│    → Processamento de dados                                     │
│    → Inferência do modelo                                       │
│    → Validação de filtros                                       │
│                                                                  │
│ 2. TRANSMISSÃO (10-50ms)                                        │
│    → Serialização                                               │
│    → Rede interna                                               │
│    → Processamento de fila                                      │
│                                                                  │
│ 3. PREPARAÇÃO DE ORDEM (10-30ms)                                │
│    → Validação de risco                                         │
│    → Verificação de liquidez                                    │
│    → Formatação da ordem                                        │
│                                                                  │
│ 4. REDE BETFAIR (20-100ms)                                      │
│    → Latência de rede (VPS → Betfair)                           │
│    → TLS handshake                                               │
│    → API processing                                             │
│                                                                  │
│ 5. EXECUÇÃO BETFAIR (10-50ms)                                   │
│    → Matching engine                                             │
│    → Liquidez check                                              │
│    → Order placement                                             │
│                                                                  │
│ 6. RESPOSTA (20-100ms)                                          │
│    → API response                                                │
│    → Rede Betfair → VPS                                          │
│    → Desserialização                                             │
│                                                                  │
│ 7. CONFIRMAÇÃO (10-30ms)                                        │
│    → Processamento de resposta                                  │
│    → Atualização de BD                                           │
│    → Notificação                                                 │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ TOTAL: 130-460ms (ideal: < 300ms)                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Bottlenecks Comuns

| Componente | Latência Típica | Bottleneck | Otimização |
|------------|-----------------|------------|------------|
| Geração de sinal | 50-100ms | GPU/CPU limitado | GPU, otimização de código |
| Rede interna | 10-50ms | Switch/roteador | Rede dedicada, 10Gbps |
| API Betfair | 50-200ms | Distância geográfica | Proximity hosting |
| TLS handshake | 20-50ms | Criptografia | Keep-alive, session reuse |
| Processamento de fila | 10-30ms | Blocking I/O | Async, event-driven |

---

## 3. ESTRATÉGIAS DE OTIMIZAÇÃO

### 3.1 Proximity Hosting

**Conceito:** Hospedar servidor o mais próximo possível dos servidores Betfair.

**Opções:**

| Localização | Latência para Betfair | Custo | Disponibilidade |
|-------------|----------------------|-------|-----------------|
| Londres (UK) | 10-20ms | Alto | Excelente |
| Frankfurt (DE) | 20-30ms | Médio | Excelente |
| Amsterdã (NL) | 25-35ms | Médio | Excelente |
| Lisboa (PT) | 40-50ms | Baixo | Boa |
| São Paulo (BR) | 150-200ms | Baixo | Boa |

**Recomendação:** Londres ou Frankfurt para latência mínima.

**Implementação:**
```bash
# Exemplo: Deploy em AWS Londres
aws ec2 run-instances \
  --image-id ami-xxxx \
  --instance-type c5.large \
  --region eu-west-2 \
  --placement AvailabilityZone=eu-west-2a
```

### 3.2 Otimização de Rede

**Configuração de TCP:**
```bash
# /etc/sysctl.conf
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_low_latency = 1
net.ipv4.tcp_fastopen = 3
net.core.netdev_max_backlog = 5000
```

**Keep-alive de conexões:**
```python
import requests

session = requests.Session()
session.mount('https://', requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=10,
    max_retries=3,
    pool_block=False
))

# Configurar keep-alive
session.headers.update({
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=30, max=100'
})
```

### 3.3 Otimização de Código

**Async I/O:**
```python
import asyncio
import aiohttp

async def place_order_async(signal, session):
    """Coloca ordem de forma assíncrona"""
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/placeOrders",
        "params": {...},
        "id": 1
    }

    async with session.post(url, json=payload) as response:
        return await response.json()

async def execute_signals_async(signals):
    """Executa múltiplos sinais em paralelo"""
    async with aiohttp.ClientSession() as session:
        tasks = [place_order_async(s, session) for s in signals]
        results = await asyncio.gather(*tasks)
        return results
```

**Cache de liquidez:**
```python
from functools import lru_cache
import time

class LiquidityCache:
    def __init__(self, ttl=5):
        self.cache = {}
        self.ttl = ttl

    def get_liquidity(self, market_id, selection_id):
        """Obtém liquidez do cache se disponível"""
        key = f"{market_id}_{selection_id}"

        if key in self.cache:
            cached, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return cached

        # Cache miss - buscar da API
        liquidity = self._fetch_liquidity(market_id, selection_id)
        self.cache[key] = (liquidity, time.time())
        return liquidity
```

### 3.4 Otimização de Banco de Dados

**Connection Pooling:**
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:pass@localhost/db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**Índices otimizados:**
```sql
-- Índice para queries frequentes
CREATE INDEX idx_orders_signal_id ON orders(signal_id);
CREATE INDEX idx_orders_timestamp ON orders(execution_timestamp);
CREATE INDEX idx_orders_status ON orders(status);

-- Índice composto para queries complexas
CREATE INDEX idx_orders_signal_timestamp ON orders(signal_id, execution_timestamp);
```

**Query otimizada:**
```python
# Ruim - N+1 queries
for signal in signals:
    order = db.query(Order).filter_by(signal_id=signal.id).first()

# Bom - Single query
signal_ids = [s.id for s in signals]
orders = db.query(Order).filter(Order.signal_id.in_(signal_ids)).all()
order_map = {o.signal_id: o for o in orders}
```

---

## 4. MONITORIZAÇÃO DE LATÊNCIA

### 4.1 Métricas Chave

| Métrica | Target | Warning | Critical |
|---------|--------|---------|----------|
| Latência média | < 300ms | > 500ms | > 1s |
| Latência P95 | < 500ms | > 1s | > 2s |
| Latência P99 | < 1s | > 2s | > 5s |
| Jitter | < 50ms | > 100ms | > 200ms |
| Taxa de timeout | < 0.1% | > 1% | > 5% |

### 4.2 Sistema de Monitorização

```python
import time
from collections import deque

class LatencyMonitor:
    def __init__(self, window_size=1000):
        self.window_size = window_size
        self.latencies = deque(maxlen=window_size)

    def record_latency(self, latency_ms):
        """Registra latência"""
        self.latencies.append(latency_ms)

    def get_metrics(self):
        """Calcula métricas"""
        if not self.latencies:
            return None

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        return {
            'count': n,
            'mean': sum(sorted_latencies) / n,
            'min': sorted_latencies[0],
            'max': sorted_latencies[-1],
            'p50': sorted_latencies[n // 2],
            'p95': sorted_latencies[int(n * 0.95)],
            'p99': sorted_latencies[int(n * 0.99)],
            'std': self._stddev(sorted_latencies)
        }

    def _stddev(self, values):
        """Calcula desvio padrão"""
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
```

### 4.3 Tracing Distribuído

```python
import opentelemetry
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configurar tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("execute_signal")
def execute_signal(signal):
    """Executa sinal com tracing"""
    with tracer.start_as_current_span("generate_signal"):
        signal = generate_signal()

    with tracer.start_as_current_span("validate_risk"):
        validate_risk(signal)

    with tracer.start_as_current_span("place_order"):
        response = place_order(signal)

    return response
```

---

## 5. ARQUITETURA DE BAIXA LATÊNCIA

### 5.1 Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│ ARQUITETURA DE BAIXA LATÊNCIA                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Data Source │───→│ Ingestion   │───→│ Model       │        │
│  │ (NBA API)   │    │ (Kafka)     │    │ (GPU)       │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                            ↓                    ↓               │
│                    ┌─────────────┐    ┌─────────────┐        │
│                    │ Feature     │───→│ Signal      │        │
│                    │ Store       │    │ Generator   │        │
│                    │ (Redis)     │    └─────────────┘        │
│                    └─────────────┘            ↓               │
│                                              │                │
│                            ┌───────────────┐ │                │
│                            │ Message Queue │←┘                │
│                            │ (ZeroMQ)      │                  │
│                            └───────────────┘                  │
│                                     ↓                           │
│                            ┌───────────────┐                  │
│                            │ Order Engine  │                  │
│                            │ (Async)       │                  │
│                            └───────────────┘                  │
│                                     ↓                           │
│                            ┌───────────────┐                  │
│                            │ Betfair API   │                  │
│                            │ (London)      │                  │
│                            └───────────────┘                  │
│                                     ↓                           │
│                            ┌───────────────┐                  │
│                            │ Database      │                  │
│                            │ (PostgreSQL)  │                  │
│                            └───────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Tecnologias Recomendadas

| Componente | Tecnologia | Justificação |
|------------|-----------|--------------|
| Message Queue | ZeroMQ / NATS | Ultra-baixa latência (< 1ms) |
| Cache | Redis | In-memory, nanosegundos |
| Banco de Dados | PostgreSQL + TimescaleDB | Relacional + time-series otimizado |
| API Client | aiohttp / httpx | Async, eficiente |
| Tracing | Jaeger / OpenTelemetry | Observabilidade |
| Monitorização | Prometheus + Grafana | Métricas em tempo real |

---

## 6. TESTES DE LATÊNCIA

### 6.1 Benchmark de Latência

```python
import time
import statistics

def benchmark_latency(n=1000):
    """Benchmark de latência de execução"""
    latencies = []

    for i in range(n):
        start = time.perf_counter()

        # Simular execução completa
        signal = generate_test_signal()
        response = place_order(signal)

        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

    return {
        'mean': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'stdev': statistics.stdev(latencies),
        'min': min(latencies),
        'max': max(latencies),
        'p95': sorted(latencies)[int(n * 0.95)],
        'p99': sorted(latencies)[int(n * 0.99)],
    }
```

### 6.2 Test de Stress

```python
def stress_test(rps=100, duration=60):
    """Test de stress - requests por segundo"""
    import threading
    import queue

    results = queue.Queue()
    start_time = time.time()

    def worker():
        while time.time() - start_time < duration:
            lat = benchmark_latency(1)['mean']
            results.put(lat)

    threads = [threading.Thread(target=worker) for _ in range(rps)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Analisar resultados
    latencies = []
    while not results.empty():
        latencies.append(results.get())

    return {
        'mean': statistics.mean(latencies),
        'p95': sorted(latencies)[int(len(latencies) * 0.95)],
        'p99': sorted(latencies)[int(len(latencies) * 0.99)],
    }
```

---

## 7. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Seção mãe
- [[44_Exchange_Execution/BETFAIR_EXECUTION]] → Execução automática
- [[13_Infrastructure/INDEX]] → Infraestrutura geral
- [[09_Execution_System/INDEX]] → Sistema de execução geral