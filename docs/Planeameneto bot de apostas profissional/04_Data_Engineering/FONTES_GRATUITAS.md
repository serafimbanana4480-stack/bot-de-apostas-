# Fontes de Dados Gratuitas - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Documentação completa de todas as fontes de dados 100% gratuitas disponíveis para o sistema VBQ-UNIFIED, com exemplos de código e instruções de implementação.

---

## 📊 TABELA DE FONTES GRATUITAS

| Fonte | Tipo | Custo | Rate Limit | Uso Principal |
|-------|------|-------|------------|---------------|
| NBA API | Oficial | 0€ | Ilimitado | Dados NBA em tempo real |
| Basketball-Reference | Scraping | 0€ | 1 req/sec | Estatísticas históricas |
| The-Odds-API | API | 0€ (500 req/day) | 500/day | Odds atuais |
| Sportsbookreview | Scraping | 0€ | 1 req/sec | Odds históricas 10 anos |
| GitHub Datasets | Repositório | 0€ | N/A | Dados pré-processados |

---

## 🏀 NBA API (OFICIAL)

### **Descrição**
API oficial da NBA, 100% gratuita e ilimitada. Fornece dados em tempo real de jogos, jogadores, equipas, estatísticas e muito mais.

### **Instalação**
```bash
pip install nba_api
```

### **Script Completo de Coleta**
```python
"""
Script completo de coleta de dados da NBA API
Inclui cache, tratamento de erros e validação
"""

import pandas as pd
import time
from datetime import datetime, timedelta
from nba_api.stats.endpoints import (
    leaguegamefinder,
    playergamelog,
    leaguestandings,
    leaguedashteamstats,
    leagueleaders,
    commonplayerinfo,
    boxscoretraditional
)
from nba_api.stats.static import players, teams
import json
from pathlib import Path

class NBADataCollector:
    """Coletor completo de dados da NBA API"""
    
    def __init__(self, cache_dir="cache/nba_api"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_request = None
        self.min_delay = 0.5  # 500ms entre requests
        
    def _wait_rate_limit(self):
        """Respeitar rate limits"""
        if self.last_request:
            elapsed = time.time() - self.last_request
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        self.last_request = time.time()
    
    def _cache_key(self, endpoint, params):
        """Gerar chave de cache"""
        params_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}_{hash(params_str)}.json"
    
    def _get_cached(self, key):
        """Obter dados do cache"""
        cache_file = self.cache_dir / key
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def _save_cache(self, key, data):
        """Salvar dados no cache"""
        cache_file = self.cache_dir / key
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    
    def get_all_games(self, season="2023-24", use_cache=True):
        """Obter todos os jogos de uma temporada"""
        cache_key = self._cache_key("leaguegamefinder", {"season": season})
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                print(f"✅ Jogos carregados do cache: {len(cached)} jogos")
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season
            )
            games = gamefinder.get_data_frames()[0]
            
            if use_cache:
                self._save_cache(cache_key, games.to_dict('records'))
            
            print(f"✅ Jogos obtidos: {len(games)}")
            return games
        except Exception as e:
            print(f"❌ Erro ao obter jogos: {e}")
            return pd.DataFrame()
    
    def get_player_stats(self, player_id, season="2023-24", use_cache=True):
        """Obter stats de um jogador"""
        cache_key = self._cache_key("playergamelog", {"player_id": player_id, "season": season})
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season
            )
            stats = gamelog.get_data_frames()[0]
            
            if use_cache:
                self._save_cache(cache_key, stats.to_dict('records'))
            
            return stats
        except Exception as e:
            print(f"❌ Erro ao obter stats do jogador: {e}")
            return pd.DataFrame()
    
    def get_team_stats(self, season="2023-24", use_cache=True):
        """Obter stats de equipas"""
        cache_key = self._cache_key("leaguedashteamstats", {"season": season})
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            team_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season
            )
            stats = team_stats.get_data_frames()[0]
            
            if use_cache:
                self._save_cache(cache_key, stats.to_dict('records'))
            
            print(f"✅ Stats equipas obtidas: {len(stats)} equipas")
            return stats
        except Exception as e:
            print(f"❌ Erro ao obter stats equipas: {e}")
            return pd.DataFrame()
    
    def get_standings(self, season="2023-24", use_cache=True):
        """Obter classificação"""
        cache_key = self._cache_key("leaguestandings", {"season": season})
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return pd.DataFrame(cached)
        
        self._wait_rate_limit()
        
        try:
            standings = leaguestandings.LeagueStandings(
                season=season
            )
            data = standings.get_data_frames()[0]
            
            if use_cache:
                self._save_cache(cache_key, data.to_dict('records'))
            
            print(f"✅ Classificação obtida: {len(data)} equipas")
            return data
        except Exception as e:
            print(f"❌ Erro ao obter classificação: {e}")
            return pd.DataFrame()
    
    def get_all_players(self, use_cache=True):
        """Obter lista de jogadores"""
        cache_key = "all_players.json"
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            player_list = players.get_players()
            
            if use_cache:
                self._save_cache(cache_key, player_list)
            
            print(f"✅ Jogadores obtidos: {len(player_list)}")
            return player_list
        except Exception as e:
            print(f"❌ Erro ao obter jogadores: {e}")
            return []
    
    def get_all_teams(self, use_cache=True):
        """Obter lista de equipas"""
        cache_key = "all_teams.json"
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            team_list = teams.get_teams()
            
            if use_cache:
                self._save_cache(cache_key, team_list)
            
            print(f"✅ Equipas obtidas: {len(team_list)}")
            return team_list
        except Exception as e:
            print(f"❌ Erro ao obter equipas: {e}")
            return []
    
    def collect_season_data(self, season="2023-24"):
        """Coletar todos os dados de uma temporada"""
        print(f"\n🏀 Coletando dados da temporada {season}...")
        print("="*60)
        
        # Jogos
        games = self.get_all_games(season)
        
        # Stats equipas
        team_stats = self.get_team_stats(season)
        
        # Classificação
        standings = self.get_standings(season)
        
        # Jogadores
        all_players = self.get_all_players()
        
        # Equipas
        all_teams = self.get_all_teams()
        
        # Criar dataframe consolidado
        data = {
            'games': games,
            'team_stats': team_stats,
            'standings': standings,
            'players': all_players,
            'teams': all_teams
        }
        
        print("="*60)
        print("✅ Coleta completa!")
        
        return data

# Uso
if __name__ == "__main__":
    collector = NBADataCollector()
    season_data = collector.collect_season_data("2023-24")
    
    # Guardar dados
    output_dir = Path("data/nba")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for key, df in season_data.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.to_csv(output_dir / f"{key}.csv", index=False)
            print(f"💾 {key}.csv salvo")
        elif isinstance(df, list) and df:
            pd.DataFrame(df).to_csv(output_dir / f"{key}.csv", index=False)
            print(f"💾 {key}.csv salvo")
```

### **Exemplos de Uso Simplificados**

#### **Dados de Jogos**
```python
from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd

# Obter todos os jogos
gamefinder = leaguegamefinder.LeagueGameFinder()
games = gamefinder.get_data_frames()[0]

print(f"Total jogos: {len(games)}")
print(games.head())
```

#### **Estatísticas de Jogadores**
```python
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players

# Obter lista de jogadores
player_list = players.get_players()
lebron = [p for p in player_list if p['full_name'] == 'LeBron James'][0]

# Obter stats de jogos
gamelog = playergamelog.PlayerGameLog(player_id=lebron['id'])
df = gamelog.get_data_frames()[0]
print(df.head())
```

#### **Dados de Equipas**
```python
from nba_api.stats.static import teams

# Obter todas as equipas
team_list = teams.get_teams()
print(f"Total equipas: {len(team_list)}")

# Encontrar equipa específica
lakers = [t for t in team_list if t['full_name'] == 'Los Angeles Lakers'][0]
print(f"Lakers ID: {lakers['id']}")
```

### **Endpoints Úteis**
```python
from nba_api.stats.endpoints import (
    leaguestandings,      # Classificação
    leaguedashteamstats,  # Stats equipas
    leagueleaders,        # Líderes em stats
    commonplayerinfo,     # Info jogadores
    boxscoretraditional   # Box score
)
```

### **Limitações**
- Nenhuma significativa
- Pode ter rate limits em casos extremos
- Dados atualizados em tempo real

---

## 📊 BASKETBALL-REFERENCE (SCRAPING)

### **Descrição**
Scraping de Basketball-Reference.com, site com estatísticas históricas completas da NBA.

### **Instalação**
```bash
pip install basketball-reference-web-scraper
```

### **Exemplos de Uso**

#### **Estatísticas de Equipas**
```python
import basketball_reference_web_scraper as br

# Obter stats de equipas (temporada regular)
team_stats = br.team_season_stats(season_end_year=2023)
print(team_stats.head())

# Obter stats por jogo
per_game = br.team_season_stats(season_end_year=2023, per_game=True)
print(per_game.head())
```

#### **Estatísticas de Jogadores**
```python
# Obter stats de jogadores
player_stats = br.players_season_stats(season_end_year=2023)
print(player_stats.head())

# Stats avançadas
advanced = br.players_advanced_stats(season_end_year=2023)
print(advanced.head())
```

#### **Dados de Jogos**
```python
# Obter jogos de uma equipa
games = br.team_schedule(team_abbreviation="LAL", season_end_year=2023)
print(games.head())

# Box scores
boxscores = br.box_scores(season_end_year=2023)
print(boxscores.head())
```

### **Rate Limiting**
```python
import time

# Adicionar delays entre requests
for year in range(2020, 2024):
    stats = br.team_season_stats(season_end_year=year)
    time.sleep(1)  # 1 segundo delay
```

---

## 🎲 THE-ODDS-API (GRATUITO)

### **Descrição**
API de odds com tier gratuito de 500 requests por dia. Cobertura de múltiplos bookmakers.

### **Registo**
```bash
# 1. Ir para https://the-odds-api.com/
# 2. Criar conta gratuita
# 3. Obter API key
# 4. Adicionar ao .env:
THE_ODDS_API_KEY=your_api_key_here
```

### **Instalação**
```bash
pip install requests
```

### **Script Completo com Rate Limiting**
```python
"""
Script completo para The-Odds-API
Inclui rate limiting inteligente, cache e tratamento de erros
"""

import requests
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import os

class OddsAPIRateLimiter:
    """Rate limiter inteligente para The-Odds-API"""
    
    def __init__(self, max_requests_per_day=500):
        self.max_requests = max_requests_per_day
        self.requests_log = []
        self.cache_dir = Path("cache/odds_api")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _clean_old_requests(self):
        """Remove requests antigos (mais de 24h)"""
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        self.requests_log = [r for r in self.requests_log if r > day_ago]
    
    def _get_remaining_requests(self):
        """Retorna número de requests restantes hoje"""
        self._clean_old_requests()
        return self.max_requests - len(self.requests_log)
    
    def wait_if_needed(self):
        """Aguarda se necessário para respeitar rate limit"""
        self._clean_old_requests()
        
        if len(self.requests_log) >= self.max_requests:
            # Calcular tempo até reset
            oldest_request = min(self.requests_log)
            reset_time = oldest_request + timedelta(days=1)
            now = datetime.now()
            wait_seconds = (reset_time - now).total_seconds()
            
            if wait_seconds > 0:
                print(f"⏳ Rate limit atingido. Aguardando {wait_seconds/60:.0f} minutos...")
                time.sleep(wait_seconds)
        
        # Registar request
        self.requests_log.append(datetime.now())

class OddsAPIClient:
    """Cliente completo para The-Odds-API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY não encontrada no .env")
        
        self.base_url = "https://api.the-odds-api.com/v4"
        self.limiter = OddsAPIRateLimiter()
        self.cache_dir = Path("cache/odds_api")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _cache_key(self, endpoint, params):
        """Gerar chave de cache"""
        params_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}_{hash(params_str)}.json"
    
    def _get_cached(self, key):
        """Obter dados do cache"""
        cache_file = self.cache_dir / key
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def _save_cache(self, key, data):
        """Salvar dados no cache"""
        cache_file = self.cache_dir / key
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    
    def _make_request(self, endpoint, params=None, use_cache=True, cache_hours=1):
        """Fazer request com cache e rate limiting"""
        cache_key = self._cache_key(endpoint, params or {})
        
        # Verificar cache
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                # Verificar se cache ainda é válido
                cache_file = self.cache_dir / cache_key
                cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if cache_age < timedelta(hours=cache_hours):
                    print(f"✅ Dados carregados do cache: {endpoint}")
                    return cached
        
        # Rate limiting
        self.limiter.wait_if_needed()
        
        # Fazer request
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Salvar no cache
                if use_cache:
                    self._save_cache(cache_key, data)
                
                print(f"✅ Request bem-sucedido: {endpoint}")
                print(f"📊 Requests restantes hoje: {self.limiter._get_remaining_requests()}")
                return data
            elif response.status_code == 429:
                print(f"❌ Rate limit excedido")
                self.limiter.wait_if_needed()
                return self._make_request(endpoint, params, use_cache, cache_hours)
            else:
                print(f"❌ Erro: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"❌ Timeout ao acessar {endpoint}")
            return None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def get_nba_odds(self, regions="us", markets="h2h,spreads,totals", odds_format="decimal"):
        """Obter odds NBA atuais"""
        params = {
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        
        data = self._make_request("sports/basketball_nba/odds", params)
        
        if data:
            print(f"🏀 Total jogos com odds: {len(data)}")
        
        return data
    
    def get_sports(self):
        """Obter lista de sports disponíveis"""
        data = self._make_request("sports", use_cache=True, cache_hours=24)
        return data
    
    def get_game_odds(self, game_id, regions="us", markets="h2h,spreads,totals"):
        """Obter odds de um jogo específico"""
        params = {
            "regions": regions,
            "markets": markets
        }
        
        data = self._make_request(f"sports/basketball_nba/odds/{game_id}", params)
        return data
    
    def get_historical_odds(self, date_str, regions="us", markets="h2h"):
        """Obter odds históricas para uma data"""
        params = {
            "regions": regions,
            "markets": markets
        }
        
        data = self._make_request(f"sports/basketball_nba/odds-historical/{date_str}", params)
        return data
    
    def collect_daily_odds(self, use_cache=True):
        """Coletar odds do dia"""
        print("\n🎲 Coletando odds NBA...")
        print("="*60)
        
        # Obter odds atuais
        odds = self.get_nba_odds(use_cache=use_cache)
        
        if odds:
            # Analisar dados
            total_games = len(odds)
            total_bookmakers = set()
            
            for game in odds:
                for bookmaker in game.get('bookmakers', []):
                    total_bookmakers.add(bookmaker['key'])
            
            print(f"📊 Total jogos: {total_games}")
            print(f"📊 Total bookmakers: {len(total_bookmakers)}")
            print(f"📊 Bookmakers: {', '.join(total_bookmakers)}")
        
        print("="*60)
        print("✅ Coleta completa!")
        
        return odds
    
    def save_odds_to_csv(self, odds, filename="nba_odds.csv"):
        """Salvar odds em CSV"""
        if not odds:
            print("❌ Sem dados para salvar")
            return
        
        import pandas as pd
        
        # Flatten data
        flattened = []
        for game in odds:
            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        flattened.append({
                            'game_id': game.get('id'),
                            'game_date': game.get('commence_time'),
                            'home_team': game.get('home_team'),
                            'away_team': game.get('away_team'),
                            'bookmaker': bookmaker.get('key'),
                            'market': market.get('key'),
                            'outcome_name': outcome.get('name'),
                            'price': outcome.get('price'),
                            'point': outcome.get('point', 0)
                        })
        
        df = pd.DataFrame(flattened)
        output_dir = Path("data/odds")
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_dir / filename, index=False)
        print(f"💾 Odds salvas em: {output_dir / filename}")
        
        return df

# Uso
if __name__ == "__main__":
    client = OddsAPIClient()
    
    # Coletar odds do dia
    odds = client.collect_daily_odds(use_cache=True)
    
    # Salvar em CSV
    if odds:
        client.save_odds_to_csv(odds, f"nba_odds_{datetime.now().strftime('%Y%m%d')}.csv")
```

---

## 📈 SPORTSBOOKREVIEW SCRAPER (GITHUB)

### **Descrição**
Scraper de Sportsbookreview.com com 10 anos de dados históricos de odds para NBA, NFL, MLB, NHL.

### **Repositório GitHub**
```
https://github.com/flancast90/sportsbookreview-scraper
```

### **Instalação**
```bash
# Clonar repositório
git clone https://github.com/flancast90/sportsbookreview-scraper.git

# Instalar dependências
cd sportsbookreview-scraper
pip install -r requirements.txt
```

### **Exemplos de Uso**

#### **Obter Odds Históricas**
```python
import pandas as pd
from sportsbookreview_scraper import Scraper

# Inicializar scraper
scraper = Scraper()

# Obter odds NBA
nba_odds = scraper.scrape_nba_odds(
    start_year=2014,
    end_year=2024
)

print(f"Total jogos: {len(nba_odds)}")
print(nba_odds.head())

# Guardar em CSV
nba_odds.to_csv('nba_historical_odds.csv', index=False)
```

#### **Obter Odds por Bookmaker**
```python
# Filtrar por bookmaker específico
pinnacle_odds = nba_odds[nba_odds['bookmaker'] == 'Pinnacle']
print(f"Odds Pinnacle: {len(pinnacle_odds)}")
```

### **Limitações**
- Scraping pode ser lento
- Pode quebrar se site mudar
- Legal grey area (uso pessoal ok)

---

## 🤖 GITHUB DATASETS

### **Repositórios Úteis**

#### **Sports-Betting-ML-Tools-NBA**
```
https://github.com/nealmick/Sports-Betting-ML-Tools-NBA
```
- Dados NBA pré-processados
- Features já computadas
- Scripts de ML

#### **Shin Method**
```
https://github.com/mberk/shin
```
- Método de cálculo de probabilidades
- Implementação Python
- Útil para odds

#### **OddsHarvester**
```
https://github.com/jordantete/OddsHarvester
```
- Coletor de odds múltiplas fontes
- Normalização de odds
- Histórico de odds

### **Como Usar**
```python
# Clonar repositório
git clone https://github.com/nealmick/Sports-Betting-ML-Tools-NBA.git

# Navegar para dados
cd Sports-Betting-ML-Tools-NBA/data

# Carregar dados
import pandas as pd
df = pd.read_csv('nba_data.csv')
print(df.head())
```

---

## 🔧 INTEGRAÇÃO NO SISTEMA

### **Pipeline de Dados**
```python
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder
import basketball_reference_web_scraper as br
import requests
import time

class DataIngestion:
    """Pipeline de ingestão de dados gratuito"""
    
    def __init__(self):
        self.nba_api = None
        self.br_scraper = None
        self.odds_api = None
    
    def get_nba_games(self):
        """Obter jogos da NBA API"""
        gamefinder = leaguegamefinder.LeagueGameFinder()
        games = gamefinder.get_data_frames()[0]
        return games
    
    def get_team_stats(self, year):
        """Obter stats de equipas"""
        stats = br.team_season_stats(season_end_year=year)
        return stats
    
    def get_current_odds(self):
        """Obter odds atuais"""
        # Implementar com The-Odds-API
        pass
    
    def get_historical_odds(self, start_year, end_year):
        """Obter odds históricas"""
        # Implementar com sportsbookreview scraper
        pass
    
    def integrate_all(self):
        """Integrar todas as fontes"""
        games = self.get_nba_games()
        stats = self.get_team_stats(2023)
        
        # Merge datasets
        merged = pd.merge(games, stats, on='TEAM_ID')
        return merged

# Uso
ingestion = DataIngestion()
data = ingestion.integrate_all()
print(data.head())
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **NBA API**
- [ ] nba_api instalado
- [ ] Testar conexão
- [ ] Obter jogos
- [ ] Obter stats jogadores
- [ ] Obter stats equipas

### **Basketball-Reference**
- [ ] basketball-reference-web-scraper instalado
- [ ] Testar scraping
- [ ] Implementar rate limiting
- [ ] Obter dados históricos
- [ ] Validar qualidade

### **The-Odds-API**
- [ ] Conta criada
- [ ] API key obtida
- [ ] Adicionada ao .env
- [ ] Testar requests
- [ ] Implementar rate limiting

### **Sportsbookreview**
- [ ] Repositório clonado
- [ ] Dependências instaladas
- [ ] Testar scraper
- [ ] Obter dados históricos
- [ ] Guardar em database

---

## 🚀 PRÓXIMOS PASSOS

### **Implementação:**
1. **Testar cada fonte** individualmente
2. **Implementar rate limiting** para todas
3. **Criar pipeline integrado**
4. **Validar qualidade de dados**
5. **Implementar cache** para reduzir requests

### **Documentação Adicional:**
- [[04_Data_Engineering/SCRAPING_LOCAL]] - Scripts scraping
- [[04_Data_Engineering/CLV_PROXY]] - Workaround Pinnacle
- [[04_Data_Engineering/RATE_LIMITS]] - Gestão de limits

---

**Status:** Fontes gratuitas documentadas  
**Custo total:** 0€  
**Cobertura:** NBA, odds, stats históricas  

---

#status/active #priority/critical #phase/dados-gratuitos
