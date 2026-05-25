# Agent Monitor

**ID:** AI-002 | **Fase:** #phase/8+ | **Owner:** Chief Systems Architect | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Agente de IA para deteção de anomalias em métricas e geração de alertas explicativos. O Agent-Monitor usa regras + LLM para narrar anomalias de forma compreensível para operadores humanos.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Deteção de anomalias com narração explicativa |
| **Stack** | Regras + LLM (GPT-4o-mini) + Prometheus |
| **Custo** | ~$5/mês (API LLM) |

---

## 2. ARQUITETURA DO AGENTE

### 2.1 Fluxo de Detecção

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT-MONITOR                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. COLETA DE MÉTRICAS                                │   │
│  │    - CLV médio                                        │   │
│  │    - ROI                                             │   │
│  │    - Drawdown                                        │   │
│  │    - Latência                                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. DETECÇÃO DE ANOMALIAS (REGRAS)                   │   │
│  │    - CLV < threshold?                                │   │
│  │    - ROI < threshold?                                │   │
│  │    - Drawdown > threshold?                          │   │
│  │    - Latência > threshold?                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. NARRAÇÃO LLM                                      │   │
│  │    - Explica causa provável                          │   │
│  │    - Sugere ação                                     │   │
│  │    - Formata para Telegram                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. ENVIO DE ALERTA                                   │   │
│  │    - Telegram                                         │   │
│  │    - Formato compreensível                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. REGRAS DE DETECÇÃO

### 3.1 Thresholds

```python
# vbq/agents/monitor/rules.py
ANOMALY_THRESHOLDS = {
    'clv_low': 0.5,  # CLV < 0.5%
    'roi_low': 0.0,  # ROI < 0%
    'drawdown_high': 15.0,  # Drawdown > 15%
    'latency_high': 30.0,  # Latência > 30s
    'fill_rate_low': 80.0,  # Fill rate < 80%
    'brier_high': 0.25  # Brier Score > 0.25
}
```

### 3.2 Função de Detecção

```python
# vbq/agents/monitor/detector.py
def detect_anomalies(metrics: dict) -> list:
    """Detecta anomalias nas métricas"""
    anomalies = []
    
    if metrics['clv'] < ANOMALY_THRESHOLDS['clv_low']:
        anomalies.append({
            'type': 'clv_low',
            'value': metrics['clv'],
            'threshold': ANOMALY_THRESHOLDS['clv_low'],
            'severity': 'WARNING'
        })
    
    if metrics['roi'] < ANOMALY_THRESHOLDS['roi_low']:
        anomalies.append({
            'type': 'roi_low',
            'value': metrics['roi'],
            'threshold': ANOMALY_THRESHOLDS['roi_low'],
            'severity': 'WARNING'
        })
    
    if metrics['drawdown'] > ANOMALY_THRESHOLDS['drawdown_high']:
        anomalies.append({
            'type': 'drawdown_high',
            'value': metrics['drawdown'],
            'threshold': ANOMALY_THRESHOLDS['drawdown_high'],
            'severity': 'CRITICAL'
        })
    
    if metrics['latency'] > ANOMALY_THRESHOLDS['latency_high']:
        anomalies.append({
            'type': 'latency_high',
            'value': metrics['latency'],
            'threshold': ANOMALY_THRESHOLDS['latency_high'],
            'severity': 'WARNING'
        })
    
    return anomalies
```

---

## 4. NARRAÇÃO LLM

### 4.1 Template de Prompt

```python
# vbq/agents/monitor/llm_narrator.py
from openai import OpenAI

client = OpenAI()

def narrate_anomaly(anomaly: dict, context: dict) -> str:
    """Gera narração explicativa para anomalia"""
    
    prompt = f"""
És um analista de sistemas especializado em value betting NBA.

ANOMALIA DETECTADA:
Tipo: {anomaly['type']}
Valor: {anomaly['value']}
Threshold: {anomaly['threshold']}
Severity: {anomaly['severity']}

CONTEXTO:
CLV médio: {context['clv']}%
ROI médio: {context['roi']}%
Drawdown atual: {context['drawdown']}%
Latência média: {context['latency']}s
Número de sinais: {context['signals']}

INSTRUÇÕES:
1. Explica a causa provável da anomalia (1-2 frases)
2. Sugere uma ação concreta para resolver (1 frase)
3. Tom: profissional, factual, sem exageros
4. Máximo 100 palavras

Formato de resposta:
🔍 Análise: [explicação]
🔧 Ação: [ação]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.3
    )
    
    return response.choices[0].message.content
```

### 4.2 Exemplo de Narrativa

```
🔍 Análise: CLV abaixo de threshold pode indicar calibração ruim do modelo ou regime change no mercado. A consistência dos sinais parece afetada.

🔧 Ação: Revisar calibração do modelo e verificar se houve mudança nas odds das casas nos últimos dias.
```

---

## 5. INTEGRAÇÃO COM TELEGRAM

### 5.1 Formatação de Alerta

```python
# vbq/agents/monitor/telegram_formatter.py
def format_telegram_alert(anomaly: dict, narration: str) -> str:
    """Formata alerta para Telegram"""
    
    emoji = {
        'CRITICAL': '🔴',
        'WARNING': '🟡',
        'INFO': '🟢'
    }
    
    return f"""
{emoji.get(anomaly['severity'], '⚪')} *{anomaly['severity']}*

{anomaly['type'].replace('_', ' ').title()}

Valor: {anomaly['value']}
Threshold: {anomaly['threshold']}

{narration}
"""
```

### 5.2 Envio de Alerta

```python
# vbq/agents/monitor/alert_sender.py
from vbq.alerts.telegram_client import TelegramClient

telegram = TelegramClient(
    token=TELEGRAM_BOT_TOKEN,
    chat_id=TELEGRAM_ALERT_CHAT_ID
)

def send_anomaly_alert(anomaly: dict, context: dict):
    """Envia alerta de anomalia para Telegram"""
    
    # Gerar narração
    narration = narrate_anomaly(anomaly, context)
    
    # Formatar alerta
    alert = format_telegram_alert(anomaly, narration)
    
    # Enviar
    telegram.send_message(alert)
```

---

## 6. AGENDAMENTO

### 6.1 Execução Periódica

```python
# vbq/agents/monitor/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from vbq.monitoring.metrics import collect_business_metrics
from vbq.agents.monitor.detector import detect_anomalies
from vbq.agents.monitor.alert_sender import send_anomaly_alert

scheduler = BackgroundScheduler()

def monitor_task():
    """Tarefa de monitorização"""
    # Coletar métricas
    metrics = collect_business_metrics()
    
    # Detectar anomalias
    anomalies = detect_anomalies(metrics)
    
    # Para cada anomalia
    for anomaly in anomalies:
        # Enviar alerta
        send_anomaly_alert(anomaly, metrics)

scheduler.add_job(
    func=monitor_task,
    trigger="interval",
    minutes=15  # Executar a cada 15 minutos
)

scheduler.start()
```

---

## 7. EXEMPLOS DE ALERTAS

### 7.1 CLV Baixo

```
🟡 *WARNING*

CLV Low

Valor: 0.3%
Threshold: 0.5%

🔍 Análise: CLV abaixo de threshold pode indicar calibração ruim do modelo ou regime change no mercado. A consistência dos sinais parece afetada.

🔧 Ação: Revisar calibração do modelo e verificar se houve mudança nas odds das casas nos últimos dias.
```

### 7.2 Drawdown Alto

```
🔴 *CRITICAL*

Drawdown High

Valor: 16.5%
Threshold: 15.0%

🔍 Análise: Drawdown acima de 15% indica perda significativa. Pode ser variância normal ou problema no modelo. A tendência de recuperação é importante.

🔧 Ação: Reduzir stakes temporariamente e monitorar se drawdown continua a aumentar. Considerar parar se > 20%.
```

### 7.3 Latência Alta

```
🟡 *WARNING*

Latency High

Valor: 35s
Threshold: 30s

🔍 Análise: Latência acima de threshold pode indicar problema de performance ou congestionamento de API. Impacta a qualidade das odds obtidas.

🔧 Ação: Investigar latência de API e otimizar pipeline de ingestão. Verificar se há gargalos no sistema.
```

---

## 8. CONFIGURAÇÃO

### 8.1 Variáveis de Ambiente

```bash
# .env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALERT_CHAT_ID=...
TELEGRAM_CHAT_ID=...
```

### 8.2 Configuração do Agente

```python
# vbq/agents/monitor/config.py
import os

AGENT_MONITOR_CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'model': 'gpt-4o-mini',
    'max_tokens': 200,
    'temperature': 0.3,
    'check_interval_minutes': 15
}
```

---

## 9. TESTES

### 9.1 Teste de Detecção

```python
# vbq/agents/monitor/tests/test_detector.py
def test_detect_anomalies():
    """Teste de deteção de anomalias"""
    metrics = {
        'clv': 0.3,
        'roi': -1.5,
        'drawdown': 16.5,
        'latency': 35,
        'fill_rate': 75,
        'brier': 0.27
    }
    
    anomalies = detect_anomalies(metrics)
    
    assert len(anomalies) == 5
    assert all(a['severity'] in ['WARNING', 'CRITICAL'] for a in anomalies)
```

### 9.2 Teste de Narração

```python
def test_narrate_anomaly():
    """Teste de narração de anomalia"""
    anomaly = {
        'type': 'clv_low',
        'value': 0.3,
        'threshold': 0.5,
        'severity': 'WARNING'
    }
    
    context = {
        'clv': 0.3,
        'roi': -1.5,
        'drawdown': 16.5,
        'latency': 35,
        'signals': 10
    }
    
    narration = narrate_anomaly(anomaly, context)
    
    assert len(narration) > 50
    assert 'Análise' in narration
    assert 'Ação' in narration
```

---

## 10. LINKS CRUZADOS

- [[40_AI_Agents/INDEX]] ← Secção mãe
- [[40_AI_Agents/ASSISTENTE_ANALISE]] → Agente de análise
- [[33_Alerting/INDEX]] → Sistema de alertas
- [[39_Automation/ALERTING_AUTOMATION]] → Alerting automation

---

**Custo de implementação:** ~$5/mês (API LLM)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (útil mas não crítico)
