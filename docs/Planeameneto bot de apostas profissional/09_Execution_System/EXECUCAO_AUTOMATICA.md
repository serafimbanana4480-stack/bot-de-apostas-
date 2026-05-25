# EXECUCAO_AUTOMATICA — Execução Automática de Apostas

**ID:** `EX-001` | **Fase:** #phase/7+ | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar o sistema de execução automática de apostas via API.

---

## 2. ARQUITETURA DE EXECUÇÃO AUTOMÁTICA

### 2.1 Fluxo Completo

```
Sinal Aprovado → Validação Pré-Execução → Betfair API → Confirmação → Registro → Reconciliação
```

### 2.2 Componentes

| Componente | Função | Tecnologia |
|------------|--------|------------|
| Execution Engine | Orquestra execução | Python + FastAPI |
| Betfair API Client | Coloca apostas | Betfair Exchange API |
| Validation Layer | Verifica limites, odds, liquidez | Python + PostgreSQL |
| Order Manager | Gestão de ordens pendentes | Redis + PostgreSQL |
| Reconciliation | Compara execução vs registro | PostgreSQL |

---

## 3. VALIDAÇÃO PRÉ-EXECUÇÃO

### 3.1 Checklist Automático

```python
class PreExecutionValidator:
    """Valida se sinal pode ser executado automaticamente."""
    
    def validate(self, signal: Signal) -> ValidationResult:
        checks = {
            'odd_unchanged': self.check_odd_current(signal),
            'liquidity_ok': self.check_liquidity(signal),
            'exposure_limits': self.check_exposure(signal),
            'circuit_breakers': self.check_circuit_breakers(),
            'market_open': self.check_market_status(signal),
            'latency_acceptable': self.check_latency(),
        }
        
        passed = all(checks.values())
        return ValidationResult(passed=passed, checks=checks)
    
    def check_odd_current(self, signal: Signal) -> bool:
        """Odd atual deve estar dentro de ±2% da odd do sinal."""
        current_odd = self.betfair.get_current_odd(signal.market_id, signal.selection_id)
        slippage = abs(current_odd - signal.odd) / signal.odd
        return slippage <= 0.02
    
    def check_liquidity(self, signal: Signal) -> bool:
        """Liquidez disponível deve ser >= 2x a stake."""
        liquidity = self.betfair.get_available_liquidity(signal.market_id, signal.selection_id)
        return liquidity >= signal.stake * 2
    
    def check_exposure(self, signal: Signal) -> bool:
        """Verificar limites de exposição."""
        daily_exposure = self.db.get_daily_exposure()
        game_exposure = self.db.get_game_exposure(signal.game_id)
        return (daily_exposure + signal.stake <= self.limits.daily_max and
                game_exposure + signal.stake <= self.limits.per_game_max)
    
    def check_circuit_breakers(self) -> bool:
        """Verificar se algum circuit breaker está ativo."""
        return not any(cb.is_triggered() for cb in self.circuit_breakers)
    
    def check_market_status(self, signal: Signal) -> bool:
        """Mercado deve estar aberto e ativo."""
        status = self.betfair.get_market_status(signal.market_id)
        return status == 'OPEN'
    
    def check_latency(self) -> bool:
        """Latência para Betfair < 500ms."""
        latency = self.betfair.ping()
        return latency < 500  # ms
```

---

## 4. EXECUÇÃO VIA BETFAIR API

### 4.1 Colocação de Ordem

```python
class BetfairExecutionClient:
    """Cliente para execução de apostas na Betfair Exchange."""
    
    def __init__(self, app_key: str, session_token: str):
        self.app_key = app_key
        self.session_token = session_token
        self.base_url = "https://api.betfair.com/exchange/betting"
    
    def place_order(
        self,
        market_id: str,
        selection_id: str,
        side: str,  # 'BACK' ou 'LAY'
        size: float,
        price: float,
        persistence_type: str = 'LAPSE'
    ) -> OrderResult:
        """
        Coloca ordem na Betfair Exchange.
        
        Args:
            market_id: ID do mercado (ex: "1.23456789")
            selection_id: ID da seleção
            side: 'BACK' (a favor) ou 'LAY' (contra)
            size: Stake em EUR
            price: Odd decimal (ex: 1.85)
            persistence_type: 'LAPSE' (cancela no início), 'PERSIST' (mantém in-play)
        
        Returns:
            OrderResult com bet_id, status, average_price, etc.
        """
        payload = {
            "marketId": market_id,
            "instructions": [{
                "selectionId": selection_id,
                "handicap": 0,
                "side": side,
                "orderType": "LIMIT",
                "limitOrder": {
                    "size": round(size, 2),
                    "price": round(price, 2),
                    "persistenceType": persistence_type
                }
            }]
        }
        
        response = self._post("/rest/v1.0/placeOrders/", payload)
        
        return OrderResult(
            bet_id=response['instructions'][0]['betId'],
            status=response['instructions'][0]['orderStatus'],
            average_price=response['instructions'][0].get('averageMatchedPrice', price),
            size_matched=response['instructions'][0].get('sizeMatched', 0)
        )
    
    def cancel_order(self, market_id: str, bet_id: str) -> bool:
        """Cancela ordem não executada."""
        payload = {
            "marketId": market_id,
            "instructions": [{"betId": bet_id}]
        }
        response = self._post("/rest/v1.0/cancelOrders/", payload)
        return response['status'] == 'SUCCESS'
    
    def get_current_odd(self, market_id: str, selection_id: str) -> float:
        """Obtém odd atual do mercado."""
        payload = {
            "marketIds": [market_id],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS"],
                "virtualise": True
            }
        }
        response = self._post("/rest/v1.0/listMarketBook/", payload)
        
        for runner in response[0]['runners']:
            if str(runner['selectionId']) == selection_id:
                # Melhor odd de back
                if runner.get('ex', {}).get('availableToBack'):
                    return runner['ex']['availableToBack'][0]['price']
        return 0.0
    
    def get_available_liquidity(self, market_id: str, selection_id: str) -> float:
        """Obtém liquidez disponível na odd atual."""
        payload = {
            "marketIds": [market_id],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS"]
            }
        }
        response = self._post("/rest/v1.0/listMarketBook/", payload)
        
        for runner in response[0]['runners']:
            if str(runner['selectionId']) == selection_id:
                if runner.get('ex', {}).get('availableToBack'):
                    return runner['ex']['availableToBack'][0]['size']
        return 0.0
```

### 4.2 Simulação de Execução (Paper Mode)

```python
class SimulatedExecutionClient:
    """Simula execução sem colocar apostas reais."""
    
    def place_order(self, **kwargs) -> OrderResult:
        """Simula colocação de ordem."""
        # Simular slippage: 50% das vezes com slippage de -0.5% a -2%
        import random
        if random.random() < 0.5:
            slippage = random.uniform(-0.02, -0.005)
            actual_price = kwargs['price'] * (1 + slippage)
        else:
            actual_price = kwargs['price']
        
        return OrderResult(
            bet_id=f"SIM-{uuid4().hex[:8]}",
            status='EXECUTION_COMPLETE',
            average_price=round(actual_price, 2),
            size_matched=kwargs['size']
        )
```

---

## 5. GESTÃO DE ORDENS

### 5.1 Estados de Ordem

| Estado | Descrição | Ação |
|--------|-----------|------|
| PENDING | Ordem colocada, aguardando match | Monitorizar a cada 5s |
| PARTIALLY_MATCHED | Parte da ordem executada | Aguardar ou cancelar |
| EXECUTION_COMPLETE | Ordem totalmente executada | Registrar e notificar |
| EXPIRED | Ordem expirou (início do jogo) | Registrar como não executada |
| CANCELLED | Ordem cancelada manualmente | Registrar motivo |

### 5.2 Timeout de Execução

```python
class OrderManager:
    """Gerencia ordens pendentes e timeouts."""
    
    TIMEOUT_SECONDS = 60  # Cancelar após 60s se não executada
    
    async def monitor_orders(self):
        """Monitoriza ordens pendentes e cancela se timeout."""
        while True:
            pending = self.db.get_pending_orders()
            for order in pending:
                elapsed = (datetime.now() - order.created_at).total_seconds()
                if elapsed > self.TIMEOUT_SECONDS:
                    self.betfair.cancel_order(order.market_id, order.bet_id)
                    self.db.update_order_status(order.bet_id, 'CANCELLED_TIMEOUT')
                    logger.warning(f"Ordem {order.bet_id} cancelada por timeout")
            await asyncio.sleep(5)
```

---

## 6. RECONCILIAÇÃO

### 6.1 Processo de Reconciliação

```python
class ReconciliationEngine:
    """Reconcilia apostas executadas com registro interno."""
    
    def reconcile(self, date: date) -> ReconciliationReport:
        """
        1. Obter todas as apostas do dia da Betfair API
        2. Comparar com registro interno
        3. Identificar discrepâncias
        4. Gerar relatório
        """
        betfair_bets = self.betfair.get_settled_bets(date)
        internal_bets = self.db.get_bets_by_date(date)
        
        discrepancies = []
        for bb in betfair_bets:
            ib = next((b for b in internal_bets if b.bet_id == bb.bet_id), None)
            if ib is None:
                discrepancies.append(f"Aposta {bb.bet_id} na Betfair mas não no sistema")
            elif abs(ib.stake - bb.stake) > 0.01:
                discrepancies.append(f"Stake diferente: sistema={ib.stake}, betfair={bb.stake}")
        
        return ReconciliationReport(
            date=date,
            total_betfair=len(betfair_bets),
            total_internal=len(internal_bets),
            discrepancies=discrepancies
        )
```

---

## 7. RISCOS E MITIGAÇÕES

| Risco | Mitigação |
|-------|-----------|
| API indisponível | Fallback para execução manual (one-click) |
| Ordem parcialmente match | Cancelar restante ou aceitar stake menor |
| Slippage excessivo | Validar odd antes de executar; rejeitar se > 2% |
| Rate limiting da Betfair | Respeitar limites; backoff exponencial |
| Erro de autenticação | Renovar token automaticamente; alertar se falhar |
| Ordem duplicada | Verificar bet_id único antes de colocar |

---

## 8. BACKLOG

- [x] Documentar arquitetura de execução automática
- [x] Implementar validação pré-execução com 6 checks
- [x] Documentar Betfair API client (placeOrder, cancelOrder, getCurrentOdd)
- [x] Implementar simulação de execução (paper mode)
- [x] Documentar gestão de ordens e timeout
- [x] Documentar reconciliação automática
- [ ] Implementar integração real com Betfair API (Fase 7+)
- [ ] Testar com conta demo Betfair
- [ ] Implementar fallback para execução manual

---

## 9. LINKS CRUZADOS

- [[09_Execution_System/INDEX]] ← Secção mãe
- [[09_Execution_System/EXECUCAO_MANUAL]] → Execução manual (Fase 4)
- [[09_Execution_System/ONE_CLICK_BETTING]] → One-click betting (Fase 6)
- [[44_Exchange_Execution/BETFAIR_EXECUTION]] → Detalhes da API Betfair
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
