# BETFAIR_EXECUTION — Execução Automática via API

**ID:** `EXE-001` | **Fase:** #phase/7-12 | **Owner:** DevOps Lead + Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Especificar a implementação de execução automática de apostas via Betfair API, incluindo gestão de ordens, tratamento de erros, e reconciliação. A execução automática elimina erro humano e reduz latência, mas requer robustez extrema.

**Princípio:** Zero confiança na API - validar tudo, assumir falhas, implementar redundância.

---

## 2. ARQUITETURA DO SISTEMA

### 2.1 Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│ SISTEMA DE EXECUÇÃO AUTOMÁTICA BETFAIR                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Signal Queue │───→│ Order Engine │───→│ Betfair API │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ↓                    ↓                    ↓             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Risk Manager │←───│ Order Monitor│←───│ Response    │      │
│  └──────────────┘    └──────────────┘    │ Processor   │      │
│         ↓                    ↓            └──────────────┘      │
│  ┌──────────────┐    ┌──────────────┐            ↓             │
│  │ Reconciler   │←───│ Database     │    ┌──────────────┐      │
│  └──────────────┘    └──────────────┘    │ Alert System│      │
│                                             └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Dados

```
1. Signal Queue
   - Recebe sinais do motor de value
   - Valida filtros de risco
   - Prioriza por CLV esperado

2. Order Engine
   - Prepara ordem Betfair
   - Valida liquidez
   - Envia para API

3. Betfair API
   - Recebe ordem
   - Executa ou rejeita
   - Retorna status

4. Response Processor
   - Processa resposta
   - Atualiza status
   - Trata erros

5. Order Monitor
   - Monitora ordens pendentes
   - Cancela timeouts
   - Atualiza preenchimentos

6. Database
   - Registra todas as ordens
   - Mantém histórico
   - Suporta reconciliação

7. Reconciler
   - Compara com Betfair
   - Identifica discrepâncias
   - Corrige automaticamente

8. Alert System
   - Notifica erros críticos
   - Reporta anomalias
   - Envia resumos diários
```

---

## 3. CONFIGURAÇÃO DA API BETFAIR

### 3.1 Autenticação

```python
import betfairlightweight
from betfairlightweight import APIClient

class BetfairAuth:
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.app_key = config['app_key']
        self.cert_file = config['cert_file']
        self.key_file = config['key_file']

    def get_client(self):
        """Inicializa cliente Betfair com autenticação"""
        trading = betfairlightweight.APIClient(
            username=self.username,
            password=self.password,
            app_key=self.app_key,
            certs=self.cert_file,
        )

        # Login
        trading.login()

        return trading
```

### 3.2 Configuração de Conexão

```python
BETFAIR_CONFIG = {
    # Autenticação
    'username': 'your_username',
    'password': 'your_password',
    'app_key': 'your_app_key',
    'cert_file': '/path/to/certificate.crt',
    'key_file': '/path/to/private.key',

    # Conexão
    'endpoint': 'https://api.betfair.com/exchange/betting/json-rpc/v1',
    'timeout': 30,  # segundos
    'max_retries': 3,
    'retry_delay': 1,  # segundos

    # Limits
    'rate_limit': 1000,  # requests/hour
    'concurrent_orders': 50,
    'max_order_value': 10000,  # €

    # Execution
    'default_timeout': 60,  # segundos para preenchimento
    'max_slippage': 0.01,  # 1%
    'min_liquidity_multiplier': 2,  # stake × 2
}
```

---

## 4. TIPOS DE ORDEM

### 4.1 Limit Order (Padrão)

**Uso:** Ordem a um preço específico ou melhor

```python
def place_limit_order(signal, client):
    """
    Coloca Limit Order na Betfair
    """
    order = betfairlightweight.resources.betting.PlaceOrder(
        market_id=signal.market_id,
        instructions=[
            betfairlightweight.resources.betting.PlaceInstruction(
                selection_id=signal.selection_id,
                side='BACK',  # ou 'LAY'
                order_type='LIMIT',
                limit_order=betfairlightweight.resources.betting.LimitOrder(
                    size=signal.stake,
                    price=signal.odds - 0.01,  # ligeiramente melhor
                    persistence_type='LAPSE'  # cancela se não preenchida
                )
            )
        ],
        customer_ref=signal.signal_id
    )

    response = client.betting.place_orders([order])

    return response
```

**Características:**
- Preço definido
- Tamanho definido
- Timeout configurável
- Cancela se não preenchida

### 4.2 Market Order (Emergência)

**Uso:** Execução imediata a preço de mercado

```python
def place_market_order(signal, client):
    """
    Coloca Market Order (apenas emergência)
    """
    order = betfairlightweight.resources.betting.PlaceOrder(
        market_id=signal.market_id,
        instructions=[
            betfairlightweight.resources.betting.PlaceInstruction(
                selection_id=signal.selection_id,
                side='BACK',
                order_type='LIMIT',
                limit_order=betfairlightweight.resources.betting.LimitOrder(
                    size=signal.stake,
                    price=1.01,  # preço mínimo para garantir preenchimento
                    persistence_type='LAPSE'
                )
            )
        ],
        customer_ref=signal.signal_id
    )

    response = client.betting.place_orders([order])

    return response
```

**Características:**
- Execução imediata
- Slippage imprevisível
- Apenas em emergência
- Requer aprovação manual

### 4.3 Stop Order (Futuro)

**Uso:** Proteção de posição (trailing stop)

```python
def place_stop_order(signal, client, stop_price):
    """
    Coloca Stop Order (para trading, não apostas simples)
    """
    order = betfairlightweight.resources.betting.PlaceOrder(
        market_id=signal.market_id,
        instructions=[
            betfairlightweight.resources.betting.PlaceInstruction(
                selection_id=signal.selection_id,
                side='LAY',
                order_type='LIMIT',
                limit_order=betfairlightweight.resources.betting.LimitOrder(
                    size=signal.stake,
                    price=stop_price,
                    persistence_type='LAPSE'
                )
            )
        ],
        customer_ref=f"{signal.signal_id}_STOP"
    )

    response = client.betting.place_orders([order])

    return response
```

---

## 5. GESTÃO DE ORDENS

### 5.1 Workflow de Execução

```python
class OrderExecutor:
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.client = self._init_client()

    def execute_signal(self, signal):
        """Executa um sinal completamente"""
        try:
            # 1. Validar sinal
            if not self._validate_signal(signal):
                return {'status': 'REJECTED', 'reason': 'Validation failed'}

            # 2. Verificar liquidez
            liquidity = self._check_liquidity(signal)
            if liquidity < signal.stake * self.config['min_liquidity_multiplier']:
                return {'status': 'REJECTED', 'reason': 'Insufficient liquidity'}

            # 3. Colocar ordem
            response = self._place_order(signal)

            # 4. Processar resposta
            if response.status == 'SUCCESS':
                order_id = response.order_id
                self._register_order(signal, order_id)
                self._start_monitoring(order_id)
                return {'status': 'PLACED', 'order_id': order_id}
            else:
                return {'status': 'REJECTED', 'reason': response.error}

        except Exception as e:
            self._handle_error(e, signal)
            return {'status': 'ERROR', 'reason': str(e)}

    def _validate_signal(self, signal):
        """Valida sinal antes de execução"""
        # Verificar timestamp (não expirado)
        if signal.timestamp < datetime.now() - timedelta(minutes=5):
            return False

        # Verificar mercado aberto
        market_status = self._get_market_status(signal.market_id)
        if market_status != 'OPEN':
            return False

        # Verificar exposição
        current_exposure = self.db.get_current_exposure()
        if current_exposure + signal.stake > self.config['max_daily_exposure']:
            return False

        return True

    def _check_liquidity(self, signal):
        """Verifica liquidez disponível"""
        market_book = self.client.betting.get_market_book(
            market_ids=[signal.market_id]
        )

        # Encontrar runner correspondente
        for runner in market_book[0].runners:
            if runner.selection_id == signal.selection_id:
                # Verificar liquidez no preço alvo
                for price_level in runner.ex.available_to_back:
                    if price_level.price >= signal.odds - 0.01:
                        return price_level.size

        return 0
```

### 5.2 Monitoramento de Ordens

```python
class OrderMonitor:
    def __init__(self, client, db):
        self.client = client
        self.db = db

    def monitor_order(self, order_id, timeout=60):
        """Monitora ordem até preenchimento ou timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self._get_order_status(order_id)

            if status == 'EXECUTION_COMPLETE':
                return self._get_final_order(order_id)
            elif status == 'EXECUTABLE':
                time.sleep(1)  # esperar 1 segundo
                continue
            else:
                # Ordem expirada ou cancelada
                return self._get_final_order(order_id)

        # Timeout - cancelar ordem
        self._cancel_order(order_id)
        return {'status': 'CANCELLED_TIMEOUT'}

    def _get_order_status(self, order_id):
        """Obtém status atual da ordem"""
        current_orders = self.client.betting.get_current_orders(
            order_ids=[order_id]
        )

        if not current_orders:
            return 'UNKNOWN'

        return current_orders[0].status

    def _cancel_order(self, order_id):
        """Cancela ordem pendente"""
        self.client.betting.cancel_orders(
            market_id=None,
            instructions=[
                betfairlightweight.resources.betting.CancelInstruction(
                    bet_id=order_id
                )
            ]
        )
```

---

## 6. TRATAMENTO DE ERROS

### 6.1 Classificação de Erros

| Erro Betfair | Categoria | Ação |
|--------------|-----------|------|
| INSUFFICIENT_FUNDS | Crítico | Parar operação, alertar |
| MARKET_SUSPENDED | Alto | Cancelar ordem, aguardar |
| INVALID_MARKET_ID | Alto | Validar dados, corrigir |
| RATE_LIMIT_EXCEEDED | Médio | Implementar backoff |
| TIMEOUT | Médio | Retentar com backoff |
| INVALID_BET_SIZE | Baixo | Validar stake, corrigir |
| DUPLICATE_TRANSACTION | Baixo | Ignorar, já processado |

### 6.2 Sistema de Retentativas

```python
class RetryHandler:
    def __init__(self, max_retries=3, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func, *args, **kwargs):
        """Executa função com retentativas exponenciais"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise  # última tentativa falhou

                # Calcular delay exponencial
                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)

                # Log
                log_error(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s")
```

### 6.3 Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Executa função com circuit breaker"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Reseta em sucesso"""
        self.failures = 0
        self.state = 'CLOSED'

    def _on_failure(self):
        """Incrementa falhas e abre circuit breaker se necessário"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = 'OPEN'
            log_critical(f"Circuit breaker OPEN after {self.failures} failures")
```

---

## 7. RECONCILIAÇÃO

### 7.1 Reconciliação Automática

```python
class BetfairReconciler:
    def __init__(self, client, db):
        self.client = client
        self.db = db

    def reconcile_orders(self, date):
        """Reconcilia ordens do dia"""
        # Obter ordens da Betfair
        betfair_orders = self._get_betfair_orders(date)

        # Obter ordens do sistema
        system_orders = self.db.get_orders_by_date(date)

        # Comparar
        discrepancies = self._compare_orders(betfair_orders, system_orders)

        # Corrigir discrepâncias
        for discrepancy in discrepancies:
            self._correct_discrepancy(discrepancy)

        return discrepancies

    def _get_betfair_orders(self, date):
        """Obtém ordens da Betfair para o dia"""
        cleared_orders = self.client.betting.get_cleared_orders(
            bet_status='SETTLED',
            settled_date_range={
                'from': date,
                'to': date
            }
        )
        return cleared_orders

    def _compare_orders(self, betfair_orders, system_orders):
        """Compara ordens e identifica discrepâncias"""
        discrepancies = []

        # Criar mapa por order_id
        betfair_map = {o.bet_id: o for o in betfair_orders}
        system_map = {o.betfair_order_id: o for o in system_orders}

        # Verificar ordens em Betfair mas não no sistema
        for bet_id in betfair_map:
            if bet_id not in system_map:
                discrepancies.append({
                    'type': 'MISSING_IN_SYSTEM',
                    'bet_id': bet_id,
                    'betfair_order': betfair_map[bet_id]
                })

        # Verificar ordens no sistema mas não na Betfair
        for betfair_id in system_map:
            if betfair_id not in betfair_map:
                discrepancies.append({
                    'type': 'MISSING_IN_BETFAIR',
                    'betfair_order_id': betfair_id,
                    'system_order': system_map[betfair_id]
                })

        # Verificar detalhes de ordens correspondentes
        for bet_id in betfair_map:
            if bet_id in system_map:
                bf = betfair_map[bet_id]
                sys = system_map[bet_id]

                if abs(bf.size - sys.stake) > 0.01:
                    discrepancies.append({
                        'type': 'STAKE_MISMATCH',
                        'bet_id': bet_id,
                        'betfair_stake': bf.size,
                        'system_stake': sys.stake
                    })

                if abs(bf.price_requested - sys.odds) > 0.01:
                    discrepancies.append({
                        'type': 'ODDS_MISMATCH',
                        'bet_id': bet_id,
                        'betfair_odds': bf.price_requested,
                        'system_odds': sys.odds
                    })

        return discrepancies
```

### 7.2 Reconciliação Manual

Se reconciliação automática falhar:

1. **Exportar dados da Betfair**
   - Usar Betfair website ou API
   - Exportar para CSV
   - Incluir todas as colunas

2. **Exportar dados do sistema**
   - Exportar para CSV
   - Mesmo formato que Betfair

3. **Comparar manualmente**
   - Usar Excel ou similar
   - Identificar discrepâncias
   - Documentar cada uma

4. **Corrigir manualmente**
   - Atualizar sistema se Betfair correto
   - Contactar Betfair se sistema correto
   - Documentar resolução

---

## 8. MÉTRICAS E MONITORIZAÇÃO

### 8.1 Métricas de Execução

| Métrica | Target | Warning | Critical |
|---------|--------|---------|----------|
| Latência de execução | < 500ms | > 1s | > 5s |
| Fill rate | > 95% | < 90% | < 80% |
| Taxa de erro | < 1% | > 5% | > 10% |
| Slippage médio | < 1% | > 2% | > 5% |
| Uptime da API | > 99.5% | < 99% | < 95% |

### 8.2 Alertas Automáticos

```python
class ExecutionMonitor:
    def __init__(self, alert_system):
        self.alert_system = alert_system
        self.metrics = {}

    def check_metrics(self):
        """Verifica métricas e envia alertas"""
        # Coletar métricas
        self.metrics = self._collect_metrics()

        # Verificar latência
        if self.metrics['latency'] > 5000:
            self.alert_system.send_critical(
                "Latência crítica: " + str(self.metrics['latency']) + "ms"
            )

        # Verificar fill rate
        if self.metrics['fill_rate'] < 0.80:
            self.alert_system.send_critical(
                "Fill rate crítico: " + str(self.metrics['fill_rate']) + "%"
            )

        # Verificar taxa de erro
        if self.metrics['error_rate'] > 0.10:
            self.alert_system.send_critical(
                "Taxa de erro crítica: " + str(self.metrics['error_rate']) + "%"
            )
```

---

## 9. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Seção mãe
- [[44_Exchange_Execution/LATENCY_OPTIMIZATION]] → Otimização de latência
- [[09_Execution_System/INDEX]] → Sistema de execução geral
- [[22_Real_Money_Operations/INDEX]] → Operações com dinheiro real