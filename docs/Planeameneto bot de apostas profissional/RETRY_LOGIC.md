# RETRY_LOGIC — Lógica de Retry

**ID:** `OP-002` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir lógica de retry para falhas na execução de apostas (API timeout, odds mudaram, etc.).

---

## 2. RETRY COM EXPONENTIAL BACKOFF

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, initial_delay=1.0):
    """
    Decorator para retry com exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            
        return wrapper
    return decorator
```

---

## 3. APLICAÇÃO A EXECUÇÃO DE APOSTA

```python
@retry_with_backoff(max_retries=3, initial_delay=1.0)
def place_bet_with_retry(bet_details):
    """
    Executa aposta com retry.
    """
    return betting_api.place_bet(bet_details)
```

---

## 4. VERIFICAÇÃO DE ODDS

```python
def verify_odds_still_valid(original_odds, current_odds, tolerance=0.02):
    """
    Verifica se odds ainda são válidas antes de retry.
    
    Se odds mudaram > 2%, não fazer retry.
    """
    change = abs(current_odds - original_odds) / original_odds
    
    if change > tolerance:
        raise ValueError("Odds mudaram significativamente - cancelar aposta")
    
    return True
```

---

## 5. RETRY CONDICIONAL

```python
def should_retry(exception_type, attempt):
    """
    Determina se deve fazer retry baseado no tipo de erro.
    """
    retryable_errors = [
        TimeoutError,
        ConnectionError,
        APIRateLimitError
    ]
    
    non_retryable_errors = [
        InsufficientFundsError,
        OddsChangedError,
        InvalidBetError
    ]
    
    if exception_type in non_retryable_errors:
        return False
    
    if exception_type in retryable_errors and attempt < 3:
        return True
    
    return False
```

---

## 6. LOGGING DE RETRIES

```python
def log_retry(attempt, exception, delay):
    """Registra tentativa de retry."""
    logger.warning({
        'event': 'retry_attempt',
        'attempt': attempt,
        'error': str(exception),
        'delay_seconds': delay,
        'timestamp': datetime.now()
    })
```

---

## 7. CRITÉRIOS

- **Máximo 3 retries** por operação
- **Exponential backoff** (1s, 2s, 4s)
- **Não retry** se odds mudaram > 2%
- **Não retry** erros não recuperáveis

---

## 8. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[33_Alerting/INDEX]]
