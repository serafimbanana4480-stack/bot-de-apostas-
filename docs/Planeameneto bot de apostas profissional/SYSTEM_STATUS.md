# SYSTEM_STATUS — Status do Sistema

**ID:** `OP-010` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Fornecer status consolidado do sistema para operadores.

---

## 2. ESTADOS DO SISTEMA

| Estado | Descrição | Ação |
|--------|-----------|------|
| RUNNING | Sistema operacional normal | Nenhuma |
| DEGRADED | Performance degradada | Monitorizar |
| PAUSED | Sistema pausado manualmente | Investigar |
| ERROR | Erro crítico | Ação imediata |

---

## 3. STATUS CONSOLIDADO

```python
def get_system_status():
    """
    Retorna status consolidado do sistema.
    
    Returns:
        Dict com status completo
    """
    health = system_health_check()
    performance = track_performance()
    
    # Determinar estado
    if not health['overall']:
        status = 'ERROR'
    elif any(p > threshold for p, threshold in performance.items()):
        status = 'DEGRADED'
    else:
        status = 'RUNNING'
    
    return {
        'status': status,
        'health': health,
        'performance': performance,
        'last_update': datetime.now()
    }
```

---

## 4. ENDPOINT DE STATUS

```python
@app.get('/api/status')
def status_endpoint():
    """Endpoint HTTP para status."""
    return jsonify(get_system_status())
```

---

## 5. DASHBOARD

Status deve ser visualizado em dashboard em tempo real com:

- Estado atual (color-coded)
- Health de cada componente
- Métricas de performance
- Última atualização

---

## 6. CRITÉRIOS

- **Status atualizado a cada 5 minutos**
- **Endpoint HTTP** para consultas externas
- **Dashboard visual** em tempo real

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_HEALTH_CHECK]]
