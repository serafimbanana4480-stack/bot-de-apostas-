# ARQUITETURA DE SEGURANÇA

**ID:** `SEC-001` | **Fase:** Todas | **Owner:** Security Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Garantir a segurança do sistema em múltiplas dimensões: secrets, autenticação, autorização, audit logging, e proteção contra ataques comuns.

---

## 2. PRINCÍPIOS DE SEGURANÇA

### 2.1 Zero Hardcoded Secrets
- Todas as credenciais (API keys, passwords) devem estar em variáveis de ambiente
- Nunca comitar secrets em repositórios
- Usar `.env.example` como template
- Adicionar `.env` ao `.gitignore`

### 2.2 Princípio do Menor Privilégio
- Operadores têm acesso apenas ao necessário para as suas funções
- Nível 1: Leitura (view-only dashboards)
- Nível 2: Operação (executar apostas manuais)
- Nível 3: Admin (configurar sistema, ver logs)
- Nível 4: Super-admin (root, alterar modelos)

### 2.3 Audit Trail Completo
- Toda ação manual deve ser registada
- Toda alteração de parâmetros deve ser auditada
- Toda intervenção em circuit breakers deve ter motivo documentado

---

## 3. GESTÃO DE SECRETS

### 3.1 Variáveis de Ambiente

O sistema usa as seguintes variáveis de ambiente (ver `.env.example`):

```bash
# PostgreSQL
POSTGRES_PASSWORD

# Redis
REDIS_PASSWORD

# Betfair API
BETFAIR_APP_KEY
BETFAIR_USERNAME
BETFAIR_PASSWORD

# Telegram Bot
TELEGRAM_BOT_TOKEN

# SendGrid
SENDGRID_API_KEY
```

### 3.2 Rotation Policy

- **Senhas de base de dados:** Rotação trimestral
- **API Keys:** Rotação se comprometida
- **Bot Tokens:** Rotação se comprometido
- **Processo:** 1. Gerar nova key → 2. Atualizar .env → 3. Deploy → 4. Invalidar antiga

### 3.3 Secrets Management (Futuro)

Para produção institucional, considerar:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault

---

## 4. AUTENTICAÇÃO E AUTORIZAÇÃO

### 4.1 API Authentication

A API FastAPI usa API keys para autenticação:

```python
# src/api/middleware/auth.py

from fastapi import Security, HTTPBearer, HTTPException
from fastapi.security import OAuth2PasswordBearer

security = HTTPBearer()

API_KEYS = {
    "admin_key_abc123": {"role": "admin", "permissions": ["read", "write", "admin"]},
    "operator_key_xyz789": {"role": "operator", "permissions": ["read", "write"]},
    "viewer_key_def456": {"role": "viewer", "permissions": ["read"]},
}

def get_api_key(api_key: str = Security(auto_error=False)):
    if api_key in API_KEYS:
        return API_KEYS[api_key]
    raise HTTPException(status_code=403, detail="Invalid API Key")
```

### 4.2 Role-Based Access Control (RBAC)

| Role | Permissões | Endpoints |
|------|-----------|-----------|
| admin | read, write, admin | TODOS |
| operator | read, write | /signals, /predict, /health |
| viewer | read | /signals, /health, /metrics |

### 4.3 Telegram Bot Authentication

- Bot usa Chat ID whitelist
- Apenas utilizadores autorizados podem receber sinais
- Comandos administrativos protegidos por password

---

## 5. AUDIT LOGGING

### 5.1 Tabela de Audit

```sql
CREATE TABLE audit.manual_interventions (
    id              BIGSERIAL PRIMARY KEY,
    operator_id     VARCHAR(50) NOT NULL,
    action_type     VARCHAR(50) NOT NULL,
    target_signal_id VARCHAR(30),
    reason          TEXT,
    action_taken     TEXT,
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    ip_address      VARCHAR(45)
);

CREATE TABLE audit.model_updates (
    id              BIGSERIAL PRIMARY KEY,
    model_name      VARCHAR(50) NOT NULL,
    old_version     VARCHAR(20),
    new_version     VARCHAR(20),
    reason          TEXT,
    operator_id     VARCHAR(50),
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit.circuit_breaker_overrides (
    id              BIGSERIAL PRIMARY KEY,
    breaker_name    VARCHAR(20) NOT NULL,
    original_status VARCHAR(10),
    new_status      VARCHAR(10),
    reason          TEXT,
    operator_id     VARCHAR(50),
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 Eventos Auditados

- Override manual de circuit breaker
- Alteração de parâmetros de risco (edge_min, KELLY_K, etc.)
- Promoção de modelo para produção
- Intervenção manual em execução (cancelar aposta)
- Alteração de subscritores (adicionar/remover)
- Acesso a dados sensíveis (banca, PnL real)

---

## 6. PROTEÇÃO CONTRA ATAQUES COMUNS

### 6.1 SQL Injection

- **Proteção:** Todos os queries usam parâmetros preparados (SQLAlchemy)
- **Validação:** SQLAlchemy ORM previne injection por padrão

### 6.2 XSS (Cross-Site Scripting)

- **Proteção:** FastAPI auto-escapa JSON
- **Validação:** Pydantic valida tipos automaticamente

### 6.3 Rate Limiting

- **API:** 100 requests/minuto por IP
- **Telegram:** 20 comandos/minuto por utilizador
- **Betfair API:** Respeitar rate limits da Betfair (30 requests/segundo)

```python
# src/api/middleware/rate_limit.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
@app.middleware("http")
@limiter.limit("100/minute")
async def rate_limit_middleware(request: Request, call_next):
    await call_next(request)
```

### 6.4 DDoS Protection

- **Cloudflare:** Considerar Cloudflare para DDoS protection
- **Nginx:** Rate limiting no nível de proxy
- **Fail2Ban:** Ban IPs com tentativas falhadas de login

### 6.5 Input Validation

- Todos os inputs validados com Pydantic
- Validação de ranges (odd > 1, stake > 0, etc.)
- Validação de tipos (não aceitar strings onde se espera números)

```python
# src/api/schemas.py

from pydantic import BaseModel, Field, validator

class SignalRequest(BaseModel):
    game_id: str = Field(..., min_length=10, max_length=20)
    market_type: str = Field(..., regex="^(MONEYLINE|SPREAD)$")
    odd: float = Field(..., gt=1.0, le=100.0)
    stake_euros: float = Field(..., gt=0.0, le=10000.0)
    
    @validator('odd')
    def odd_must_be_positive(cls, v):
        if v <= 1.0:
            raise ValueError("Odd must be > 1.0")
        return v
```

---

## 7. COMPLIANCE E REGULATÓRIA

### 7.1 GDPR

- **Consentimento:** Checkbox explícito para processamento de dados
- **Direito ao esquecimento:** Utilizador pode pedir eliminação dos seus dados
- **Portabilidade:** Utilizador pode pedir export dos seus dados
- **Minimização:** Recolher apenas dados necessários

### 7.2 SRIJ (Portugal)

- **Licença de jogo online:** NÃO necessária para tipster (serviço de informação)
- **Licença de gestão de ativos:** NECESSÁRIA se aceitar capital externo (fase 9+)
- **Impostos:** Lucros de apostas podem ser tributados como mais-valias (28%)

### 7.3 KYC/AML

- Para subscritores: Email + nome (fase inicial)
- Para investidores: KYC completo (fase 9+)
- Monitorização de transações suspeitas

---

## 8. BACKUP E DISASTER RECOVERY

### 8.1 Backup Strategy

- **PostgreSQL:** Backup diário (automático), retenção 30 dias
- **Redis:** Não persistente (apenas cache), não faz backup
- **Modelos:** Backup via MLflow (artefacts)
- **Logs:** Backup semanal, retenção 90 dias

### 8.2 RTO e RPO

| Componente | RTO (Recovery Time) | RPO (Recovery Point) |
|-----------|---------------------|-------------------|
| PostgreSQL | 4 horas | 1 hora |
| Redis | 5 minutos | N/A (cache) |
| Modelos | 1 dia | 1 semana |
| Logs | 1 dia | 1 dia |

### 8.3 Disaster Recovery

- **Backup offsite:** Backups copiados para cloud separado (S3, Backblaze)
- **Failover:** Se VPS principal falhar, ativar VPS de backup
- **Processo de recovery:**
  1. Restaurar backup PostgreSQL
  2. Redeploy containers
  3. Atualizar DNS
  4. Verificar integridade dos dados

---

## 9. MONITIZAÇÃO DE SEGURANÇA

### 9.1 Métricas de Segurança

- Tentativas de login falhadas
- API keys inválidas
- Rate limit violations
- Override de circuit breakers
- Acesso a endpoints administrativos

### 9.2 Alertas de Segurança

- **P0:** 10+ tentativas de login falhadas em 1 minuto
- **P0:** API key inválida usada 100+ vezes em 1 hora
- **P1:** Override de circuit breaker sem motivo documentado
- **P1:** Alteração de parâmetros críticos (edge_min, KELLY_K)

---

## 10. CHECKLIST DE SEGURANÇA

### 10.1 Setup Inicial

- [ ] Criar `.env` a partir de `.env.example`
- [ ] Definir passwords fortes (16+ caracteres, misto de tipos)
- [ ] Configurar API keys (Betfair, Telegram, SendGrid)
- [ ] Adicionar `.env` ao `.gitignore`
- [ ] Ativar autenticação na API
- [ ] Configurar rate limiting
- [ ] Configurar backups automatizados

### 10.2 Operacional

- [ ] Usar SSH keys para acesso ao VPS (não password)
- [ ] Atualizar sistema operativo regularmente
- [ ] Rotação de passwords trimestralmente
- [ ] Revisar logs de auditoria semanalmente
- [ ] Testar processo de disaster recovery trimestralmente

---

## 11. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[34_Security/INDEX]] → Secção mãe de segurança
- [[28_Failure_Scenarios/INDEX]] → Cenários de falha e DR