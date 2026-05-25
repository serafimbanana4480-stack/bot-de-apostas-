# API_INTERNAL — APIs FastAPI Internas

**ID:** `API-003` | **Fase:** #phase/2 | **Owner:** Backend Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar todas as APIs FastAPI internas do sistema, incluindo endpoints, autenticação, autorização, rate limiting, e boas práticas de implementação.

---

## 2. ARQUITETURA

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (FastAPI)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth      │  │   Rate      │  │  Logging    │         │
│  │  Middleware │  │  Limiting   │  │ Middleware  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Data      │  │  Predict    │  │   Signal    │         │
│  │  Routers    │  │  Routers    │  │  Routers    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │    Redis    │  │   ML Model  │         │
│  │   Database  │  │   Cache     │  │   Service   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Stack Tecnológico

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| Framework | FastAPI | 0.104+ |
| ASGI Server | Uvicorn | 0.24+ |
| ORM | SQLAlchemy | 2.0+ |
| Autenticação | JWT (PyJWT) | 2.8+ |
| Rate Limiting | slowapi | 0.1.9+ |
| Validation | Pydantic | 2.5+ |
| Documentation | OpenAPI/Swagger | Integrado |

---

## 3. ESTRUTURA DO PROJETO

```
api/
├── main.py                 # Entry point da aplicação
├── config.py               # Configurações (env vars)
├── dependencies.py         # Dependências de injeção
├── middleware/
│   ├── auth.py            # Middleware de autenticação
│   ├── rate_limit.py      # Middleware de rate limiting
│   └── logging.py         # Middleware de logging
├── routers/
│   ├── data.py            # Endpoints de dados
│   ├── predictions.py     # Endpoints de predições
│   ├── signals.py         # Endpoints de sinais
│   ├── bets.py            # Endpoints de apostas
│   └── admin.py           # Endpoints administrativos
├── models/
│   ├── schemas.py         # Pydantic schemas
│   └── database.py        # SQLAlchemy models
├── services/
│   ├── auth_service.py    # Lógica de autenticação
│   ├── data_service.py    # Lógica de dados
│   └── prediction_service.py  # Lógica de predições
└── utils/
    ├── jwt_handler.py     # Utilitários JWT
    └── response.py        # Respostas padronizadas
```

---

## 4. AUTENTICAÇÃO E AUTORIZAÇÃO

### 4.1 Estratégia de Autenticação

**Mecanismo:** JWT (JSON Web Tokens)

**Fluxo:**
1. Cliente envia credenciais para `/auth/login`
2. Servidor valida credenciais e gera JWT
3. Cliente inclui JWT no header `Authorization: Bearer <token>`
4. Middleware valida JWT em cada requisição protegida

### 4.2 Implementação JWT

```python
# utils/jwt_handler.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

### 4.3 Middleware de Autenticação

```python
# middleware/auth.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def auth_middleware(request: Request, call_next):
    """Middleware para validar JWT em todas as rotas protegidas"""
    
    # Rotas públicas não requerem autenticação
    public_paths = ["/docs", "/openapi.json", "/auth/login", "/health"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # Validar token
    try:
        credentials: HTTPAuthorizationCredentials = await security(request)
        token = credentials.credentials
        payload = verify_token(token)
        request.state.user = payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    response = await call_next(request)
    return response
```

### 4.4 Endpoints de Autenticação

```python
# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Autentica usuário e retorna JWT"""
    
    # Validar credenciais (exemplo simplificado)
    user = await auth_service.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Gerar token
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    
    return TokenResponse(access_token=access_token)

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout (invalida token no lado do cliente)"""
    return {"message": "Successfully logged out"}
```

### 4.5 Controle de Acesso Baseado em Roles (RBAC)

```python
# dependencies.py
from fastapi import Depends, HTTPException, status

def require_role(required_role: str):
    """Dependency para verificar se usuário tem role específica"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Uso em endpoints
@router.get("/admin/users")
async def list_users(
    current_user: dict = Depends(require_role("admin"))
):
    """Apenas admin pode listar usuários"""
    return {"users": []}
```

---

## 5. RATE LIMITING

### 5.1 Estratégia de Rate Limiting

**Mecanismo:** Token Bucket com Redis

**Limites por Role:**
| Role | Requests/min | Requests/hour |
|------|--------------|---------------|
| Admin | 1000 | 10000 |
| User | 100 | 1000 |
| Service | 500 | 5000 |

### 5.2 Implementação com SlowAPI

```python
# middleware/rate_limit.py
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/minute")
async def rate_limited_endpoint(request: Request):
    """Endpoint com rate limiting"""
    return {"message": "Hello"}
```

### 5.3 Rate Limiting com Redis

```python
# middleware/redis_rate_limit.py
import redis
import time
from fastapi import Request, HTTPException, status

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def check_rate_limit(
    request: Request,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """Verifica rate limit usando Redis"""
    
    user_id = request.state.user.get("sub", get_remote_address(request))
    key = f"rate_limit:{user_id}"
    
    current = redis_client.incr(key)
    
    if current == 1:
        redis_client.expire(key, window_seconds)
    
    if current > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
```

---

## 6. ENDPOINTS PRINCIPAIS

### 6.1 Routers de Dados

```python
# routers/data.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/api/v1/data", tags=["Data"])

@router.get("/games")
async def get_games(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    team_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Obtém jogos filtrados por data e equipa"""
    return await data_service.get_games(start_date, end_date, team_id)

@router.get("/games/{game_id}/boxscore")
async def get_boxscore(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtém box score de um jogo específico"""
    return await data_service.get_boxscore(game_id)

@router.get("/teams/{team_id}/stats")
async def get_team_stats(
    team_id: int,
    season: str = Query(..., description="Formato: 2023-24"),
    current_user: dict = Depends(get_current_user)
):
    """Obtém estatísticas de equipa por temporada"""
    return await data_service.get_team_stats(team_id, season)

@router.get("/injuries")
async def get_injuries(
    report_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """Obtém relatório de lesões"""
    return await data_service.get_injuries(report_date)
```

### 6.2 Routers de Predições

```python
# routers/predictions.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])

class PredictionRequest(BaseModel):
    game_id: str
    market: str  # 'moneyline', 'spread', 'total'
    
class PredictionResponse(BaseModel):
    game_id: str
    market: str
    predicted_outcome: str
    confidence: float
    model_version: str
    generated_at: str

@router.post("/generate", response_model=PredictionResponse)
async def generate_prediction(
    request: PredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Gera predição para um jogo e mercado específicos"""
    prediction = await prediction_service.generate(
        request.game_id,
        request.market
    )
    return prediction

@router.get("/history")
async def get_prediction_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """Obtém histórico de predições"""
    return await prediction_service.get_history(start_date, end_date)
```

### 6.3 Routers de Sinais

```python
# routers/signals.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/signals", tags=["Signals"])

class SignalResponse(BaseModel):
    signal_id: str
    game_id: str
    market: str
    selection: str
    odd: float
    edge: float
    kelly_fraction: float
    recommended_stake: float
    generated_at: str

@router.get("/active", response_model=List[SignalResponse])
async def get_active_signals(
    current_user: dict = Depends(get_current_user)
):
    """Obtém sinais ativos (não executados)"""
    return await signal_service.get_active_signals()

@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtém detalhes de um sinal específico"""
    return await signal_service.get_signal(signal_id)

@router.post("/{signal_id}/mark-executed")
async def mark_signal_executed(
    signal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Marca sinal como executado manualmente"""
    return await signal_service.mark_executed(signal_id)
```

### 6.4 Routers de Apostas

```python
# routers/bets.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/bets", tags=["Bets"])

class BetResponse(BaseModel):
    bet_id: str
    signal_id: str
    game_id: str
    market: str
    selection: str
    odd_taken: float
    stake: float
    outcome: Optional[str]
    pnl: Optional[float]
    executed_at: Optional[str]

@router.get("/", response_model=List[BetResponse])
async def get_bets(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    bet_type: Optional[str] = None,  # 'real', 'shadow', 'paper'
    current_user: dict = Depends(get_current_user)
):
    """Obtém apostas filtradas"""
    return await bet_service.get_bets(start_date, end_date, bet_type)

@router.get("/performance")
async def get_bet_performance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """Obtém métricas de performance de apostas"""
    return await bet_service.get_performance(start_date, end_date)
```

### 6.5 Routers Administrativos

```python
# routers/admin.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.get("/system/health")
async def system_health(
    current_user: dict = Depends(require_role("admin"))
):
    """Verifica saúde do sistema"""
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "ml_service": await check_ml_service()
    }

@router.get("/system/metrics")
async def system_metrics(
    current_user: dict = Depends(require_role("admin"))
):
    """Obtém métricas do sistema"""
    return {
        "cpu_usage": get_cpu_usage(),
        "memory_usage": get_memory_usage(),
        "disk_usage": get_disk_usage(),
        "active_connections": get_active_connections()
    }

@router.post("/pipelines/trigger/{pipeline_name}")
async def trigger_pipeline(
    pipeline_name: str,
    current_user: dict = Depends(require_role("admin"))
):
    """Trigger manual de pipeline"""
    return await pipeline_service.trigger(pipeline_name)
```

---

## 7. VALIDAÇÃO E SCHEMAS

### 7.1 Pydantic Schemas

```python
# models/schemas.py
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

class GameSchema(BaseModel):
    game_id: str = Field(..., description="ID único do jogo")
    season: str = Field(..., regex=r"\d{4}-\d{2}", description="Formato: 2023-24")
    game_date: date
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = Field(..., regex="^(scheduled|in_progress|final|cancelled)$")
    
    @validator('home_score', 'away_score')
    def validate_scores(cls, v, values):
        if v is not None and v < 0:
            raise ValueError('Score cannot be negative')
        return v

class OddsSchema(BaseModel):
    game_id: str
    market: str = Field(..., regex="^(moneyline|spread|total)$")
    bookmaker: str
    odd: Decimal = Field(..., gt=1.0, description="Odd deve ser > 1.0")
    recorded_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class PredictionSchema(BaseModel):
    game_id: str
    market: str
    predicted_outcome: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    features: dict = Field(default_factory=dict)
```

### 7.2 Respostas Padronizadas

```python
# utils/response.py
from fastapi import status
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None

def success_response(data: T, message: str = "Success") -> APIResponse[T]:
    return APIResponse[T](
        success=True,
        message=message,
        data=data
    )

def error_response(message: str, error: Optional[str] = None) -> APIResponse[None]:
    return APIResponse[None](
        success=False,
        message=message,
        error=error
    )
```

---

## 8. LOGGING E MONITORING

### 8.1 Configuração de Logging

```python
# middleware/logging.py
import logging
import time
from fastapi import Request
import json

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """Middleware para logging de requisições"""
    
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"Response: {response.status_code} - "
        f"Time: {process_time:.2f}ms"
    )
    
    # Adicionar header de tempo
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### 8.2 Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formatter para logs em JSON"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data)
```

---

## 9. DEPLOYMENT

### 9.1 Configuração de Produção

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Value Betting API",
    description="API interna para sistema de value betting",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar origins específicos em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middlewares
app.middleware("http")(logging_middleware)
app.middleware("http")(auth_middleware)

# Routers
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(predictions_router)
app.include_router(signals_router)
app.include_router(bets_router)
app.include_router(admin_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
```

### 9.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/valuebetting
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=valuebetting
      - POSTGRES_USER=vb_admin
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## 10. SEGURANÇA

### 10.1 Boas Práticas de Segurança

- [ ] Usar HTTPS em produção
- [ ] Validar e sanitizar todos os inputs
- [ ] Implementar rate limiting por IP e usuário
- [ ] Usar secrets management (HashiCorp Vault ou AWS Secrets Manager)
- [ ] Rotacionar chaves JWT regularmente
- [ ] Implementar CORS restrito
- [ ] Logs de auditoria para ações sensíveis
- [ ] Input validation com Pydantic
- [ ] SQL injection prevention (ORM SQLAlchemy)
- [ ] XSS prevention (templates sanitizados)

### 10.2 Headers de Segurança

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.valuebetting.com", "*.valuebetting.com"]
)

# Adicionar security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 11. BACKLOG

- [ ] Implementar refresh tokens
- [ ] Adicionar suporte a OAuth2
- [ ] Implementar rate limiting granular por endpoint
- [ ] Adicionar métricas Prometheus
- [ ] Implementar distributed tracing (Jaeger/Zipkin)
- [ ] Adicionar testes de integração
- [ ] Implementar API versioning completo
- [ ] Adicionar webhook para notificações

---

## 11. IMPLEMENTAÇÃO COMPLETA

### 11.1 Script FastAPI Completo e Robusto
```python
"""
API FastAPI completa para sistema de value betting
Inclui autenticação, rate limiting, logging, e todos os endpoints
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
import time

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Criar app
app = FastAPI(
    title="Value Betting API",
    description="API interna para sistema de value betting na NBA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar origins específicos em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ============ SCHEMAS ============

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class GameSchema(BaseModel):
    game_id: str = Field(..., description="ID único do jogo")
    season: str = Field(..., regex=r"\d{4}-\d{2}", description="Formato: 2023-24")
    game_date: datetime
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = Field(..., regex="^(scheduled|in_progress|final|cancelled)$")
    
    @validator('home_score', 'away_score')
    def validate_scores(cls, v, values):
        if v is not None and v < 0:
            raise ValueError('Score cannot be negative')
        return v

class OddsSchema(BaseModel):
    game_id: str
    market: str = Field(..., regex="^(moneyline|spread|total)$")
    bookmaker: str
    odd: Decimal = Field(..., gt=1.0, description="Odd deve ser > 1.0")
    recorded_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class PredictionRequest(BaseModel):
    game_id: str
    market: str = Field(..., regex="^(moneyline|spread|total)$")

class PredictionResponse(BaseModel):
    game_id: str
    market: str
    predicted_outcome: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    generated_at: str
    features: Dict[str, Any] = Field(default_factory=dict)

class SignalResponse(BaseModel):
    signal_id: str
    game_id: str
    market: str
    selection: str
    odd: float
    edge: float
    kelly_fraction: float
    recommended_stake: float
    generated_at: str

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

# ============ UTILITÁRIOS ============

def create_access_token(data: dict) -> str:
    """Cria JWT token"""
    from jose import jwt
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verifica JWT token"""
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Resposta de sucesso padronizada"""
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str, error: Optional[str] = None) -> Dict[str, Any]:
    """Resposta de erro padronizada"""
    return {
        "success": False,
        "message": message,
        "error": error
    }

# ============ MIDDLEWARE ============

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware para logging de requisições"""
    start_time = time.time()
    
    logger.info(f"📥 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"📤 {response.status_code} - {process_time:.2f}ms")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware para autenticação JWT"""
    
    # Rotas públicas não requerem autenticação
    public_paths = ["/docs", "/openapi.json", "/redoc", "/auth/login", "/health"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # Validar token
    try:
        credentials: HTTPAuthorizationCredentials = await security(request)
        token = credentials.credentials
        payload = verify_token(token)
        request.state.user = payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return await call_next(request)

# ============ DEPENDÊNCIAS ============

async def get_current_user(request: Request) -> dict:
    """Dependency para obter usuário atual"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user

def require_role(required_role: str):
    """Dependency para verificar role"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# ============ ENDPOINTS DE SAÚDE ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# ============ ENDPOINTS DE AUTENTICAÇÃO ============

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Autentica usuário e retorna JWT"""
    
    # Validar credenciais (exemplo simplificado - usar database real)
    if request.username == "admin" and request.password == "admin123":
        user = {"sub": "admin", "role": "admin"}
    elif request.username == "user" and request.password == "user123":
        user = {"sub": "user", "role": "user"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Gerar token
    access_token = create_access_token(user)
    
    logger.info(f"✅ Login successful: {request.username}")
    
    return TokenResponse(access_token=access_token)

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout"""
    logger.info(f"👋 Logout: {current_user.get('sub')}")
    return success_response(message="Successfully logged out")

# ============ ENDPOINTS DE DADOS ============

@app.get("/api/v1/data/games")
async def get_games(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    team_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Obtém jogos filtrados"""
    
    logger.info(f"📊 Fetching games: {start_date} to {end_date}, team: {team_id}")
    
    # Exemplo de dados mockados - substituir com database real
    games = [
        {
            "game_id": "0022300001",
            "season": "2023-24",
            "game_date": "2024-01-15T19:00:00",
            "home_team_id": 1,
            "away_team_id": 2,
            "home_score": 110,
            "away_score": 105,
            "status": "final"
        }
    ]
    
    return success_response(data=games)

@app.get("/api/v1/data/games/{game_id}")
async def get_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtém detalhes de um jogo específico"""
    
    logger.info(f"📊 Fetching game: {game_id}")
    
    return success_response(data={"game_id": game_id})

@app.get("/api/v1/data/teams/{team_id}/stats")
async def get_team_stats(
    team_id: int,
    season: str = Query(..., description="Formato: 2023-24"),
    current_user: dict = Depends(get_current_user)
):
    """Obtém estatísticas de equipa por temporada"""
    
    logger.info(f"📊 Fetching stats for team {team_id}, season {season}")
    
    return success_response(data={"team_id": team_id, "season": season})

@app.get("/api/v1/data/injuries")
async def get_injuries(
    report_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Obtém relatório de lesões"""
    
    logger.info(f"📊 Fetching injuries for {report_date}")
    
    return success_response(data=[])

# ============ ENDPOINTS DE PREDIÇÕES ============

@app.post("/api/v1/predictions/generate", response_model=PredictionResponse)
async def generate_prediction(
    request: PredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Gera predição para um jogo e mercado específicos"""
    
    logger.info(f"🔮 Generating prediction: {request.game_id} - {request.market}")
    
    # Exemplo de predição mockada - substituir com modelo real
    prediction = PredictionResponse(
        game_id=request.game_id,
        market=request.market,
        predicted_outcome="home",
        confidence=0.75,
        model_version="v1.0.0",
        generated_at=datetime.utcnow().isoformat(),
        features={"feature1": 0.5, "feature2": 0.3}
    )
    
    return prediction

@app.get("/api/v1/predictions/history")
async def get_prediction_history(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Obtém histórico de predições"""
    
    logger.info(f"📊 Fetching prediction history: {start_date} to {end_date}")
    
    return success_response(data=[])

# ============ ENDPOINTS DE SINAIS ============

@app.get("/api/v1/signals/active", response_model=List[SignalResponse])
async def get_active_signals(
    current_user: dict = Depends(get_current_user)
):
    """Obtém sinais ativos"""
    
    logger.info("📊 Fetching active signals")
    
    signals = [
        SignalResponse(
            signal_id="sig_001",
            game_id="0022300001",
            market="moneyline",
            selection="home",
            odd=1.85,
            edge=0.05,
            kelly_fraction=0.02,
            recommended_stake=100.0,
            generated_at=datetime.utcnow().isoformat()
        )
    ]
    
    return signals

@app.get("/api/v1/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtém detalhes de um sinal específico"""
    
    logger.info(f"📊 Fetching signal: {signal_id}")
    
    return SignalResponse(
        signal_id=signal_id,
        game_id="0022300001",
        market="moneyline",
        selection="home",
        odd=1.85,
        edge=0.05,
        kelly_fraction=0.02,
        recommended_stake=100.0,
        generated_at=datetime.utcnow().isoformat()
    )

@app.post("/api/v1/signals/{signal_id}/mark-executed")
async def mark_signal_executed(
    signal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Marca sinal como executado"""
    
    logger.info(f"✅ Marking signal executed: {signal_id}")
    
    return success_response(message="Signal marked as executed")

# ============ ENDPOINTS DE APOSTAS ============

@app.get("/api/v1/bets")
async def get_bets(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    bet_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Obtém apostas filtradas"""
    
    logger.info(f"📊 Fetching bets: {start_date} to {end_date}, type: {bet_type}")
    
    return success_response(data=[])

@app.get("/api/v1/bets/performance")
async def get_bet_performance(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Obtém métricas de performance de apostas"""
    
    logger.info(f"📊 Fetching performance: {start_date} to {end_date}")
    
    return success_response(data={
        "total_bets": 100,
        "win_rate": 0.55,
        "total_pnl": 500.0,
        "roi": 0.05
    })

# ============ ENDPOINTS ADMINISTRATIVOS ============

@app.get("/api/v1/admin/system/health")
async def system_health(
    current_user: dict = Depends(require_role("admin"))
):
    """Verifica saúde do sistema"""
    
    logger.info("🔍 System health check (admin)")
    
    return success_response(data={
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "ml_service": "available"
    })

@app.get("/api/v1/admin/system/metrics")
async def system_metrics(
    current_user: dict = Depends(require_role("admin"))
):
    """Obtém métricas do sistema"""
    
    logger.info("📊 System metrics (admin)")
    
    return success_response(data={
        "cpu_usage": 45.5,
        "memory_usage": 60.2,
        "disk_usage": 55.0,
        "active_connections": 42
    })

@app.post("/api/v1/admin/pipelines/trigger/{pipeline_name}")
async def trigger_pipeline(
    pipeline_name: str,
    current_user: dict = Depends(require_role("admin"))
):
    """Trigger manual de pipeline"""
    
    logger.info(f"🚀 Triggering pipeline: {pipeline_name}")
    
    return success_response(message=f"Pipeline {pipeline_name} triggered")

# ============ ERROR HANDLING ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para exceções HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            error=f"HTTP_{exc.status_code}"
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="Internal server error",
            error=str(exc)
        )
    )

# ============ MAIN ============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

---

## 12. LINKS CRUZADOS

- [[14_APIs/INDEX]] ← Secao mae
- [[13_Infrastructure/VPS_CONFIGURACAO]] → Configuração de deployment
- [[10_Monitoring/ARQUITETURA_MONITORIZACAO]] → Monitoring e alerting
- [[12_DevOps/CI_CD_SETUP]] → CI/CD para API