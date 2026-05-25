# NBA_API — Integracao com nba_api (Python)

**ID:** `API-001` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar todos os endpoints, rate limits, e boas praticas para extrair dados da NBA via `nba_api`.

---

## 2. INSTALACAO

```bash
pip install nba_api pandas requests
```

---

## 3. ENDPOINTS PRINCIPAIS

### 3.1 Todos os jogos de uma epoca
```python
from nba_api.stats.endpoints import leaguegamefinder

def get_season_games(season='2023-24'):
    response = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        league_id_nullable='00'  # NBA
    )
    df = response.get_data_frames()[0]
    return df
```

### 3.2 Box Score (estatisticas de jogo)
```python
from nba_api.stats.endpoints import boxscoretraditionalv2, boxscoreadvancedv2, boxscorefourfactorsv2

def get_box_scores(game_id):
    traditional = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    advanced = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id)
    fourfactors = boxscorefourfactorsv2.BoxScoreFourFactorsV2(game_id=game_id)
    
    return {
        'traditional': traditional.get_data_frames(),
        'advanced': advanced.get_data_frames(),
        'four_factors': fourfactors.get_data_frames()
    }
```

### 3.3 Calendario
```python
from nba_api.stats.endpoints import scheduleleaguev2

def get_schedule(season='2023-24'):
    response = scheduleleaguev2.ScheduleLeagueV2(season=season)
    return response.get_data_frames()[0]
```

### 3.4 Estatisticas de equipa (season-long)
```python
from nba_api.stats.endpoints import teamdashboardbygeneralsplits

def get_team_season_stats(team_id, season='2023-24'):
    response = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
        team_id=team_id,
        season=season,
        per_mode_detailed='Per100Possessions'
    )
    return response.get_data_frames()[0]
```

### 3.5 Lesoes / Injury Report
```python
from nba_api.stats.endpoints import injuryreport

def get_injury_report():
    response = injuryreport.InjuryReport()
    return response.get_data_frames()[0]
```

---

## 4. RATE LIMITS E BOAS PRATICAS

| Regra | Detalhe |
|-------|---------|
| Delay entre chamadas | Minimo 0.6s (1 chamada/segundo) |
| Retry em falha | 3 tentativas com backoff exponencial (1s, 2s, 4s) |
| Timeout | 30 segundos |
| Cache | Guardar todas as respostas em raw para evitar re-chamadas |
| Erro 429 (Too Many) | Esperar 60s e tentar novamente |

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def safe_api_call(endpoint_class, **kwargs):
    time.sleep(0.6)  # Rate limiting
    response = endpoint_class(**kwargs)
    return response.get_data_frames()[0]
```

---

## 5. MAPEAMENTO COMPLETO DE ENDPOINTS

### 5.1 Endpoints de Jogos e Calendário

| Endpoint | Categoria | Frequência | Uso |
|----------|-----------|------------|-----|
| `leaguegamefinder` | Jogos | Diária | Obter todos os jogos de uma temporada |
| `scheduleleaguev2` | Calendário | Diária | Calendário completo da temporada |
| `scoreboardv2` | Live | A cada 5 min | Scores em tempo real |
| `boxscoretraditionalv2` | Box Score | Pós-jogo | Estatísticas tradicionais |
| `boxscoreadvancedv2` | Box Score | Pós-jogo | Estatísticas avançadas |
| `boxscorefourfactorsv2` | Box Score | Pós-jogo | Four Factors |
| `boxscoremiscv2` | Box Score | Pós-jogo | Miscelâneas |

### 5.2 Endpoints de Estatísticas de Equipa

| Endpoint | Categoria | Frequência | Uso |
|----------|-----------|------------|-----|
| `teamdashboardbygeneralsplits` | Season Stats | Diária | Stats agregadas por temporada |
| `teamdashboardbyopponent` | Matchups | Diária | Stats vs oponentes específicos |
| `teamdashboardbygamesplits` | Situacional | Diária | Home/Away, B2B, etc |
| `teamyearbyyearstats` | Histórico | Uma vez | Histórico multi-temporada |

### 5.3 Endpoints de Estatísticas de Jogador

| Endpoint | Categoria | Frequência | Uso |
|----------|-----------|------------|-----|
| `playerdashboardbygeneralsplits` | Season Stats | Diária | Stats agregadas por jogador |
| `playergamelog` | Game Log | Diária | Histórico de jogos |
| `playercareerstats` | Carreira | Uma vez | Estatísticas de carreira |
| `commonplayerinfo` | Metadata | Uma vez | Info básica do jogador |
| `leaguedashplayerstats` | Líderes | Diária | Top performers |

### 5.4 Endpoints de Contexto e Lesões

| Endpoint | Categoria | Frequência | Uso |
|----------|-----------|------------|-----|
| `injuryreport` | Lesões | A cada hora | Status de lesões |
| `playoffpicture` | Standings | Diária | Classificação |
| `leaguedashteamstats` | Rankings | Diária | Rankings de equipas |
| `teaminfocommon` | Metadata | Uma vez | Info de equipas |

---

## 6. RATE LIMITS DETALHADOS

### 6.1 Limites Oficiais

A NBA API não documenta limites oficiais explícitos, mas na prática:

| Tipo de Limite | Valor | Observação |
|----------------|-------|------------|
| Requests por segundo | ~1 req/s | Recomendado 0.6s delay |
| Requests por minuto | ~60 req/min | Com delay de 0.6s |
| Burst | 10 req/5s | Evitar bursts |
| Timeout | 30s | Timeout padrão |

### 6.2 Estratégia de Rate Limiting

```python
import time
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter para NBA API com token bucket"""
    
    def __init__(self, requests_per_second=1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_call_time = 0
    
    def wait(self):
        """Aguarda tempo necessário para respeitar rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()

rate_limiter = RateLimiter(requests_per_second=1.0)

def rate_limited_api_call(func):
    """Decorator para aplicar rate limiting e retry"""
    @wraps(func)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry_error_callback=lambda x: None
    )
    def wrapper(*args, **kwargs):
        rate_limiter.wait()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
    return wrapper
```

### 6.3 Tratamento de Erros

| Código HTTP | Significado | Ação |
|-------------|-------------|------|
| 200 | Sucesso | Processar resposta |
| 429 | Too Many Requests | Esperar 60s e retry |
| 500 | Internal Server Error | Retry com backoff |
| 503 | Service Unavailable | Retry com backoff |
| Timeout | Request timeout | Retry com backoff |

---

## 7. CASOS DE USO

### 7.1 Ingestão Histórica (Backfill)

**Objetivo:** Carregar dados históricos de múltiplas temporadas

```python
def backfill_seasons(start_season='2018-19', end_season='2023-24'):
    """Backfill de todas as temporadas no intervalo"""
    seasons = generate_season_range(start_season, end_season)
    
    for season in seasons:
        logger.info(f"Processing season {season}")
        
        # 1. Obter calendário
        schedule = get_schedule(season)
        
        # 2. Para cada jogo, obter box scores
        for game_id in schedule['GAME_ID']:
            try:
                box_scores = get_box_scores(game_id)
                save_to_bronze(game_id, box_scores)
            except Exception as e:
                logger.error(f"Failed to process {game_id}: {e}")
                continue
        
        # 3. Aguardar entre temporadas para evitar rate limiting
        time.sleep(60)
```

### 7.2 Atualização Diária (Incremental)

**Objetivo:** Atualizar dados do dia anterior

```python
def daily_update():
    """Atualização diária incremental"""
    yesterday = datetime.now() - timedelta(days=1)
    
    # 1. Obter jogos de ontem
    games = get_games_by_date(yesterday)
    
    # 2. Para cada jogo finalizado, obter box scores
    for game in games:
        if game['status'] == 'Final':
            box_scores = get_box_scores(game['game_id'])
            save_to_bronze(game['game_id'], box_scores)
    
    # 3. Atualizar injury report
    injuries = get_injury_report()
    save_injuries(injuries)
    
    # 4. Atualizar stats de equipa
    for team_id in get_all_teams():
        stats = get_team_season_stats(team_id)
        save_team_stats(team_id, stats)
```

### 7.3 Monitorização em Tempo Real

**Objetivo:** Obter scores de jogos em andamento

```python
def live_scores_monitor():
    """Monitorização de jogos em tempo real"""
    while True:
        scoreboard = get_scoreboard()
        
        for game in scoreboard['gameHeader']:
            if game['gameStatus'] == 2:  # In progress
                logger.info(f"{game['homeTeam']} {game['homeScore']} - "
                           f"{game['awayTeam']} {game['awayScore']}")
        
        time.sleep(300)  # A cada 5 minutos
```

### 7.4 Validação de Dados

**Objetivo:** Validar integridade dos dados recebidos

```python
def validate_game_data(game_data):
    """Valida dados de jogo"""
    required_fields = ['game_id', 'game_date', 'home_team_id', 'away_team_id']
    
    for field in required_fields:
        if field not in game_data or game_data[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # Validar scores
    if game_data.get('status') == 'Final':
        if 'home_score' not in game_data or 'away_score' not in game_data:
            raise ValueError("Final game must have scores")
        
        if game_data['home_score'] == game_data['away_score']:
            raise ValueError("Final game cannot be a tie")
    
    return True
```

---

## 8. CACHE E OTIMIZAÇÃO

### 8.1 Estratégia de Cache

```python
import json
import hashlib
from pathlib import Path

class NBAAPICache:
    """Cache local para respostas da NBA API"""
    
    def __init__(self, cache_dir='./cache/nba_api'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, endpoint_name, params):
        """Gera chave única baseada em endpoint e parâmetros"""
        key_string = f"{endpoint_name}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, endpoint_name, params):
        """Obtém resposta do cache se existir"""
        cache_key = self._get_cache_key(endpoint_name, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def set(self, endpoint_name, params, data):
        """Guarda resposta no cache"""
        cache_key = self._get_cache_key(endpoint_name, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
```

### 8.2 Tabela de Mapeamento API → Schema Interno

| Campo API | Schema Bronze | Schema Silver | Tipo |
|-----------|---------------|---------------|------|
| GAME_ID | game_id | game_id | VARCHAR(20) |
| GAME_DATE | game_date | game_date | DATE |
| TEAM_ID | team_id | team_id | INT |
| PTS | pts | pts | INT |
| FG_PCT | fg_pct | fg_pct | NUMERIC(5,3) |
| EFG_PCT | efg_pct | efg_pct | NUMERIC(5,3) |
| OFF_RATING | off_rating | off_rating | NUMERIC(8,3) |
| DEF_RATING | def_rating | def_rating | NUMERIC(8,3) |

---

## 9. BACKLOG

- [ ] Criar wrapper robusto com retry, cache, e logging
- [ ] Implementar extrator batch para multiplas epocas
- [ ] Documentar mapeamento completo de campos API -> schema interno
- [x] Adicionar casos de uso detalhados
- [x] Detalhar estratégia de rate limiting
- [x] Mapear todos os endpoints disponíveis

---

## 10. LINKS CRUZADOS

- [[14_APIs/INDEX]] ← Secao mae
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Pipeline que consome esta API
- [[15_Database/SCHEMA_POSTGRESQL]] → Schema de destino dos dados
