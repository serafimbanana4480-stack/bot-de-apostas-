# TAXONOMIA_ERROS — Taxonomia de Erros

**ID:** `OP-011` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Classificar erros do sistema para facilitar debugging e alertas.

---

## 2. CATEGORIAS DE ERROS

### 2.1 Erros de Dados
| Código | Descrição | Severidade |
|--------|-----------|------------|
| DATA_MISSING | Dados não disponíveis | Alta |
| DATA_INVALID | Dados inválidos | Alta |
| DATA_STALE | Dados desatualizados | Média |

### 2.2 Erros de API
| Código | Descrição | Severidade |
|--------|-----------|------------|
| API_TIMEOUT | API não responde | Média |
| API_RATE_LIMIT | Limite de taxa excedido | Média |
| API_AUTH_ERROR | Erro de autenticação | Alta |

### 2.3 Erros de Execução
| Código | Descrição | Severidade |
|--------|-----------|------------|
| EXEC_FAILED | Aposta falhou | Alta |
| EXEC_PARTIAL | Aposta parcialmente executada | Média |
| EXEC_REJECTED | Aposta rejeitada | Baixa |

### 2.4 Erros de Modelo
| Código | Descrição | Severidade |
|--------|-----------|------------|
| MODEL_NOT_LOADED | Modelo não carregado | Crítica |
| MODEL_PREDICT_FAILED | Predição falhou | Alta |
| MODEL_VERSION_MISMATCH | Versão incorreta | Média |

---

## 3. LOGGING DE ERROS

```python
def log_error(error_code, context, severity):
    """
    Registra erro com contexto.
    
    Args:
        error_code: Código do erro
        context: Dict com contexto
        severity: Severidade (low, medium, high, critical)
    """
    log_entry = {
        'timestamp': datetime.now(),
        'error_code': error_code,
        'severity': severity,
        'context': context
    }
    
    logger.error(log_entry)
    
    # Alerta se severidade alta ou crítica
    if severity in ['high', 'critical']:
        send_alert(f"🚨 Erro {error_code}: {severity}")
```

---

## 4. ANÁLISE DE ERROS

```python
def analyze_errors(time_window_hours=24):
    """Analisa erros nas últimas 24 horas."""
    errors = get_errors_since(hours=time_window_hours)
    
    # Contar por código
    error_counts = errors['error_code'].value_counts()
    
    # Contar por severidade
    severity_counts = errors['severity'].value_counts()
    
    return {
        'total_errors': len(errors),
        'by_code': error_counts.to_dict(),
        'by_severity': severity_counts.to_dict()
    }
```

---

## 5. CRITÉRIOS

- **Classificar todos os erros**
- **Alerta imediato** para severidade crítica
- **Análise diária** de padrões de erros

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[33_Alerting/INDEX]]
