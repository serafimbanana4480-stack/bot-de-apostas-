# AUDIT_LOGGING — Logging de Auditoria

**ID:** `SEC-004` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. VISÃO GERAL

Todo o acesso ao sistema, alterações de configuração e operações críticas são registados em audit logs imutáveis. Estes logs são essenciais para:
- **Compliance:** Regulamentação de jogos de azar
- **Forensics:** Investigação de incidentes
- **Accountability:** Rastreabilidade de ações
- **Debugging:** Diagnóstico de problemas

---

## 2. O QUE LOGAR

### 2.1 Eventos Obrigatórios

| Categoria | Eventos | Nível |
|-----------|---------|-------|
| **Autenticação** | Login, logout, falhas de autenticação, revogação de tokens | INFO |
| **Autorização** | Acesso negado, escalonamento de privilégios | WARN |
| **Operações de Apostas** | Placement, cancelamento, alteração de stake | INFO |
| **Alterações de Config** | Mudanças em parâmetros de risco, circuit breakers | WARN |
| **Acesso a Dados** | Export de dados, queries sensíveis | INFO |
| **Alterações de Código** | Deploy, rollback, alterações em produção | WARN |
| **Incidentes** | Erros críticos, falhas de sistema, timeouts | ERROR |
| **Segurança** | Tentativas de intrusão, IPs banidos, anomalias | WARN |

### 2.2 Exemplos de Log Entries

```json
{
  "timestamp": "2024-01-15T14:32:10Z",
  "level": "INFO",
  "event_type": "bet_placed",
  "user_id": "op_123",
  "bet_id": "bet_456",
  "market_id": "1.12345678",
  "selection_id": "789012",
  "stake": 10.50,
  "odds": 2.15,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "success"
}

{
  "timestamp": "2024-01-15T14:35:22Z",
  "level": "WARN",
  "event_type": "config_changed",
  "user_id": "admin_001",
  "parameter": "max_stake",
  "old_value": 100,
  "new_value": 150,
  "ip_address": "192.168.1.50",
  "justification": "Ajuste trimestral baseado em bankroll",
  "result": "success"
}

{
  "timestamp": "2024-01-15T14:40:05Z",
  "level": "ERROR",
  "event_type": "authentication_failed",
  "username": "unknown",
  "ip_address": "203.0.113.50",
  "reason": "Invalid credentials",
  "attempts": 5
}
```

---

## 3. ARQUITETURA DE LOGGING

### 3.1 Pipeline de Logs

```
Application → Structlog → File (JSON) → Logrotate → S3/Offsite
                                      ↓
                                 PostgreSQL (audit table)
```

### 3.2 Implementação com Structlog

```python
import structlog
from datetime import datetime

# Configurar structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Exemplo de uso
def log_bet_placed(user_id: str, bet_id: str, market_id: str, stake: float, odds: float):
    logger.info(
        "bet_placed",
        event_type="bet_placed",
        user_id=user_id,
        bet_id=bet_id,
        market_id=market_id,
        stake=stake,
        odds=odds,
        ip_address=request.remote_addr,
        result="success"
    )
```

### 3.3 Armazenamento em PostgreSQL

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(10) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    service_id VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    payload JSONB NOT NULL,
    result VARCHAR(20) NOT NULL
);

-- Índices para queries comuns
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_level ON audit_logs(level);

-- Partitioning por mês (para performance)
-- Implementar em fase 2
```

---

## 4. RETENÇÃO E ARQUIVO

### 4.1 Políticas de Retenção

| Tipo de Log | Retenção Online | Retenção Offline | Arquivo |
|-------------|-----------------|------------------|---------|
| **Operacional** | 30 dias | 1 ano | S3/Glacier |
| **Segurança** | 90 dias | 7 anos | S3/Glacier |
| **Compliance** | 1 ano | 10 anos | S3/Glacier |
| **Debug** | 7 dias | 30 dias | S3 |

### 4.2 Logrotate Configuration

```bash
# /etc/logrotate.d/valuebetting
/var/log/valuebetting/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 vb_user vb_group
    sharedscripts
    postrotate
        # Enviar para S3 após rotação
        /usr/local/bin/send_logs_to_s3.sh
    endscript
}
```

---

## 5. PROTEÇÃO DE LOGS

### 5.1 Imutabilidade

- Logs em produção são **append-only**
- Uma vez escrito, um log nunca é alterado ou deletado (apenas arquivado)
- Logs de segurança têm hash SHA-256 para integridade

### 5.2 Acesso a Logs

| Role | Permissões |
|------|------------|
| **ADMIN** | Full access (read + export) |
| **OPERATIONS** | Read logs de operações (últimos 30 dias) |
| **DEVELOPER** | Read logs de erro/debug (últimos 7 dias) |
| **VIEWER** | Read-only dashboards agregados |

---

## 6. MONITORIZAÇÃO E ALERTAS

### 6.1 Alertas Automáticos

| Condição | Nível | Ação |
|----------|-------|------|
| >10 falhas de autenticação em 5 min (mesmo IP) | WARN | Banir IP + alerta Telegram |
| Alteração de config crítica | WARN | Notificar ADMIN |
| >50 apostas falhadas em 1 hora | ERROR | PagerDuty + parar sistema |
| Acesso de IP não autorizado | WARN | Alerta Telegram |
| Query SQL suspeita (SELECT *, DELETE sem WHERE) | ERROR | PagerDuty |

### 6.2 Dashboard de Auditoria

Métricas em tempo real:
- Taxa de sucesso de autenticação
- Top IPs por volume de acessos
- Operações por utilizador
- Alterações de configuração
- Tentativas de acesso negado

---

## 7. INVESTIGAÇÃO E FORENSICS

### 7.1 Queries Comuns

```sql
-- Acessos de um utilizador num período
SELECT * FROM audit_logs
WHERE user_id = 'op_123'
  AND timestamp BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY timestamp DESC;

-- Tentativas de autenticação falhadas
SELECT * FROM audit_logs
WHERE event_type = 'authentication_failed'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Alterações de configuração
SELECT * FROM audit_logs
WHERE event_type = 'config_changed'
ORDER BY timestamp DESC
LIMIT 100;

-- Top IPs com acessos negados
SELECT ip_address, COUNT(*) as denied_count
FROM audit_logs
WHERE level = 'WARN'
  AND result = 'denied'
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY ip_address
ORDER BY denied_count DESC
LIMIT 10;
```

### 7.2 Export para Investigação

```python
def export_audit_logs(start_date: datetime, end_date: datetime, event_type: str = None):
    query = """
        SELECT * FROM audit_logs
        WHERE timestamp BETWEEN %s AND %s
    """
    params = [start_date, end_date]

    if event_type:
        query += " AND event_type = %s"
        params.append(event_type)

    logs = db.execute(query, params)

    # Export para CSV com hash de integridade
    csv_content = convert_to_csv(logs)
    sha256_hash = hashlib.sha256(csv_content.encode()).hexdigest()

    filename = f"audit_export_{start_date}_{end_date}_{sha256_hash[:8]}.csv"

    # Upload para S3 com encriptação
    s3_client.upload_file(
        filename,
        'audit-logs-bucket',
        f'exports/{filename}',
        ExtraArgs={'ServerSideEncryption': 'AES256'}
    )

    return filename
```

---

## 8. COMPLIANCE

### 8.1 Requisitos Regulamentares

| Regulamento | Requisito | Implementação |
|-------------|-----------|---------------|
| **GDPR** | Logs pessoais anonimizados após 2 anos | Retenção 2 anos, depois anonimização |
| **SOC2** | Logs imutáveis e auditáveis | Append-only + integridade SHA-256 |
| **Jogos de Azar** | Trilha completa de apostas | Todas as apostas logadas com timestamp |
| **PCI-DSS** (se aplicável) | Logs de acesso a dados de pagamento | N/A (sem dados de pagamento) |

---

## 9. BACKLOG

- [ ] Implementar partitioning por mês em PostgreSQL
- [ ] Configurar ELK Stack para visualização de logs
- [ ] Implementar anonimização automática após período de retenção
- [ ] Criar dashboard em Grafana para métricas de auditoria
- [ ] Implementar SIEM (Security Information and Event Management)

---

## 10. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secão mãe
- [[34_Security/INCIDENT_RESPONSE]] → Investigação de incidentes
- [[34_Security/ACCESS_CONTROL]] → Autenticação e autorização
- [[12_DevOps/INDEX]] → Monitorização e alertas