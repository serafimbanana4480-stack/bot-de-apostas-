# LATENCIA_EXECUCAO — Latência de Execução

**ID:** `OP-025` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Medir e otimizar latência de execução em produção.

---

## 2. COMPONENTES DE LATÊNCIA

| Componente | Target | Medição |
|------------|--------|---------|
| Inferência | < 50ms | Tempo de predição |
| Odds fetch | < 100ms | API call |
| Validação | < 10ms | Checks de risco |
| Execução API | < 50ms | Call ao bookmaker |
| Total | < 250ms | End-to-end |

---

## 3. MEDIÇÃO

```python
def measure_execution_latency(bet_request):
    """
    Mede latência de execução real.
    
    Args:
        bet_request: Pedido de aposta
    
    Returns:
        Dict com latências por componente
    """
    start_total = time.time()
    
    # Inferência
    start_inference = time.time()
    prediction = model.predict(bet_request['game_id'])
    inference_time = (time.time() - start_inference) * 1000
    
    # Fetch odds
    start_odds = time.time()
    odds = fetch_odds(bet_request['game_id'])
    odds_time = (time.time() - start_odds) * 1000
    
    # Validação
    start_validation = time.time()
    validate_prediction(prediction, odds)
    validation_time = (time.time() - start_validation) * 1000
    
    # Execução API
    start_execution = time.time()
    execute_bet(bet_request)
    execution_time = (time.time() - start_execution) * 1000
    
    total_time = (time.time() - start_total) * 1000
    
    return {
        'inference_ms': inference_time,
        'odds_ms': odds_time,
        'validation_ms': validation_time,
        'execution_ms': execution_time,
        'total_ms': total_time
    }
```

---

## 4. OTIMIZAÇÃO

```python
def optimize_latency():
    """Otimiza latência do sistema."""
    # 1. Cache de modelo
    cache_model_in_memory()
    
    # 2. Batch inference
    enable_batch_inference()
    
    # 3. Pool de conexões para APIs
    enable_connection_pooling()
    
    # 4. Async execution
    enable_async_execution()
```

---

## 5. MONITORIZAÇÃO

```python
def monitor_latency():
    """Monitoriza latência continuamente."""
    latencies = []
    
    for bet in recent_bets:
        latency = measure_execution_latency(bet)
        latencies.append(latency)
    
    avg_latency = np.mean([l['total_ms'] for l in latencies])
    
    if avg_latency > 250:
        send_alert(f"⚠️ Latência alta: {avg_latency:.0f}ms")
```

---

## 6. CRITÉRIOS

- **Latência total < 250ms** em produção
- **Alerta se > 300ms** por 5 min
- **Otimizar** se > 250ms consistente

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_PERFORMANCE]]
