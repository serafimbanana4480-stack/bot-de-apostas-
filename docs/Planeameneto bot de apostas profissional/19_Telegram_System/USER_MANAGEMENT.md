---
ID: TEL-007
tags: #status/active #telegram #users #auth #permissions #rbac
---

# Gestão de Utilizadores

## Objetivo
Documentar o sistema completo de gestão de utilizadores do bot Telegram, incluindo autenticação, autorização, controlo de acessos baseado em roles (RBAC), ciclo de vida de contas, e compliance com GDPR. O sistema deve ser seguro, auditável, e capaz de escalar para milhares de utilizadores sem degradação de performance.

## O que faz
- Define o modelo de dados de utilizadores: perfis, subscrições, preferências, e metadados de auditoria.
- Implementa autenticação via Telegram (user_id como identificador único) com verificação opcional de email/telefone para compliance.
- Estabelece sistema de permissões baseado em roles: VISITOR, SUBSCRIBER, PRO, INSTITUTIONAL, MODERATOR, ADMIN, SUPER_ADMIN.
- Define workflow de onboarding: registo → verificação → pagamento → ativação → onboarding → subscrição ativa.
- Implementa mecanismos de recuperação de conta, cancelamento, e reativação.

## Porque existe
- **Segurança**: Sem um sistema robusto de autenticação e autorização, qualquer utilizador poderia aceder a funcionalidades administrativas ou sinais premium sem pagamento.
- **Compliance GDPR**: A lei exige que os utilizadores possam aceder, corrigir, e eliminar os seus dados pessoais. O sistema de gestão de utilizadores deve suportar estes direitos.
- **Monetização**: A segregação clara entre utilizadores gratuitos e pagos é essencial para o modelo de negócio. O sistema de roles garante que apenas subscritores ativos recebem sinais premium.
- **Auditoria**: Em caso de disputa ou investigação regulatória, é necessário ter um registo completo de quem acedeu a quê e quando.

## Modelo de Dados

### Tabela: users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(255),
    telegram_first_name VARCHAR(255),
    telegram_last_name VARCHAR(255),
    email VARCHAR(255) UNIQUE,  -- Opcional para compliance
    phone VARCHAR(50),  -- Opcional para compliance
    language VARCHAR(10) DEFAULT 'pt',
    timezone VARCHAR(50) DEFAULT 'Europe/Lisbon',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_telegram_id ON users(telegram_user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Tabela: subscriptions
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,  -- ESSENCIAL, PRO, INSTITUTIONAL
    status VARCHAR(20) NOT NULL,  -- ACTIVE, EXPIRED, CANCELLED, PENDING
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_provider VARCHAR(50),  -- stripe, paypal
    payment_id VARCHAR(255),
    amount_eur DECIMAL(10, 2),
    auto_renew BOOLEAN DEFAULT TRUE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);
```

### Tabela: user_preferences
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stake_unit_eur DECIMAL(10, 2) DEFAULT 10.00,
    notification_signals BOOLEAN DEFAULT TRUE,
    notification_results BOOLEAN DEFAULT TRUE,
    notification_marketing BOOLEAN DEFAULT FALSE,
    preferred_markets TEXT[],  -- ['spread', 'total', 'moneyline']
    min_edge_threshold DECIMAL(5, 2),  -- Mínimo edge para receber sinal
    max_daily_stakes INTEGER DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);
```

### Tabela: audit_log
```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
```

---

## Sistema de Roles e Permissões

### Hierarquia de Roles
```
SUPER_ADMIN
├── ADMIN
│   ├── MODERATOR
│   └── INSTITUTIONAL
│       └── PRO
│           └── ESSENCIAL
│               └── VISITOR
```

### Matriz de Permissões

| Permissão | VISITOR | ESSENCIAL | PRO | INSTITUTIONAL | MODERATOR | ADMIN | SUPER_ADMIN |
|-----------|---------|-----------|-----|---------------|-----------|-------|-------------|
| /start | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /help | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /status | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /stats | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /historico | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /unidade | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /alertas | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Receber sinais básicos | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Receber sinais premium | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Acesso API | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| /broadcast | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| /manutencao | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Banir utilizadores | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gerir subscrições | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Configurar sistema | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Workflows de Utilizador

### Workflow 1: Onboarding de Novo Utilizador
```python
class UserOnboarding:
    """
    Orquestra o processo de onboarding de um novo utilizador.
    """
    def __init__(self, db, telegram_client, payment_gateway):
        self.db = db
        self.telegram = telegram_client
        self.payment = payment_gateway

    async def handle_start(self, telegram_user):
        # 1. Verificar se utilizador já existe
        user = await self.db.get_user_by_telegram_id(telegram_user["id"])

        if not user:
            # 2. Criar novo utilizador
            user = await self.db.create_user({
                "telegram_user_id": telegram_user["id"],
                "telegram_username": telegram_user.get("username"),
                "telegram_first_name": telegram_user.get("first_name"),
                "telegram_last_name": telegram_user.get("last_name"),
                "language": telegram_user.get("language_code", "pt")
            })

            await self.log_audit(user["id"], "USER_CREATED", None, None, user)

        # 3. Verificar subscrição ativa
        subscription = await self.db.get_active_subscription(user["id"])

        if subscription:
            return await self.send_welcome_back(user, subscription)
        else:
            return await self.send_onboarding_flow(user)

    async def send_onboarding_flow(self, user):
        """
        Envia mensagens de onboarding com opções de plano.
        """
        message = f"""
👋 Bem-vindo ao NBA Value Signals!

Sou o seu assistente de value betting NBA. Aqui vais receber sinais de alta qualidade baseados em modelos quantitativos.

📊 **Nossos Planos:**

🔹 **ESSENCIAL** — 29€/mês
   • Sinais de spread e total
   • 5-10 sinais por dia
   • Estatísticas pessoais

🔹 **PRO** — 79€/mês
   • Tudo do Essencial
   • Sinais de player props
   • Acesso a API
   • Suporte prioritário

🔹 **INSTITUCIONAL** — 299€/mês
   • Tudo do Pro
   • Sinais em tempo real
   • API completa
   • Consultoria personalizada

Escolhe o teu plano para começar:
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Essencial 29€", callback_data="plan_essential")],
            [InlineKeyboardButton("Pro 79€", callback_data="plan_pro")],
            [InlineKeyboardButton("Institucional 299€", callback_data="plan_institutional")]
        ])

        await self.telegram.send_message(user["telegram_user_id"], message, reply_markup=keyboard)
```

### Workflow 2: Verificação de Identidade (Opcional)
```python
class IdentityVerification:
    """
    Implementa verificação de identidade para compliance.
    """
    def __init__(self, db, email_service, sms_service):
        self.db = db
        self.email = email_service
        self.sms = sms_service

    async def request_email_verification(self, user_id, email):
        # 1. Validar formato de email
        if not self.validate_email(email):
            raise InvalidEmailError()

        # 2. Gerar código de verificação
        code = self.generate_verification_code()
        expiry = datetime.utcnow() + timedelta(hours=24)

        # 3. Guardar código
        await self.db.store_verification_code(user_id, "EMAIL", code, expiry)

        # 4. Enviar email
        await self.email.send(
            to=email,
            subject="Verificação de Email - NBA Value Signals",
            body=f"O teu código de verificação é: {code}"
        )

    async def verify_email(self, user_id, code):
        # 1. Validar código
        stored = await self.db.get_verification_code(user_id, "EMAIL")

        if not stored or stored["code"] != code or stored["expiry"] < datetime.utcnow():
            raise InvalidVerificationCodeError()

        # 2. Marcar email como verificado
        await self.db.update_user(user_id, {"email": stored["email"], "is_verified": True})

        # 3. Eliminar código
        await self.db.delete_verification_code(user_id, "EMAIL")

        await self.log_audit(user_id, "EMAIL_VERIFIED", "user", user_id, {"is_verified": True})
```

### Workflow 3: Cancelamento de Subscrição
```python
class SubscriptionCancellation:
    """
    Gerencia o processo de cancelamento de subscrições.
    """
    def __init__(self, db, telegram_client, payment_gateway):
        self.db = db
        self.telegram = telegram_client
        self.payment = payment_gateway

    async def request_cancellation(self, user_id):
        # 1. Verificar subscrição ativa
        subscription = await self.db.get_active_subscription(user_id)

        if not subscription:
            raise NoActiveSubscriptionError()

        # 2. Enviar confirmação
        message = f"""
⚠️ **Cancelamento de Subscrição**

Estás prestes a cancelar a tua subscrição {subscription['plan']}.

📅 Data de término: {subscription['end_date'].strftime('%Y-%m-%d')}

Após cancelamento:
• Continuarás a ter acesso até ao fim do período atual
• Não serás cobrado novamente
• Serás removido dos grupos Telegram automaticamente

Tens a certeza?
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Sim, cancelar", callback_data=f"cancel_confirm_{subscription['id']}")],
            [InlineKeyboardButton("Não, manter", callback_data="cancel_keep")]
        ])

        await self.telegram.send_message(user_id, message, reply_markup=keyboard)

    async def confirm_cancellation(self, user_id, subscription_id):
        # 1. Atualizar subscrição
        await self.db.update_subscription(subscription_id, {
            "status": "CANCELLED",
            "auto_renew": False,
            "cancelled_at": datetime.utcnow()
        })

        # 2. Cancelar no payment gateway
        subscription = await self.db.get_subscription(subscription_id)
        if subscription["payment_provider"] == "stripe":
            await self.payment.cancel_subscription(subscription["payment_id"])

        # 3. Agendar remoção de grupos
        await self.schedule_group_removal(user_id, subscription["end_date"])

        # 4. Enviar confirmação
        await self.telegram.send_message(user_id, """
✅ Subscrição cancelada com sucesso.

Continuarás a ter acesso até ao fim do período atual.
Agradecemos a tua preferência!
        """)

        await self.log_audit(user_id, "SUBSCRIPTION_CANCELLED", "subscription", subscription_id, {
            "status": "CANCELLED",
            "cancelled_at": datetime.utcnow().isoformat()
        })
```

---

## GDPR e Privacidade

### Direitos do Titular dos Dados

| Direito | Implementação | Endpoint |
|---------|---------------|----------|
| Direito de acesso | Utilizador pode solicitar exportação de todos os seus dados | /meusdados |
| Direito de correção | Utilizador pode atualizar email, telefone, preferências | /atualizarperfil |
| Direito de eliminação | Utilizador pode solicitar eliminação da conta (após 30 dias de retenção) | /eliminarconta |
| Direito de portabilidade | Exportação em JSON/CSV de todos os dados | /exportardados |
| Direito de oposição | Opt-out de marketing | /alertas marketing off |

### Retenção de Dados
```python
class DataRetention:
    """
    Implementa políticas de retenção de dados conforme GDPR.
    """
    async def anonymize_inactive_users(self):
        """
        Anonimiza utilizadores inativos há mais de 3 anos.
        """
        cutoff = datetime.utcnow() - timedelta(days=365 * 3)

        users = await self.db.get_users_inactive_since(cutoff)

        for user in users:
            await self.db.update_user(user["id"], {
                "telegram_username": None,
                "telegram_first_name": "Anonimizado",
                "telegram_last_name": None,
                "email": None,
                "phone": None,
                "metadata": {"anonymized_at": datetime.utcnow().isoformat()}
            })

    async def delete_user_request(self, user_id):
        """
        Processa pedido de eliminação de conta.
        """
        # 1. Verificar que não há subscrição ativa
        subscription = await self.db.get_active_subscription(user_id)
        if subscription:
            raise ActiveSubscriptionError()

        # 2. Soft delete (marcar para eliminação)
        await self.db.update_user(user_id, {
            "is_banned": True,
            "ban_reason": "USER_REQUESTED_DELETION",
            "deleted_at": datetime.utcnow()
        })

        # 3. Agendar eliminação definitiva após 30 dias
        await self.schedule_hard_delete(user_id, days=30)

        # 4. Notificar utilizador
        await self.telegram.send_message(user_id, """
✅ Pedido de eliminação recebido.

A tua conta será eliminada permanentemente dentro de 30 dias.
Se mudares de ideia, contacta-nos antes desse prazo.
        """)
```

---

## Auditoria e Logging

### Eventos Auditáveis
```python
AUDIT_EVENTS = {
    "USER_CREATED": "Novo utilizador registado",
    "USER_UPDATED": "Perfil atualizado",
    "USER_DELETED": "Utilizador eliminado",
    "USER_BANNED": "Utilizador banido",
    "USER_UNBANNED": "Utilizador desbanido",
    "SUBSCRIPTION_CREATED": "Subscrição criada",
    "SUBSCRIPTION_UPDATED": "Subscrição atualizada",
    "SUBSCRIPTION_CANCELLED": "Subscrição cancelada",
    "SUBSCRIPTION_EXPIRED": "Subscrição expirada",
    "PAYMENT_RECEIVED": "Pagamento recebido",
    "PAYMENT_FAILED": "Pagamento falhou",
    "PERMISSION_GRANTED": "Permissão concedida",
    "PERMISSION_REVOKED": "Permissão revogada",
    "LOGIN_ATTEMPT": "Tentativa de login",
    "PASSWORD_RESET": "Reset de password",
    "DATA_EXPORT": "Exportação de dados",
    "DATA_DELETED": "Eliminação de dados"
}
```

### Implementação de Audit Log
```python
class AuditLogger:
    """
    Registra todos os eventos relevantes para auditoria.
    """
    async def log(self, user_id, action, resource_type, resource_id, old_values, new_values, request=None):
        await self.db.insert("audit_log", {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": request.remote_addr if request else None,
            "user_agent": request.headers.get("User-Agent") if request else None,
            "created_at": datetime.utcnow()
        })

    async def get_user_audit_trail(self, user_id, limit=100):
        """
        Obtém histórico de auditoria de um utilizador.
        """
        return await self.db.query("""
            SELECT * FROM audit_log
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, user_id, limit)
```

---

## Thresholds e Tabelas

| Métrica | Threshold | Alerta | Ação |
|---------|-----------|--------|------|
| Novos registos/dia | > 100 | Info | — |
| Novos registos/dia | > 500 | Aviso | Verificar se é legítimo |
| Cancelamentos/dia | > 10 | Aviso | Investigar causa |
| Cancelamentos/dia | > 50 | Crítico | Revisão de produto |
| Taxa de conversão | < 5% | Aviso | Otimizar onboarding |
| Taxa de conversão | < 2% | Crítico | Revisão pricing |
| Utilizadores inativos (90d) | > 30% | Aviso | Campanha reativação |
| Tentativas de login falhadas | > 5/min/user | Aviso | Bloquear temporariamente |

| Estado da Subscrição | Duração Máxima | Ação Automática |
|----------------------|----------------|------------------|
| PENDING | 24 horas | Cancelar |
| EXPIRED | 30 dias | Anonimizar dados |
| CANCELLED | Imediato | Remover grupos |
| BANNED | Permanente | Remover grupos |

---

## Links Cruzados

- [[TELEGRAM_BOT_ARCHITECTURE]] → Arquitetura do bot
- [[COMANDOS_BOT]] → Comandos disponíveis por role
- [[SEGURANCA_TELEGRAM]] → Segurança do sistema
- [[GRUPOS_CANAIS]] → Sincronização com grupos
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES]] → Planos e preços