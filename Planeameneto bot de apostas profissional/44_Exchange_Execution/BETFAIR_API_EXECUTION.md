# BETFAIR_API_EXECUTION — Execução Algorítmica Avançada

**ID:** `EXC-001` | **Fase:** #phase/7 | **Owner:** Operations Lead + Dev | **Status:** #status/pending | **Versão:** `2.0.0-ALGORITHMIC`

---

## 1. OBJETIVO

Integração total com Betfair Exchange API para execução algorítmica com limit orders, controlo de slippage e timeouts.

---

## 2. ARQUITETURA DE EXECUÇÃO

```
Sinal aprovado -> Verificar liquidez e odds
                    |
                    v
         Calcular preço limite (slippage control)
                    |
                    v
           Place Limit Order
                    |
                    v
              Monitorizar fill
                    |
          +---------+---------+
          |                   |
    Preenchido          Timeout (30s)
          |                   |
    Confirmar          Cancelar ou
    (registo BD)       aceitar worse price
          |                   |
          v                   v
   Hedge opcional       Registo + alerta
```

---

## 3. LIMIT ORDER COM SLIPPAGE CONTROL

### 3.1 Cálculo de Preço Limite

```python
def calculate_limit_price(current_back_odd, max_slippage_pct=0.5):
    """
    Calcula preço limite com controlo de slippage.
    
    max_slippage_pct: % máximo de slippage aceitável (ex: 0.5% = 0.005)
    """
    # Preço limite é ligeiramente pior que odd atual para garantir execução
    # Mas não excede o slippage máximo
    slippage_factor = 1 - (max_slippage_pct / 100)
    limit_price = current_back_odd * slippage_factor
    
    # Arredondar para tick válido da Betfair
    limit_price = round_to_betfair_tick(limit_price)
    
    return limit_price

def round_to_betfair_tick(price):
    """
    Arredonda preço para tick válido da Betfair.
    """
    # Betfair ticks variam por range de preço
    if price >= 2.0:
        tick_size = 0.01
    elif price >= 1.5:
        tick_size = 0.02
    else:
        tick_size = 0.05
    
    return round(price / tick_size) * tick_size
```

### 3.2 Place Order Avançado

```python
def place_limit_order_advanced(session_token, market_id, selection_id, 
                             current_odd, stake, max_slippage_pct=0.5,
                             timeout_seconds=30):
    """
    Coloca limit order com controlo de slippage e timeout.
    """
    # Calcular preço limite
    limit_price = calculate_limit_price(current_odd, max_slippage_pct)
    
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    headers = {
        "X-Application": os.environ["BETFAIR_APP_KEY"],
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
                "side": "BACK",
                "orderType": "LIMIT",
                "limitOrder": {
                    "size": stake,
                    "price": limit_price,
                    "persistenceType": "LAPSE",  # Cancela se não preenchida
                    "timeInForce": "FILL_OR_KILL"  # Tenta preencher imediatamente
                }
            }]
        },
        "id": 1
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    result = response.json()
    
    return {
        'order_id': result['result']['instructionReports'][0]['orderId'],
        'limit_price': limit_price,
        'status': result['result']['instructionReports'][0]['status'],
        'placed_at': datetime.now()
    }
```

---

## 4. GESTÃO DE ORDENS AVANÇADA

```python
class AdvancedOrderManager:
    def __init__(self, timeout_seconds=30, max_retries=2):
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.orders = {}
    
    def submit_order(self, signal):
        """
        Submete ordem com retry logic.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                order_result = place_limit_order_advanced(
                    session_token=get_session_token(),
                    market_id=signal['market_id'],
                    selection_id=signal['selection_id'],
                    current_odd=signal['current_odd'],
                    stake=signal['stake'],
                    max_slippage_pct=signal.get('max_slippage', 0.5),
                    timeout_seconds=self.timeout
                )
                
                self.orders[order_result['order_id']] = {
                    'signal': signal,
                    'submitted_at': datetime.now(),
                    'status': 'PENDING',
                    'limit_price': order_result['limit_price'],
                    'retries': retries
                }
                
                return order_result
                
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    raise e
                time.sleep(1)  # Wait before retry
    
    def monitor_and_cancel(self, order_id):
        """
        Monitoriza ordem e cancela se timeout.
        """
        order = self.orders[order_id]
        elapsed = (datetime.now() - order['submitted_at']).total_seconds()
        
        if elapsed > self.timeout:
            # Cancelar ordem
            cancel_order(order_id)
            order['status'] = 'CANCELLED_TIMEOUT'
            
            # Tentar aceitar worse price se edge ainda válido
            if self.check_edge_still_valid(order['signal']):
                self.submit_worse_price_order(order['signal'])
    
    def submit_worse_price_order(self, signal):
        """
        Submete ordem com pior preço (mais slippage) se edge ainda válido.
        """
        # Aumentar slippage para 1.0%
        place_limit_order_advanced(
            session_token=get_session_token(),
            market_id=signal['market_id'],
            selection_id=signal['selection_id'],
            current_odd=signal['current_odd'],
            stake=signal['stake'],
            max_slippage_pct=1.0,  # Mais slippage
            timeout_seconds=15  # Menor timeout
        )
    
    def check_edge_still_valid(self, signal):
        """
        Verifica se edge ainda é válido após timeout.
        """
        current_odd = get_current_odd(signal['market_id'], signal['selection_id'])
        current_edge = (signal['p_model'] * current_odd) - 1
        
        return current_edge > 0.02  # Threshold mínimo reduzido
    
    def get_order_status(self, order_id):
        """
        Obtém status atual da ordem da Betfair.
        """
        url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
        headers = {
            "X-Application": os.environ["BETFAIR_APP_KEY"],
            "X-Authentication": get_session_token(),
            "Content-Type": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listCurrentOrders",
            "params": {
                "marketIds": [self.orders[order_id]['signal']['market_id']],
                "orderIds": [order_id]
            },
            "id": 1
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
```

---

## 5. VERIFICAÇÃO DE LIQUIDEZ

```python
def check_liquidity(market_id, selection_id, required_stake):
    """
    Verifica se há liquidez suficiente antes de colocar ordem.
    """
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    headers = {
        "X-Application": os.environ["BETFAIR_APP_KEY"],
        "X-Authentication": get_session_token(),
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketBook",
        "params": {
            "marketId": market_id,
            "priceProjection": ["EX_BEST_OFFERS"]
        },
        "id": 1
    }
    
    response = requests.post(url, json=payload, headers=headers)
    market_book = response.json()
    
    # Verificar volume disponível ao preço atual
    for runner in market_book['result']['runners']:
        if runner['selectionId'] == selection_id:
            available = runner['ex']['availableToBack']
            if available and len(available) > 0:
                available_volume = available[0]['size']
                return available_volume >= required_stake
    
    return False
```

---

## 6. BACKLOG

- [x] Implementar placeOrders e cancelOrders
- [x] Adicionar slippage control
- [x] Implementar retry logic
- [x] Verificação de liquidez antes de ordem
- [ ] Criar gestão de partial fills
- [ ] Implementar hedging automático
- [ ] Testar em ambiente de sandbox
- [ ] Adicionar logging detalhado de execução

---

## 6. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Secao mae
- [[14_APIs/BETFAIR_API]] → API basica
