# RUNBOOK_DOWNTIME — Runbook de Downtime

**ID:** `OP-017` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimento para lidar com downtime do sistema.

---

## 2. DETEÇÃO DE DOWNTIME

```python
def detect_downtime():
    """
    Deteta se sistema está em downtime.
    
    Returns:
        Boolean se em downtime
    """
    health = system_health_check()
    
    if not health['overall']:
        logger.error("Sistema em downtime")
        return True
    
    return False
```

---

## 3. RUNBOOK

### Passo 1: Identificar causa
```python
def identify_downtime_cause():
    """Identifica causa do downtime."""
    # Verificar cada componente
    components = ['database', 'cache', 'queue', 'model', 'api']
    
    for component in components:
        if not check_component_health(component):
            return component
    
    return "unknown"
```

### Passo 2: Tentar recuperar
```python
def attempt_recovery(component):
    """Tenta recuperar componente."""
    if component == 'database':
        restart_database()
    elif component == 'cache':
        restart_cache()
    elif component == 'queue':
        restart_queue()
    # ...
```

### Passo 3: Escalonar se necessário
```python
def escalate_if_needed(component, duration_minutes):
    """Escalona se downtime prolongado."""
    if duration_minutes > 30:
        escalate_to_tier_2(component)
    
    if duration_minutes > 60:
        escalate_to_tier_3(component)
```

---

## 4. COMUNICAÇÃO

```python
def notify_downtime(component, duration):
    """Notifica stakeholders."""
    message = f"⚠️ Downtime detetado: {component} há {duration} minutos"
    send_alert(message)
    send_email(message)
```

---

## 5. CRITÉRIOS

- **Detetar downtime** em < 1 minuto
- **Tentar recuperação** automática
- **Escalonar** após 30 minutos

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SUPPORT_TIERS]]
