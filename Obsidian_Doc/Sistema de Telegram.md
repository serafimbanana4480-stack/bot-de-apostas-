# 💬 Sistema de Telegram

**Componente:** Distribution System  
**Status:** 🚧 Em desenvolvimento (80%)  
**Responsável:** Backend Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Distribuir sinais de apostas em tempo real para subscritores via Telegram, gerir subscrições, e fornecer uma interface interativa para gestão e monitorização.

---

## 🏗️ Arquitetura

### Componentes do Sistema

| Componente | Status | Prioridade |
|------------|--------|------------|
| **Telegram Bot** | ✅ Implementado | Alta |
| **Subscription Management** | 🚧 Em desenvolvimento | Alta |
| **Signal Distribution** | 🚧 Em desenvolvimento | Alta |
| **User Management** | 🚧 Em desenvolvimento | Alta |
| **Payment Integration** | ❌ Não iniciado | Média |

---

## 🔧 Componentes Técnicos

### 1. Telegram Bot

**Arquivo:** `src/telegram/bot.py`

**Descrição:** Bot principal para interação com utilizadores

**Implementação:**
```python
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler

class TelegramBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update, context):
        """
        Comando /start - Inicia o bot
        """
        welcome_message = """
🏀 Bem-vindo ao VBQ-UNIFIED Bot!

Este bot fornece sinais de value betting para NBA baseados em modelos de ML.

Comandos disponíveis:
/start - Inicia o bot
/help - Mostra ajuda
/subscribe - Subscrever aos sinais
/unsubscribe - Cancelar subscrição
/signals - Ver sinais recentes
/stats - Ver estatísticas
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update, context):
        """
        Comando /help - Mostra ajuda
        """
        help_message = """
📚 Ajuda - VBQ-UNIFIED Bot

Comandos:
/start - Inicia o bot
/help - Mostra esta mensagem
/subscribe - Subscrever aos sinais (premium)
/unsubscribe - Cancelar subscrição
/signals - Ver últimos sinais
/stats - Ver estatísticas de performance

Para suporte, contacte: @support
        """
        await update.message.reply_text(help_message)
    
    async def subscribe_command(self, update, context):
        """
        Comando /subscribe - Inicia processo de subscrição
        """
        user_id = update.effective_user.id
        
        # Check if already subscribed
        if self.is_subscribed(user_id):
            await update.message.reply_text("✅ Já estás subscrito aos sinais!")
            return
        
        # Start subscription process
        await update.message.reply_text(
            "💎 Para subscrever aos sinais premium, escolhe o teu plano:\n\n"
            "🥉 Bronze - 19€/mês\n"
            "🥈 Prata - 49€/mês\n"
            "🥇 Ouro - 99€/mês\n\n"
            "Responde com o plano desejado (bronze/prata/ouro)"
        )
    
    async def signals_command(self, update, context):
        """
        Comando /signals - Mostra sinais recentes
        """
        user_id = update.effective_user.id
        
        # Check subscription
        if not self.is_subscribed(user_id):
            await update.message.reply_text("❌ Precisas de uma subscrição para ver sinais.")
            return
        
        # Get recent signals
        signals = self.get_recent_signals(limit=5)
        
        if not signals:
            await update.message.reply_text("📭 Sem sinais recentes.")
            return
        
        # Format signals
        message = "🎯 Sinais Recentes:\n\n"
        for signal in signals:
            message += f"""
🏀 {signal['teams']}
📊 Edge: {signal['edge']}%
💰 Stake: {signal['stake']}%
🎲 Odds: {signal['odds']}
⏰ {signal['time']}
            """
        
        await update.message.reply_text(message)
    
    async def stats_command(self, update, context):
        """
        Comando /stats - Mostra estatísticas
        """
        user_id = update.effective_user.id
        
        # Check subscription
        if not self.is_subscribed(user_id):
            await update.message.reply_text("❌ Precisas de uma subscrição para ver estatísticas.")
            return
        
        # Get stats
        stats = self.get_user_stats(user_id)
        
        message = f"""
📊 As Tuas Estatísticas:

🎯 Total de Apostas: {stats['total_bets']}
✅ Vitórias: {stats['wins']}
❌ Derrotas: {stats['losses']}
📈 Win Rate: {stats['win_rate']}%
💰 ROI: {stats['roi']}%
💵 Lucro: {stats['profit']}€
        """
        
        await update.message.reply_text(message)
    
    def start(self):
        """
        Inicia o bot
        """
        self.application.run_polling()
```

### 2. Subscription Management

**Arquivo:** `src/telegram/subscriptions.py`

**Descrição:** Gestão de subscrições de utilizadores

**Planos:**
```python
SUBSCRIPTION_PLANS = {
    'bronze': {
        'name': 'Bronze',
        'price': 19,
        'duration': 30,  # dias
        'features': ['daily_signals', 'basic_stats']
    },
    'silver': {
        'name': 'Prata',
        'price': 49,
        'duration': 30,  # dias
        'features': ['daily_signals', 'detailed_stats', 'performance_reports']
    },
    'gold': {
        'name': 'Ouro',
        'price': 99,
        'duration': 30,  # dias
        'features': ['daily_signals', 'detailed_stats', 'performance_reports', 'priority_support', 'custom_alerts']
    }
}
```

**Implementação:**
```python
class SubscriptionManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_subscription(self, user_id, plan):
        """
        Cria uma nova subscrição
        """
        plan_details = SUBSCRIPTION_PLANS[plan]
        
        subscription = {
            'user_id': user_id,
            'plan': plan,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=plan_details['duration']),
            'status': 'active',
            'features': plan_details['features']
        }
        
        self.db.insert('subscriptions', subscription)
        return subscription
    
    def is_subscribed(self, user_id):
        """
        Verifica se o utilizador tem subscrição ativa
        """
        subscription = self.db.get_active_subscription(user_id)
        
        if not subscription:
            return False
        
        # Check if expired
        if subscription['end_date'] < datetime.now():
            self.update_subscription_status(user_id, 'expired')
            return False
        
        return True
    
    def get_subscription(self, user_id):
        """
        Obtém subscrição do utilizador
        """
        return self.db.get_active_subscription(user_id)
    
    def update_subscription_status(self, user_id, status):
        """
        Atualiza status da subscrição
        """
        self.db.update('subscriptions', 
                      {'user_id': user_id}, 
                      {'status': status})
    
    def cancel_subscription(self, user_id):
        """
        Cancela subscrição
        """
        self.update_subscription_status(user_id, 'cancelled')
```

### 3. Signal Distribution

**Arquivo:** `src/telegram/handlers.py`

**Descrição:** Distribuição de sinais para subscritores

**Implementação:**
```python
class SignalDistributor:
    def __init__(self, bot, subscription_manager):
        self.bot = bot
        self.subscription_manager = subscription_manager
    
    async def distribute_signal(self, signal):
        """
        Distribui sinal para todos os subscritores
        """
        # Get all active subscribers
        subscribers = self.subscription_manager.get_all_active_subscribers()
        
        # Format signal message
        message = self.format_signal(signal)
        
        # Send to each subscriber
        for subscriber in subscribers:
            try:
                await self.bot.send_message(
                    chat_id=subscriber['telegram_id'],
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send signal to {subscriber['telegram_id']}: {e}")
    
    def format_signal(self, signal):
        """
        Formata sinal para Telegram
        """
        message = f"""
🎯 *NOVO SINAL DETETADO*

🏀 {signal['home_team']} vs {signal['away_team']}
📊 *Edge:* {signal['edge']}%
💰 *Stake:* {signal['stake']}%
🎲 *Odds:* {signal['odds']}
⏰ *Início:* {signal['game_time']}

📈 *Probabilidade:* {signal['probability']}%
🏠 *Casa:* {signal['bookmaker']}

---
*Análise baseada em modelo ML com rigor estatístico*
        """
        return message
    
    async def distribute_daily_summary(self):
        """
        Distribui resumo diário
        """
        subscribers = self.subscription_manager.get_all_active_subscribers()
        
        # Get daily stats
        stats = self.get_daily_stats()
        
        message = f"""
📊 *RESUMO DIÁRIO*

🎯 Sinais Hoje: {stats['total_signals']}
✅ Vitórias: {stats['wins']}
❌ Derrotas: {stats['losses']}
📈 Win Rate: {stats['win_rate']}%
💰 ROI: {stats['roi']}%
💵 Lucro: {stats['profit']}€

---
*VBQ-UNIFIED - Value Betting Quantitative*
        """
        
        for subscriber in subscribers:
            try:
                await self.bot.send_message(
                    chat_id=subscriber['telegram_id'],
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send summary to {subscriber['telegram_id']}: {e}")
```

### 4. User Management

**Arquivo:** `src/telegram/user_management.py`

**Descrição:** Gestão de utilizadores

**Implementação:**
```python
class UserManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def register_user(self, telegram_id, username):
        """
        Regista novo utilizador
        """
        user = {
            'telegram_id': telegram_id,
            'username': username,
            'registered_at': datetime.now(),
            'status': 'active'
        }
        
        self.db.insert('users', user)
        return user
    
    def get_user(self, telegram_id):
        """
        Obtém utilizador por Telegram ID
        """
        return self.db.get('users', {'telegram_id': telegram_id})
    
    def update_user_stats(self, telegram_id, stats):
        """
        Atualiza estatísticas do utilizador
        """
        self.db.update('users', 
                      {'telegram_id': telegram_id}, 
                      {'stats': stats})
```

---

## 🔄 Pipeline de Distribuição

### Fluxo de Sinais

```python
async def signal_distribution_pipeline(signal):
    """
    Pipeline de distribuição de sinais
    """
    # 1. Validate signal
    if not validate_signal(signal):
        return
    
    # 2. Format signal
    formatted_signal = format_signal(signal)
    
    # 3. Get subscribers
    subscribers = subscription_manager.get_all_active_subscribers()
    
    # 4. Distribute signal
    for subscriber in subscribers:
        try:
            await bot.send_message(
                chat_id=subscriber['telegram_id'],
                text=formatted_signal,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send to {subscriber['telegram_id']}: {e}")
    
    # 5. Log distribution
    log_signal_distribution(signal, len(subscribers))
```

---

## 📊 Monitorização

### Métricas

**Bot Metrics:**
- Utilizadores ativos
- Subscritores ativos
- Taxa de engagement
- Taxa de entrega

**Signal Metrics:**
- Sinais enviados
- Taxa de entrega
- Tempo de entrega
- Taxa de cliques

### Alertas

**Telegram Alerts:**
- Falha no envio de sinal
- Bot offline
- Subscrição expirando
- Pagamento falhado

---

## 🚀 Configuração

### Parâmetros do Bot

```python
TELEGRAM_CONFIG = {
    'token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'webhook_url': os.getenv('TELEGRAM_WEBHOOK_URL'),
    'admin_chat_id': os.getenv('TELEGRAM_ADMIN_CHAT_ID'),
    
    # Rate limiting
    'max_messages_per_minute': 20,
    'max_broadcasts_per_hour': 10,
    
    # Message formatting
    'parse_mode': 'Markdown',
    'disable_web_page_preview': True,
}
```

---

## 📝 Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Completar subscription management
- [ ] Implementar signal distribution
- [ ] Adicionar user management
- [ ] Criar painel de administração

### Médio Prazo (1-2 meses)
- [ ] Implementar payment integration
- [ ] Adicionar analytics dashboard
- [ ] Criar sistema de referrals
- [ ] Implementar multi-language support

### Longo Prazo (3-6 meses)
- [ ] Web app para gestão
- [ ] Sistema de gamification
- [ ] Community features
- [ ] API para terceiros

---

## 🔗 Links Relacionados

- [[Motor de Edge]] - Fonte de sinais
- [[Gestão de Risco]] - Informação de stakes
- [[Modelo de Negócio]] - Planos e pricing
- [[Índice Mestre]] - Documentação completa

---

**Última atualização:** 2026-05-19  
**Responsável:** Backend Engineer  
**Status:** 🚧 Em desenvolvimento