# SYSLOG_CONFIG — Configuração de Syslog

**ID:** `OP-014` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Configurar syslog para centralização de logs.

---

## 2. CONFIGURAÇÃO

```python
import logging
import logging.handlers

def setup_syslog():
    """Configura envio de logs para syslog server."""
    logger = logging.getLogger('betting_system')
    logger.setLevel(logging.INFO)
    
    # Handler para syslog
    syslog_handler = logging.handlers.SysLogHandler(
        address=('syslog.example.com', 514),
        facility=logging.handlers.SysLogHandler.LOG_LOCAL0
    )
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    syslog_handler.setFormatter(formatter)
    
    logger.addHandler(syslog_handler)
    
    return logger
```

---

## 3. LOG LEVELS

| Nível | Uso |
|-------|-----|
| DEBUG | Detalhes de execução |
| INFO | Eventos normais |
| WARNING | Avisos não críticos |
| ERROR | Erros recuperáveis |
| CRITICAL | Erros críticos |

---

## 4. CRITÉRIOS

- **Todos os logs** enviados para syslog
- **Rotação de logs** a cada dia
- **Retenção** por 30 dias

---

## 5. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_MONITORING]]
