# SERVICO_FEATURES — API de Serviço de Features

**ID:** `FEAT-004` | **Fase:** #phase/1-6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar uma API robusta e performática para servir features em tempo real aos consumidores (modelos de ML, dashboards, sistemas de alertas). A API deve garantir baixa latência, alta disponibilidade e consistência entre ambientes de treino e produção.

---

## 2. CONTEXTO

O Feature Service é a interface entre o Feature Store e os consumidores. Em value betting, onde decisões precisam ser tomadas rapidamente antes dos jogos, a API deve:

- **Servir features em <10ms** para inferência em tempo real
- **Suportar múltiplos consumidores** simultaneamente
- **Garantir consistência** com features usadas no treino
- **Fornecer metadados** sobre features (versão, timestamp)
- **Implementar caching** para reduzir latência
- **Fornecer fallback** em caso de falhas

Sem uma API bem desenhada, cada consumidor implementaria sua própria lógica de acesso, levando a inconsistências, duplicação de código e dificuldade de manutenção.

---

## 3. ARQUITETURA DA API

### 3.1 Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    FEATURE SERVICE API                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  REST API   │    │  GraphQL    │    │  gRPC       │    │
│  │  (FastAPI)  │    │  (Optional) │    │  (Internal) │    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            │                               │
│                            ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API Gateway / Router                    │   │
│  │  (Rate limiting, Auth, Logging, Metrics)            │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Feature Service Layer                   │   │
│  │  (Business logic, validation, transformation)       │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│         ┌──────────────┴──────────────┐                    │
│         ▼                             ▼                    │
│  ┌─────────────┐              ┌─────────────┐              │
│  │  Cache      │              │  Feature    │              │
│  │  (Redis)    │              │  Store      │              │
│  │             │              │  (PostgreSQL)│              │
│  └─────────────┘              └─────────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Stack Tecnológico

| Componente | Escolha | Justificação |
|------------|---------|--------------|
| API Framework | FastAPI | Alto desempenho, async/await, OpenAPI automático |
| Cache | Redis | Baixa latência, TTL automático |
| Database | PostgreSQL | Fonte de verdade, queries complexas |
| Auth | JWT + API Keys | Simples, sem estado |
| Rate Limiting | Redis + Token Bucket | Escalável, distribuído |
| Monitoring | Prometheus + Grafana | Métricas detalhadas |
| Logging | Structlog | Logs estruturados, fácil parsing |

---

## 4. API REST (FASTAPI)

### 4.1 Endpoints Principais

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging

app = FastAPI(
    title="Feature Store API",
    description="API para servir features de ML em tempo real",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar adequadamente em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class FeatureRequest(BaseModel):
    feature_ids: List[str]
    entity_id: str
    entity_type: str  # team, game, player
    timestamp: Optional[datetime] = None
    version: Optional[str] = None  # Se None, usa versão ativa

class FeatureResponse(BaseModel):
    entity_id: str
    entity_type: str
    timestamp: datetime
    features: Dict[str, dict]  # {feature_id: {value, version, metadata}}
    cached: bool
    response_time_ms: float

class FeatureMetadataResponse(BaseModel):
    feature_id: str
    name: str
    description: str
    data_type: str
    current_version: str
    category: str
    owner: str
    created_at: datetime
```

### 4.2 Endpoint: Obter Features

```python
@app.post("/api/v1/features", response_model=FeatureResponse)
async def get_features(
    request: FeatureRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtém múltiplas features para uma entidade.
    
    - **feature_ids**: Lista de IDs das features desejadas
    - **entity_id**: ID da entidade (team_id, game_id, etc.)
    - **entity_type**: Tipo de entidade (team, game, player)
    - **timestamp**: Timestamp desejado (default: agora)
    - **version**: Versão específica (default: versão ativa)
    """
    start_time = datetime.now()
    
    # Validar request
    validate_feature_request(request)
    
    # Determinar timestamp
    timestamp = request.timestamp or datetime.now()
    
    # Tentar obter do cache
    cache_key = f"features:{request.entity_type}:{request.entity_id}:{timestamp}"
    cached_response = await redis_client.get(cache_key)
    
    if cached_response:
        response = FeatureResponse.parse_raw(cached_response)
        response.cached = True
        response.response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return response
    
    # Cache miss: buscar do Feature Store
    features = {}
    for feature_id in request.feature_ids:
        try:
            feature_data = await get_feature_from_store(
                feature_id=feature_id,
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                timestamp=timestamp,
                version=request.version
            )
            features[feature_id] = feature_data
        except FeatureNotFoundError:
            logger.warning(f"Feature not found: {feature_id}")
            features[feature_id] = None
    
    # Criar response
    response = FeatureResponse(
        entity_id=request.entity_id,
        entity_type=request.entity_type,
        timestamp=timestamp,
        features=features,
        cached=False,
        response_time_ms=(datetime.now() - start_time).total_seconds() * 1000
    )
    
    # Cache por 5 minutos
    await redis_client.setex(
        cache_key,
        300,
        response.json()
    )
    
    return response
```

### 4.3 Endpoint: Obter Feature Única

```python
@app.get("/api/v1/features/{feature_id}", response_model=dict)
async def get_single_feature(
    feature_id: str,
    entity_id: str,
    entity_type: str,
    timestamp: Optional[datetime] = None,
    version: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtém uma única feature para uma entidade.
    """
    timestamp = timestamp or datetime.now()
    
    feature_data = await get_feature_from_store(
        feature_id=feature_id,
        entity_id=entity_id,
        entity_type=entity_type,
        timestamp=timestamp,
        version=version
    )
    
    return {
        "feature_id": feature_id,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "timestamp": timestamp,
        "value": feature_data["value"],
        "version": feature_data["version"],
        "metadata": feature_data["metadata"]
    }
```

### 4.4 Endpoint: Obter Features em Batch

```python
@app.post("/api/v1/features/batch", response_model=List[FeatureResponse])
async def get_features_batch(
    requests: List[FeatureRequest],
    api_key: str = Depends(verify_api_key)
):
    """
    Obtém features para múltiplas entidades em batch.
    Útil para backtests e análises em lote.
    """
    responses = []
    
    # Processar em paralelo
    async def process_request(req):
        return await get_features(req, api_key)
    
    import asyncio
    responses = await asyncio.gather(*[process_request(req) for req in requests])
    
    return responses
```

### 4.5 Endpoint: Metadados de Feature

```python
@app.get("/api/v1/features/{feature_id}/metadata", response_model=FeatureMetadataResponse)
async def get_feature_metadata(
    feature_id: str,
    version: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtém metadados de uma feature.
    """
    metadata = await get_feature_metadata_from_db(feature_id, version)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    return FeatureMetadataResponse(**metadata)
```

### 4.6 Endpoint: Listar Features

```python
@app.get("/api/v1/features", response_model=List[dict])
async def list_features(
    category: Optional[str] = None,
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(verify_api_key)
):
    """
    Lista features disponíveis com filtros.
    """
    features = await list_features_from_db(
        category=category,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return features
```

### 4.7 Endpoint: Health Check

```python
@app.get("/health")
async def health_check():
    """
    Health check endpoint para monitoring.
    """
    # Verificar conexão com Redis
    try:
        await redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    # Verificar conexão com PostgreSQL
    try:
        await db_pool.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    status_code = 200 if redis_status == "healthy" and db_status == "healthy" else 503
    
    return {
        "status": "healthy" if status_code == 200 else "degraded",
        "redis": redis_status,
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }, status_code
```

---

## 5. AUTENTICAÇÃO E AUTORIZAÇÃO

### 5.1 API Keys

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verifica a API key do cliente.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key missing")
    
    # Buscar API key no banco de dados
    key_data = await get_api_key_from_db(api_key)
    
    if not key_data:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    # Verificar se a key está ativa
    if not key_data["is_active"]:
        raise HTTPException(status_code=403, detail="API Key deactivated")
    
    # Verificar rate limit
    if not await check_rate_limit(key_data["client_id"]):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Log request
    await log_api_request(key_data["client_id"], api_key)
    
    return key_data["client_id"]
```

### 5.2 Role-Based Access Control (RBAC)

```python
async def check_feature_access(client_id: str, feature_id: str):
    """
    Verifica se o cliente tem acesso a uma feature específica.
    """
    client_roles = await get_client_roles(client_id)
    feature_permissions = await get_feature_permissions(feature_id)
    
    # Admin tem acesso a tudo
    if "admin" in client_roles:
        return True
    
    # Verificar permissões específicas
    for role in client_roles:
        if role in feature_permissions["allowed_roles"]:
            return True
    
    return False

# Middleware para verificar acesso
@app.middleware("http")
async def check_feature_access_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/v1/features"):
        feature_id = request.path_params.get("feature_id")
        if feature_id:
            client_id = request.state.client_id
            if not await check_feature_access(client_id, feature_id):
                raise HTTPException(status_code=403, detail="Access denied")
    
    return await call_next(request)
```

---

## 6. RATE LIMITING

### 6.1 Implementação com Redis

```python
import time

async def check_rate_limit(client_id: str, limit: int = 1000, window: int = 60):
    """
    Implementa rate limiting com Token Bucket algorithm.
    
    - limit: Número máximo de requests
    - window: Janela de tempo em segundos
    """
    key = f"ratelimit:{client_id}"
    
    # Obter estado atual
    current = await redis_client.get(key)
    
    if current is None:
        # Primeiro request
        await redis_client.setex(key, window, limit - 1)
        return True
    
    current = int(current)
    
    if current > 0:
        # Decrementar
        await redis_client.decr(key)
        return True
    else:
        # Limit exceeded
        return False

# Decorator para rate limiting
from functools import wraps

def rate_limit(limit: int = 1000, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client_id = kwargs.get("client_id") or args[1].get("client_id")
            if not await check_rate_limit(client_id, limit, window):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {limit} requests per {window}s"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 7. CACHING

### 7.1 Estratégia de Cache

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Configurar cache
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# Cache decorator
@app.get("/api/v1/features/{feature_id}")
@cache(expire=300)  # 5 minutos
async def get_feature_cached(
    feature_id: str,
    entity_id: str,
    entity_type: str,
    timestamp: Optional[datetime] = None
):
    """
    Endpoint com cache automático.
    """
    return await get_feature_from_store(feature_id, entity_id, entity_type, timestamp)

# Cache manual para casos complexos
async def get_features_with_manual_cache(request: FeatureRequest):
    cache_key = f"features:{request.entity_type}:{request.entity_id}:{request.timestamp}"
    
    # Tentar cache
    cached = await redis_client.get(cache_key)
    if cached:
        return FeatureResponse.parse_raw(cached)
    
    # Cache miss: computar
    features = await compute_features(request)
    
    # Escrever no cache
    await redis_client.setex(cache_key, 300, features.json())
    
    return features
```

### 7.2 Cache Invalidation

```python
async def invalidate_feature_cache(feature_id: str, entity_id: str = None):
    """
    Invalida cache de uma feature (ou todas as features de uma entidade).
    """
    if entity_id:
        # Invalidar cache específico
        pattern = f"features:*:{entity_id}:*"
    else:
        # Invalidar todas as caches desta feature
        pattern = f"features:*:*:*"
    
    # Buscar todas as keys
    keys = await redis_client.keys(pattern)
    
    # Deletar
    if keys:
        await redis_client.delete(*keys)
```

---

## 8. MONITORIZAÇÃO E LOGGING

### 8.1 Métricas Prometheus

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Métricas
feature_requests_total = Counter(
    'feature_requests_total',
    'Total number of feature requests',
    ['feature_id', 'status']
)

feature_request_duration = Histogram(
    'feature_request_duration_seconds',
    'Feature request duration in seconds',
    ['feature_id', 'endpoint']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['feature_id']
)

# Middleware para métricas
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    feature_request_duration.labels(
        feature_id=request.path_params.get("feature_id", "unknown"),
        endpoint=request.url.path
    ).observe(duration)
    
    feature_requests_total.labels(
        feature_id=request.path_params.get("feature_id", "unknown"),
        status=response.status_code
    ).inc()
    
    return response
```

### 8.2 Logging Estruturado

```python
import structlog

logger = structlog.get_logger()

@app.post("/api/v1/features")
async def get_features(request: FeatureRequest):
    logger.info(
        "feature_request",
        feature_ids=request.feature_ids,
        entity_id=request.entity_id,
        entity_type=request.entity_type
    )
    
    try:
        features = await get_features_impl(request)
        logger.info(
            "feature_request_success",
            entity_id=request.entity_id,
            features_count=len(features)
        )
        return features
    except Exception as e:
        logger.error(
            "feature_request_error",
            entity_id=request.entity_id,
            error=str(e),
            exc_info=True
        )
        raise
```

---

## 9. CLIENT SDK

### 9.1 Python SDK

```python
import httpx
from typing import List, Dict, Optional
from datetime import datetime

class FeatureStoreClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={"X-API-Key": api_key}
        )
    
    async def get_features(
        self,
        feature_ids: List[str],
        entity_id: str,
        entity_type: str,
        timestamp: Optional[datetime] = None,
        version: Optional[str] = None
    ) -> Dict[str, dict]:
        """
        Obtém features do Feature Store.
        """
        response = await self.client.post(
            "/api/v1/features",
            json={
                "feature_ids": feature_ids,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "timestamp": timestamp.isoformat() if timestamp else None,
                "version": version
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_feature(
        self,
        feature_id: str,
        entity_id: str,
        entity_type: str,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Obtém uma única feature.
        """
        features = await self.get_features(
            feature_ids=[feature_id],
            entity_id=entity_id,
            entity_type=entity_type,
            timestamp=timestamp
        )
        return features[feature_id]["value"]
    
    async def close(self):
        await self.client.aclose()

# Exemplo de uso
async def main():
    client = FeatureStoreClient(
        api_url="http://localhost:8000",
        api_key="your-api-key"
    )
    
    features = await client.get_features(
        feature_ids=["home_win_rate_decay5", "away_win_rate_decay5"],
        entity_id="BOS",
        entity_type="team"
    )
    
    print(features)
    
    await client.close()
```

### 9.2 Uso em Modelos de ML

```python
class BettingModel:
    def __init__(self, model_path: str, feature_store_client: FeatureStoreClient):
        self.model = load_model(model_path)
        self.feature_store = feature_store_client
    
    async def predict(self, game_id: str, home_team: str, away_team: str) -> dict:
        """
        Faz previsão para um jogo.
        """
        # Obter features
        features = await self.feature_store.get_features(
            feature_ids=[
                "home_win_rate_decay5",
                "away_win_rate_decay5",
                "home_efg_pct_decay5",
                "away_efg_pct_decay5",
                "home_is_b2b",
                "away_is_b2b"
            ],
            entity_id=game_id,
            entity_type="game"
        )
        
        # Preparar input para modelo
        X = self._prepare_features(features)
        
        # Fazer previsão
        prediction = self.model.predict(X)
        
        return {
            "game_id": game_id,
            "home_win_prob": prediction[0],
            "away_win_prob": prediction[1],
            "features": features
        }
```

---

## 10. BOAS PRÁTICAS

### 10.1 Performance

- **Usar async/await** para operações I/O
- **Implementar caching** em múltiplos níveis
- **Usar connection pooling** para database
- **Limitar tamanho de responses** (paginação para listas)
- **Compressão** para responses grandes

### 10.2 Segurança

- **Validar inputs** rigorosamente
- **Usar HTTPS** em produção
- **Rotacionar API keys** regularmente
- **Implementar rate limiting** para prevenir abuse
- **Log tentativas de acesso** não autorizadas

### 10.2 Confiabilidade

- **Implementar retries** com exponential backoff
- **Circuit breaker** para serviços dependentes
- **Graceful degradation** em caso de falhas
- **Health checks** para monitoring
- **Backup endpoints** para emergências

---

## 11. BACKLOG TÉCNICO

- [ ] Implementar API FastAPI com todos os endpoints
- [ ] Configurar autenticação com API keys
- [ ] Implementar rate limiting com Redis
- [ ] Adicionar caching em múltiplos níveis
- [ ] Implementar monitoring com Prometheus
- [ ] Criar logging estruturado
- [ ] Desenvolver Python SDK
- [ ] Implementar cache invalidation
- [ ] Adicionar testes de integração
- [ ] Criar documentação OpenAPI/Swagger
- [ ] Implementar circuit breaker
- [ ] Adicionar suporte a GraphQL (opcional)

---

## 12. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secção mãe
- [[32_Feature_Store/ARQUITETURA_FEATURE_STORE]] → Arquitetura geral
- [[32_Feature_Store/COMPUTACAO_FEATURES]] → Computação de features
- [[32_Feature_Store/MONITORIZACAO_FEATURES]] → Monitorização de qualidade
- [[32_Feature_Store/INTEGRACAO_ML]] → Integração com ML models
- [[05_Machine_Learning/INDEX]] → Consumidores da API