# STOP_SYSTEMS — Parar Sistemas

**ID:** `OP-015` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimentos para parar o sistema em caso de emergência.

---

## 2. CONDIÇÕES DE PARADA

| Condição | Ação | Automático |
|----------|------|------------|
| Drawdown > 20% | Parar apostas | ✅ |
| Sistema offline > 1h | Parar apostas | ✅ |
| Erro crítico de modelo | Parar apostas | ✅ |
| Manual (operação) | Parar sistema | ❌ |

---

## 3. STOP AUTOMÁTICO

```python
def auto_stop_system():
    """Verifica condições e para sistema se necessário."""
    # 1. Verificar drawdown
    current_drawdown = calculate_current_drawdown()
    if current_drawdown > 0.20:
        stop_betting()
        send_alert("🚨 Sistema parado: drawdown > 20%")
        return True
    
    # 2. Verificar uptime
    uptime = get_system_uptime()
    if uptime > 3600:  # 1 hora
        stop_betting()
        send_alert("🚨 Sistema parado: offline > 1h")
        return True
    
    return False
```

---

## 4. STOP MANUAL

```python
def manual_stop(reason):
    """
    Para sistema manualmente.
    
    Args:
        reason: Razão da parada
    """
    stop_betting()
    log_manual_stop(reason)
    send_alert(f"🛑 Sistema parado manualmente: {reason}")
```

---

## 5. REINÍCIO

```python
def restart_system():
    """
    Reinicia sistema após parada.
    
    Requer:
    - Aprovação manual
    - Verificação de saúde
    """
    if approve_restart():
        if system_health_check()['overall']:
            start_betting()
            send_alert("✅ Sistema reiniciado")
        else:
            send_alert("❌ Sistema não saudável - não reiniciar")
```

---

## 6. CRITÉRIOS

- **Stop automático** em condições críticas
- **Stop manual** sempre disponível
- **Aprovação** para reiniciar

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[RISK_LIMITS]]
