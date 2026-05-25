# Alerting Automation

**ID:** AUTO-004 | **Fase:** #phase/6-12 | **Owner:** DevOps + Operations Lead | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Sistema de alertas automatizado para notificar anomalias, falhas, e eventos importantes. Alertas são enviados via Telegram, email, e Slack para garantir resposta rápida.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Sistema de alertas automatizado |
| **Stack** | Telegram Bot, Email, Slack Webhook |
| **Custo** | 0€ (Telegram gratuito) |

---

## 2. ARQUITETURA DE ALERTAS

### 2.1 Estrutura de Alertas

```
┌─────────────────────────────────────────────────────────────┐
│ SISTEMA DE ALERTAS                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ALERTAS CRÍTICAS (Imediato)                          │   │
│  │ ├── Falha de pipeline                                │   │
│  │ ├── Erro de ingestão de dados                         │   │
│  │ ├── Drawdown > 15%                                   │   │
│  │ ├── SLA violation                                    │   │
│  │ └── Alerta: Telegram + Email + Slack               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ALERTAS DE AVISO (1 hora)                             │   │
│  │ ├── CLV caindo abaixo de threshold                   │   │
│  │ ├── Latência aumentando                               │   │
│  │ ├── Fill rate caindo                                  │   │
│  │ ├── Alerta: Telegram + Email                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ALERTAS INFO (Diário)                                │   │
│  │ ├── Relatório diário                                 │   │
│  │ ├── Métricas de performance                          │   │
│  │ ├── Alerta: Telegram                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO TELEGRAM BOT

### 3.1 Criação do Bot

1. Criar bot via @BotFather no Telegram
2. Obter token do bot
3. Adicionar bot ao canal de operações
4. Obter chat_id do canal

### 3.2 Configuração

```python
# vbq/alerts/telegram_config.py
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Canal de operações
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID")  # Canal de alertas críticos
```

### 3.3 Cliente Telegram

```python
# vbq/alerts/telegram_client.py
import requests
from typing import Optional

class TelegramClient:
    """Cliente para enviar alertas via Telegram"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(
        self,
        message: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """Envia mensagem via Telegram"""
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id or self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Erro ao enviar mensagem Telegram: {e}")
            return False
    
    def send_alert(
        self,
        level: str,
        title: str,
        message: str,
        chat_id: Optional[str] = None
    ) -> bool:
        """Envia alerta formatado"""
        emoji = {
            "CRITICAL": "🔴",
            "WARNING": "🟡",
            "INFO": "🟢"
        }
        
        formatted_message = f"""
{emoji.get(level, "⚪")} *{level}*

{title}

{message}
"""
        
        return self.send_message(formatted_message, chat_id)
```

---

## 4. CATEGORIAS DE ALERTAS

### 4.1 Alertas Críticos

**Condições:**
- Falha de pipeline (3 retries falharam)
- Erro de ingestão de dados (> 1 hora sem dados)
- Drawdown > 15%
- SLA violation (latência > 5 minutos)
- Database connection error

**Ação:** Enviar para Telegram + Email + Slack imediatamente

```python
# vbq/alerts/critical_alerts.py
from vbq.alerts.telegram_client import TelegramClient

telegram = TelegramClient(
    token=TELEGRAM_BOT_TOKEN,
    chat_id=TELEGRAM_ALERT_CHAT_ID
)

def alert_pipeline_failure(pipeline_name: str, error: str):
    """Alerta de falha de pipeline"""
    telegram.send_alert(
        level="CRITICAL",
        title=f"Falha no pipeline: {pipeline_name}",
        message=f"Erro: {error}\n\nAção: Investigar imediatamente"
    )

def alert_drawdown_exceeded(drawdown: float, threshold: float):
    """Alerta de drawdown excedido"""
    telegram.send_alert(
        level="CRITICAL",
        title=f"Drawdown excedido: {drawdown:.2f}%",
        message=f"Threshold: {threshold:.2f}%\n\nAção: Considerar parar operação"
    )
```

### 4.2 Alertas de Aviso

**Condições:**
- CLV < 1.0% (consecutivo 3 dias)
- Latência > 30 segundos
- Fill rate < 80%
- Brier Score > 0.25

**Ação:** Enviar para Telegram + Email

```python
# vbq/alerts/warning_alerts.py
def alert_clv_low(clv: float, threshold: float):
    """Alerta de CLV baixo"""
    telegram.send_alert(
        level="WARNING",
        title=f"CLV baixo: {clv:.2f}%",
        message=f"Threshold: {threshold:.2f}%\n\nAção: Investigar calibração"
    )

def alert_latency_high(latency: float, threshold: float):
    """Alerta de latência alta"""
    telegram.send_alert(
        level="WARNING",
        title=f"Latência alta: {latency:.1f}s",
        message=f"Threshold: {threshold:.1f}s\n\nAção: Investigar performance"
    )
```

### 4.3 Alertas Info

**Condições:**
- Relatório diário gerado
- Pipeline concluído com sucesso
- Modelo promovido para staging

**Ação:** Enviar para Telegram (canal de operações)

```python
# vbq/alerts/info_alerts.py
def alert_daily_report(report: dict):
    """Alerta de relatório diário"""
    telegram.send_alert(
        level="INFO",
        title="Relatório Diário",
        message=f"""
PnL: €{report['pnl']:.2f}
CLV: {report['clv']:.2f}%
ROI: {report['roi']:.2f}%
Apostas: {report['bets']}
"""
    )

def alert_pipeline_success(pipeline_name: str, duration: float):
    """Alerta de sucesso de pipeline"""
    telegram.send_alert(
        level="INFO",
        title=f"Pipeline concluído: {pipeline_name}",
        message=f"Duração: {duration:.1f}s"
    )
```

---

## 5. INTEGRAÇÃO COM PIPELINES

### 5.1 Prefect Notifications

```python
# vbq/prefect/pipelines/daily_pipeline.py
from prefect import flow, task
from vbq.alerts.critical_alerts import alert_pipeline_failure
from vbq.alerts.info_alerts import alert_pipeline_success

@flow(name="daily_pipeline_with_alerts")
def daily_pipeline_with_alerts(date: str):
    """Pipeline diário com alertas"""
    try:
        # Executar pipeline
        result = daily_pipeline(date)
        
        # Alerta de sucesso
        alert_pipeline_success("daily_pipeline", result['duration'])
        
        return result
        
    except Exception as e:
        # Alerta de falha
        alert_pipeline_failure("daily_pipeline", str(e))
        raise
```

### 5.2 Webhook Integration

```python
# vbq/alerts/webhook.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class AlertRequest(BaseModel):
    level: str
    title: str
    message: str

@app.post("/alert")
async def send_alert(request: AlertRequest):
    """Endpoint webhook para enviar alertas"""
    telegram.send_alert(
        level=request.level,
        title=request.title,
        message=request.message
    )
    return {"status": "sent"}
```

---

## 6. MONITORIZAÇÃO DE ALERTAS

### 6.1 Dashboard de Alertas

```
┌─────────────────────────────────────────────────────────────┐
│ ALERTAS - ÚLTIMAS 24 HORAS                                 │
├─────────────────────────────────────────────────────────────┤
│ CRITICAL: 2                                                │
│   - Pipeline daily falhou (10:30 UTC)                     │
│   - Drawdown 16.2% (14:15 UTC)                             │
├─────────────────────────────────────────────────────────────┤
│ WARNING: 5                                                 │
│   - CLV 0.8% (09:00 UTC)                                  │
│   - Latência 35s (11:30 UTC)                              │
│   - Fill rate 75% (12:00 UTC)                             │
├─────────────────────────────────────────────────────────────┤
│ INFO: 12                                                   │
│   - Relatório diário (08:00 UTC)                          │
│   - Pipeline weekly concluído (04:00 UTC)                 │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Métricas de Alertas

```python
# vbq/alerts/metrics.py
from datetime import datetime, timedelta

def get_alert_metrics(hours: int = 24):
    """Obtém métricas de alertas"""
    from vbq.database.models import Alert
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    alerts = Alert.query.filter(Alert.timestamp >= cutoff).all()
    
    metrics = {
        'critical': len([a for a in alerts if a.level == 'CRITICAL']),
        'warning': len([a for a in alerts if a.level == 'WARNING']),
        'info': len([a for a in alerts if a.level == 'INFO']),
        'total': len(alerts)
    }
    
    return metrics
```

---

## 7. TESTES DE ALERTAS

### 7.1 Teste de Alerta Crítico

```python
# vbq/alerts/tests/test_alerts.py
def test_critical_alert():
    """Teste de envio de alerta crítico"""
    result = telegram.send_alert(
        level="CRITICAL",
        title="Teste Alerta Crítico",
        message="Este é um teste"
    )
    assert result == True
```

### 7.2 Teste de Alerta de Aviso

```python
def test_warning_alert():
    """Teste de envio de alerta de aviso"""
    result = telegram.send_alert(
        level="WARNING",
        title="Teste Alerta Aviso",
        message="Este é um teste"
    )
    assert result == True
```

---

## 8. LINKS CRUZADOS

- [[39_Automation/INDEX]] ← Secção mãe
- [[33_Alerting/INDEX]] → Sistema de alertas
- [[19_Telegram_System/INDEX]] → Sistema Telegram
- [[18_Operations/GESTAO_ALERTAS]] → Gestão de alertas

---

**Custo de implementação:** 0€ (Telegram gratuito)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para resposta rápida)
