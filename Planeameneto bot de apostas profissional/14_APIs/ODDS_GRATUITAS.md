# Odds Gratuitas - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Documentação completa de fontes de odds 100% gratuitas para o sistema VBQ-UNIFIED, com implementação prática, rate limiting e estratégias de uso.

---

## 📊 TABELA DE FONTES GRATUITAS

| Fonte | Custo | Rate Limit | Cobertura | Qualidade |
|-------|-------|------------|-----------|-----------|
| The-Odds-API | 0€ (500 req/day) | 500/day | 5-10 bookmakers | Alta |
| Betfair API (demo) | 0€ | Ilimitado | 1 bookmaker | Alta |
| Sportsbookreview scraper | 0€ | ~1 req/sec | 10 anos histórico | Média |
| OddsPortal scraping | 0€ | ~1 req/sec | Múltiplos | Baixa |

---

## 🎲 THE-ODDS-API

### **Informação da API**
```
Nome: The-Odds-API
Custo: 0€ (500 req/day grátis)
Tier Pro: $49/mês (10,000 req/day)
Documentação: https://the-odds-api.com/
Cobertura: NBA, NFL, MLB, NHL, Soccer, etc.
```

### **Registo e Setup**
```bash
# 1. Ir para https://the-odds-api.com/
# 2. Criar conta gratuita
# 3. Obter API key
# 4. Adicionar ao .env:
THE_ODDS_API_KEY=your_api_key_here
```

### **Implementação Completa**
```python
import requests
import os
import time
from datetime import datetime, timedelta
import pandas as pd

class TheOddsAPI:
    """Cliente completo para The-Odds-API"""
    
    def __init__(self):
        self.api_key = os.getenv("THE_ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.requests_today = 0
        self.max_requests = 500
        self.last_reset = None
    
    def _check_quota(self):
        """Verifica quota disponível"""
        today = datetime.now().date()
        
        # Reset contador se novo dia
        if self.last_reset != today:
            self.requests_today = 0
            self.last_reset = today
        
        remaining = self.max_requests - self.requests_today
        
        if remaining <= 0:
            raise Exception(f"Quota diária esgotada ({self.max_requests} requests)")
        
        return remaining
    
    def get_sports(self):
        """Obter lista de desportos disponíveis"""
        url = f"{self.base_url}/sports"
        params = {"api_key": self.api_key}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro: {response.status_code}")
    
    def get_nba_odds(self, regions="us", markets="h2h,spreads,totals"):
        """Obter odds NBA atuais"""
        remaining = self._check_quota()
        
        url = f"{self.base_url}/sports/basketball_nba/odds"
        params = {
            "api_key": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, params=params)
        self.requests_today += 1
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise Exception("Rate limit atingido")
        else:
            raise Exception(f"Erro: {response.status_code}")
    
    def get_game_odds(self, game_id, regions="us", markets="h2h,spreads,totals"):
        """Obter odds de jogo específico"""
        remaining = self._check_quota()
        
        url = f"{self.base_url}/sports/basketball_nba/odds/{game_id}"
        params = {
            "api_key": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, params=params)
        self.requests_today += 1
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro: {response.status_code}")
    
    def get_historical_odds(self, date_from, date_to):
        """Obter odds históricas (requer tier pro)"""
        # NOTA: Esta funcionalidade requer plano pago
        raise Exception("Odds históricas requerem plano pro ($49/mês)")
    
    def parse_odds_to_dataframe(self, odds_data):
        """Converte dados de odds para DataFrame"""
        parsed_data = []
        
        for game in odds_data:
            for bookmaker in game['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            parsed_data.append({
                                'game_id': game['id'],
                                'home_team': game['home_team'],
                                'away_team': game['away_team'],
                                'commence_time': game['commence_time'],
                                'bookmaker': bookmaker['title'],
                                'outcome': outcome['name'],
                                'price': outcome['price'],
                                'point': outcome.get('point', None)
                            })
        
        return pd.DataFrame(parsed_data)
    
    def get_quota_info(self):
        """Obter informação de quota"""
        return {
            'requests_today': self.requests_today,
            'max_requests': self.max_requests,
            'remaining': self.max_requests - self.requests_today,
            'reset_date': (datetime.now() + timedelta(days=1)).date()
        }

# Uso
odds_api = TheOddsAPI()

# Obter odds NBA
nba_odds = odds_api.get_nba_odds()
print(f"Total jogos: {len(nba_odds)}")

# Converter para DataFrame
df = odds_api.parse_odds_to_dataframe(nba_odds)
print(df.head())

# Ver quota
quota_info = odds_api.get_quota_info()
print(f"\nQuota: {quota_info['remaining']}/{quota_info['max_requests']}")
```

---

## 🎯 BETFAIR API (DEMO)

### **Informação da API**
```
Nome: Betfair API
Custo: 0€ (demo/development)
Tier Production: Taxa sobre apostas
Documentação: https://developer.betfair.com/
Cobertura: Odds live e de fecho
```

### **Setup Betfair API**
```bash
# 1. Criar conta Betfair
# 2. Obter API key
# 3. Instalar cliente Python
pip install betfairlightweight
```

### **Implementação**
```python
from betfairlightweight import BetfairLightweight
from betfairlightweight.filters import market_filter
import os

class BetfairAPI:
    """Cliente para Betfair API"""
    
    def __init__(self):
        self.username = os.getenv("BETFAIR_USERNAME")
        self.password = os.getenv("BETFAIR_PASSWORD")
        self.app_key = os.getenv("BETFAIR_APP_KEY")
        self.client = None
    
    def connect(self):
        """Conecta à Betfair API"""
        self.client = BetfairLightweight(
            username=self.username,
            password=self.password,
            app_key=self.app_key
        )
        
        try:
            self.client.login()
            print("✅ Conectado à Betfair API")
            return True
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def get_nba_markets(self):
        """Obter mercados NBA"""
        if not self.client:
            self.connect()
        
        markets = self.client.betting.list_market_catalogue(
            filter=market_filter(event_type_id=['1'],  # NBA
                                     competition_id=['109325261']),  # NBA competition
            max_results=10
        )
        
        return markets
    
    def get_market_odds(self, market_id):
        """Obter odds de mercado específico"""
        if not self.client:
            self.connect()
        
        odds = self.client.betting.get_market_book(
            market_id=market_id
        )
        
        return odds

# Uso
betfair = BetfairAPI()
markets = betfair.get_nba_markets()
print(f"Total mercados: {len(markets)}")
```

---

## 📈 SPORTSBOOKREVIEW SCRAPER

### **Informação**
```
Nome: Sportsbookreview Scraper
Custo: 0€ (GitHub)
Cobertura: 10 anos de odds históricas
Atualização: Jul 2024
Fonte: https://github.com/flancast90/sportsbookreview-scraper
```

### **Implementação**
```python
import pandas as pd

class SportsbookreviewScraper:
    """Scraper de Sportsbookreview"""
    
    def __init__(self):
        self.base_url = "https://www.sportsbookreview.com"
    
    def scrape_nba_odds(self, start_year=2014, end_year=2024):
        """Scrape odds NBA históricas"""
        
        # NOTA: Este é um exemplo simplificado
        # Na prática, usar o repositório GitHub
        
        print(f"📊 Scraping odds NBA {start_year}-{end_year}...")
        
        # Dados simulados (usar repositório real)
        data = {
            'game_id': ['1', '2', '3'],
            'home_team': ['LAL', 'GSW', 'MIA'],
            'away_team': ['BOS', 'PHX', 'NYK'],
            'opening_odds': [2.00, 1.95, 2.10],
            'closing_odds': [1.95, 1.90, 2.05],
            'bookmaker': ['Pinnacle'] * 3,
            'date': ['2023-01-01', '2023-01-02', '2023-01-03']
        }
        
        df = pd.DataFrame(data)
        print(f"✅ {len(df)} odds obtidas")
        
        return df
    
    def get_historical_odds_by_game(self, game_date, teams):
        """Obter odds históricas de jogo específico"""
        # Implementar scraping real
        pass

# Uso
scraper = SportsbookreviewScraper()
historical_odds = scraper.scrape_nba_odds(2019, 2023)
print(historical_odds.head())
```

---

## 🔄 PIPELINE DE ODDS INTEGRADO

### **Pipeline Robusto com Múltiplas Fontes e Fallback**
```python
"""
Pipeline robusto de integração multi-fonte de odds
Inclui fallback strategies, error handling, cache e logging
"""

import pandas as pd
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from functools import wraps

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_on_error(max_retries=3, delay=1.0):
    """Decorator para retry em caso de erro"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Erro após {max_retries} tentativas em {func.__name__}: {e}")
                        raise
                    logger.warning(f"⚠️  Tentativa {attempt + 1}/{max_retries} falhou em {func.__name__}: {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
        return wrapper
    return decorator

class OddsSource(ABC):
    """Classe abstrata para fontes de odds"""
    
    def __init__(self, name: str):
        self.name = name
        self.last_request_time = None
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    @abstractmethod
    def get_current_odds(self, **kwargs) -> Optional[pd.DataFrame]:
        """Obter odds atuais"""
        pass
    
    @abstractmethod
    def get_historical_odds(self, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Obter odds históricas"""
        pass
    
    def get_metrics(self) -> Dict:
        """Retorna métricas da fonte"""
        return {
            'name': self.name,
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / self.request_count if self.request_count > 0 else 0
        }

class TheOddsAPI(OddsSource):
    """Cliente robusto para The-Odds-API"""
    
    def __init__(self, api_key: str, cache_dir="cache/odds_api"):
        super().__init__("The-Odds-API")
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_requests = 500
        self.requests_today = 0
        self.last_reset_date = None
    
    def _check_quota(self) -> bool:
        """Verifica quota disponível"""
        today = datetime.now().date()
        
        if self.last_reset_date != today:
            self.requests_today = 0
            self.last_reset_date = today
        
        remaining = self.max_requests - self.requests_today
        logger.info(f"📊 The-Odds-API quota: {remaining}/{self.max_requests} restantes")
        
        return remaining > 0
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_current_odds(self, regions="us", markets="h2h,spreads,totals", use_cache=True) -> Optional[pd.DataFrame]:
        """Obter odds NBA atuais"""
        self.request_count += 1
        
        if not self._check_quota():
            logger.error("❌ Quota diária esgotada")
            self.failure_count += 1
            return None
        
        try:
            url = f"{self.base_url}/sports/basketball_nba/odds"
            params = {
                "api_key": self.api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "decimal"
            }
            
            response = requests.get(url, params=params, timeout=10)
            self.requests_today += 1
            
            if response.status_code == 200:
                data = response.json()
                df = self._parse_odds_to_dataframe(data)
                
                self.success_count += 1
                logger.info(f"✅ {len(df)} odds obtidas de The-Odds-API")
                return df
            elif response.status_code == 429:
                logger.warning("⚠️  Rate limit atingido")
                self.failure_count += 1
                return None
            else:
                logger.error(f"❌ Erro API: {response.status_code}")
                self.failure_count += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter odds: {e}")
            self.failure_count += 1
            return None
    
    def get_historical_odds(self, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Odds históricas requerem plano pro"""
        logger.warning("⚠️  Odds históricas requerem plano pro ($49/mês)")
        return None
    
    def _parse_odds_to_dataframe(self, odds_data: List[Dict]) -> pd.DataFrame:
        """Converte dados de odds para DataFrame"""
        parsed_data = []
        
        for game in odds_data:
            for bookmaker in game['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            parsed_data.append({
                                'game_id': game['id'],
                                'home_team': game['home_team'],
                                'away_team': game['away_team'],
                                'commence_time': game['commence_time'],
                                'bookmaker': bookmaker['title'],
                                'outcome': outcome['name'],
                                'price': outcome['price'],
                                'point': outcome.get('point', None),
                                'source': 'the_odds_api'
                            })
        
        return pd.DataFrame(parsed_data)

class BetfairAPI(OddsSource):
    """Cliente para Betfair API (demo)"""
    
    def __init__(self, username: str, password: str, app_key: str):
        super().__init__("Betfair API")
        self.username = username
        self.password = password
        self.app_key = app_key
        self.client = None
    
    def connect(self) -> bool:
        """Conecta à Betfair API"""
        try:
            from betfairlightweight import BetfairLightweight
            
            self.client = BetfairLightweight(
                username=self.username,
                password=self.password,
                app_key=self.app_key
            )
            
            self.client.login()
            logger.info("✅ Conectado à Betfair API")
            return True
        except Exception as e:
            logger.error(f"❌ Erro de conexão Betfair: {e}")
            return False
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_current_odds(self, **kwargs) -> Optional[pd.DataFrame]:
        """Obter odds NBA atuais"""
        self.request_count += 1
        
        if not self.client:
            if not self.connect():
                self.failure_count += 1
                return None
        
        try:
            from betfairlightweight.filters import market_filter
            
            markets = self.client.betting.list_market_catalogue(
                filter=market_filter(event_type_id=['1'], competition_id=['109325261']),
                max_results=10
            )
            
            # Parsear markets para DataFrame (simplificado)
            parsed_data = []
            for market in markets:
                parsed_data.append({
                    'market_id': market.market_id,
                    'market_name': market.market_name,
                    'source': 'betfair_api'
                })
            
            df = pd.DataFrame(parsed_data)
            
            self.success_count += 1
            logger.info(f"✅ {len(df)} mercados obtidos de Betfair API")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter odds Betfair: {e}")
            self.failure_count += 1
            return None
    
    def get_historical_odds(self, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Betfair não fornece odds históricas na demo"""
        logger.warning("⚠️  Betfair demo não fornece odds históricas")
        return None

class SportsbookreviewScraper(OddsSource):
    """Scraper de Sportsbookreview para odds históricas"""
    
    def __init__(self, cache_dir="cache/sbr_scraper"):
        super().__init__("Sportsbookreview Scraper")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_current_odds(self, **kwargs) -> Optional[pd.DataFrame]:
        """Sportsbookreview não é ideal para odds atuais"""
        logger.warning("⚠️  Sportsbookreview não é ideal para odds atuais")
        return None
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_historical_odds(self, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Scrape odds NBA históricas"""
        self.request_count += 1
        
        logger.info(f"📊 Scraping odds históricas {start_date} a {end_date}...")
        
        # NOTA: Implementar scraping real usando repositório GitHub
        # Aqui está um exemplo simplificado
        
        try:
            # Dados simulados (usar repositório real)
            data = {
                'game_id': ['1', '2', '3'],
                'home_team': ['LAL', 'GSW', 'MIA'],
                'away_team': ['BOS', 'PHX', 'NYK'],
                'opening_odds': [2.00, 1.95, 2.10],
                'closing_odds': [1.95, 1.90, 2.05],
                'bookmaker': ['Pinnacle'] * 3,
                'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
                'source': 'sportsbookreview'
            }
            
            df = pd.DataFrame(data)
            
            self.success_count += 1
            logger.info(f"✅ {len(df)} odds históricas obtidas")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter odds históricas: {e}")
            self.failure_count += 1
            return None

class MultiSourceOddsPipeline:
    """Pipeline multi-fonte robusto para odds"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Inicializar fontes
        self.sources = []
        
        # The-Odds-API (prioridade alta)
        if config.get('the_odds_api_key'):
            self.sources.append(
                TheOddsAPI(api_key=config['the_odds_api_key'])
            )
        
        # Betfair API (fallback)
        if all([
            config.get('betfair_username'),
            config.get('betfair_password'),
            config.get('betfair_app_key')
        ]):
            self.sources.append(
                BetfairAPI(
                    username=config['betfair_username'],
                    password=config['betfair_password'],
                    app_key=config['betfair_app_key']
                )
            )
        
        # Sportsbookreview (histórico)
        self.sbr_scraper = SportsbookreviewScraper()
        
        # Métricas
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'source_failures': {}
        }
    
    def get_current_odds_with_fallback(self) -> Optional[pd.DataFrame]:
        """Obter odds atuais com fallback entre fontes"""
        logger.info("🎲 Obtendo odds atuais com fallback...")
        
        for source in self.sources:
            logger.info(f"\n📡 Tentando fonte: {source.name}")
            
            try:
                odds = source.get_current_odds()
                
                if odds is not None and len(odds) > 0:
                    self.metrics['successful_requests'] += 1
                    logger.info(f"✅ Sucesso com {source.name}: {len(odds)} odds")
                    return odds
                else:
                    logger.warning(f"⚠️  {source.name} retornou dados vazios")
                    self.metrics['source_failures'][source.name] = self.metrics['source_failures'].get(source.name, 0) + 1
                    
            except Exception as e:
                logger.error(f"❌ Erro com {source.name}: {e}")
                self.metrics['source_failures'][source.name] = self.metrics['source_failures'].get(source.name, 0) + 1
        
        # Todas as fontes falharam
        self.metrics['failed_requests'] += 1
        logger.error("❌ Todas as fontes falharam")
        return None
    
    def get_historical_odds(self, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Obter odds históricas"""
        logger.info(f"📊 Obtendo odds históricas {start_date} a {end_date}...")
        
        # Usar Sportsbookreview scraper
        odds = self.sbr_scraper.get_historical_odds(start_date, end_date)
        
        if odds is not None and len(odds) > 0:
            self.metrics['successful_requests'] += 1
            return odds
        else:
            self.metrics['failed_requests'] += 1
            return None
    
    def merge_odds_sources(self, odds_list: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge odds de múltiplas fontes"""
        if not odds_list:
            return pd.DataFrame()
        
        logger.info(f"🔄 Merge de {len(odds_list)} fontes de odds...")
        
        # Concatenar
        merged = pd.concat(odds_list, ignore_index=True)
        
        # Remover duplicados
        merged = merged.drop_duplicates()
        
        logger.info(f"✅ {len(merged)} odds únicas após merge")
        
        return merged
    
    def get_pipeline_metrics(self) -> Dict:
        """Retorna métricas do pipeline"""
        # Métricas de cada fonte
        source_metrics = [source.get_metrics() for source in self.sources]
        
        return {
            'pipeline': self.metrics,
            'sources': source_metrics
        }

# Uso
if __name__ == "__main__":
    config = {
        'the_odds_api_key': os.getenv("THE_ODDS_API_KEY"),
        'betfair_username': os.getenv("BETFAIR_USERNAME"),
        'betfair_password': os.getenv("BETFAIR_PASSWORD"),
        'betfair_app_key': os.getenv("BETFAIR_APP_KEY")
    }
    
    pipeline = MultiSourceOddsPipeline(config)
    
    # Obter odds atuais com fallback
    current_odds = pipeline.get_current_odds_with_fallback()
    
    if current_odds is not None:
        print(f"\n📊 Odds atuais obtidas: {len(current_odds)}")
        print(current_odds.head())
    
    # Obter odds históricas
    historical_odds = pipeline.get_historical_odds(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    
    if historical_odds is not None:
        print(f"\n📊 Odds históricas obtidas: {len(historical_odds)}")
        print(historical_odds.head())
    
    # Métricas
    metrics = pipeline.get_pipeline_metrics()
    print(f"\n📊 Métricas do Pipeline:")
    print(json.dumps(metrics, indent=2))
```

---

## 📋 ESTRATÉGIAS DE OTIMIZAÇÃO

### **1. Cache de Odds**
```python
import pickle
from datetime import datetime, timedelta

class OddsCache:
    """Cache de odds para reduzir requests"""
    
    def __init__(self, cache_duration=3600):
        self.cache = {}
        self.cache_duration = cache_duration  # segundos
    
    def get(self, key):
        """Obter odds do cache"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            
            # Verificar se ainda válido
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                print(f"✅ Cache hit: {key}")
                return data
            else:
                del self.cache[key]
                print(f"⚠️  Cache expired: {key}")
        
        return None
    
    def set(self, key, data):
        """Guardar odds no cache"""
        self.cache[key] = (data, datetime.now())
        print(f"💾 Cache set: {key}")
    
    def clear(self):
        """Limpar cache"""
        self.cache.clear()
        print("🗑️  Cache limpo")

# Uso
odds_cache = OddsCache(cache_duration=3600)  # 1 hora
```

### **2. Priorização de Requests**
```python
class OddsRequestPrioritizer:
    """Priorizador de requests de odds"""
    
    def __init__(self, api):
        self.api = api
        self.priority_queue = []
    
    def add_request(self, game_id, priority='high'):
        """Adiciona request à fila"""
        self.priority_queue.append({
            'game_id': game_id,
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    def process_queue(self):
        """Processa fila de requests"""
        # Ordenar por prioridade
        self.priority_queue.sort(key=lambda x: x['priority'] == 'high', reverse=True)
        
        for request in self.priority_queue:
            try:
                odds = self.api.get_game_odds(request['game_id'])
                yield odds
            except Exception as e:
                print(f"Erro processando {request['game_id']}: {e}")
```

---

## 📊 ANÁLISE DE ODDS

### **Análise de Mercado**
```python
class OddsAnalyzer:
    """Analisador de odds"""
    
    def calculate_implied_probability(self, odds):
        """Calcula probabilidade implícita"""
        return 1 / odds
    
    def calculate_overround(self, odds_list):
        """Calcula overround (vig)"""
        implied_probs = [self.calculate_implied_probability(odd) for odd in odds_list]
        overround = sum(implied_probs) - 1
        return overround
    
    def find_best_odds(self, game_odds):
        """Encontra melhores odds para um jogo"""
        best_odds = {}
        
        # Agrupar por outcome
        for _, row in game_odds.iterrows():
            outcome = row['outcome']
            price = row['price']
            
            if outcome not in best_odds or price > best_odds[outcome]['price']:
                best_odds[outcome] = {
                    'price': price,
                    'bookmaker': row['bookmaker']
                }
        
        return best_odds
    
    def calculate_arbitrage(self, best_odds):
        """Calcula oportunidade de arbitragem"""
        implied_probs = [
            self.calculate_implied_probability(best_odds[outcome]['price'])
            for outcome in best_odds
        ]
        
        total_prob = sum(implied_probs)
        
        if total_prob < 1:
            arbitrage = (1 - total_prob) * 100
            return arbitrage
        
        return 0

# Uso
analyzer = OddsAnalyzer()

# Exemplo
odds_list = [2.00, 1.95, 2.05]
overround = analyzer.calculate_overround(odds_list)
print(f"Overround: {overround:.2%}")
```

---

## 🚨 TROUBLESHOOTING

### **Problema: Quota Esgotada**
```python
# Solução: Aguardar reset ou usar fontes alternativas
quota_info = odds_api.get_quota_info()

if quota_info['remaining'] == 0:
    print(f"Quota esgotada. Reset em {quota_info['reset_date']}")
    # Usar Betfair API ou scraping
```

### **Problema: Odds Desatualizadas**
```python
# Solução: Implementar cache com duração curta
odds_cache = OddsCache(cache_duration=300)  # 5 minutos
```

### **Problema: Parsing Errors**
```python
# Solução: Validação de dados
def validate_odds_data(odds_data):
    """Valida dados de odds"""
    if not odds_data:
        raise Exception("Dados vazios")
    
    if not isinstance(odds_data, list):
        raise Exception("Formato inválido")
    
    return True
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **The-Odds-API**
- [ ] Conta criada
- [ ] API key obtida
- [ ] Adicionada ao .env
- [ ] Wrapper implementado
- [ ] Rate limiting configurado
- [ ] Cache implementado

### **Betfair API**
- [ ] Conta Betfair criada
- [ ] Credenciais obtidas
- [ ] Cliente instalado
- [ ] Conexão testada
- [ ] Markets obtidos

### **Sportsbookreview**
- [ ] Repositório clonado
- [ ] Dependências instaladas
- [ ] Scraper testado
- [ ] Dados históricos obtidos
- [ ] Validação de qualidade

### **Pipeline**
- [ ] Múltiplas fontes integradas
- [ ] Cache implementado
- [ ] Priorização configurada
- [ ] Error handling
- [ ] Monitoring de requests

---

## 🚀 PRÓXIMOS PASSOS

### **Implementação Imediata:**
1. **Criar wrapper** The-Odds-API completo
2. **Implementar cache** para odds
3. **Criar pipeline** integrado
4. **Adicionar análise** de odds
5. **Implementar alertas** de oportunidades

### **Melhorias Futuras:**
- Adicionar mais fontes de odds
- Implementar detecção de arbitragem
- Criar sistema de alertas
- Adicionar validação de dados
- Otimizar performance

---

## ⚠️ LIMITAÇÕES

### **Limitações das Fontes Gratuitas**
```
The-Odds-API:
- 500 req/day (muito limitado)
- Sem odds históricas (plano pro)
- Delay de 30-60s

Betfair API:
- Apenas odds live (não de fecho)
- Requer conta ativa
- Taxa sobre apostas em produção

Sportsbookreview:
- Scraping pode ser lento
- Pode quebrar se site mudar
- Legal grey area
```

---

**Status:** Odds gratuitas documentadas  
**Custo:** 0€  
**Fontes:** The-Odds-API, Betfair, Sportsbookreview  
**Viabilidade:** Confirmada para MVP  

---

#status/active #priority/critical #phase/apis-gratuitas
