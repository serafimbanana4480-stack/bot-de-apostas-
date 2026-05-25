# Rate Limits - Gestão de Limites de APIs Gratuitas

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Documentação completa de estratégias de rate limiting para APIs gratuitas, garantindo uso sustentável sem bloqueios.

---

## 📊 TABELA DE RATE LIMITS

| API | Limite Gratuito | Período | Estratégia |
|-----|----------------|---------|------------|
| NBA API | Ilimitado | N/A | Uso generoso com delays |
| The-Odds-API | 500 requests | 1 dia | Rate limiting estrito |
| Basketball-Reference | ~1 req/sec | Informal | Delays de 1-2 segundos |
| GitHub API | 5000 req/hour | 1 hora | Cache agressivo |
| Sportsbookreview | ~1 req/sec | Informal | Delays + proxies |

---

## 🎯 ESTRATÉGIAS DE RATE LIMITING

### **Estratégia 1: Rate Limiter Simples (Sliding Window)**
```python
"""
Rate limiter com sliding window - implementação robusta
Garante que não excede max_requests em time_window
"""

import time
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

class SlidingWindowRateLimiter:
    """Rate limiter com sliding window"""
    
    def __init__(self, max_requests, time_window_seconds):
        self.max_requests = max_requests
        self.time_window = time_window_seconds
        self.requests = deque()
        self.lock = None  # Para uso com threading se necessário
    
    def _clean_old_requests(self):
        """Remove requests fora da janela temporal"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def acquire(self, block=True, timeout=None):
        """Tenta adquirir um token do rate limiter"""
        self._clean_old_requests()
        
        if len(self.requests) < self.max_requests:
            # Token disponível
            self.requests.append(datetime.now())
            return True
        
        if not block:
            return False
        
        # Calcular tempo de espera
        oldest = self.requests[0]
        wait_time = (oldest + timedelta(seconds=self.time_window)) - datetime.now()
        wait_seconds = max(0, wait_time.total_seconds())
        
        if timeout is not None and wait_seconds > timeout:
            return False
        
        logger.info(f"⏳ Rate limit atingido. Aguardando {wait_seconds:.1f}s...")
        time.sleep(wait_seconds)
        
        # Tentar novamente após espera
        self._clean_old_requests()
        if len(self.requests) < self.max_requests:
            self.requests.append(datetime.now())
            return True
        
        return False
    
    def get_remaining_requests(self):
        """Retorna número de requests restantes na janela"""
        self._clean_old_requests()
        return max(0, self.max_requests - len(self.requests))
    
    def get_reset_time(self):
        """Retorna timestamp quando o rate limit resetará"""
        if not self.requests:
            return datetime.now()
        
        oldest = self.requests[0]
        return oldest + timedelta(seconds=self.time_window)
    
    def reset(self):
        """Reseta o rate limiter"""
        self.requests.clear()

# Uso para The-Odds-API (500 requests/day)
odds_limiter = SlidingWindowRateLimiter(max_requests=500, time_window_seconds=86400)

for i in range(505):
    if odds_limiter.acquire():
        logger.info(f"✅ Request {i+1} permitido")
        # Fazer request...
    else:
        logger.warning(f"❌ Request {i+1} bloqueado")
    
    logger.info(f"📊 Requests restantes: {odds_limiter.get_remaining_requests()}")
```

### **Estratégia 2: Exponential Backoff com Jitter e Circuit Breaker**
```python
"""
Exponential backoff com jitter para evitar thundering herd
Inclui circuit breaker para evitar chamadas a serviços degradados
"""

import time
import random
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Estados do circuit breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Circuito aberto, rejeita requests
    HALF_OPEN = "half_open"  # Testando se serviço recuperou

class CircuitBreaker:
    """Circuit breaker para evitar chamadas a serviços degradados"""
    
    def __init__(
        self,
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # segundos
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def _should_attempt_reset(self):
        """Verifica se deve tentar resetar o circuito"""
        if self.state != CircuitState.OPEN:
            return False
        
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função com circuit breaker"""
        # Se circuito está aberto, verificar se deve tentar reset
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("🔄 Tentando resetar circuit breaker...")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker está OPEN - serviço indisponível")
        
        try:
            result = func(*args, **kwargs)
            
            # Sucesso - resetar contagem e fechar circuito
            if self.state == CircuitState.HALF_OPEN:
                logger.info("✅ Serviço recuperado, fechando circuit breaker")
                self.state = CircuitState.CLOSED
            
            self.failure_count = 0
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            logger.error(f"❌ Falha {self.failure_count}/{self.failure_threshold}: {e}")
            
            # Se atingiu threshold, abrir circuito
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"🚨 Circuit breaker OPEN após {self.failure_count} falhas")
            
            raise

class ExponentialBackoff:
    """Exponential backoff com jitter e circuit breaker"""
    
    def __init__(
        self,
        max_retries=5,
        base_delay=1,
        max_delay=60,
        jitter_range=0.5,
        enable_circuit_breaker=True,
        circuit_failure_threshold=5
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_range = jitter_range
        
        self.circuit_breaker = None
        if enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=circuit_failure_threshold,
                recovery_timeout=60,
                expected_exception=Exception
            )
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função com retry e backoff"""
        # Usar circuit breaker se habilitado
        if self.circuit_breaker:
            return self.circuit_breaker.call(
                self._retry_with_backoff,
                func,
                *args,
                **kwargs
            )
        else:
            return self._retry_with_backoff(func, *args, **kwargs)
    
    def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Implementação interna de retry com backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries - 1:
                    logger.error(f"❌ Falha após {self.max_retries} tentativas")
                    raise
                
                # Calcular delay com exponential backoff + jitter
                exponential_delay = self.base_delay * (2 ** attempt)
                jitter = random.uniform(-self.jitter_range, self.jitter_range)
                delay = min(
                    exponential_delay + jitter,
                    self.max_delay
                )
                delay = max(0, delay)  # Garantir delay não negativo
                
                logger.warning(
                    f"⚠️  Tentativa {attempt + 1}/{self.max_retries} falhou. "
                    f"Aguardando {delay:.1f}s antes de retry..."
                )
                time.sleep(delay)
        
        # Se chegou aqui, todas as tentativas falharam
        raise last_exception
    
    def get_circuit_state(self):
        """Retorna estado do circuit breaker"""
        if self.circuit_breaker:
            return self.circuit_breaker.state.value
        return "disabled"

# Uso
backoff = ExponentialBackoff(
    max_retries=5,
    base_delay=1,
    max_delay=60,
    jitter_range=0.5,
    enable_circuit_breaker=True
)

def make_request(url):
    """Exemplo de função com possíveis falhas"""
    import requests
    response = requests.get(url, timeout=10)
    if response.status_code == 429:
        raise Exception("Rate limit")
    elif response.status_code >= 500:
        raise Exception("Server error")
    return response.json()

# Executar com retry
try:
    result = backoff.execute_with_retry(
        make_request,
        "https://api.example.com/data"
    )
    logger.info(f"✅ Request bem-sucedido")
except Exception as e:
    logger.error(f"❌ Request falhou: {e}")
    logger.info(f"Estado circuit breaker: {backoff.get_circuit_state()}")
```

### **Estratégia 3: Token Bucket**
```python
import time

class TokenBucket:
    """Token bucket para rate limiting"""
    
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens por segundo
        self.last_refill = time.time()
    
    def consume(self, tokens=1):
        """Consome tokens se disponíveis"""
        now = time.time()
        
        # Refill tokens
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        # Consumir se disponível
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def wait_for_token(self, tokens=1):
        """Aguarda até token disponível"""
        while not self.consume(tokens):
            wait_time = (tokens - self.tokens) / self.refill_rate
            time.sleep(wait_time)

# Uso: 10 requests por segundo
bucket = TokenBucket(capacity=10, refill_rate=10)

for i in range(15):
    bucket.wait_for_token()
    # Fazer request...
    print(f"Request {i+1}")
```

---

## 🏀 NBA API RATE LIMITING

### **Estratégia: Delays Conservativos**
```python
import time

class NBARateLimiter:
    """Rate limiter para NBA API (ilimitado mas com delays)"""
    
    def __init__(self, delay=0.5):
        self.delay = delay  # segundos entre requests
    
    def execute(self, func, *args, **kwargs):
        """Executa com delay"""
        time.sleep(self.delay)
        return func(*args, **kwargs)

# Uso
nba_limiter = NBARateLimiter(delay=0.5)

from nba_api.stats.endpoints import leaguegamefinder

for i in range(10):
    result = nba_limiter.execute(leaguegamefinder.LeagueGameFinder)
    print(f"Request {i+1}")
```

---

## 🎲 THE-ODDS-API RATE LIMITING

### **Estratégia: Rate Limiter Diário**
```python
import requests
import os
from datetime import datetime, timedelta

class TheOddsAPIRateLimiter:
    """Rate limiter específico para The-Odds-API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.max_requests = 500
        self.requests_today = []
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def check_quota(self):
        """Verifica quota disponível"""
        today = datetime.now().date()
        
        # Limpar requests de dias anteriores
        self.requests_today = [
            r for r in self.requests_today 
            if r.date() == today
        ]
        
        used = len(self.requests_today)
        remaining = self.max_requests - used
        
        print(f"Quota: {used}/{self.max_requests} usados ({remaining} restantes)")
        return remaining > 0
    
    def make_request(self, endpoint, params=None):
        """Faz request com rate limiting"""
        if not self.check_quota():
            raise Exception("Quota diária esgotada")
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        try:
            response = requests.get(url, params=params)
            
            # Registar request
            self.requests_today.append(datetime.now())
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                raise Exception("Rate limit atingido")
            else:
                raise Exception(f"Erro {response.status_code}")
                
        except Exception as e:
            print(f"Erro request: {e}")
            return None
    
    def get_remaining_quota(self):
        """Retorna quota restante"""
        today = datetime.now().date()
        self.requests_today = [
            r for r in self.requests_today 
            if r.date() == today
        ]
        return self.max_requests - len(self.requests_today)

# Uso
API_KEY = os.getenv("THE_ODDS_API_KEY")
limiter = TheOddsAPIRateLimiter(API_KEY)

# Fazer requests
for i in range(10):
    odds = limiter.make_request("sports/basketball_nba/odds")
    print(f"Request {i+1}: Quota restante {limiter.get_remaining_quota()}")
```

---

## 📊 BASKETBALL-REFERENCE RATE LIMITING

### **Estratégia: Delays Adaptativos**
```python
import time
import random

class BasketballReferenceRateLimiter:
    """Rate limiter para scraping de Basketball-Reference"""
    
    def __init__(self, base_delay=1.0, max_delay=5.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.consecutive_errors = 0
    
    def execute(self, func, *args, **kwargs):
        """Executa com delay adaptativo"""
        # Calcular delay baseado em erros anteriores
        delay = min(
            self.base_delay * (1 + self.consecutive_errors * 0.5),
            self.max_delay
        )
        
        # Adicionar jitter
        delay += random.uniform(0, 0.5)
        
        print(f"Aguardando {delay:.1f}s...")
        time.sleep(delay)
        
        try:
            result = func(*args, **kwargs)
            self.consecutive_errors = 0  # Reset em sucesso
            return result
        except Exception as e:
            self.consecutive_errors += 1
            print(f"Erro: {e}. Aumentando delay...")
            raise

# Uso
br_limiter = BasketballReferenceRateLimiter(base_delay=1.5)

import basketball_reference_web_scraper as br

for year in range(2020, 2024):
    try:
        stats = br_limiter.execute(br.team_season_stats, season_end_year=year)
        print(f"✅ Ano {year}: {len(stats)} registos")
    except Exception as e:
        print(f"❌ Ano {year}: {e}")
```

---

## 🔄 CACHE PARA REDUZIR REQUESTS

### **Estratégia: Cache em Memória**
```python
import time
from functools import lru_cache
from datetime import datetime, timedelta

class APICache:
    """Cache simples para reduzir requests"""
    
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl  # tempo de vida em segundos
    
    def get(self, key):
        """Obter do cache"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                print(f"✅ Cache hit: {key}")
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        """Guardar no cache"""
        self.cache[key] = (value, datetime.now())
        print(f"💾 Cache set: {key}")
    
    def clear(self):
        """Limpar cache"""
        self.cache.clear()

# Uso
cache = APICache(ttl=3600)  # 1 hora

def get_nba_games(team_id):
    cache_key = f"nba_games_{team_id}"
    
    # Tentar obter do cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Se não em cache, fazer request
    data = fetch_nba_games(team_id)
    cache.set(cache_key, data)
    return data
```

### **Estratégia: Cache com LRU**
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_nba_request(endpoint, params_hash):
    """Request com cache LRU"""
    return make_nba_request(endpoint, params_hash)

# Uso
# Primeira request: faz API call
result1 = cached_nba_request("games", "params123")

# Segunda request com mesmos params: usa cache
result2 = cached_nba_request("games", "params123")

# Ver estatísticas do cache
print(f"Cache info: {cached_nba_request.cache_info()}")
```

---

## 📋 PIPELINE COMPLETO DE RATE LIMITING

### **Integração de Todas as Estratégias**
```python
class UnifiedRateLimiter:
    """Rate limiter unificado para todas as APIs"""
    
    def __init__(self):
        self.odds_limiter = TheOddsAPIRateLimiter(os.getenv("THE_ODDS_API_KEY"))
        self.br_limiter = BasketballReferenceRateLimiter()
        self.nba_limiter = NBARateLimiter()
        self.cache = APICache(ttl=3600)
    
    def get_nba_data(self, team_id):
        """Obter dados NBA com cache"""
        cache_key = f"nba_{team_id}"
        
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Fazer request com rate limiting
        data = self.nba_limiter.execute(fetch_nba_games, team_id)
        self.cache.set(cache_key, data)
        return data
    
    def get_odds(self, game_id):
        """Obter odds com rate limiting"""
        return self.odds_limiter.make_request(f"sports/basketball_nba/odds/{game_id}")
    
    def scrape_br_data(self, year):
        """Scrape Basketball-Reference com rate limiting"""
        return self.br_limiter.execute(br.team_season_stats, season_end_year=year)

# Uso
limiter = UnifiedRateLimiter()

# Obter dados com rate limiting automático
nba_data = limiter.get_nba_data("LAL")
odds = limiter.get_odds("game123")
br_data = limiter.scrape_br_data(2023)
```

---

## 📊 MONITORING DE RATE LIMITS

### **Dashboard de Uso de APIs**
```python
class RateLimitMonitor:
    """Monitor de uso de rate limits"""
    
    def __init__(self):
        self.usage = {
            'nba_api': {'requests': 0, 'errors': 0},
            'odds_api': {'requests': 0, 'errors': 0},
            'br_scraper': {'requests': 0, 'errors': 0}
        }
    
    def log_request(self, api_name, success=True):
        """Registra request"""
        self.usage[api_name]['requests'] += 1
        if not success:
            self.usage[api_name]['errors'] += 1
    
    def get_stats(self):
        """Obter estatísticas"""
        stats = {}
        for api, data in self.usage.items():
            total = data['requests']
            errors = data['errors']
            success_rate = (total - errors) / total if total > 0 else 0
            
            stats[api] = {
                'total_requests': total,
                'errors': errors,
                'success_rate': f"{success_rate:.2%}"
            }
        
        return stats
    
    def print_report(self):
        """Imprime relatório"""
        print("📊 Relatório de Rate Limits")
        print("="*50)
        
        stats = self.get_stats()
        for api, data in stats.items():
            print(f"\n{api}:")
            print(f"  Requests: {data['total_requests']}")
            print(f"  Erros: {data['errors']}")
            print(f"  Success Rate: {data['success_rate']}")

# Uso
monitor = RateLimitMonitor()

try:
    odds = limiter.get_odds("game123")
    monitor.log_request('odds_api', success=True)
except:
    monitor.log_request('odds_api', success=False)

monitor.print_report()
```

---

## 🚨 ALERTAS DE RATE LIMIT

### **Sistema de Alertas**
```python
class RateLimitAlerts:
    """Sistema de alertas de rate limits"""
    
    def __init__(self, threshold=0.9):
        self.threshold = threshold  # 90% do limite
        self.alerted = False
    
    def check_quota(self, used, total):
        """Verifica se quota está perto do limite"""
        usage_ratio = used / total
        
        if usage_ratio >= self.threshold and not self.alerted:
            self.send_alert(f"⚠️  Quota a {usage_ratio:.1%}: {used}/{total}")
            self.alerted = True
        
        if usage_ratio < self.threshold * 0.8:
            self.alerted = False  # Reset alerta
    
    def send_alert(self, message):
        """Envia alerta"""
        print(f"🚨 ALERTA: {message}")
        # Aqui poderia integrar com Telegram, email, etc.

# Uso
alerts = RateLimitAlerts(threshold=0.8)

for i in range(450):
    alerts.check_quota(i, 500)
    # Fazer requests...
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **Rate Limiting The-Odds-API**
- [ ] Rate limiter diário implementado
- [ ] Verificação de quota antes de requests
- [ ] Cache para reduzir requests
- [ ] Alertas de limite próximo
- [ ] Logging de uso

### **Rate Limiting Basketball-Reference**
- [ ] Delays adaptativos implementados
- [ ] Backoff em erros
- [ ] Jitter para evitar bloqueios
- [ ] User-Agent rotation
- [ ] Cache de dados

### **Rate Limiting NBA API**
- [ ] Delays conservativos
- [ ] Cache de resultados
- [ ] Monitoring de uso
- [ ] Error handling
- [ ] Logging detalhado

### **Monitoring**
- [ ] Dashboard de uso
- [ ] Alertas automáticos
- [ ] Relatórios diários
- [ ] Análise de padrões
- [ ] Otimização contínua

---

## 🎯 MELHORES PRÁTICAS

### **Regras Gerais**
1. **Sempre implementar rate limiting** mesmo se API não tem limite oficial
2. **Usar cache agressivo** para reduzir requests
3. **Implementar backoff** em caso de erros
4. **Monitorar uso** continuamente
5. **Ter planos de contingência** para limites esgotados

### **Priorização de Requests**
```python
# Priorizar requests críticos
CRITICAL_REQUESTS = [
    'odds_atuais',  # Mais importante
    'jogos_hoje',
    'stats_basicas'
]

LOW_PRIORITY_REQUESTS = [
    'stats_historicas',
    'dados_avancados',
    'analises'
]

# Processar críticos primeiro
for request in CRITICAL_REQUESTS:
    process_request(request)

# Processar low priority se quota disponível
if limiter.get_remaining_quota() > 50:
    for request in LOW_PRIORITY_REQUESTS:
        process_request(request)
```

---

**Status:** Rate limiting documentado  
**Custo:** 0€  
**Cobertura:** Todas as APIs gratuitas  

---

#status/active #priority/critical #phase/dados-gratuitos
