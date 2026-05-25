# LATENCIA_PAPER — Latência em Paper Trading

**ID:** `OP-024` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Medir latência em paper trading para simular condições reais.

---

## 2. COMPONENTES DE LATÊNCIA

| Componente | Target | Medição |
|------------|--------|---------|
| Inferência | < 50ms | Tempo de predição |
| Odds fetch | < 100ms | API call |
| Validação | < 10ms | Checks de risco |
| Total | < 200ms | End-to-end |

---

## 3. MEDIÇÃO

```python
def measure_paper_trading_latency(game_id):
    """
    Mede latência de paper trading.
    
    Args:
        game_id: ID do jogo
    
    Returns:
        Dict com latências por componente
    """
    start_total = time.time()
    
    # Inferência
    start_inference = time.time()
    prediction = model.predict(game_id)
    inference_time = (time.time() - start_inference) * 1000
    
    # Fetch odds
    start_odds = time.time()
    odds = fetch_odds(game_id)
    odds_time = (time.time() - start_odds) * 1000
    
    # Validação
    start_validation = time.time()
    validate_prediction(prediction, odds)
    validation_time = (time.time() - start_validation) * 1000
    
    total_time = (time.time() - start_total) * 1000
    
    return {
        'inference_ms': inference_time,
        'odds_ms': odds_time,
        'validation_ms': validation_time,
        'total_ms': total_time
    }
```

---

## 4. SIMULAÇÃO DE CONDIÇÕES REAIS

```python
def simulate_real_conditions():
    """
    Simula condições reais adicionando latência artificial.
    """
    # Adicionar jitter para simular network variability
    jitter = np.random.uniform(0, 50)  # 0-50ms
    
    # Simular API rate limiting
    time.sleep(0.01)  # 10ms delay
    
    return jitter
```

---

## 5. CRITÉRIOS

- **Latência total < 200ms** em paper
- **Medir continuamente** para detetar degradação
- **Comparar com real** após deploy

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[LATENCIA_EXECUCAO]]
