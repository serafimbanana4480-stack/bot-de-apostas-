# BETFAIR_API — Integracao Betfair Exchange

**ID:** `API-002` | **Fase:** #phase/3 | **Owner:** Operations Lead + Dev | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar a integracao com a Betfair Exchange API para obtencao de odds em tempo real e (futuramente) execucao automatica de apostas.

---

## 2. CREDENCIAIS E SETUP

1. Criar conta Betfair Exchange (nao Sportsbook)
2. Aceder a https://developer.betfair.com/
3. Criar app e obter:
   - App Key (de desenvolvimento)
   - Session Token (via login com username/password)

**Variaveis de ambiente:**
```bash
BETFAIR_APP_KEY=seu_app_key
BETFAIR_USERNAME=seu_username
BETFAIR_PASSWORD=sua_password
```

---

## 3. AUTENTICACAO

```python
import requests
import os

BETFAIR_API_URL = "https://api.betfair.com/exchange/account/json-rpc/v1"

def get_session_token():
    url = "https://identitysso-cert.betfair.com/api/certlogin"
    payload = {
        "username": os.environ["BETFAIR_USERNAME"],
        "password": os.environ["BETFAIR_PASSWORD"]
    }
    headers = {
        "X-Application": os.environ["BETFAIR_APP_KEY"],
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, data=payload, headers=headers)
    return response.json()["sessionToken"]
```

---

## 4. LISTAR MERCADOS (NBA)

```python
def list_nba_markets(session_token, app_key):
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketCatalogue",
        "params": {
            "filter": {
                "eventTypeIds": ["7522"],  # Basquetebol
                "marketCountries": ["US"],
                "textQuery": "NBA"
            },
            "maxResults": 100,
            "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME", "EVENT"]
        },
        "id": 1
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

---

## 5. OBTER ODDS (Market Book)

```python
def get_market_odds(session_token, app_key, market_id):
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketBook",
        "params": {
            "marketIds": [market_id],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS"]
            }
        },
        "id": 1
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

---

## 6. RATE LIMITS DETALHADOS

### 6.1 Limites por Endpoint

| Endpoint | Limite Base | Limite Burst | Observação |
|----------|-------------|--------------|------------|
| `listMarketCatalogue` | 20/seg | 100/5min | Dev account |
| `listMarketBook` | 20/seg | 100/5min | Dev account |
| `placeOrders` | 20/seg | 100/5min | Dev account |
| `cancelOrders` | 20/seg | 100/5min | Dev account |
| `replaceOrders` | 20/seg | 100/5min | Dev account |
| `listCurrentOrders` | 20/seg | 100/5min | Dev account |
| `listClearedOrders` | 20/seg | 100/5min | Dev account |
| Streaming API | Ilimitado | Ilimitado | Requer conexão dedicada |

### 6.2 Limites por Tipo de Conta

| Tipo de Conta | Requisitos | Rate Limit | Streaming |
|---------------|------------|------------|-----------|
| Desenvolvedor | App Key gratuita | 100 req/5min | Não |
| Interactive | €200/mês | 200 req/5min | Sim |
| Professional | Licença necessária | 1000 req/5min | Sim |

### 6.3 Estratégia de Rate Limiting

```python
import time
from collections import deque
from threading import Lock

class BetfairRateLimiter:
    """Rate limiter para Betfair API com sliding window"""
    
    def __init__(self, max_requests=100, window_seconds=300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = Lock()
    
    def wait(self):
        """Aguarda se necessário para respeitar rate limit"""
        with self.lock:
            now = time.time()
            
            # Remover requests fora da janela
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()
            
            # Se atingiu limite, esperar
            if len(self.requests) >= self.max_requests:
                sleep_time = self.window_seconds - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Limpar novamente após sleep
                    while self.requests and self.requests[0] < time.time() - self.window_seconds:
                        self.requests.popleft()
            
            self.requests.append(now)
```

---

## 7. AUTENTICAÇÃO AVANÇADA

### 7.1 Certificado SSL (Production)

Para produção, Betfair exige autenticação com certificado SSL:

```bash
# Gerar chave privada
openssl genrsa -out betfair_client.key 2048

# Gerar CSR
openssl req -new -key betfair_client.key -out betfair_client.csr

# Submeter CSR a Betfair para assinatura
# Receber betfair_client.crt

# Combinar certificado e chave
cat betfair_client.crt betfair_client.key > betfair_client.pem
```

### 7.2 Login com Certificado

```python
import requests
import os

def login_with_cert(app_key, cert_path='betfair_client.pem'):
    """Login usando certificado SSL (production)"""
    url = "https://identitysso.betfair.com/api/certlogin"
    
    payload = {
        "username": os.environ["BETFAIR_USERNAME"],
        "password": os.environ["BETFAIR_PASSWORD"]
    }
    
    headers = {
        "X-Application": app_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    cert = cert_path
    
    response = requests.post(url, data=payload, headers=headers, cert=cert)
    response.raise_for_status()
    
    return response.json()["sessionToken"]
```

### 7.3 Renovação de Sessão

```python
def keep_alive(session_token, app_key):
    """Mantém sessão ativa"""
    url = "https://identitysso.betfair.com/api/keepAlive"
    
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    return response.json()["status"] == "SUCCESS"
```

### 7.4 Logout

```python
def logout(session_token, app_key):
    """Termina sessão explicitamente"""
    url = "https://identitysso.betfair.com/api/logout"
    
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    return response.json()["status"] == "SUCCESS"
```

---

## 8. STREAMING API

### 8.1 Visão Geral

A Streaming API permite receber atualizações de odds em tempo real via WebSocket, evitando polling excessivo.

**Vantagens:**
- Latência reduzida (< 100ms)
- Menor consumo de rate limit
- Atualizações incrementais (delta)

**Desvantagens:**
- Complexidade de implementação
- Requer gerenciamento de conexão
- Necessita reconnection logic

### 8.2 Conexão Streaming

```python
import sseclient
import requests

def connect_to_stream(session_token, app_key):
    """Conecta ao streaming API"""
    url = "https://stream-api.betfair.com/rest/stream"
    
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    # Subscription para market updates
    payload = {
        "op": "authentication",
        "appKey": app_key,
        "session": session_token
    }
    
    response = requests.post(url, json=payload, headers=headers, stream=True)
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        data = json.loads(event.data)
        process_stream_update(data)
```

### 8.3 Subscription para Mercados

```python
def subscribe_to_markets(market_ids):
    """Subscreve para atualizações de mercados específicos"""
    subscription = {
        "op": "marketSubscription",
        "marketFilter": {
            "marketIds": market_ids
        },
        "marketDataFilter": {
            "fields": [
                "EX_ALL_OFFERS",
                "EX_TRADED",
                "EX_TRADED_VOL",
                "EX_LTP",
                "SP_AVAILABLE",
                "SP_TRADED"
            ]
        }
    }
    return subscription
```

### 8.4 Gerenciamento de Conexão

```python
import threading
import time

class BetfairStreamManager:
    """Gerencia conexão streaming com auto-reconnect"""
    
    def __init__(self, session_token, app_key):
        self.session_token = session_token
        self.app_key = app_key
        self.connected = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 300
    
    def connect(self):
        """Conecta com auto-reconnect"""
        while True:
            try:
                self._do_connect()
                self.reconnect_delay = 5  # Reset delay
            except Exception as e:
                logger.error(f"Stream connection failed: {e}")
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    def _do_connect(self):
        """Implementação da conexão"""
        # Implementação real da conexão
        pass
```

---

## 9. TRATAMENTO DE ERROS

### 9.1 Códigos de Erro Betfair

| Código | Significado | Ação |
|--------|-------------|------|
| `INVALID_SESSION_TOKEN` | Sessão expirada | Reautenticar |
| `NO_APP_KEY` | App Key inválida | Verificar credenciais |
| `INVALID_APP_KEY` | App Key inválida | Verificar credenciais |
| `TOO_MANY_REQUESTS` | Rate limit excedido | Esperar e retry |
| `SERVICE_BUSY` | Servidor ocupado | Retry com backoff |
| `TIMEOUT` | Timeout da requisição | Retry com backoff |
| `MARKET_NOT_FOUND` | Mercado não encontrado | Verificar market_id |
| `INSUFFICIENT_FUNDS` | Saldo insuficiente | Não retry |

### 9.2 Wrapper com Tratamento de Erros

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class BetfairAPIError(Exception):
    """Erro base da API Betfair"""
    pass

class SessionExpiredError(BetfairAPIError):
    """Sessão expirada"""
    pass

class RateLimitError(BetfairAPIError):
    """Rate limit excedido"""
    pass

class BetfairAPIClient:
    """Cliente API Betfair com tratamento de erros"""
    
    def __init__(self, app_key, username, password):
        self.app_key = app_key
        self.username = username
        self.password = password
        self.session_token = None
        self.rate_limiter = BetfairRateLimiter()
    
    def authenticate(self):
        """Autentica e obtém session token"""
        self.session_token = get_session_token()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    def make_request(self, method, params):
        """Faz requisição com retry automático"""
        self.rate_limiter.wait()
        
        try:
            response = self._do_request(method, params)
            
            # Verificar erros na resposta
            if 'error' in response:
                error_code = response['error']['code']
                
                if error_code == 'INVALID_SESSION_TOKEN':
                    raise SessionExpiredError("Session expired")
                elif error_code == 'TOO_MANY_REQUESTS':
                    raise RateLimitError("Rate limit exceeded")
                else:
                    raise BetfairAPIError(f"API error: {error_code}")
            
            return response
            
        except requests.exceptions.Timeout:
            raise BetfairAPIError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise BetfairAPIError(f"Request failed: {e}")
```

### 9.3 Circuit Breaker

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """Circuit breaker para prevenir chamadas a API em falha"""
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Executa função com circuit breaker"""
        if self.state == 'open':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = 'half-open'
            else:
                raise BetfairAPIError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()
            
            if self.failures >= self.failure_threshold:
                self.state = 'open'
            
            raise
```

---

## 10. CASOS DE USO

### 10.1 Polling de Odds (Fase 1)

**Objetivo:** Obter odds a cada 5 minutos

```python
def poll_odds(market_ids, interval_minutes=5):
    """Polling de odds para mercados específicos"""
    while True:
        for market_id in market_ids:
            try:
                odds = get_market_odds(session_token, app_key, market_id)
                save_odds_to_db(market_id, odds)
            except Exception as e:
                logger.error(f"Failed to get odds for {market_id}: {e}")
        
        time.sleep(interval_minutes * 60)
```

### 10.2 Streaming de Odds (Fase 2+)

**Objetivo:** Receber odds em tempo real

```python
def stream_odds(market_ids):
    """Streaming de odds em tempo real"""
    stream_manager = BetfairStreamManager(session_token, app_key)
    
    # Subscrever para mercados
    subscription = subscribe_to_markets(market_ids)
    stream_manager.subscribe(subscription)
    
    # Processar atualizações
    for update in stream_manager.stream():
        process_odds_update(update)
```

### 10.3 Execução Manual (One-Click Betting)

**Objetivo:** Gerar deep links para execução manual

```python
def generate_deep_link(market_id, selection_id, odds, stake):
    """Gera deep link para execução manual"""
    base_url = "https://www.betfair.com/exchange/football"
    
    params = {
        "marketId": market_id,
        "selectionId": selection_id,
        "odds": odds,
        "stake": stake
    }
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{query_string}"
```

### 10.4 Execução Automática (Fase 3)

**Objetivo:** Executar apostas automaticamente

```python
def place_bet(market_id, selection_id, odds, stake, side='BACK'):
    """Executa aposta automaticamente"""
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/placeOrders",
        "params": {
            "marketId": market_id,
            "instructions": [{
                "selectionId": selection_id,
                "handicap": 0,
                "side": side,
                "orderType": "LIMIT",
                "limitOrder": {
                    "size": stake,
                    "price": odds,
                    "persistenceType": "LAPSE"
                }
            }],
            "customerRef": f"bet_{datetime.now().isoformat()}"
        },
        "id": 1
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

---

## 11. BACKLOG

- [x] Detalhar autenticação com certificado SSL
- [x] Documentar Streaming API
- [x] Adicionar tratamento de erros completo
- [x] Implementar circuit breaker
- [x] Adicionar casos de uso detalhados
- [ ] Implementar wrapper com cache e retry
- [ ] Mapear market_ids para jogos NBA
- [ ] Implementar polling de odds a cada 5 minutos
- [ ] Documentar deep links para one-click betting (Fase 2)
- [ ] Implementar placeOrders para execucao automatica (Fase 3)

---

## 12. LINKS CRUZADOS

- [[14_APIs/INDEX]] ← Secao mae
- [[09_Execution_System/INDEX]] → Execucao de apostas
- [[44_Exchange_Execution/INDEX]] → Execucao avancada em exchange
- [[13_Infrastructure/VPS_CONFIGURACAO]] → Configuração de firewall e SSL
