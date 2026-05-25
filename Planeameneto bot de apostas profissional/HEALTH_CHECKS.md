# HEALTH_CHECKS — Health Checks

**ID:** `OP-026` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir health checks para monitorização de componentes do sistema.

---

## 2. CHECKS POR COMPONENTE

| Componente | Check | Frequência |
|------------|-------|------------|
| Database | Conexão e query | Minuto |
| Cache | Ping e set/get | Minuto |
| Queue | Mensagens pendentes | Minuto |
| Model | Carregamento e inferência | Minuto |
| API Bookmaker | Latência e status | Minuto |

---

## 3. IMPLEMENTAÇÃO

```python
def health_check_database():
    """Health check da base de dados."""
    try:
        # Testar conexão
        db.execute("SELECT 1")
        
        # Testar query
        result = db.execute("SELECT COUNT(*) FROM bets")
        
        return {'status': 'healthy', 'query_time_ms': result['time']}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

def health_check_cache():
    """Health check do cache."""
    try:
        # Ping
        cache.ping()
        
        # Set/get
        cache.set('health_check', 'ok', ttl=10)
        value = cache.get('health_check')
        
        return {'status': 'healthy' if value == 'ok' else 'unhealthy'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

def health_check_model():
    """Health check do modelo."""
    try:
        # Verificar se modelo está carregado
        if model is None:
            return {'status': 'unhealthy', 'error': 'Model not loaded'}
        
        # Testar inferência
        test_input = get_test_input()
        prediction = model.predict(test_input)
        
        return {'status': 'healthy', 'inference_time_ms': prediction['time']}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

---

## 4. AGREGAÇÃO

```python
def aggregate_health_checks():
    """Agrega todos os health checks."""
    checks = {
        'database': health_check_database(),
        'cache': health_check_cache(),
        'queue': health_check_queue(),
        'model': health_check_model(),
        'api': health_check_api()
    }
    
    overall = all(c['status'] == 'healthy' for c in checks.values())
    
    return {
        'overall': overall,
        'components': checks,
        'timestamp': datetime.now()
    }
```

---

## 5. CRITÉRIOS

- **Check a cada minuto**
- **Alerta se componente unhealthy**
- **Dashboard** com status em tempo real

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_HEALTH]]
