# SYSTEM_HEALTH_CHECK — Health Check do Sistema

**ID:** `OP-008` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Verificar saúde do sistema em intervalos regulares para detetar problemas precocemente.

---

## 2. CHECKS DE SAÚDE

```python
def system_health_check():
    """
    Executa check completo de saúde do sistema.
    
    Returns:
        Dict com status de cada componente
    """
    health = {}
    
    # 1. Database
    health['database'] = check_database_connection()
    
    # 2. Cache (Redis)
    health['cache'] = check_redis_connection()
    
    # 3. Queue (RabbitMQ)
    health['queue'] = check_queue_status()
    
    # 4. ML Model
    health['model'] = check_model_loaded()
    
    # 5. API Bookmaker
    health['bookmaker_api'] = check_bookmaker_api()
    
    # 6. Disk space
    health['disk'] = check_disk_space()
    
    # Status geral
    health['overall'] = all(v['status'] == 'ok' for v in health.values())
    
    return health
```

---

## 3. CHECKS INDIVIDUAIS

```python
def check_database_connection():
    """Verifica conexão com database."""
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
        return {'status': 'ok', 'message': 'Database conectado'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def check_redis_connection():
    """Verifica conexão com Redis."""
    try:
        redis_client.ping()
        return {'status': 'ok', 'message': 'Redis conectado'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def check_model_loaded():
    """Verifica se modelo está carregado."""
    if model is None:
        return {'status': 'error', 'message': 'Modelo não carregado'}
    return {'status': 'ok', 'message': 'Modelo carregado'}
```

---

## 4. SCHEDULE

```python
# Health check a cada 5 minutos
schedule.every(5).minutes.do(system_health_check)
```

---

## 5. ALERTAS

```python
def health_check_alerts(health):
    """Envia alertas se algum componente falhou."""
    for component, status in health.items():
        if component != 'overall' and status['status'] != 'ok':
            send_alert(f"🚨 {component} falhou: {status['message']}")
    
    if not health['overall']:
        send_alert("🚨 Sistema em estado crítico")
```

---

## 6. CRITÉRIOS

- **Health check a cada 5 minutos**
- **Alerta imediato** se componente crítico falha
- **Dashboard** com status em tempo real

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_MONITORING]]
