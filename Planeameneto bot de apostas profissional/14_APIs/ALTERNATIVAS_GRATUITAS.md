# Alternativas Gratuitas - APIs Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Documentação completa de alternativas 100% gratuitas para APIs pagas no sistema VBQ-UNIFIED, com comparação de funcionalidades e implementação.

---

## 📊 TABELA DE ALTERNATIVAS

| API Original | Custo | Alternativa Gratuita | Custo | Perda de Funcionalidade |
|---------------|-------|---------------------|-------|------------------------|
| Pinnacle API | 50-100€/mês | CLV Proxy + APIs grátis | 0€ | 15-25% precisão |
| SportsDataIO | 100-1000€/mês | NBA API + scraping | 0€ | Dados avançados |
| OddsJam | 5000€+/mês | The-Odds-API | 0€ (500 req/day) | Cobertura reduzida |
| Betgenius | Enterprise | GitHub datasets | 0€ | Tempo real |
| Sportradar | Enterprise | Scraping manual | 0€ | Cobertura limitada |

---

## 🏀 NBA API GRATUITA

### **Comparação: NBA API Oficial vs SportsDataIO**

| Funcionalidade | NBA API (Gratuito) | SportsDataIO (Pago) | Veredito |
|----------------|---------------------|-------------------|----------|
| Jogos em tempo real | ✅ | ✅ | Empate |
| Estatísticas jogadores | ✅ | ✅ | Empate |
| Estatísticas equipas | ✅ | ✅ | Empate |
| Play-by-play | ✅ | ✅ | Empate |
| Dados históricos | ✅ (com scraping) | ✅ | Empate |
| Advanced metrics | ⚠️ (com scraping) | ✅ | SportsDataIO melhor |
| Fantasy data | ❌ | ✅ | SportsDataIO melhor |
| API calls | Ilimitado | Limitado | NBA API melhor |

### **Implementação NBA API**
```python
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd

class NBAAPIWrapper:
    """Wrapper para NBA API gratuita"""
    
    def get_games(self, season):
        """Obter jogos de uma temporada"""
        gamefinder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season
        )
        games = gamefinder.get_data_frames()[0]
        return games
    
    def get_player_stats(self, player_id):
        """Obter stats de um jogador"""
        gamelog = playergamelog.PlayerGameLog(player_id=player_id)
        stats = gamelog.get_data_frames()[0]
        return stats
    
    def get_all_players(self):
        """Obter lista de todos os jogadores"""
        player_list = players.get_players()
        return player_list

# Uso
nba = NBAAPIWrapper()
games = nba.get_games('2023-24')
print(f"Total jogos: {len(games)}")
```

---

## 🎲 ODDS GRATUITAS

### **Comparação: The-Odds-API vs OddsJam**

| Funcionalidade | The-Odds-API (Gratuito) | OddsJam (Pago) | Veredito |
|----------------|-------------------------|---------------|----------|
| Odds em tempo real | ⚠️ (delay 30-60s) | ✅ (instantâneo) | OddsJam melhor |
| Múltiplos bookmakers | ✅ (5-10) | ✅ (50+) | OddsJam melhor |
| Rate limit | 500 req/day | Ilimitado | OddsJam melhor |
| Arbitrage detection | ❌ | ✅ | OddsJam melhor |
| Positive EV | ❌ | ✅ | OddsJam melhor |
| Custo | 0€ | 5000€+/mês | The-Odds-API melhor custo |

### **Implementação The-Odds-API**
```python
import requests
import os
from datetime import datetime, timedelta

class TheOddsAPIWrapper:
    """Wrapper para The-Odds-API gratuito"""
    
    def __init__(self):
        self.api_key = os.getenv("THE_ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.requests_today = 0
        self.max_requests = 500
    
    def check_quota(self):
        """Verifica quota disponível"""
        today = datetime.now().date()
        
        # Reset contador se novo dia
        if not hasattr(self, 'last_reset_date') or self.last_reset_date != today:
            self.requests_today = 0
            self.last_reset_date = today
        
        remaining = self.max_requests - self.requests_today
        return remaining
    
    def get_nba_odds(self):
        """Obter odds NBA"""
        if self.check_quota() <= 0:
            raise Exception("Quota diária esgotada")
        
        url = f"{self.base_url}/sports/basketball_nba/odds"
        params = {
            "api_key": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, params=params)
        self.requests_today += 1
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro API: {response.status_code}")
    
    def get_game_odds(self, game_id):
        """Obter odds de jogo específico"""
        if self.check_quota() <= 0:
            raise Exception("Quota diária esgotada")
        
        url = f"{self.base_url}/sports/basketball_nba/odds/{game_id}"
        params = {
            "api_key": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals"
        }
        
        response = requests.get(url, params=params)
        self.requests_today += 1
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro API: {response.status_code}")

# Uso
odds_api = TheOddsAPIWrapper()
nba_odds = odds_api.get_nba_odds()
print(f"Total jogos: {len(nba_odds)}")
```

---

## 📊 GITHUB DATASETS GRATUITOS

### **Comparação: GitHub vs Betgenius**

| Funcionalidade | GitHub (Gratuito) | Betgenius (Pago) | Veredito |
|----------------|-------------------|------------------|----------|
| Odds históricas | ✅ (10 anos) | ✅ | Empate |
| Dados em tempo real | ❌ | ✅ | Betgenius melhor |
| APIs de acesso | ❌ (manual) | ✅ | Betgenius melhor |
| Atualização | Manual | Automática | Betgenius melhor |
| Custo | 0€ | Enterprise | GitHub melhor custo |

### **Repositórios Recomendados**

#### **Sportsbookreview Scraper**
```bash
# URL: https://github.com/flancast90/sportsbookreview-scraper
# Dados: 10 anos de odds NBA/NFL/MLB/NHL
# Custo: 0€
# Atualização: Jul 2024

git clone https://github.com/flancast90/sportsbookreview-scraper.git
cd sportsbookreview-scraper
pip install -r requirements.txt
```

#### **Sports-Betting-ML-Tools-NBA**
```bash
# URL: https://github.com/nealmick/Sports-Betting-ML-Tools-NBA
# Dados: NBA com features pré-computadas
# Custo: 0€
# Atualização: Mar 2025

git clone https://github.com/nealmick/Sports-Betting-ML-Tools-NBA.git
```

---

## 🤖 TELEGRAM BOT GRATUITO

### **Comparação: Telegram Bot vs Email Services**

| Funcionalidade | Telegram Bot (Gratuito) | SendGrid (Pago) | Verdicto |
|----------------|------------------------|-----------------|----------|
| Mensagens | Ilimitado | 1000 grátis/mês | Telegram melhor |
| Rich media | ✅ | ⚠️ | Telegram melhor |
| Interactive | ✅ | ❌ | Telegram melhor |
| Groups/Bots | ✅ | ❌ | Telegram melhor |
| Rate limit | Generoso | Limitado | Telegram melhor |
| Custo | 0€ | $10+/mês | Telegram melhor |

### **Implementação Telegram Bot**
```python
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging

class TelegramBot:
    """Bot Telegram para VBQ-UNIFIED"""
    
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        
        # Handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("signals", self.signals))
        self.dispatcher.add_handler(CommandHandler("performance", self.performance))
    
    def start(self, update: Update, context: CallbackContext):
        """Comando /start"""
        update.message.reply_text(
            "🏀 VBQ-UNIFIED Bot\n\n"
            "Comandos disponíveis:\n"
            "/signals - Últimos sinais\n"
            "/performance - Métricas de performance\n"
            "/help - Ajuda"
        )
    
    def signals(self, update: Update, context: CallbackContext):
        """Comando /signals"""
        # Obter últimos sinais do sistema
        signals = self.get_latest_signals()
        
        message = "📊 Últimos Sinais:\n\n"
        for signal in signals[:5]:
            message += f"🎯 {signal['game']}\n"
            message += f"   Odds: {signal['odds']}\n"
            message += f"   Edge: {signal['edge']:.2%}\n\n"
        
        update.message.reply_text(message)
    
    def performance(self, update: Update, context: CallbackContext):
        """Comando /performance"""
        # Obter métricas de performance
        metrics = self.get_performance_metrics()
        
        message = "📈 Performance:\n\n"
        message += f"ROI: {metrics['roi']:.2%}\n"
        message += f"Win Rate: {metrics['win_rate']:.2%}\n"
        message += f"Total Apostas: {metrics['total_bets']}\n"
        
        update.message.reply_text(message)
    
    def run(self):
        """Inicia o bot"""
        self.updater.start_polling()
    
    def get_latest_signals(self):
        """Obter últimos sinais (implementação placeholder)"""
        return [
            {'game': 'LAL vs BOS', 'odds': 2.10, 'edge': 0.05},
            {'game': 'GSW vs MIA', 'odds': 1.95, 'edge': 0.08},
        ]
    
    def get_performance_metrics(self):
        """Obter métricas de performance (implementação placeholder)"""
        return {
            'roi': 0.15,
            'win_rate': 0.55,
            'total_bets': 150
        }

# Uso
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = TelegramBot(TOKEN)
bot.run()
```

---

## 📧 EMAIL GRATUITO

### **Comparação: Gmail SMTP vs SendGrid**

| Funcionalidade | Gmail SMTP (Gratuito) | SendGrid (Pago) | Veredito |
|----------------|----------------------|-----------------|----------|
| Emails/dia | 500 (limite) | 100 grátis/mês | Gmail melhor |
| Rate limit | Limitado | Limitado | Empate |
| Templates | ❌ | ✅ | SendGrid melhor |
| Analytics | ❌ | ✅ | SendGrid melhor |
| Custo | 0€ | $10+/mês | Gmail melhor custo |

### **Implementação Gmail SMTP**
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailNotifier:
    """Notificador de email usando Gmail SMTP"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("GMAIL_EMAIL")
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")
    
    def send_email(self, to_email, subject, body):
        """Envia email via Gmail SMTP"""
        
        # Criar mensagem
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = to_email
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "plain"))
        
        try:
            # Conectar ao servidor SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login
            server.login(self.sender_email, self.sender_password)
            
            # Enviar email
            server.send_message(message)
            
            # Fechar conexão
            server.quit()
            
            print("✅ Email enviado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro enviando email: {e}")
            return False

# Uso
notifier = EmailNotifier()
notifier.send_email(
    "user@example.com",
    "Novo Sinal VBQ-UNIFIED",
    "Foi gerado um novo sinal para o jogo LAL vs BOS..."
)
```

---

## 🔄 INTEGRAÇÃO DE ALTERNATIVAS

### **Pipeline Robusto com APIs Gratuitas e Fallback**
```python
"""
Pipeline robusto de integração de APIs gratuitas
Inclui fallback strategies, error handling, caching e logging
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIClient(ABC):
    """Classe abstrata para clientes de API"""
    
    def __init__(self, name: str):
        self.name = name
        self.last_request_time = None
        self.request_count = 0
    
    @abstractmethod
    def fetch_data(self, *args, **kwargs) -> Optional[Dict]:
        """Método abstrato para obter dados"""
        pass
    
    def _rate_limit_delay(self, min_delay: float = 1.0):
        """Aplica delay para respeitar rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1

class NBAAPIWrapper(APIClient):
    """Wrapper robusto para NBA API gratuita"""
    
    def __init__(self, cache_dir="cache/nba_api"):
        super().__init__("NBA API")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, season: str) -> str:
        """Gera chave de cache"""
        return f"nba_games_{season.replace('-', '_')}.json"
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Carrega dados do cache"""
        cache_file = self.cache_dir / cache_key
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"✅ NBA API dados carregados do cache: {cache_key}")
                return data
            except Exception as e:
                logger.error(f"Erro ao ler cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Salva dados no cache"""
        cache_file = self.cache_dir / cache_key
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"💾 NBA API dados salvados no cache: {cache_key}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def fetch_data(self, season: str, use_cache: bool = True) -> Optional[Dict]:
        """Obter jogos de uma temporada com cache"""
        cache_key = self._get_cache_key(season)
        
        # Tentar cache primeiro
        if use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Aplicar rate limit
        self._rate_limit_delay(min_delay=0.5)
        
        try:
            from nba_api.stats.endpoints import leaguegamefinder
            
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season
            )
            games_df = gamefinder.get_data_frames()[0]
            
            # Converter para dict
            data = {
                'season': season,
                'games': games_df.to_dict('records'),
                'count': len(games_df),
                'fetched_at': datetime.now().isoformat()
            }
            
            # Salvar no cache
            self._save_to_cache(cache_key, data)
            
            logger.info(f"✅ NBA API: {len(games_df)} jogos obtidos para temporada {season}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados NBA API: {e}")
            return None
    
    def get_player_stats(self, player_id: str, use_cache: bool = True) -> Optional[Dict]:
        """Obter stats de um jogador"""
        cache_key = f"nba_player_{player_id}.json"
        
        # Tentar cache
        if use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Aplicar rate limit
        self._rate_limit_delay(min_delay=0.5)
        
        try:
            from nba_api.stats.endpoints import playergamelog
            
            gamelog = playergamelog.PlayerGameLog(player_id=player_id)
            stats_df = gamelog.get_data_frames()[0]
            
            data = {
                'player_id': player_id,
                'stats': stats_df.to_dict('records'),
                'count': len(stats_df),
                'fetched_at': datetime.now().isoformat()
            }
            
            self._save_to_cache(cache_key, data)
            
            logger.info(f"✅ NBA API: {len(stats_df)} jogos obtidos para jogador {player_id}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter stats jogador {player_id}: {e}")
            return None

class TheOddsAPIWrapper(APIClient):
    """Wrapper robusto para The-Odds-API gratuito"""
    
    def __init__(self, api_key: str, cache_dir="cache/odds_api"):
        super().__init__("The-Odds-API")
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_requests = 500
        self.requests_today = 0
    
    def _check_quota(self) -> bool:
        """Verifica quota disponível"""
        today = datetime.now().date()
        
        # Reset contador se novo dia
        if not hasattr(self, 'last_reset_date') or self.last_reset_date != today:
            self.requests_today = 0
            self.last_reset_date = today
        
        remaining = self.max_requests - self.requests_today
        logger.info(f"📊 The-Odds-API quota: {remaining}/{self.max_requests} restantes")
        
        return remaining > 0
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Gera chave de cache"""
        params_str = json.dumps(params, sort_keys=True)
        return f"odds_{endpoint}_{hash(params_str)}.json"
    
    def _load_from_cache(self, cache_key: str, max_age_hours: int = 1) -> Optional[Dict]:
        """Carrega dados do cache se válido"""
        cache_file = self.cache_dir / cache_key
        
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            
            if cache_age < timedelta(hours=max_age_hours):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    logger.info(f"✅ The-Odds-API dados carregados do cache: {cache_key}")
                    return data
                except Exception as e:
                    logger.error(f"Erro ao ler cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Salva dados no cache"""
        cache_file = self.cache_dir / cache_key
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"💾 The-Odds-API dados salvados no cache: {cache_key}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def fetch_data(self, endpoint: str, params: Dict, use_cache: bool = True) -> Optional[Dict]:
        """Faz request com rate limiting e cache"""
        cache_key = self._get_cache_key(endpoint, params)
        
        # Tentar cache primeiro
        if use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Verificar quota
        if not self._check_quota():
            logger.error("❌ Quota diária esgotada")
            return None
        
        # Aplicar rate limit
        self._rate_limit_delay(min_delay=2.0)
        
        try:
            url = f"{self.base_url}/{endpoint}"
            params['api_key'] = self.api_key
            
            response = requests.get(url, params=params, timeout=10)
            self.requests_today += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # Salvar no cache
                self._save_to_cache(cache_key, data)
                
                logger.info(f"✅ The-Odds-API: dados obtidos para {endpoint}")
                return data
            elif response.status_code == 429:
                logger.warning(f"⚠️  Rate limit atingido: {response.status_code}")
                return None
            else:
                logger.error(f"❌ Erro API: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro request The-Odds-API: {e}")
            return None

class TelegramBotNotifier:
    """Notificador via Telegram Bot"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Envia mensagem via Telegram"""
        url = f"{self.api_url}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Mensagem enviada via Telegram")
                return True
            else:
                logger.error(f"❌ Erro enviando mensagem: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem Telegram: {e}")
            return False
    
    def send_alert(self, alert_type: str, message: str):
        """Envia alerta formatado"""
        formatted_message = f"🚨 *{alert_type}*\n\n{message}"
        return self.send_message(formatted_message)

class FreeAPIPipeline:
    """Pipeline robusto usando apenas APIs gratuitas"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Inicializar clientes
        self.nba_api = NBAAPIWrapper()
        self.odds_api = TheOddsAPIWrapper(
            api_key=config.get('the_odds_api_key'),
            cache_dir="cache/odds_api"
        )
        
        # Inicializar notificadores
        if config.get('telegram_bot_token') and config.get('telegram_chat_id'):
            self.telegram_notifier = TelegramBotNotifier(
                bot_token=config['telegram_bot_token'],
                chat_id=config['telegram_chat_id']
            )
        else:
            self.telegram_notifier = None
        
        # Métricas
        self.metrics = {
            'successful_fetches': 0,
            'failed_fetches': 0,
            'cache_hits': 0,
            'api_errors': []
        }
    
    def run_daily_pipeline(self, season: str = "2023-24") -> Dict:
        """Executa pipeline diário com error handling"""
        logger.info("="*60)
        logger.info("🚀 Iniciando pipeline diário com APIs gratuitas")
        logger.info("="*60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'season': season,
            'stages': {}
        }
        
        # Stage 1: Obter jogos NBA
        logger.info("\n1️⃣ Stage 1: Obtendo jogos NBA...")
        nba_data = self.nba_api.fetch_data(season, use_cache=True)
        
        if nba_data:
            results['stages']['nba_games'] = {
                'status': 'success',
                'count': nba_data['count']
            }
            self.metrics['successful_fetches'] += 1
        else:
            results['stages']['nba_games'] = {
                'status': 'failed',
                'error': 'Failed to fetch NBA data'
            }
            self.metrics['failed_fetches'] += 1
            self.metrics['api_errors'].append('NBA API')
        
        # Stage 2: Obter odds atuais
        logger.info("\n2️⃣ Stage 2: Obtendo odds atuais...")
        odds_data = self.odds_api.fetch_data(
            endpoint="sports/basketball_nba/odds",
            params={
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "decimal"
            },
            use_cache=True
        )
        
        if odds_data:
            results['stages']['odds'] = {
                'status': 'success',
                'count': len(odds_data)
            }
            self.metrics['successful_fetches'] += 1
        else:
            results['stages']['odds'] = {
                'status': 'failed',
                'error': 'Failed to fetch odds data'
            }
            self.metrics['failed_fetches'] += 1
            self.metrics['api_errors'].append('The-Odds-API')
        
        # Stage 3: Processar dados
        logger.info("\n3️⃣ Stage 3: Processando dados...")
        if nba_data:
            processed_data = self._process_data(nba_data, odds_data)
            results['stages']['processing'] = {
                'status': 'success',
                'count': len(processed_data)
            }
        else:
            processed_data = []
            results['stages']['processing'] = {
                'status': 'skipped',
                'reason': 'No NBA data available'
            }
        
        # Stage 4: Gerar sinais
        logger.info("\n4️⃣ Stage 4: Gerando sinais...")
        signals = self._generate_signals(processed_data)
        results['stages']['signals'] = {
            'status': 'success',
            'count': len(signals)
        }
        
        # Stage 5: Notificar
        logger.info("\n5️⃣ Stage 5: Notificando...")
        if self.telegram_notifier and signals:
            self._send_telegram_notification(signals)
            results['stages']['notification'] = {
                'status': 'success',
                'method': 'telegram'
            }
        else:
            results['stages']['notification'] = {
                'status': 'skipped',
                'reason': 'No telegram config or no signals'
            }
        
        # Adicionar métricas
        results['metrics'] = self.metrics
        
        # Status geral
        all_success = all(
            stage.get('status') == 'success' 
            for stage in results['stages'].values()
            if stage.get('status') != 'skipped'
        )
        results['overall_status'] = 'success' if all_success else 'partial_failure'
        
        logger.info("\n" + "="*60)
        logger.info(f"✅ Pipeline completo: {results['overall_status']}")
        logger.info(f"📊 Métricas: {self.metrics['successful_fetches']} sucesso, {self.metrics['failed_fetches']} falhas")
        logger.info("="*60)
        
        return results
    
    def _process_data(self, nba_data: Dict, odds_data: Optional[Dict]) -> List[Dict]:
        """Processa dados (implementação placeholder)"""
        processed = []
        
        if nba_data and 'games' in nba_data:
            for game in nba_data['games'][:10]:  # Limitar para demo
                processed.append({
                    'game_id': game.get('GAME_ID'),
                    'date': game.get('GAME_DATE'),
                    'home_team': game.get('MATCHUP', '').split(' vs ')[1] if ' vs ' in game.get('MATCHUP', '') else None,
                    'away_team': game.get('MATCHUP', '').split(' vs ')[0] if ' vs ' in game.get('MATCHUP', '') else None
                })
        
        return processed
    
    def _generate_signals(self, data: List[Dict]) -> List[Dict]:
        """Gera sinais (implementação placeholder)"""
        signals = []
        
        for item in data:
            # Simular geração de sinal
            signals.append({
                'game': f"{item.get('away_team', 'Unknown')} vs {item.get('home_team', 'Unknown')}",
                'odds': 2.10,
                'edge': 0.05,
                'confidence': 0.65
            })
        
        return signals
    
    def _send_telegram_notification(self, signals: List[Dict]):
        """Envia notificação via Telegram"""
        message = "📊 *Novos Sinais VBQ-UNIFIED*\n\n"
        
        for signal in signals[:5]:
            message += f"🎯 {signal['game']}\n"
            message += f"   Odds: {signal['odds']:.2f}\n"
            message += f"   Edge: {signal['edge']:.2%}\n"
            message += f"   Confiança: {signal['confidence']:.0%}\n\n"
        
        self.telegram_notifier.send_alert("Novos Sinais", message)
    
    def get_metrics(self) -> Dict:
        """Retorna métricas do pipeline"""
        return self.metrics

# Uso
if __name__ == "__main__":
    config = {
        'the_odds_api_key': os.getenv("THE_ODDS_API_KEY"),
        'telegram_bot_token': os.getenv("TELEGRAM_BOT_TOKEN"),
        'telegram_chat_id': os.getenv("TELEGRAM_CHAT_ID")
    }
    
    pipeline = FreeAPIPipeline(config)
    results = pipeline.run_daily_pipeline(season="2023-24")
    
    print("\n📊 Resultados do Pipeline:")
    print(json.dumps(results, indent=2))
```

---

## 📋 COMPARAÇÃO DE CUSTOS

### **Custo Total por Mês**

| Componente | Original (Pago) | Alternativa (Gratuito) | Economia |
|-----------|------------------|------------------------|----------|
| APIs de dados | 150-1100€/mês | 0€ | 100% |
| Comunicação | 10-50€/mês | 0€ | 100% |
| Monitoring | 20-30€/mês | 0€ | 100% |
| **TOTAL** | **180-1180€/mês** | **0€** | **100%** |

---

## ⚠️ LIMITAÇÕES E TRADE-OFFS

### **Limitações das Alternativas Gratuitas**
```
NBA API:
- ❌ Sem fantasy data oficial
- ⚠️  Advanced metrics requerem scraping

The-Odds-API:
- ❌ Apenas 500 req/day
- ⚠️  Delay de 30-60s
- ❌ Sem arbitrage detection

GitHub Datasets:
- ❌ Sem dados em tempo real
- ⚠️  Atualização manual
- ❌ Sem APIs automatizadas

Telegram Bot:
- ❌ Sem analytics nativo
- ⚠️  Rate limits generosos mas existem
```

### **Quando Considerar APIs Pagas**
```
- Quando receita > 500€/mês
- Quando escala > 50 utilizadores
- Quando precisar de dados em tempo real
- Quando precisar de features avançadas
```

---

## 🚀 MIGRAÇÃO PATH

### **De Gratuito para Pago**
```python
# Fase 1: Gratuito (atual)
- NBA API
- The-Odds-API (500 req/day)
- GitHub datasets

# Fase 2: Híbrido (quando receita justificar)
- NBA API (mantém)
- The-Odds-API Pro ($49/mês)
- GitHub datasets (mantém)

# Fase 3: Completo (quando escala justificar)
- SportsDataIO ($100/mês)
- OddsJam Enterprise ($5000/mês)
- Betgenius (custom pricing)
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **NBA API**
- [ ] nba_api instalado
- [ ] Testar endpoints
- [ ] Implementar wrappers
- [ ] Adicionar rate limiting
- [ ] Cache de resultados

### **The-Odds-API**
- [ ] Conta criada
- [ ] API key obtida
- [ ] Adicionada ao .env
- [ ] Rate limiting implementado
- [ ] Cache de odds

### **Telegram Bot**
- [ ] Bot criado
- [ ] Token obtido
- [ ] Handlers configurados
- [ ] Comandos implementados
- [ ] Testado com utilizadores

### **Email**
- [ ] Gmail configurado
- [ ] App password obtida
- [ ] SMTP testado
- [ ] Templates criados
- [ ] Rate limiting implementado

---

## 🎯 CONCLUSÃO

### **Veredito Final**
```
✅ Alternativas gratuitas são VIÁVEIS para MVP
✅ Cobertura funcional suficiente para learning
✅ Economia de 100% em APIs
⚠️  Limitações aceitáveis para fase inicial
🚀 Path claro para migração para APIs pagas
```

### **Recomendação**
```
Fase 1-3: Usar 100% alternativas gratuitas
Fase 4-6: Avaliar necessidade de upgrade
Fase 7+: Migrar se ROI justificar
```

---

**Status:** Alternativas gratuitas documentadas  
**Custo:** 0€ vs 180-1180€/mês original  
**Viabilidade:** Confirmada para MVP  
**Path de escalabilidade:** Definido  

---

#status/active #priority/critical #phase/apis-gratuitas
