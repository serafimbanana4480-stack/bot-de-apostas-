# LOGGING_ESTRUTURADO — Logging Estruturado

**ID:** `OP-023` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Padronizar logging estruturado em todo o sistema.

---

## 2. FORMATO DE LOG

```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "betting_system",
    "message": "Aposta executada",
    "context": {
        "game_id": "GS-LAL-20240115",
        "stake": 100.0,
        "odd": 2.50,
        "prob": 0.45
    }
}
```

---

## 3. IMPLEMENTAÇÃO

```python
import structlog

def setup_structured_logging():
    """Configura logging estruturado."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()

logger = setup_structured_logging()
```

---

## 4. USO

```python
def execute_bet(game_id, stake, odd, prob):
    """Executa aposta com logging estruturado."""
    logger.info(
        "Aposta executada",
        game_id=game_id,
        stake=stake,
        odd=odd,
        prob=prob
    )
```

---

## 5. LEVELS

| Level | Uso |
|-------|-----|
| DEBUG | Detalhes de execução |
| INFO | Eventos normais |
| WARNING | Avisos não críticos |
| ERROR | Erros recuperáveis |
| CRITICAL | Erros críticos |

---

## 6. CRITÉRIOS

- **Logs estruturados** em JSON
- **Contexto rico** em cada log
- **Centralização** em syslog

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSLOG_CONFIG]]
