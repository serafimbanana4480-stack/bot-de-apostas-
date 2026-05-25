# Integração com Odds de Casas Reais

**ID:** `ODDS-001` | **Fase:** #phase/4-8 | **Owner:** Data Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Sistema de integração com APIs de casas de apostas reais para obtenção de odds em tempo real, normalização entre casas, detecção de melhor preço, e cache inteligente. Baseado na implementação do projeto kyleskom/NBA-ML-Betting que suporta Fanduel, DraftKings, BetMGM, PointsBet, Caesars, Wynn, e BetRivers.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Obter odds de múltiplas casas para encontrar melhor preço e validar edge |
| **Casas Suportadas** | 7+ casas (Fanduel, DraftKings, BetMGM, PointsBet, Caesars, Wynn, BetRivers) |
| **Latência** | < 5 segundos para odds live |
| **Cache** | Redis TTL 60 segundos |
| **Custo** | 0€ (APIs públicas ou scraping autorizado) |

---

## 2. OVERVIEW DE CASAS SUPORTADAS

### 2.1 Tabela de Casas

| Casa | API | Auth | Rate Limit | Mercados NBA | Status |
|------|-----|------|------------|--------------|--------|
| **Fanduel** | API Pública | API Key | 100 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **DraftKings** | API Pública | API Key | 100 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **BetMGM** | API Pública | API Key | 50 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **PointsBet** | API Pública | API Key | 50 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **Caesars** | API Pública | API Key | 50 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **Wynn** | API Pública | API Key | 30 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **BetRivers** | API Pública | API Key | 30 req/min | Moneyline, Spread, Total | ✅ Ativo |
| **Betfair** | API Premium | App Key + Session | 200 req/min | Todos os mercados | 🔄 Opcional |

### 2.2 Priorização de Fontes

1. **Tier 1 (Primary):** Fanduel, DraftKings (maior liquidez, odds mais estáveis)
2. **Tier 2 (Secondary):** BetMGM, PointsBet, Caesars (liquidez média)
3. **Tier 3 (Tertiary):** Wynn, BetRivers (liquidez menor, odds mais voláteis)
4. **Tier 4 (Exchange):** Betfair (melhor preço mas com comissão)

---

## 3. API POR CASA

### 3.1 Fanduel

**Endpoint Base:** `https://api.fanduel.com`

**Autenticação:**
```python
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
```

**Rate Limit:** 100 req/min

**Endpoint de Odds NBA:**
```http
GET /api/sportsbook/v1/competitions/{competition_id}/events
```

**Exemplo de Response:**
```json
{
  "events": [
    {
      "id": "event-123",
      "name": "Boston Celtics vs LA Lakers",
      "startTime": "2024-01-15T20:00:00Z",
      "markets": [
        {
          "id": "market-456",
          "name": "Moneyline",
          "selections": [
            {
              "id": "sel-789",
              "name": "Boston Celtics",
              "odds": {
                "decimal": 1.85,
                "american": -117
              }
            },
            {
              "id": "sel-790",
              "name": "LA Lakers",
              "odds": {
                "decimal": 2.10,
                "american": +110
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### 3.2 DraftKings

**Endpoint Base:** `https://api.draftkings.com`

**Autenticação:**
```python
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
```

**Rate Limit:** 100 req/min

**Endpoint de Odds NBA:**
```http
GET /sportsbook/v1/leagues/{league_id}/events
```

**Exemplo de Response:**
```json
{
  "events": [
    {
      "eventId": "evt-123",
      "eventName": "Boston Celtics vs LA Lakers",
      "eventDate": "2024-01-15T20:00:00Z",
      "markets": [
        {
          "marketId": "mkt-456",
          "marketName": "Moneyline",
          "outcomes": [
            {
              "outcomeId": "out-789",
              "outcomeName": "Boston Celtics",
              "price": {
                "decimal": 1.85,
                "american": -117
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### 3.3 BetMGM

**Endpoint Base:** `https://api.betmgm.com`

**Autenticação:** OAuth 2.0

**Rate Limit:** 50 req/min

**Endpoint de Odds NBA:**
```http
GET /api/v1/sports/{sport_id}/events
```

### 3.4 PointsBet

**Endpoint Base:** `https://api.pointsbet.com`

**Autenticação:** API Key

**Rate Limit:** 50 req/min

**Endpoint de Odds NBA:**
```http
GET /api/v1/competitions/{competition_id}/fixtures
```

### 3.5 Caesars

**Endpoint Base:** `https://api.caesars.com`

**Autenticação:** API Key

**Rate Limit:** 50 req/min

**Endpoint de Odds NBA:**
```http
GET /api/v1/sports/{sport_id}/events
```

### 3.6 Wynn

**Endpoint Base:** `https://api.wynn.com`

**Autenticação:** API Key

**Rate Limit:** 30 req/min

**Endpoint de Odds NBA:**
```http
GET /api/v1/sports/{sport_id}/events
```

### 3.7 BetRivers

**Endpoint Base:** `https://api.betrivers.com`

**Autenticação:** API Key

**Rate Limit:** 30 req/min

**Endpoint de Odds NBA:**
```http
GET /api/v1/sports/{sport_id}/events
```

---

## 4. NORMALIZAÇÃO DE ODDS

### 4.1 Schema Unificado

```python
# Schema unificado para odds de todas as casas
class NormalizedOdds(BaseModel):
    game_id: str
    game_date: datetime
    home_team: str
    away_team: str
    source: str  # "fanduel", "draftkings", etc.
    market: str  # "moneyline", "spread", "total"
    
    # Para Moneyline
    home_odds: Optional[float]  # Decimal
    away_odds: Optional[float]
    
    # Para Spread
    home_spread: Optional[float]
    home_spread_odds: Optional[float]
    away_spread: Optional[float]
    away_spread_odds: Optional[float]
    
    # Para Total
    total_line: Optional[float]
    over_odds: Optional[float]
    under_odds: Optional[float]
    
    # Metadados
    fetched_at: datetime
    is_live: bool
    liquidity_score: Optional[int]  # 1-10
```

### 4.2 Função de Normalização

```python
def normalize_odds(raw_data: dict, source: str) -> NormalizedOdds:
    """
    Normaliza dados brutos de uma casa para o schema unificado.
    
    Args:
        raw_data: Dados brutos da API da casa
        source: Nome da casa (fanduel, draftkings, etc.)
    
    Returns:
        NormalizedOdds: Odds normalizadas
    """
    if source == "fanduel":
        return _normalize_fanduel(raw_data)
    elif source == "draftkings":
        return _normalize_draftkings(raw_data)
    # ... outras casas
    
def _normalize_fanduel(raw_data: dict) -> NormalizedOdds:
    """Normaliza dados específicos do Fanduel."""
    event = raw_data["events"][0]
    
    # Extrair moneyline
    moneyline_market = next(
        (m for m in event["markets"] if m["name"] == "Moneyline"),
        None
    )
    
    if moneyline_market:
        home_sel = next(
            (s for s in moneyline_market["selections"] 
             if "Celtics" in s["name"]),  # Simplificado
            None
        )
        away_sel = next(
            (s for s in moneyline_market["selections"] 
             if "Lakers" in s["name"]),
            None
        )
    
    return NormalizedOdds(
        game_id=event["id"],
        game_date=datetime.fromisoformat(event["startTime"]),
        home_team="Boston Celtics",
        away_team="LA Lakers",
        source="fanduel",
        market="moneyline",
        home_odds=home_sel["odds"]["decimal"] if home_sel else None,
        away_odds=away_sel["odds"]["decimal"] if away_sel else None,
        fetched_at=datetime.now(),
        is_live=False,
        liquidity_score=8  # Estimado
    )
```

---

## 5. BEST PRICE DETECTION

### 5.1 Algoritmo de Comparação

```python
def find_best_price(game_id: str, market: str, selection: str) -> dict:
    """
    Encontra a melhor odd para um jogo/mercado/seleção específico.
    
    Args:
        game_id: ID do jogo
        market: Tipo de mercado (moneyline, spread, total)
        selection: Seleção (home, away, over, under)
    
    Returns:
        dict: Melhor preço e fonte
    """
    # Buscar odds de todas as casas
    all_odds = []
    for source in SUPPORTED_SOURCES:
        odds = get_cached_odds(game_id, source)
        if odds:
            all_odds.append(odds)
    
    # Encontrar melhor preço
    best_odds = None
    best_source = None
    
    for odds in all_odds:
        if market == "moneyline":
            if selection == "home":
                price = odds.home_odds
            else:
                price = odds.away_odds
        elif market == "spread":
            # ... similar para spread
            pass
        elif market == "total":
            # ... similar para total
            pass
        
        if price and (best_odds is None or price > best_odds):
            best_odds = price
            best_source = odds.source
    
    return {
        "best_odds": best_odds,
        "source": best_source,
        "all_odds": [
            {"source": o.source, "odds": getattr(o, f"{selection}_odds")}
            for o in all_odds
        ]
    }
```

### 5.2 Exemplo de Output

```json
{
  "game_id": "game-123",
  "market": "moneyline",
  "selection": "home",
  "best_odds": 1.90,
  "source": "draftkings",
  "all_odds": [
    {"source": "fanduel", "odds": 1.85},
    {"source": "draftkings", "odds": 1.90},
    {"source": "betmgm", "odds": 1.87},
    {"source": "pointsbet", "odds": 1.88}
  ]
}
```

---

## 6. CACHE STRATEGY

### 6.1 Redis Cache

```python
import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_cached_odds(game_id: str, source: str) -> Optional[NormalizedOdds]:
    """
    Busca odds em cache.
    
    TTL: 60 segundos para odds live, 3600 segundos para odds pré-jogo
    """
    cache_key = f"odds:{source}:{game_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return NormalizedOdds.parse_raw(cached)
    return None

def cache_odds(odds: NormalizedOdds, ttl: int = 60):
    """
    Guarda odds em cache.
    
    Args:
        odds: Odds normalizadas
        ttl: Time-to-live em segundos (default: 60s para live)
    """
    cache_key = f"odds:{odds.source}:{odds.game_id}"
    redis_client.setex(cache_key, ttl, odds.json())

def invalidate_cache(game_id: str):
    """Invalida cache para um jogo específico."""
    for source in SUPPORTED_SOURCES:
        cache_key = f"odds:{source}:{game_id}"
        redis_client.delete(cache_key)
```

### 6.2 Cache Hierárquico

```
Level 1: Redis (in-memory, TTL 60s) ← Mais rápido
Level 2: PostgreSQL (persistente, TTL 1h) ← Backup
Level 3: API externa (fetch real-time) ← Fonte primária
```

---

## 7. ERROR HANDLING E FALLBACK

### 7.1 Estratégia de Fallback

```python
def get_odds_with_fallback(game_id: str, market: str) -> dict:
    """
    Obtém odds com fallback automático em caso de falha.
    
    Ordem de tentativas:
    1. Cache Redis
    2. Cache PostgreSQL
    3. API Fanduel (Tier 1)
    4. API DraftKings (Tier 1)
    5. API BetMGM (Tier 2)
    6. API Betfair (Tier 4 - opcional)
    """
    # 1. Tentar cache
    cached = get_cached_odds(game_id, "fanduel")
    if cached:
        return cached
    
    # 2. Tentar APIs em ordem de prioridade
    sources_by_tier = {
        1: ["fanduel", "draftkings"],
        2: ["betmgm", "pointsbet", "caesars"],
        3: ["wynn", "betrivers"],
        4: ["betfair"]
    }
    
    for tier, sources in sources_by_tier.items():
        for source in sources:
            try:
                odds = fetch_odds_from_api(game_id, source)
                if odds:
                    cache_odds(odds)
                    return odds
            except Exception as e:
                log_error(f"Falha ao buscar odds de {source}: {e}")
                continue
    
    # Se todas as falharem, usar odds mais recentes do PostgreSQL
    latest_odds = get_latest_odds_from_db(game_id)
    if latest_odds:
        log_warning(f"Usando odds antigas do DB para jogo {game_id}")
        return latest_odds
    
    raise Exception("Impossível obter odds para jogo {game_id}")
```

### 7.2 Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def fetch_odds_from_api(game_id: str, source: str) -> Optional[NormalizedOdds]:
    """
    Busca odds de API com circuit breaker.
    
    Se falhar 5 vezes consecutivas, abre circuito por 60 segundos.
    """
    # Implementação de fetch
    pass
```

---

## 8. RATE LIMITING

### 8.1 Token Bucket Algorithm

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, rate: int, per: int):
        """
        Args:
            rate: Número de requests permitidos
            per: Período em segundos
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
    
    def acquire(self) -> bool:
        """
        Tenta adquirir um token do bucket.
        
        Returns:
            bool: True se permitido, False se rate limit
        """
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        # Refill bucket
        self.allowance += time_passed * (self.rate / self.per)
        
        if self.allowance > self.rate:
            self.allowance = self.rate
        
        if self.allowance < 1.0:
            return False  # Rate limited
        
        self.allowance -= 1.0
        return True

# Rate limiters por casa
RATE_LIMITERS = {
    "fanduel": RateLimiter(100, 60),      # 100 req/min
    "draftkings": RateLimiter(100, 60),
    "betmgm": RateLimiter(50, 60),
    "pointsbet": RateLimiter(50, 60),
    "caesars": RateLimiter(50, 60),
    "wynn": RateLimiter(30, 60),
    "betrivers": RateLimiter(30, 60)
}
```

### 8.2 Uso

```python
def fetch_odds_with_ratelimit(game_id: str, source: str):
    limiter = RATE_LIMITERS[source]
    
    if not limiter.acquire():
        log_warning(f"Rate limit atingido para {source}")
        # Fallback para cache ou outra fonte
        return get_cached_odds(game_id, source)
    
    # Se permitido, fazer request
    return fetch_odds_from_api(game_id, source)
```

---

## 9. INTEGRAÇÃO COM O SISTEMA

### 9.1 Pipeline de Ingestão

```python
# scripts/ingest_odds.py
from datetime import datetime
from vbq.odds.ingester import OddsIngester
from vbq.database import SessionLocal

def ingest_odds_for_date(date: datetime):
    """
    Ingesta odds de todas as casas para uma data específica.
    """
    db = SessionLocal()
    
    try:
        ingester = OddsIngester(db)
        
        # Obter jogos da data
        games = ingester.get_games_for_date(date)
        
        for game in games:
            # Buscar odds de todas as casas
            all_odds = []
            for source in SUPPORTED_SOURCES:
                try:
                    odds = fetch_odds_with_fallback(
                        game['game_id'],
                        source
                    )
                    if odds:
                        all_odds.append(odds)
                except Exception as e:
                    log_error(f"Falha {source}: {e}")
            
            # Persistir odds
            if all_odds:
                ingester.persist_odds(all_odds)
        
        db.commit()
        print(f"✅ Odds ingeridas para {len(games)} jogos")
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
```

### 9.2 CLI Integration

```bash
# Comando CLI para ingestão de odds
vbq-cli ingest odds --source fanduel --date 2024-01-15
vbq-cli ingest odds --source all --backfill 7
```

---

## 10. MONITORIZAÇÃO

### 10.1 Métricas

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| odds_fetch_latency | Latência de fetch de odds | < 5s |
| odds_cache_hit_rate | Taxa de cache hit | > 80% |
| odds_fetch_success_rate | Taxa de sucesso de fetch | > 95% |
| odds_source_availability | Disponibilidade por fonte | > 90% |

### 10.2 Alertas

- Fonte down por > 5 min → Alerta warning
- Taxa de sucesso < 80% → Alerta crítico
- Latência > 10s → Alerta warning

---

## 11. EXEMPLOS DE CÓDIGO

### 11.1 Classe Principal de Ingestão

```python
# vbq/odds/ingester.py
class OddsIngester:
    def __init__(self, db: Session):
        self.db = db
        self.redis = redis.Redis(host='localhost', port=6379)
    
    def ingest_odds(self, game_id: str, sources: List[str] = None):
        """
        Ingesta odds de múltiplas fontes para um jogo.
        """
        if sources is None:
            sources = SUPPORTED_SOURCES
        
        all_odds = []
        for source in sources:
            try:
                odds = self._fetch_odds(game_id, source)
                if odds:
                    all_odds.append(odds)
                    self._cache_odds(odds)
            except Exception as e:
                log_error(f"Falha {source}: {e}")
        
        # Encontrar melhor preço
        if all_odds:
            best_price = self._find_best_price(all_odds)
            self._persist_odds(all_odds, best_price)
        
        return all_odds
    
    def _fetch_odds(self, game_id: str, source: str) -> NormalizedOdds:
        """Busca odds de uma fonte específica."""
        # Verificar cache
        cached = self._get_cached_odds(game_id, source)
        if cached:
            return cached
        
        # Verificar rate limit
        if not RATE_LIMITERS[source].acquire():
            raise RateLimitError(f"Rate limit {source}")
        
        # Fetch da API
        raw_data = self._call_api(game_id, source)
        
        # Normalizar
        normalized = normalize_odds(raw_data, source)
        
        return normalized
```

---

## 12. TROUBLESHOOTING

### 12.1 API Não Responde

```bash
# Verificar status da API
curl -I https://api.fanduel.com

# Verificar credenciais
vbq-cli system health --full

# Testar manualmente
python scripts/test_odds_api.py --source fanduel
```

### 12.2 Rate Limit Atingido

```bash
# Verificar rate limit atual
redis-cli GET rate_limit:fanduel

# Aumentar intervalo entre requests
# Editar config.yaml: odds.fetch_interval_seconds: 2
```

### 12.3 Odds Inconsistentes

```bash
# Verificar últimas odds de todas as casas
vbq-cli report odds --game-id game-123 --compare

# Invalidar cache e re-fetch
redis-cli DEL odds:fanduel:game-123
```

---

## 13. LINKS CRUZADOS

- [[14_APIs/INDEX]] ← Secção mãe
- [[04_Data_Engineering/INGESTAO_ODDS]] → Ingestão detalhada
- [[07_Value_Detection/MOTOR_EDGE]] → Uso de odds no motor de edge
- [[09_Execution_System/CLI_OPERACOES_DIARIAS]] → CLI de ingestão
- [[10_Infrastructure/MONITORIZACAO_INFRA]] → Monitorização de APIs

---

**Custo de implementação:** 0€ (APIs públicas)  
**Tempo estimado de implementação:** 2-3 semanas  
**Prioridade:** ALTA (fundamental para validação de edge real)
