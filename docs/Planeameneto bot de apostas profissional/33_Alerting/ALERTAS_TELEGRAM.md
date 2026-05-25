# ALERTAS_TELEGRAM — Notificacoes Criticas

**ID:** `ALT-001` | **Fase:** #phase/3 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. NIVEIS DE SEVERIDADE

| Nivel | Cor | Resposta |
|-------|-----|----------|
| CRITICAL | Vermelho | Imediata (24/7) |
| HIGH | Laranja | < 1 hora |
| MEDIUM | Amarelo | < 4 horas |
| LOW | Azul | < 24 horas (resumo) |

---

## 2. ALERTAS CONFIGURADOS

### CRITICAL
- Circuit breaker ativado
- Drawdown > 15%
- Feed de odds offline > 10 min
- Erro de execucao > 5x/dia

### HIGH
- CLV 3d < 0%
- Feed offline > 5 min
- PSI > 0.25
- Modelo stale > 7 dias

### MEDIUM
- CPU > 80%
- Disco > 85%
- ECE > 0.10

### LOW
- Resumo diario de PnL
- Relatorio semanal de CLV

---

## 3. SISTEMA DE ALERTAS

### 3.1 Arquitetura

```
Prometheus/Monitorização → Alertmanager → Telegram Bot
                                      → Email (backup)
                                      → Log local
```

### 3.2 Implementação do Bot

```python
import requests
import json
from datetime import datetime
from typing import Dict, List

class AlertBot:
    """Bot Telegram para alertas críticos do sistema."""
    
    def __init__(self, bot_token: str, chat_ids: Dict[str, str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids  # {'critical': '-100123456', 'ops': '-100789012'}
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_alert(self, level: str, message: str, context: dict = None) -> bool:
        """
        Envia alerta para o canal apropriado baseado no nível.
        
        Args:
            level: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
            message: Mensagem do alerta
            context: Dados adicionais (métricas, timestamps)
        """
        icons = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️'
        }
        
        # Formatar mensagem
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        text = f"""
{icons.get(level, '🔔')} *ALERTA {level}*

🕐 {timestamp}
📋 {message}
"""
        
        if context:
            text += "\n📊 *Contexto:*\n"
            for key, value in context.items():
                text += f"• {key}: `{value}`\n"
        
        # Selecionar chat baseado no nível
        chat_id = self.chat_ids.get(
            'critical' if level == 'CRITICAL' else 'ops',
            self.chat_ids.get('ops')
        )
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_notification": level == 'LOW'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Log do alerta
            self._log_alert(level, message, context)
            return True
            
        except requests.RequestException as e:
            # Fallback: escrever em log se Telegram falhar
            logger.error(f"Falha ao enviar alerta Telegram: {e}")
            self._log_alert(level, message, context, failed=True)
            return False
    
    def _log_alert(self, level: str, message: str, context: dict, failed: bool = False):
        """Registra alerta em log estruturado."""
        import structlog
        logger = structlog.get_logger()
        logger.warning(
            "Alerta enviado" if not failed else "Alerta falhou",
            level=level,
            message=message,
            context=context,
            failed=failed
        )
```

---

## 4. ESCALADA DE ALERTAS

### 4.1 Matriz de Escalada

| Nível | Destino | Tempo de Resposta | Escalada se não resolvido |
|-------|---------|---------------------|---------------------------|
| CRITICAL | Chat Ops + SMS + Email | 15 min | SMS para on-call após 30 min |
| HIGH | Chat Ops + Email | 1 hora | Página on-call após 2h |
| MEDIUM | Chat Ops | 4 horas | Email resumido após 8h |
| LOW | Log + Resumo diário | 24 horas | Sem escalada |

### 4.2 Implementação de Escalada

```python
class EscalationManager:
    """Gerencia escalada de alertas não resolvidos."""
    
    ESCALATION_TIMES = {
        'CRITICAL': [15, 30, 60],   # minutos
        'HIGH': [60, 120, 240],
        'MEDIUM': [240, 480],
    }
    
    def check_escalation(self, alert: Alert):
        """Verifica se alerta precisa de escalada."""
        elapsed_minutes = (datetime.now() - alert.created_at).total_seconds() / 60
        
        if alert.level in self.ESCALATION_TIMES:
            for threshold in self.ESCALATION_TIMES[alert.level]:
                if elapsed_minutes >= threshold and not alert.escalated_at(threshold):
                    self.escalate(alert, threshold)
    
    def escalate(self, alert: Alert, threshold: int):
        """Executa escalada para o próximo nível."""
        if alert.level == 'CRITICAL' and threshold == 30:
            # Enviar SMS para on-call
            self.sms_service.send(
                to=ONCALL_PHONE,
                message=f"URGENTE: {alert.message} - Não resolvido em 30 min"
            )
            alert.mark_escalated(30)
        
        elif alert.level == 'HIGH' and threshold == 120:
            # Página on-call (PagerDuty/Opsgenie)
            self.pager_service.create_incident(
                title=f"Escalada: {alert.message}",
                urgency='high'
            )
            alert.mark_escalated(120)
```

---

## 5. ALERTAS CONFIGURADOS (Detalhado)

### 5.1 CRITICAL (Resposta imediata)

| ID | Condição | Mensagem | Ação |
|----|----------|----------|------|
| C-001 | Circuit breaker ativado | "Circuit breaker {nome} ativado. Operações paradas." | Parar sinais, notificar ops |
| C-002 | Drawdown > 15% | "Drawdown atingiu {valor}%. Reduzindo stakes." | Reduzir Kelly, alertar |
| C-003 | Feed odds offline > 10 min | "Feed de odds offline há {minutos} min." | Fallback manual |
| C-004 | Erro execução > 5x/hora | "{n} erros de execução na última hora." | Investigar API |
| C-005 | PostgreSQL down | "Base de dados indisponível." | Verificar Docker |

### 5.2 HIGH (< 1 hora)

| ID | Condição | Mensagem |
|----|----------|----------|
| H-001 | CLV 3d < 0% | "CLV médio 3 dias: {valor}%. Modelo pode estar degradado." |
| H-002 | Feed offline > 5 min | "Feed de odds offline há {minutos} min." |
| H-003 | PSI > 0.25 | "Feature drift detetado: PSI = {valor}." |
| H-004 | Modelo stale > 7 dias | "Modelo não re-treinado há {dias} dias." |
| H-005 | ECE > 0.10 | "Calibração degradada: ECE = {valor}." |

### 5.3 MEDIUM (< 4 horas)

| ID | Condição | Mensagem |
|----|----------|----------|
| M-001 | CPU > 80% | "CPU a {valor}% por mais de 5 min." |
| M-002 | Disco > 85% | "Disco a {valor}% de uso." |
| M-003 | Latência API > 2s | "Latência média API: {valor}ms." |
| M-004 | Memória > 85% | "RAM a {valor}% de uso." |

### 5.4 LOW (Resumo diário)

| ID | Condição | Mensagem |
|----|----------|----------|
| L-001 | Resumo diário PnL | "Resumo: {n} apostas, PnL: {valor}€, ROI: {valor}%" |
| L-002 | Relatório semanal CLV | "CLV semanal: {valor}% | Modelo: {versão}" |
| L-003 | Backup concluído | "Backup diário concluído: {tamanho}MB" |

---

## 6. SUPRESSÃO DE ALERTAS

```python
class AlertSuppression:
    """Evita spam de alertas repetidos."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def should_send(self, alert_id: str, level: str) -> bool:
        """Verifica se alerta deve ser enviado (não suprimido)."""
        key = f"alert:{alert_id}"
        
        # CRITICAL: sempre enviar
        if level == 'CRITICAL':
            return True
        
        # Verificar cooldown (5 min para HIGH, 15 min para MEDIUM)
        cooldown = {'HIGH': 300, 'MEDIUM': 900, 'LOW': 3600}
        ttl = self.redis.ttl(key)
        
        if ttl > 0:
            logger.info(f"Alerta {alert_id} suprimido (cooldown: {ttl}s)")
            return False
        
        # Setar cooldown
        self.redis.setex(key, cooldown.get(level, 3600), '1')
        return True
```

---

## 7. BACKLOG

- [x] Definir 4 níveis de severidade com cores e tempos de resposta
- [x] Documentar 15+ alertas configurados por nível
- [x] Implementar bot de alertas com contexto e formatação
- [x] Documentar matriz de escalada (Telegram → SMS → PagerDuty)
- [x] Implementar supressão de alertas (cooldown)
- [ ] Configurar chat IDs por nível
- [ ] Integrar com PagerDuty/Opsgenie para escalada
- [ ] Testar alertas end-to-end (simulação de falhas)

---

## 8. LINKS CRUZADOS

- [[33_Alerting/INDEX]] ← Secção mãe
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Thresholds detalhados de alertas
- [[10_Monitoring/INDEX]] → Métricas que disparam alertas
- [[10_Monitoring/DASHBOARD_TECNICO]] → Dashboard de alertas
- [[26_Runbooks/RB-003_CIRCUIT_BREAKER_ATIVADO]] → Runbook para circuit breaker
