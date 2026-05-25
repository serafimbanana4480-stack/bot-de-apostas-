# SYSTEM_PERFORMANCE — Performance do Sistema

**ID:** `OP-009` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Monitorizar performance do sistema para garantir tempo de resposta aceitável.

---

## 2. MÉTRICAS DE PERFORMANCE

| Métrica | Target | Alerta |
|---------|--------|--------|
| Latência inferência | < 100ms | > 500ms |
| Latência API bookmaker | < 500ms | > 2s |
| Throughput | > 10 sinais/s | < 5 sinais/s |
| CPU | < 70% | > 90% |
| Memória | < 80% | > 95% |

---

## 3. MONITORIZAÇÃO

```python
def track_performance():
    """Rastreia métricas de performance."""
    metrics = {
        'inference_latency': measure_inference_latency(),
        'api_latency': measure_api_latency(),
        'throughput': measure_throughput(),
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'timestamp': datetime.now()
    }
    
    # Enviar para Prometheus/Grafana
    push_metrics_to_prometheus(metrics)
    
    return metrics
```

---

## 4. LATÊNCIA DE INFERÊNCIA

```python
def measure_inference_latency():
    """Mede latência de inferência do modelo."""
    start_time = time.time()
    
    # Gerar 100 previsões
    for _ in range(100):
        model.predict_proba(sample_features)
    
    avg_latency = (time.time() - start_time) / 100 * 1000  # ms
    return avg_latency
```

---

## 5. LATÊNCIA DA API

```python
def measure_api_latency():
    """Mede latência da API do bookmaker."""
    start_time = time.time()
    
    response = betting_api.get_odds(sample_game_id)
    
    latency = (time.time() - start_time) * 1000  # ms
    return latency
```

---

## 6. ALERTAS

```python
def check_performance_alerts(metrics):
    """Verifica se performance requer alerta."""
    if metrics['inference_latency'] > 500:
        send_alert(f"⚠️ Latência inferência alta: {metrics['inference_latency']:.0f}ms")
    
    if metrics['api_latency'] > 2000:
        send_alert(f"⚠️ Latência API alta: {metrics['api_latency']:.0f}ms")
    
    if metrics['cpu'] > 90:
        send_alert(f"⚠️ CPU alta: {metrics['cpu']:.0f}%")
```

---

## 7. CRITÉRIOS

- **Latência inferência < 100ms**
- **Latência API < 500ms**
- **Alerta se thresholds excedidos**

---

## 8. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_MONITORING]]
