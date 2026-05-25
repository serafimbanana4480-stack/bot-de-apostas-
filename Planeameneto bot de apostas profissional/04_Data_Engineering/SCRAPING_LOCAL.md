# Scraping Local - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Documentação completa de scripts de scraping local para obter dados de fontes gratuitas sem depender de APIs pagas.

---

## 📊 FERRAMENTAS DE SCRAPING

### **Stack Recomendada**
```bash
# Instalar dependências:
pip install requests beautifulsoup4 lxml selenium
pip install basketball-reference-web-scraper
pip install pandas numpy
```

### **Por Que Scraping Local?**
- 100% gratuito
- Controle total dos dados
- Sem rate limits externos
- Dados personalizados
- Backup local

---

## 🏀 BASKETBALL-REFERENCE SCRAPER

### **Instalação**
```bash
pip install basketball-reference-web-scraper
```

### **Script Completo e Robusto de Scraping**
```python
"""
Script completo e robusto de scraping de Basketball-Reference
Inclui retry com exponential backoff, cache, user-agent rotation e logging
"""

import basketball_reference_web_scraper as br
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import random
from typing import Optional, List, Dict
from functools import wraps

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User-Agents para rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

def retry_with_backoff(max_retries=3, base_delay=1):
    """Decorator para retry com exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Falha após {max_retries} tentativas: {e}")
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️  Tentativa {attempt + 1}/{max_retries} falhou. Aguardando {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

class CacheManager:
    """Gestor de cache para scraping"""
    
    def __init__(self, cache_dir="cache/scraping"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _cache_key(self, prefix, params):
        """Gerar chave de cache"""
        params_str = json.dumps(params, sort_keys=True)
        return f"{prefix}_{hash(params_str)}.json"
    
    def get(self, prefix, params):
        """Obter dados do cache"""
        cache_key = self._cache_key(prefix, params)
        cache_file = self.cache_dir / cache_key
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao ler cache: {e}")
        return None
    
    def set(self, prefix, params, data):
        """Salvar dados no cache"""
        cache_key = self._cache_key(prefix, params)
        cache_file = self.cache_dir / cache_key
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def is_valid(self, prefix, params, max_age_hours=24):
        """Verificar se cache ainda é válido"""
        cache_key = self._cache_key(prefix, params)
        cache_file = self.cache_dir / cache_key
        
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            return cache_age < timedelta(hours=max_age_hours)
        
        return False

class BasketballReferenceScraper:
    """Scraper robusto de Basketball-Reference"""
    
    def __init__(self, use_cache=True, cache_max_age_hours=24):
        self.cache = CacheManager() if use_cache else None
        self.cache_max_age_hours = cache_max_age_hours
        self.last_request = None
        self.min_delay = 2  # 2 segundos entre requests
    
    def _wait_rate_limit(self):
        """Respeitar rate limits"""
        if self.last_request:
            elapsed = time.time() - self.last_request
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        self.last_request = time.time()
    
    @retry_with_backoff(max_retries=3, base_delay=2)
    def scrape_team_season_stats(self, year, use_cache=True):
        """Scrape stats de equipas por temporada"""
        cache_params = {'year': year, 'type': 'team_stats'}
        
        # Verificar cache
        if use_cache and self.cache and self.cache.is_valid('br_team_stats', cache_params, self.cache_max_age_hours):
            cached = self.cache.get('br_team_stats', cache_params)
            if cached:
                logger.info(f"✅ Stats equipas {year} carregadas do cache")
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            stats = br.team_season_stats(season_end_year=year)
            logger.info(f"✅ Stats equipas {year}: {len(stats)} registos")
            
            # Salvar no cache
            if use_cache and self.cache:
                self.cache.set('br_team_stats', cache_params, stats.to_dict('records'))
            
            return stats
        except Exception as e:
            logger.error(f"❌ Erro scraping stats {year}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, base_delay=2)
    def scrape_player_season_stats(self, year, use_cache=True):
        """Scrape stats de jogadores por temporada"""
        cache_params = {'year': year, 'type': 'player_stats'}
        
        # Verificar cache
        if use_cache and self.cache and self.cache.is_valid('br_player_stats', cache_params, self.cache_max_age_hours):
            cached = self.cache.get('br_player_stats', cache_params)
            if cached:
                logger.info(f"✅ Stats jogadores {year} carregadas do cache")
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            stats = br.players_season_stats(season_end_year=year)
            logger.info(f"✅ Stats jogadores {year}: {len(stats)} registos")
            
            # Salvar no cache
            if use_cache and self.cache:
                self.cache.set('br_player_stats', cache_params, stats.to_dict('records'))
            
            return stats
        except Exception as e:
            logger.error(f"❌ Erro scraping jogadores {year}: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, base_delay=2)
    def scrape_team_schedule(self, team_abbr, year, use_cache=True):
        """Scrape calendário de equipa"""
        cache_params = {'team': team_abbr, 'year': year, 'type': 'schedule'}
        
        # Verificar cache
        if use_cache and self.cache and self.cache.is_valid('br_schedule', cache_params, self.cache_max_age_hours):
            cached = self.cache.get('br_schedule', cache_params)
            if cached:
                logger.info(f"✅ Calendário {team_abbr} {year} carregado do cache")
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            schedule = br.team_schedule(team_abbreviation=team_abbr, season_end_year=year)
            logger.info(f"✅ Calendário {team_abbr} {year}: {len(schedule)} jogos")
            
            # Salvar no cache
            if use_cache and self.cache:
                self.cache.set('br_schedule', cache_params, schedule.to_dict('records'))
            
            return schedule
        except Exception as e:
            logger.error(f"❌ Erro scraping calendário {team_abbr}: {e}")
            raise
    
    def scrape_all_years(self, start_year, end_year, use_cache=True):
        """Scrape múltiplos anos com delays e cache"""
        logger.info(f"\n🏀 Iniciando scraping de {start_year} a {end_year}...")
        logger.info("="*60)
        
        all_team_stats = []
        all_player_stats = []
        
        for year in range(start_year, end_year + 1):
            logger.info(f"\n📅 Scraping temporada {year}...")
            
            try:
                # Stats equipas
                team_stats = self.scrape_team_season_stats(year, use_cache)
                if team_stats is not None:
                    team_stats['year'] = year
                    all_team_stats.append(team_stats)
                
                # Stats jogadores
                player_stats = self.scrape_player_season_stats(year, use_cache)
                if player_stats is not None:
                    player_stats['year'] = year
                    all_player_stats.append(player_stats)
                
            except Exception as e:
                logger.error(f"❌ Erro scraping ano {year}: {e}")
                continue
        
        # Concatenar todos os anos
        result = {}
        
        if all_team_stats:
            result['team_stats'] = pd.concat(all_team_stats, ignore_index=True)
            logger.info(f"✅ Total stats equipas: {len(result['team_stats'])} registos")
        
        if all_player_stats:
            result['player_stats'] = pd.concat(all_player_stats, ignore_index=True)
            logger.info(f"✅ Total stats jogadores: {len(result['player_stats'])} registos")
        
        logger.info("="*60)
        logger.info("✅ Scraping completo!")
        
        return result
    
    def save_to_csv(self, data, output_dir="data/basketball_reference"):
        """Salvar dados em CSV"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for key, df in data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                filename = output_path / f"{key}.csv"
                df.to_csv(filename, index=False)
                saved_files.append(str(filename))
                logger.info(f"💾 {key} salvo em: {filename}")
        
        return saved_files

# Uso
if __name__ == "__main__":
    scraper = BasketballReferenceScraper(use_cache=True)
    
    # Scrape 5 anos de dados
    data = scraper.scrape_all_years(2019, 2023)
    
    # Guardar em CSV
    if data:
        saved = scraper.save_to_csv(data)
        logger.info(f"\n✅ Dados guardados: {len(saved)} ficheiros")
```

---

## 🎲 THE-ODDS-API SCRAPER

### **Script de Scraping de Odds**
```python
import requests
import pandas as pd
import time
from datetime import datetime
import os

class TheOddsAPIScraper:
    """Scraper de The-Odds-API"""
    
    def __init__(self):
        self.api_key = os.getenv("THE_ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_nba_odds(self):
        """Obter odds NBA atuais"""
        url = f"{self.base_url}/sports/basketball_nba/odds"
        
        params = {
            "api_key": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal"
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Odds obtidas: {len(data)} jogos")
                return data
            else:
                print(f"❌ Erro API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro request: {e}")
            return None
    
    def parse_odds_data(self, odds_data):
        """Parse dados de odds para DataFrame"""
        parsed_data = []
        
        for game in odds_data:
            game_info = {
                'game_id': game['id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'commence_time': game['commence_time'],
                'bookmakers': []
            }
            
            for bookmaker in game['bookmakers']:
                bookmaker_info = {
                    'name': bookmaker['title'],
                    'markets': []
                }
                
                for market in bookmaker['markets']:
                    market_info = {
                        'key': market['key'],
                        'outcomes': []
                    }
                    
                    for outcome in market['outcomes']:
                        outcome_info = {
                            'name': outcome['name'],
                            'price': outcome['price'],
                            'point': outcome.get('point', None)
                        }
                        market_info['outcomes'].append(outcome_info)
                    
                    bookmaker_info['markets'].append(market_info)
                
                game_info['bookmakers'].append(bookmaker_info)
            
            parsed_data.append(game_info)
        
        return pd.DataFrame(parsed_data)
    
    def save_odds_to_csv(self, odds_data, filename='nba_odds.csv'):
        """Guardar odds em CSV"""
        df = self.parse_odds_data(odds_data)
        df.to_csv(filename, index=False)
        print(f"✅ Odds guardadas em {filename}")
        return df

# Uso
scraper = TheOddsAPIScraper()
odds = scraper.get_nba_odds()

if odds:
    df = scraper.save_odds_to_csv(odds)
    print(f"\nTotal jogos: {len(df)}")
    print(df.head())
```

---

## 📈 GITHUB DATASETS SCRAPER

### **Script para Baixar Datasets**
```python
import requests
import pandas as pd
import os

class GitHubDatasetDownloader:
    """Downloader de datasets do GitHub"""
    
    def __init__(self):
        self.datasets = {
            'sportsbookreview': {
                'url': 'https://github.com/flancast90/sportsbookreview-scraper',
                'file': 'nba_odds.csv'
            },
            'nba_ml_tools': {
                'url': 'https://github.com/nealmick/Sports-Betting-ML-Tools-NBA',
                'file': 'nba_data.csv'
            }
        }
    
    def download_raw_file(self, repo_url, file_path):
        """Download de raw file do GitHub"""
        # Converter URL para raw
        raw_url = repo_url.replace('github.com', 'raw.githubusercontent.com')
        raw_url = raw_url.replace('/blob/', '/')
        
        try:
            response = requests.get(raw_url)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"❌ Erro download: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro request: {e}")
            return None
    
    def download_dataset(self, dataset_name):
        """Download dataset específico"""
        dataset = self.datasets[dataset_name]
        
        print(f"📥 Downloading {dataset_name}...")
        
        # Para datasets grandes, clonar repositório é melhor
        import subprocess
        
        # Clonar repositório
        subprocess.run(['git', 'clone', dataset['url']], 
                      capture_output=True)
        
        # Navegar para diretório
        repo_name = dataset['url'].split('/')[-1]
        
        # Copiar ficheiro
        if os.path.exists(f"{repo_name}/{dataset['file']}"):
            df = pd.read_csv(f"{repo_name}/{dataset['file']}")
            df.to_csv(f"{dataset_name}.csv", index=False)
            print(f"✅ {dataset_name} guardado")
            return df
        else:
            print(f"❌ Ficheiro não encontrado")
            return None

# Uso
downloader = GitHubDatasetDownloader()
data = downloader.download_dataset('sportsbookreview')
```

---

## 🤖 SCRAPING PERSONALIZADO

### **Scraper Genérico para Qualquer Site**
```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

class GenericScraper:
    """Scraper genérico para sites de dados"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_page(self, url):
        """Obter página HTML"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Erro obtendo página: {e}")
            return None
    
    def parse_table(self, html, table_selector):
        """Parse tabela de HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.select_one(table_selector)
        
        if not table:
            print("❌ Tabela não encontrada")
            return None
        
        # Extrair headers
        headers = []
        for th in table.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # Extrair dados
        data = []
        for tr in table.find_all('tr')[1:]:  # Skip header row
            row = []
            for td in tr.find_all('td'):
                row.append(td.get_text(strip=True))
            data.append(row)
        
        # Criar DataFrame
        df = pd.DataFrame(data, columns=headers)
        return df
    
    def scrape_multiple_pages(self, url_pattern, start_page, end_page):
        """Scrape múltiplas páginas"""
        all_data = []
        
        for page in range(start_page, end_page + 1):
            url = url_pattern.format(page=page)
            print(f"📄 Scraping página {page}...")
            
            html = self.get_page(url)
            if html:
                df = self.parse_table(html, 'table')
                if df is not None:
                    all_data.append(df)
            
            # Delay
            time.sleep(1)
        
        # Concatenar
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return None

# Exemplo de uso
scraper = GenericScraper("https://example.com")
data = scraper.scrape_multiple_pages(
    "https://example.com/data?page={page}",
    1, 10
)
```

---

## 🔄 PIPELINE DE SCRAPING INTEGRADO

### **Pipeline Completo**
```python
class ScrapingPipeline:
    """Pipeline integrado de scraping"""
    
    def __init__(self):
        self.br_scraper = BasketballReferenceScraper()
        self.odds_scraper = TheOddsAPIScraper()
        self.github_downloader = GitHubDatasetDownloader()
    
    def run_full_pipeline(self):
        """Executa pipeline completo de scraping"""
        
        print("🚀 Iniciando pipeline de scraping...\n")
        
        # 1. Scraping Basketball-Reference
        print("="*50)
        print("1️⃣ Scraping Basketball-Reference")
        print("="*50)
        
        br_data = self.br_scraper.scrape_all_years(2019, 2023)
        
        if br_data is not None:
            br_data.to_csv('data/basketball_reference.csv', index=False)
        
        # 2. Scraping Odds
        print("\n" + "="*50)
        print("2️⃣ Scraping Odds")
        print("="*50)
        
        odds_data = self.odds_scraper.get_nba_odds()
        
        if odds_data:
            odds_df = self.odds_scraper.save_odds_to_csv(odds_data, 
                                                        'data/nba_odds.csv')
        
        # 3. Download Datasets
        print("\n" + "="*50)
        print("3️⃣ Download Datasets")
        print("="*50)
        
        github_data = self.github_downloader.download_dataset('sportsbookreview')
        
        print("\n" + "="*50)
        print("✅ Pipeline completo!")
        print("="*50)
        
        return {
            'basketball_reference': br_data,
            'odds': odds_data,
            'github': github_data
        }

# Uso
pipeline = ScrapingPipeline()
data = pipeline.run_full_pipeline()
```

---

## 📋 VERIFICAÇÃO DE QUALIDADE

### **Script de Validação**
```python
class DataValidator:
    """Validador de qualidade de dados"""
    
    def validate_dataframe(self, df, name):
        """Valida DataFrame"""
        print(f"\n🔍 Validando {name}...")
        
        # Verificar se está vazio
        if df.empty:
            print("❌ DataFrame vazio")
            return False
        
        # Verificar valores nulos
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"⚠️  Valores nulos: {null_counts.sum()}")
            print(null_counts[null_counts > 0])
        else:
            print("✅ Sem valores nulos")
        
        # Verificar duplicados
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            print(f"⚠️  Duplicados: {duplicates}")
        else:
            print("✅ Sem duplicados")
        
        # Estatísticas básicas
        print(f"📊 Registos: {len(df)}")
        print(f"📊 Colunas: {len(df.columns)}")
        
        return True
    
    def validate_all_data(self, data_dict):
        """Valida todos os dados"""
        results = {}
        
        for name, df in data_dict.items():
            if df is not None:
                results[name] = self.validate_dataframe(df, name)
            else:
                print(f"\n❌ {name}: None")
                results[name] = False
        
        return results

# Uso
validator = DataValidator()
results = validator.validate_all_data(data)
```

---

## 🚀 AUTOMAÇÃO

### **Script de Scraping Automatizado**
```python
import schedule
import time

class AutomatedScraping:
    """Scraping automatizado com schedule"""
    
    def __init__(self):
        self.pipeline = ScrapingPipeline()
        self.validator = DataValidator()
    
    def daily_scrape(self):
        """Scraping diário"""
        print(f"\n{'='*50}")
        print(f"📅 Scraping diário: {datetime.now()}")
        print(f"{'='*50}\n")
        
        data = self.pipeline.run_full_pipeline()
        results = self.validator.validate_all_data(data)
        
        print(f"\n✅ Scraping diário completo!")
    
    def run_scheduler(self):
        """Executa scheduler"""
        # Scraping diário às 00:00
        schedule.every().day.at("00:00").do(self.daily_scrape)
        
        # Scraping a cada 6 horas
        schedule.every(6).hours.do(self.daily_scrape)
        
        print("🕐 Scheduler iniciado...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

# Uso
automated = AutomatedScraping()
# automated.run_scheduler()  # Descomentar para executar
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **Scraping Basketball-Reference**
- [ ] basketball-reference-web-scraper instalado
- [ ] Testar scraping individual
- [ ] Implementar delays
- [ ] Guardar em database
- [ ] Validar qualidade

### **Scraping The-Odds-API**
- [ ] API key configurada
- [ ] Testar requests
- [ ] Implementar rate limiting
- [ ] Parse dados corretamente
- [ ] Guardar em database

### **Scraping GitHub**
- [ ] Repositórios identificados
- [ ] Download funcional
- [ ] Dados validados
- [ ] Integrados no pipeline

### **Automação**
- [ ] Scheduler configurado
- [ ] Logging implementado
- [ ] Error handling
- [ ] Backup automático

---

## 🚨 PROBLEMAS COMUNS

### **Bloqueios**
```python
# Solução: User-Agent rotation
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X)',
    'Mozilla/5.0 (X11; Linux x86_64)'
]

# Random user agent
import random
session.headers['User-Agent'] = random.choice(user_agents)
```

### **Rate Limits**
```python
# Solução: Exponential backoff
import time

def get_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                wait = 2 ** attempt
                print(f"Rate limit. Aguardando {wait}s...")
                time.sleep(wait)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(2 ** attempt)
    return None
```

---

**Status:** Scraping local documentado  
**Custo:** 0€  
**Cobertura:** Basketball-Reference, The-Odds-API, GitHub  

---

#status/active #priority/critical #phase/dados-gratuitos
