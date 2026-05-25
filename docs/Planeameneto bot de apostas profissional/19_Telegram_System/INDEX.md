# 19_Telegram_System — INDEX

**ID:** `SEC-19` | **Fase:** #phase/3-10 | **Owner:** Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Implementar sistema de distribuição de sinais via Telegram para subscritores, incluindo gestão de subscritores, integração com pagamentos, e automação de envio de sinais.

---

## 2. ARQUITETURA DO SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                    MODELO PRIMÁRIO                            │
│  (XGBoost + LightGBM + CatBoost → Ensemble)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  META-MODELO                                 │
│  (Filtragem de falsos positivos)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                MOTOR DE EDGE                                  │
│  (Cálculo de edge, geração de sinais)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              TELEGRAM BOT (python-telegram-bot)              │
│  ├─ Envio de sinais para subscritores                      │
│  ├─ Gestão de subscrições                                  │
│  ├─ Comandos de usuário                                    │
│  └─ Integração com pagamentos                              │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐
│  CANAL DE   │ │  GRUPOS │ │  PRIVADOS   │
│  SINAIS     │ │  (VIP)  │ │  (Admin)    │
└─────────────┘ └─────────┘ └─────────────┘
```

---

## 3. COMPONENTES

### 3.1 Telegram Bot

**Libraries:**
- `python-telegram-bot` (v20.7+)

**Funcionalidades:**
- Envio de sinais para subscritores
- Gestão de subscrições (start, stop, status)
- Comandos de informação (/help, /status, /performance)
- Notificações de sistema (manutenção, incidentes)

### 3.2 Database de Subscritores

**Schema:**
```sql
CREATE TABLE subscribers (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'base',
    subscription_status VARCHAR(50) DEFAULT 'active',
    subscription_start_date DATE,
    subscription_end_date DATE,
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE signals_sent (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(255) UNIQUE NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    game_id VARCHAR(255),
    team VARCHAR(255),
    market VARCHAR(255),
    odd DECIMAL(10, 2),
    edge DECIMAL(5, 4),
    stake DECIMAL(10, 2),
    subscribers_count INTEGER
);
```

### 3.3 Integração com Pagamentos

**Opções:**
- **Stripe** (Recomendado para global)
- **Paddle** (Alternativa para Europa)
- **PayPal** (Alternativa simples)

**Fluxo:**
1. Subscritor clica em link de subscrição
2. Redirecionado para Stripe Checkout
3. Pagamento processado
4. Webhook notifica sistema
5. Sistema atualiza database de subscritores
6. Bot envia mensagem de boas-vindas

---

## 4. IMPLEMENTAÇÃO

### 4.1 Telegram Bot Setup

```python
# app/telegram/bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("stop", self.stop))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("performance", self.performance))
        
    async def start(self, update: Update, context):
        """Handler para comando /start"""
        user = update.effective_user
        telegram_id = user.id
        username = user.username
        
        # Verificar se usuário já é subscritor
        subscriber = get_subscriber(telegram_id)
        
        if subscriber:
            await update.message.reply_text(
                f"Olá {username}! Você já é subscritor desde {subscriber.subscription_start_date}."
            )
        else:
            # Criar novo subscritor (trial)
            create_subscriber(telegram_id, username)
            await update.message.reply_text(
                f"Olá {username}! Bem-vindo ao VBQ-UNIFIED.\n\n"
                f"Você está em trial grátis por 7 dias.\n"
                f"Use /help para ver comandos disponíveis."
            )
    
    async def stop(self, update: Update, context):
        """Handler para comando /stop"""
        user = update.effective_user
        telegram_id = user.id
        
        # Cancelar subscrição
        cancel_subscription(telegram_id)
        
        await update.message.reply_text(
            "Sua subscrição foi cancelada.\n"
            "Você deixará de receber sinais imediatamente."
        )
    
    async def status(self, update: Update, context):
        """Handler para comando /status"""
        user = update.effective_user
        telegram_id = user.id
        
        subscriber = get_subscriber(telegram_id)
        
        if subscriber:
            await update.message.reply_text(
                f"Status da subscrição:\n"
                f"- Tier: {subscriber.subscription_tier}\n"
                f"- Status: {subscriber.subscription_status}\n"
                f"- Início: {subscriber.subscription_start_date}\n"
                f"- Fim: {subscriber.subscription_end_date}"
            )
        else:
            await update.message.reply_text("Você não é subscritor. Use /start para começar.")
    
    async def help(self, update: Update, context):
        """Handler para comando /help"""
        help_text = """
Comandos disponíveis:
/start - Iniciar subscrição (trial grátis 7 dias)
/stop - Cancelar subscrição
/status - Ver status da subscrição
/performance - Ver performance recente
/help - Mostrar esta mensagem

Para suporte: support@valuebetting.com
        """
        await update.message.reply_text(help_text)
    
    async def performance(self, update: Update, context):
        """Handler para comando /performance"""
        # Buscar performance dos últimos 30 dias
        performance = get_recent_performance()
        
        await update.message.reply_text(
            f"Performance últimos 30 dias:\n"
            f"- CLV médio: {performance['clv_avg']:.2%}\n"
            f"- ROI: {performance['roi']:.2%}\n"
            f"- Número de apostas: {performance['n_bets']}\n"
            f"- Sharpe Ratio: {performance['sharpe']:.2f}"
        )
    
    def send_signal(self, signal: dict, subscribers: list):
        """Envia sinal para lista de subscritores"""
        message = self._format_signal(signal)
        
        for subscriber in subscribers:
            try:
                # Enviar mensagem privada
                self.application.bot.send_message(
                    chat_id=subscriber.telegram_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Erro ao enviar sinal para {subscriber.telegram_id}: {e}")
    
    def _format_signal(self, signal: dict) -> str:
        """Formata sinal para Telegram"""
        return f"""
🎯 <b>SINAL APROVADO</b> #{signal['signal_id']}

🏀 {signal['team']} vs {signal['opponent']}
📊 Mercado: {signal['market']} | {signal['selection']}
💰 Odd: {signal['odd']} (mínima: {signal['odd_min']})
📈 Edge: {signal['edge']:.2%} | Prob: {signal['prob']:.0%}
💵 Stake: €{signal['stake']:.2f} ({signal['stake_pct']:.1%} da banca)
⏰ Expira em: {signal['expiry_minutes']} min

⚠️ <b>NÃO APOSTAR</b> se odd < {signal['odd_min']}
        """
    
    def run(self):
        """Inicia o bot"""
        self.application.run_polling()
```

### 4.2 Integração com Stripe

```python
# app/payments/stripe.py
import stripe
from fastapi import HTTPException

stripe.api_key = "sk_test_..."  # Do Vault

class StripeIntegration:
    def __init__(self):
        pass
    
    def create_checkout_session(self, price_id: str, customer_email: str):
        """Cria sessão de checkout Stripe"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='https://valuebetting.com/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://valuebetting.com/cancel',
                customer_email=customer_email,
            )
            return session
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def handle_webhook(self, event):
        """Handle webhook do Stripe"""
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_email = session['customer_details']['email']
            
            # Atualizar subscrição no database
            update_subscription_from_stripe(customer_email, session)
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            customer_email = subscription['customer_email']
            
            # Cancelar subscrição no database
            cancel_subscription_from_stripe(customer_email)
```

### 4.3 Envio Automático de Sinais

```python
# app/pipeline/signal_dispatcher.py
from app.telegram.bot import TelegramBot
from app.database.subscribers import get_active_subscribers

class SignalDispatcher:
    def __init__(self, bot: TelegramBot):
        self.bot = bot
    
    def dispatch_signal(self, signal: dict):
        """Envia sinal para todos os subscritores ativos"""
        # Buscar subscritores ativos
        subscribers = get_active_subscribers()
        
        # Filtrar por tier (se necessário)
        # subscribers = [s for s in subscribers if s.subscription_tier == 'base']
        
        # Enviar sinal
        self.bot.send_signal(signal, subscribers)
        
        # Registar envio
        log_signal_sent(signal, len(subscribers))
```

---

## 5. CANAIS E GRUPOS

### 5.1 Canal de Sinais (Público)
- **Nome:** @vbq_signals
- **Propósito:** Sinais gratuitos para marketing
- **Conteúdo:** Sinais com delay, performance resumida
- **Acesso:** Público (sem subscrição)

### 5.2 Canal VIP (Privado)
- **Nome:** @vbq_vip (grupo privado)
- **Propósito:** Sinais em tempo real para subscritores pagos
- **Conteúdo:** Sinais imediatos, análise detalhada
- **Acesso:** Apenas subscritores pagos

### 5.3 Canal de Admins (Privado)
- **Nome:** @vbq_admins (grupo privado)
- **Propósito:** Comunicação interna da equipa
- **Conteúdo:** Alertas, incidentes, decisões
- **Acesso:** Apenas admins

---

## 6. FORMATO DE SINAIS

### 6.1 Sinal Padrão

```
🎯 SINAL APROVADO #SIG-20261015-001

🏀 Boston Celtics vs LA Lakers
📊 Mercado: Moneyline | Celtics
💰 Odd: 1.85 (mínima aceitável: 1.83)
📈 Edge: 7.3% | Prob: 58%
💵 Stake: €25.00 (2.5% da banca)
⏰ Expira em: 5 minutos

⚠️ NÃO APOSTAR se odd < 1.83
```

### 6.2 Sinal com Contexto Adicional

```
🎯 SINAL APROVADO #SIG-20261015-001

🏀 Boston Celtics vs LA Lakers
📊 Mercado: Moneyline | Celtics
💰 Odd: 1.85 (mínima aceitável: 1.83)
📈 Edge: 7.3% | Prob: 58%
💵 Stake: €25.00 (2.5% da banca)
⏰ Expira em: 5 minutos

📊 Contexto:
- Celtics: 3-0 nos últimos 3 jogos
- Back-to-back: Não
- Travel: < 100 km
- Rest days: 2

⚠️ NÃO APOSTAR se odd < 1.83
```

---

## 7. COMANDOS DO BOT

| Comando | Descrição | Acesso |
|---------|-----------|--------|
| `/start` | Iniciar subscrição (trial) | Todos |
| `/stop` | Cancelar subscrição | Subscritores |
| `/status` | Ver status da subscrição | Subscritores |
| `/performance` | Ver performance recente | Subscritores |
| `/help` | Mostrar ajuda | Todos |
| `/admin` | Comandos de admin | Admins |

---

## 8. MONITORIZAÇÃO

### 8.1 Métricas

- **Número de subscritores ativos**
- **Taxa de churn** (cancelamentos/mês)
- **Taxa de entrega de sinais** (% de sinais entregues)
- **Engajamento** (taxa de cliques em sinais)
- **Tempo de resposta** (tempo entre sinal e entrega)

### 8.2 Alertas

- Se número de subscritores < 50 (threshold de negócio)
- Se taxa de entrega < 95% (problema técnico)
- Se taxa de churn > 10%/mês (problema de produto)

---

## 9. COMPLIANCE

### 9.1 GDPR

- Consentimento explícito para receber mensagens
- Direito ao esquecimento (comando /stop)
- Direito ao acesso (comando /status)
- Retenção de dados de subscritores por 2 anos após cancelamento

### 9.2 Terms of Service

- Disclaimer de risco em todas as mensagens
- Não promessas de lucro
- Política de reembolso (7 dias)
- Política de cancelamento (cancelamento imediato)

---

## 10. BACKLOG DE TELEGRAM SYSTEM

- [ ] Implementar TelegramBot class
- [ ] Implementar integração com Stripe
- [ ] Criar database de subscritores
- [ ] Implementar comandos do bot
- [ ] Implementar envio automático de sinais
- [ ] Criar canal de sinais público
- [ ] Criar canal VIP privado
- [ ] Implementar webhook do Stripe
- [ ] Configurar monitorização
- [ ] Criar Terms of Service
- [ ] Criar Privacy Policy

---

## 11. VARIÁVEIS DE AMBIENTE REQUERIDAS

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=-1001234567890
TELEGRAM_VIP_GROUP_ID=-1001234567891
TELEGRAM_ADMINS_GROUP_ID=-1001234567892

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_1234567890
```

---

## 10. IMPLEMENTAÇÃO COMPLETA

### 10.1 Script Robusto de Telegram Bot
```python
"""
Bot Telegram completo para sistema de value betting
Inclui gestão de subscritores, envio de sinais, integração Stripe
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.error import TelegramError
import asyncpg
import stripe

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Subscriber:
    """Dados do subscritor"""
    telegram_id: int
    username: Optional[str]
    email: Optional[str]
    subscription_tier: str
    subscription_status: str
    subscription_start_date: datetime
    subscription_end_date: Optional[datetime]
    stripe_customer_id: Optional[str]

@dataclass
class Signal:
    """Dados do sinal"""
    signal_id: str
    game_id: str
    team: str
    opponent: str
    market: str
    selection: str
    odd: float
    odd_min: float
    edge: float
    prob: float
    stake: float
    stake_pct: float
    expiry_minutes: int

class DatabaseManager:
    """Gestor de database para subscritores"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
        
        logger.info("🗄️  DatabaseManager inicializado")
    
    async def connect(self):
        """Conecta ao PostgreSQL"""
        self.pool = await asyncpg.create_pool(self.db_url)
        logger.info("✅ Conectado ao PostgreSQL")
    
    async def create_subscriber(self, subscriber: Subscriber) -> bool:
        """Cria novo subscritor"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO subscribers 
                    (telegram_id, username, email, subscription_tier, 
                     subscription_status, subscription_start_date, subscription_end_date)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (telegram_id) DO NOTHING
                    """,
                    subscriber.telegram_id, subscriber.username, subscriber.email,
                    subscriber.subscription_tier, subscriber.subscription_status,
                    subscriber.subscription_start_date, subscriber.subscription_end_date
                )
            logger.info(f"✅ Subscritor criado: {subscriber.telegram_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao criar subscritor: {e}")
            return False
    
    async def get_subscriber(self, telegram_id: int) -> Optional[Subscriber]:
        """Obtém subscritor por telegram_id"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM subscribers WHERE telegram_id = $1",
                    telegram_id
                )
                if row:
                    return Subscriber(
                        telegram_id=row['telegram_id'],
                        username=row['username'],
                        email=row['email'],
                        subscription_tier=row['subscription_tier'],
                        subscription_status=row['subscription_status'],
                        subscription_start_date=row['subscription_start_date'],
                        subscription_end_date=row['subscription_end_date'],
                        stripe_customer_id=row['stripe_customer_id']
                    )
        except Exception as e:
            logger.error(f"❌ Erro ao obter subscritor: {e}")
        return None
    
    async def get_active_subscribers(self) -> List[Subscriber]:
        """Obtém todos os subscritores ativos"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM subscribers 
                    WHERE subscription_status = 'active'
                    AND (subscription_end_date IS NULL OR subscription_end_date > NOW())
                    """
                )
                return [
                    Subscriber(
                        telegram_id=row['telegram_id'],
                        username=row['username'],
                        email=row['email'],
                        subscription_tier=row['subscription_tier'],
                        subscription_status=row['subscription_status'],
                        subscription_start_date=row['subscription_start_date'],
                        subscription_end_date=row['subscription_end_date'],
                        stripe_customer_id=row['stripe_customer_id']
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"❌ Erro ao obter subscritores ativos: {e}")
        return []
    
    async def cancel_subscription(self, telegram_id: int) -> bool:
        """Cancela subscrição"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE subscribers 
                    SET subscription_status = 'cancelled',
                        subscription_end_date = NOW()
                    WHERE telegram_id = $1
                    """,
                    telegram_id
                )
            logger.info(f"✅ Subscrição cancelada: {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao cancelar subscrição: {e}")
            return False
    
    async def log_signal_sent(self, signal: Signal, subscribers_count: int) -> bool:
        """Registra envio de sinal"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO signals_sent 
                    (signal_id, game_id, team, market, odd, edge, stake, subscribers_count)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    signal.signal_id, signal.game_id, signal.team, signal.market,
                    signal.odd, signal.edge, signal.stake, subscribers_count
                )
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao registrar sinal: {e}")
            return False

class StripeIntegration:
    """Integração com Stripe para pagamentos"""
    
    def __init__(self, secret_key: str):
        stripe.api_key = secret_key
        logger.info("💳 Stripe integration inicializada")
    
    def create_checkout_session(self, price_id: str, customer_email: str, 
                               success_url: str, cancel_url: str) -> str:
        """Cria sessão de checkout"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
            )
            logger.info(f"✅ Checkout session criada: {session.id}")
            return session.url
        except Exception as e:
            logger.error(f"❌ Erro ao criar checkout: {e}")
            raise
    
    def handle_webhook(self, event: dict) -> bool:
        """Processa webhook do Stripe"""
        try:
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                customer_email = session['customer_details']['email']
                logger.info(f"💳 Pagamento completado: {customer_email}")
                return True
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                logger.info(f"💳 Subscrição cancelada: {subscription.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook: {e}")
            return False

class TelegramBot:
    """Bot Telegram completo"""
    
    def __init__(self, token: str, db_manager: DatabaseManager, 
                 stripe_integration: Optional[StripeIntegration] = None):
        self.token = token
        self.db_manager = db_manager
        self.stripe_integration = stripe_integration
        self.application = Application.builder().token(token).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("🤖 TelegramBot inicializado")
    
    def _register_handlers(self):
        """Registra handlers do bot"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("stop", self.stop))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("performance", self.performance))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para comando /start"""
        user = update.effective_user
        telegram_id = user.id
        username = user.username
        
        logger.info(f"👤 /start de {username} ({telegram_id})")
        
        # Verificar se usuário já é subscritor
        subscriber = await self.db_manager.get_subscriber(telegram_id)
        
        if subscriber and subscriber.subscription_status == 'active':
            await update.message.reply_text(
                f"👋 Olá {username}!\n\n"
                f"✅ Você já é subscritor desde {subscriber.subscription_start_date.strftime('%d/%m/%Y')}.\n"
                f"📊 Tier: {subscriber.subscription_tier}\n\n"
                f"Use /status para ver detalhes ou /help para comandos."
            )
        else:
            # Criar novo subscritor (trial)
            new_subscriber = Subscriber(
                telegram_id=telegram_id,
                username=username,
                email=None,
                subscription_tier='trial',
                subscription_status='active',
                subscription_start_date=datetime.now(),
                subscription_end_date=datetime.now() + timedelta(days=7)
            )
            
            await self.db_manager.create_subscriber(new_subscriber)
            
            # Botão de subscrição
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Subscrever (€29/mês)", callback_data='subscribe')]
            ])
            
            await update.message.reply_text(
                f"👋 Olá {username}! Bem-vindo ao VBQ-UNIFIED!\n\n"
                f"🎁 Você está em trial grátis por 7 dias.\n"
                f"📊 Receba sinais de value betting NBA em tempo real.\n\n"
                f"Use /help para ver comandos disponíveis.",
                reply_markup=keyboard
            )
    
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para comando /stop"""
        user = update.effective_user
        telegram_id = user.id
        
        logger.info(f"🛑 /stop de {telegram_id}")
        
        await self.db_manager.cancel_subscription(telegram_id)
        
        await update.message.reply_text(
            "🛑 Sua subscrição foi cancelada.\n\n"
            "Você deixará de receber sinais imediatamente.\n"
            "Use /start para reiniciar a qualquer momento."
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para comando /status"""
        user = update.effective_user
        telegram_id = user.id
        
        logger.info(f"📊 /status de {telegram_id}")
        
        subscriber = await self.db_manager.get_subscriber(telegram_id)
        
        if subscriber:
            status_text = (
                f"📊 Status da Subscrição\n\n"
                f"👤 Username: @{subscriber.username or 'N/A'}\n"
                f"📦 Tier: {subscriber.subscription_tier.upper()}\n"
                f"✅ Status: {subscriber.subscription_status.upper()}\n"
                f"📅 Início: {subscriber.subscription_start_date.strftime('%d/%m/%Y')}\n"
            )
            
            if subscriber.subscription_end_date:
                days_left = (subscriber.subscription_end_date - datetime.now()).days
                status_text += f"📅 Fim: {subscriber.subscription_end_date.strftime('%d/%m/%Y')} ({days_left} dias restantes)\n"
            else:
                status_text += f"📅 Fim: Vitalício\n"
            
            await update.message.reply_text(status_text)
        else:
            await update.message.reply_text(
                "❌ Você não é subscritor.\n\n"
                "Use /start para começar o trial grátis."
            )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para comando /help"""
        help_text = (
            "🤖 Comandos Disponíveis\n\n"
            "/start - Iniciar subscrição (trial grátis 7 dias)\n"
            "/stop - Cancelar subscrição\n"
            "/status - Ver status da subscrição\n"
            "/performance - Ver performance recente\n"
            "/subscribe - Ver planos de subscrição\n"
            "/help - Mostrar esta mensagem\n\n"
            "📧 Para suporte: support@valuebetting.com"
        )
        await update.message.reply_text(help_text)
    
    async def performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para comando /performance"""
        # Placeholder - buscar performance real do database
        performance = {
            'clv_avg': 0.05,
            'roi': 0.08,
            'n_bets': 150,
            'sharpe': 1.2
        }
        
        performance_text = (
            f"📈 Performance Últimos 30 Dias\n\n"
            f"💰 CLV médio: {performance['clv_avg']:.2%}\n"
            f"📊 ROI: {performance['roi']:.2%}\n"
            f"🎯 Número de apostas: {performance['n_bets']}\n"
            f"📏 Sharpe Ratio: {performance['sharpe']:.2f}"
        )
        await update.message.reply_text(performance_text)
    
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para comando /subscribe"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Base (€29/mês)", callback_data='subscribe_base')],
            [InlineKeyboardButton("💎 VIP (€79/mês)", callback_data='subscribe_vip')],
            [InlineKeyboardButton("⭐ Pro (€149/mês)", callback_data='subscribe_pro')]
        ])
        
        await update.message.reply_text(
            "📦 Planos de Subscrição\n\n"
            "Escolha o plano que melhor se adapta a você:",
            reply_markup=keyboard
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para botões inline"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'subscribe':
            await self.subscribe(update, context)
        elif query.data.startswith('subscribe_'):
            tier = query.data.split('_')[1]
            
            if self.stripe_integration:
                # Criar checkout session
                checkout_url = self.stripe_integration.create_checkout_session(
                    price_id=f"price_{tier}",
                    customer_email="user@example.com",
                    success_url="https://valuebetting.com/success",
                    cancel_url="https://valuebetting.com/cancel"
                )
                
                await query.edit_message_text(
                    f"💳 Redirecionando para pagamento do plano {tier.upper()}...\n\n"
                    f"Clique no link abaixo para completar a subscrição:\n"
                    f"{checkout_url}"
                )
            else:
                await query.edit_message_text(
                    "❌ Pagamentos não disponíveis no momento.\n"
                    "Contacte support@valuebetting.com"
                )
    
    async def send_signal(self, signal: Signal, subscribers: List[int]):
        """Envia sinal para lista de subscritores"""
        message = self._format_signal(signal)
        
        success_count = 0
        error_count = 0
        
        for telegram_id in subscribers:
            try:
                await self.application.bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode='HTML'
                )
                success_count += 1
            except TelegramError as e:
                logger.error(f"❌ Erro ao enviar sinal para {telegram_id}: {e}")
                error_count += 1
        
        logger.info(f"📤 Sinal enviado: {success_count} sucesso, {error_count} erros")
        
        return success_count, error_count
    
    def _format_signal(self, signal: Signal) -> str:
        """Formata sinal para Telegram"""
        return (
            f"🎯 <b>SINAL APROVADO</b> #{signal.signal_id}\n\n"
            f"🏀 {signal.team} vs {signal.opponent}\n"
            f"📊 Mercado: {signal.market} | {signal.selection}\n"
            f"💰 Odd: {signal.odd} (mínima: {signal.odd_min})\n"
            f"📈 Edge: {signal.edge:.2%} | Prob: {signal.prob:.0%}\n"
            f"💵 Stake: €{signal.stake:.2f} ({signal.stake_pct:.1%} da banca)\n"
            f"⏰ Expira em: {signal.expiry_minutes} min\n\n"
            f"⚠️ <b>NÃO APOSTAR</b> se odd < {signal.odd_min}"
        )
    
    async def send_system_notification(self, message: str, admin_chat_id: int):
        """Envia notificação de sistema para admins"""
        try:
            await self.application.bot.send_message(
                chat_id=admin_chat_id,
                text=f"🔔 {message}",
                parse_mode='HTML'
            )
        except TelegramError as e:
            logger.error(f"❌ Erro ao enviar notificação: {e}")
    
    def run(self):
        """Inicia o bot"""
        logger.info("🚀 Iniciando bot...")
        self.application.run_polling()

class SignalDispatcher:
    """Dispatcher de sinais"""
    
    def __init__(self, bot: TelegramBot, db_manager: DatabaseManager):
        self.bot = bot
        self.db_manager = db_manager
        
        logger.info("📡 SignalDispatcher inicializado")
    
    async def dispatch_signal(self, signal: Signal):
        """Envia sinal para todos os subscritores ativos"""
        logger.info(f"📡 Disparando sinal: {signal.signal_id}")
        
        # Buscar subscritores ativos
        subscribers = await self.db_manager.get_active_subscribers()
        telegram_ids = [s.telegram_id for s in subscribers]
        
        # Enviar sinal
        success_count, error_count = await self.bot.send_signal(signal, telegram_ids)
        
        # Registar envio
        await self.db_manager.log_signal_sent(signal, success_count)
        
        return {
            'total': len(subscribers),
            'success': success_count,
            'errors': error_count
        }

# Uso
if __name__ == "__main__":
    # Configuração
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    
    # Criar componentes
    db_manager = DatabaseManager(DATABASE_URL)
    stripe_integration = StripeIntegration(STIPE_SECRET_KEY) if STRIPE_SECRET_KEY else None
    
    # Criar bot
    bot = TelegramBot(TELEGRAM_BOT_TOKEN, db_manager, stripe_integration)
    
    # Criar dispatcher
    dispatcher = SignalDispatcher(bot, db_manager)
    
    # Exemplo de envio de sinal
    async def example_send_signal():
        signal = Signal(
            signal_id="SIG-20261015-001",
            game_id="0022300001",
            team="Boston Celtics",
            opponent="LA Lakers",
            market="moneyline",
            selection="Celtics",
            odd=1.85,
            odd_min=1.83,
            edge=0.073,
            prob=0.58,
            stake=25.0,
            stake_pct=2.5,
            expiry_minutes=5
        )
        
        result = await dispatcher.dispatch_signal(signal)
        print(f"Resultado: {result}")
    
    # Executar bot
    asyncio.run(db_manager.connect())
    bot.run()
```

---

## 11. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[02_Business_Model/INDEX]] → Modelo de negócio e subscrições
- [[09_Execution_System/INDEX]] → Sistema de execução
- [[35_Financial_Tracking/INDEX]] → Tracking de receitas
