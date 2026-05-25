# Multi-Source Data Aggregation

**ID:** DATA-001 | **Fase:** #phase/2-6 | **Owner:** Data Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Sistema de agregação de dados de múltiplas fontes (NBA API, ESPN, Basketball-Reference, etc.) com schema unificado, deduplication, quality scoring, e priorização automática. Baseado na implementação do projeto NBA-Betting/NBA_Betting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Agregar dados de múltiplas fontes para maximizar qualidade e cobertura |
| **Fontes** | NBA API, ESPN, Basketball-Reference, Odds Shark, etc. |
| **Schema** | Unificado para todas as fontes |
| **Deduplication** | Automática baseada em IDs e timestamps |
| **Quality Scoring** | Por fonte e por registro |
| **Custo** | 0€ (todas as APIs são públicas) |

---

## 2. FONTES DE DADOS SUPORTADAS

### 2.1 Tabela de Fontes

| Fonte | Tipo | API | Auth | Rate Limit | Qualidade | Prioridade |
|-------|------|-----|------|------------|----------|-----------|
| **NBA API** | Oficial | Sim | API Key | 1000 req/h | Alta | 1 (Primary) |
| **ESPN** | Stats | Sim | Não | 500 req/h | Alta | 2 |
| **Basketball-Reference** | Stats | Scraping | Não | 60 req/min | Alta | 2 |
| **Odds Shark** | Odds | Scraping | Não | 30 req/min | Média | 3 |
| **StatMuse** | Stats | API | Não | 100 req/h | Alta | 3 |
| **Sports Reference** | Stats | Scraping | Não | 60 req/min | Média | 4 |

### 2.2 Priorização de Fontes

**Hierarquia de Prioridade:**
1. **NBA API** — Fonte oficial, mais confiável
2. **ESPN** — Cobertura ampla, dados atualizados
3. **Basketball-Reference** — Histórico completo, dados avançados
4. **Odds Shark** — Odds de múltiplas casas
5. **StatMuse** — Métricas avançadas
6. **Sports Reference** — Backup para Basketball-Reference

---

## 3. SCHEMA UNIFICADO

### 3.1 Schema de Jogos

```python
# vbq/data/schemas/unified.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UnifiedGame(BaseModel):
    """Schema unificado para jogos NBA."""
    
    # Identificação
    game_id: str = Field(..., description="ID único do jogo")
    nba_id: Optional[str] = Field(None, description="ID oficial NBA")
    espn_id: Optional[str] = Field(None, description="ID ESPN")
    bbref_id: Optional[str] = Field(None, description="ID Basketball-Reference")
    
    # Informações do jogo
    game_date: datetime = Field(..., description="Data e hora do jogo")
    home_team: str = Field(..., description="Nome da equipa casa")
    away_team: str = Field(..., description="Nome da equipa visitante")
    venue: Optional[str] = Field(None, description="Arena")
    
    # Resultados
    home_score: Optional[int] = Field(None, description="Pontos casa")
    away_score: Optional[int] = Field(None, description="Pontos visitante")
    winner: Optional[str] = Field(None, description="Vencedor")
    
    # Metadados
    season: str = Field(..., description="Época (ex: 2023-24)")
    season_type: str = Field(..., description="Regular/Playoffs")
    status: str = Field(..., description="Scheduled/In Progress/Final")
    
    # Quality scoring
    data_quality_score: float = Field(default=1.0, description="Score de qualidade (0-1)")
    source_confidence: str = Field(default="high", description="Confiança na fonte")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Proveniência
    sources: list[str] = Field(default_factory=list, description="Fontes que contribuíram")
    primary_source: str = Field(..., description="Fonte primária")
```

### 3.2 Schema de Estatísticas de Equipa

```python
class UnifiedTeamStats(BaseModel):
    """Schema unificado para estatísticas de equipa."""
    
    # Identificação
    team_id: str
    team_name: str
    game_id: str
    season: str
    
    # Estatísticas ofensivas
    points: Optional[float]
    field_goals_made: Optional[int]
    field_goals_attempted: Optional[int]
    three_pointers_made: Optional[int]
    three_pointers_attempted: Optional[int]
    free_throws_made: Optional[int]
    free_throws_attempted: Optional[int]
    
    # Estatísticas defensivas
    rebounds_offensive: Optional[int]
    rebounds_defensive: Optional[int]
    rebounds_total: Optional[int]
    assists: Optional[int]
    steals: Optional[int]
    blocks: Optional[int]
    turnovers: Optional[int]
    fouls: Optional[int]
    
    # Metadados
    data_quality_score: float = Field(default=1.0)
    source_confidence: str = Field(default="high")
    last_updated: datetime = Field(default_factory=datetime.now)
    sources: list[str] = Field(default_factory=list)
    primary_source: str
```

### 3.3 Schema de Lesões

```python
class UnifiedInjury(BaseModel):
    """Schema unificado para lesões."""
    
    # Identificação
    injury_id: str
    player_id: str
    player_name: str
    team_id: str
    team_name: str
    
    # Detalhes da lesão
    injury_type: str
    status: str  # Out/Questionable/Doubtful
    return_date: Optional[datetime]
    
    # Metadados
    reported_date: datetime
    data_quality_score: float = Field(default=1.0)
    source_confidence: str = Field(default="high")
    last_updated: datetime = Field(default_factory=datetime.now)
    sources: list[str] = Field(default_factory=list)
    primary_source: str
```

---

## 4. INGESTION PIPELINE POR FONTE

### 4.1 NBA API

```python
# vbq/data/ingesters/nba_api_ingester.py
from nba_api.stats.endpoints import LeagueGameLog, BoxScoreTraditionalV2
from vbq.data.schemas.unified import UnifiedGame, UnifiedTeamStats

class NBAAPIIngester:
    """Ingestor para NBA API."""
    
    def __init__(self, db: Session):
        self.db = db
        self.quality_score = 1.0  # NBA API é fonte primária
    
    def ingest_games(self, season: str, season_type: str = "Regular Season"):
        """
        Ingesta jogos da NBA API.
        
        Args:
            season: Época (ex: 2023-24)
            season_type: Regular Season ou Playoffs
        """
        games = LeagueGameLog(season=season, season_type_nullable=season_type)
        
        unified_games = []
        for game in games.get_dict()['resultSets'][0]['rowSet']:
            unified = UnifiedGame(
                game_id=self._generate_game_id(game),
                nba_id=game['GAME_ID'],
                game_date=datetime.strptime(game['GAME_DATE'], "%Y-%m-%dT%H:%M:%S"),
                home_team=game['MATCHUP'].split(' vs ')[0],
                away_team=game['MATCHUP'].split(' vs ')[1],
                venue=game.get('ARENA'),
                home_score=int(game['PTS']) if game['PTS'] else None,
                away_score=int(game['PTS']) if game['PTS'] else None,
                winner=game['WL'] if game['WL'] in ['W', 'L'] else None,
                season=season,
                season_type=season_type,
                status=game['WL'] if game['WL'] in ['W', 'L'] else 'Scheduled',
                data_quality_score=self.quality_score,
                source_confidence='high',
                primary_source='nba_api',
                sources=['nba_api']
            )
            unified_games.append(unified)
        
        return unified_games
    
    def ingest_box_scores(self, game_id: str):
        """Ingesta box scores de um jogo específico."""
        box_score = BoxScoreTraditionalV2(game_id=game_id)
        
        unified_stats = []
        for team_stats in box_score.get_dict()['resultSets'][0]['rowSet']:
            unified = UnifiedTeamStats(
                team_id=team_stats['TEAM_ID'],
                team_name=team_stats['TEAM_NAME'],
                game_id=game_id,
                season='2023-24',  # Derivado do jogo
                points=team_stats.get('PTS'),
                field_goals_made=team_stats.get('FGM'),
                field_goals_attempted=team_stats.get('FGA'),
                three_pointers_made=team_stats.get('FG3M'),
                three_pointers_attempted=team_stats.get('FG3A'),
                free_throws_made=team_stats.get('FTM'),
                free_throws_attempted=team_stats.get('FTA'),
                rebounds_offensive=team_stats.get('OREB'),
                rebounds_defensive=team_stats.get('DREB'),
                rebounds_total=team_stats.get('REB'),
                assists=team_stats.get('AST'),
                steals=team_stats.get('STL'),
                blocks=team_stats.get('BLK'),
                turnovers=team_stats.get('TOV'),
                fouls=team_stats.get('PF'),
                data_quality_score=self.quality_score,
                source_confidence='high',
                primary_source='nba_api',
                sources=['nba_api']
            )
            unified_stats.append(unified)
        
        return unified_stats
```

### 4.2 ESPN Ingester

```python
# vbq/data/ingesters/espn_ingester.py
import requests
from bs4 import BeautifulSoup

class ESPNIngester:
    """Ingestor para ESPN."""
    
    def __init__(self, db: Session):
        self.db = db
        self.quality_score = 0.9  # ESPN é fonte secundária
        self.base_url = "https://www.espn.com"
    
    def ingest_games(self, date: datetime):
        """Ingesta jogos do ESPN."""
        url = f"{self.base_url}/nba/scoreboard/_/date/{date.strftime('%Y%m%d')}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse games
        games = []
        for game_element in soup.find_all('section', class_='Scoreboard'):
            # Extrair dados
            game_id = game_element.get('data-game-id')
            teams = game_element.find_all('span', class_='team-name')
            scores = game_element.find_all('span', class_='score')
            
            unified = UnifiedGame(
                game_id=f"espn_{game_id}",
                espn_id=game_id,
                game_date=date,
                home_team=teams[1].text if len(teams) > 1 else teams[0].text,
                away_team=teams[0].text,
                home_score=int(scores[1].text) if len(scores) > 1 else None,
                away_score=int(scores[0].text) if scores else None,
                data_quality_score=self.quality_score,
                source_confidence='high',
                primary_source='espn',
                sources=['espn']
            )
            games.append(unified)
        
        return games
```

### 4.3 Basketball-Reference Ingester

```python
# vbq/data/ingesters/bbref_ingester.py
import requests
import pandas as pd

class BasketballReferenceIngester:
    """Ingestor para Basketball-Reference."""
    
    def __init__(self, db: Session):
        self.db = db
        self.quality_score = 0.9
        self.base_url = "https://www.basketball-reference.com"
    
    def ingest_team_season_stats(self, season: str, team_id: str):
        """
        Ingesta estatísticas de equipa por época.
        
        Args:
            season: Época (ex: 2024)
            team_id: ID da equipa (ex: BOS)
        """
        url = f"{self.base_url}/teams/{team_id}/{season}.html"
        
        # Ler tabela com pandas
        tables = pd.read_html(url)
        team_stats_table = tables[0]  # Primeira tabela é stats da equipa
        
        # Converter para schema unificado
        unified_stats = []
        for _, row in team_stats_table.iterrows():
            unified = UnifiedTeamStats(
                team_id=team_id,
                team_name=row['Team'],
                game_id=f"bbref_{season}_{team_id}",
                season=f"{season}-{int(season)+1}",
                points=row['PTS'],
                field_goals_made=row['FG'],
                field_goals_attempted=row['FGA'],
                three_pointers_made=row['3P'],
                three_pointers_attempted=row['3PA'],
                free_throws_made=row['FT'],
                free_throws_attempted=row['FTA'],
                rebounds_total=row['TRB'],
                assists=row['AST'],
                steals=row['STL'],
                blocks=row['BLK'],
                turnovers=row['TOV'],
                fouls=row['PF'],
                data_quality_score=self.quality_score,
                source_confidence='high',
                primary_source='basketball_reference',
                sources=['basketball_reference']
            )
            unified_stats.append(unified)
        
        return unified_stats
```

---

## 5. DEDUPLICATION E CONFLICT RESOLUTION

### 5.1 Estratégia de Deduplication

```python
# vbq/data/deduplicator.py
from typing import List, Dict
from datetime import datetime, timedelta

class DataDeduplicator:
    """Deduplicator de dados multi-source."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def deduplicate_games(self, games: List[UnifiedGame]) -> List[UnifiedGame]:
        """
        Remove duplicatas e resolve conflitos.
        
        Estratégia:
        1. Agrupar por jogo (home_team, away_team, game_date)
        2. Para cada grupo, selecionar registro de maior qualidade
        3. Se conflito de valores, usar fonte de maior prioridade
        """
        # Agrupar jogos
        game_groups = self._group_games(games)
        
        deduplicated = []
        for group_key, group_games in game_groups.items():
            # Selecionar melhor registro
            best_game = self._select_best_game(group_games)
            deduplicated.append(best_game)
        
        return deduplicated
    
    def _group_games(self, games: List[UnifiedGame]) -> Dict[str, List[UnifiedGame]]:
        """Agrupa jogos por (home_team, away_team, game_date)."""
        groups = {}
        
        for game in games:
            key = f"{game.home_team}_{game.away_team}_{game.game_date.date()}"
            if key not in groups:
                groups[key] = []
            groups[key].append(game)
        
        return groups
    
    def _select_best_game(self, games: List[UnifiedGame]) -> UnifiedGame:
        """
        Seleciona o melhor jogo de um grupo.
        
        Critérios (em ordem):
        1. Maior data_quality_score
        2. Fonte de maior prioridade (nba_api > espn > bbref)
        3. Mais recente (last_updated)
        """
        # Ordenar por critérios
        priority_order = {'nba_api': 1, 'espn': 2, 'basketball_reference': 2}
        
        sorted_games = sorted(
            games,
            key=lambda g: (
                -g.data_quality_score,
                priority_order.get(g.primary_source, 99),
                -g.last_updated.timestamp()
            )
        )
        
        return sorted_games[0]
    
    def resolve_conflicts(self, games: List[UnifiedGame]) -> UnifiedGame:
        """
        Resolve conflitos de valores entre fontes.
        
        Exemplo:
        - Fonte A: home_score = 105
        - Fonte B: home_score = 104
        - Resolução: Usar valor da fonte de maior prioridade
        """
        # Selecionar jogo base
        base_game = self._select_best_game(games)
        
        # Para cada campo, usar valor da fonte de maior prioridade
        for game in games:
            if game.home_score and game.primary_source == 'nba_api':
                base_game.home_score = game.home_score
            if game.away_score and game.primary_source == 'nba_api':
                base_game.away_score = game.away_score
            # ... outros campos
        
        # Atualizar metadados
        base_game.sources = list(set([g.primary_source for g in games]))
        
        return base_game
```

---

## 6. QUALITY SCORING

### 6.1 Algoritmo de Quality Scoring

```python
# vbq/data/quality_scorer.py
class QualityScorer:
    """Calcula score de qualidade para dados."""
    
    def calculate_game_quality(self, game: UnifiedGame) -> float:
        """
        Calcula score de qualidade para um jogo (0-1).
        
        Fatores:
        1. Completude (todos os campos preenchidos): +0.3
        2. Fonte (nba_api = +0.3, espn = +0.2, bbref = +0.2): +0.3
        3. Recência (últimas 24h = +0.2, 24-48h = +0.1): +0.2
        4. Consistência (sem valores nulos): +0.2
        """
        score = 0.0
        
        # 1. Completude
        required_fields = ['game_id', 'game_date', 'home_team', 'away_team']
        completeness = sum(1 for field in required_fields if getattr(game, field, None) is not None)
        score += (completeness / len(required_fields)) * 0.3
        
        # 2. Fonte
        source_scores = {'nba_api': 1.0, 'espn': 0.8, 'basketball_reference': 0.8}
        score += source_scores.get(game.primary_source, 0.5) * 0.3
        
        # 3. Recência
        age_hours = (datetime.now() - game.last_updated).total_seconds() / 3600
        if age_hours < 24:
            score += 0.2
        elif age_hours < 48:
            score += 0.1
        
        # 4. Consistência
        if game.home_score and game.away_score:
            score += 0.2
        
        return min(score, 1.0)
    
    def calculate_stats_quality(self, stats: UnifiedTeamStats) -> float:
        """Calcula score de qualidade para estatísticas."""
        score = 0.0
        
        # Completude de campos importantes
        important_fields = ['points', 'rebounds_total', 'assists']
        completeness = sum(1 for field in important_fields if getattr(stats, field, None) is not None)
        score += (completeness / len(important_fields)) * 0.5
        
        # Fonte
        source_scores = {'nba_api': 1.0, 'espn': 0.8, 'basketball_reference': 0.9}
        score += source_scores.get(stats.primary_source, 0.5) * 0.5
        
        return min(score, 1.0)
```

---

## 7. PRIORIZAÇÃO E FALLBACK

### 7.1 Estratégia de Fallback

```python
# vbq/data/prioritizer.py
class DataPrioritizer:
    """Prioriza fontes e implementa fallback."""
    
    def __init__(self, db: Session):
        self.db = db
        self.priority_order = ['nba_api', 'espn', 'basketball_reference']
    
    def get_game_data(self, game_id: str) -> UnifiedGame:
        """
        Obtém dados de jogo com fallback automático.
        
        Ordem de tentativas:
        1. Cache Redis
        2. PostgreSQL (dados mais recentes)
        3. NBA API
        4. ESPN
        5. Basketball-Reference
        """
        # 1. Tentar cache
        cached = self._get_from_cache(game_id)
        if cached and self._is_fresh(cached):
            return cached
        
        # 2. Tentar PostgreSQL
        db_game = self._get_from_db(game_id)
        if db_game and self._is_fresh(db_game):
            return db_game
        
        # 3-5. Tentar APIs em ordem de prioridade
        for source in self.priority_order:
            try:
                if source == 'nba_api':
                    game = self._fetch_from_nba_api(game_id)
                elif source == 'espn':
                    game = self._fetch_from_espn(game_id)
                elif source == 'basketball_reference':
                    game = self._fetch_from_bbref(game_id)
                
                if game:
                    # Calcular quality score
                    game.data_quality_score = self.quality_scorer.calculate_game_quality(game)
                    # Persistir
                    self._persist_game(game)
                    # Cache
                    self._cache_game(game)
                    return game
            except Exception as e:
                log_warning(f"Falha ao buscar de {source}: {e}")
                continue
        
        raise Exception(f"Impossível obter dados para jogo {game_id}")
```

---

## 8. BACKFILL E HISTÓRICO

### 8.1 Estratégia de Backfill

```python
# vbq/data/backfill.py
class DataBackfiller:
    """Backfill de dados históricos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def backfill_season(self, season: str):
        """
        Faz backfill de uma época completa.
        
        Estratégia:
        1. Obter lista de jogos da época
        2. Para cada jogo, tentar todas as fontes
        3. Usar dados de maior qualidade
        4. Persistir no PostgreSQL
        """
        # Obter lista de jogos (da NBA API ou outra fonte)
        games = self._get_game_list(season)
        
        for game in games:
            try:
                # Tentar obter dados de todas as fontes
                game_data = []
                for source in ['nba_api', 'espn', 'basketball_reference']:
                    try:
                        if source == 'nba_api':
                            data = self._fetch_from_nba_api(game['game_id'])
                        elif source == 'espn':
                            data = self._fetch_from_espn(game['game_id'])
                        elif source == 'basketball_reference':
                            data = self._fetch_from_bbref(game['game_id'])
                        
                        if data:
                            game_data.append(data)
                    except Exception as e:
                        log_error(f"Falha {source} para jogo {game['game_id']}: {e}")
                
                # Selecionar melhor
                if game_data:
                    best_game = self.deduplicator.select_best_game(game_data)
                    self._persist_game(best_game)
                    log_info(f"Backfill jogo {game['game_id']} concluído")
            except Exception as e:
                log_error(f"Falha no backfill do jogo {game['game_id']}: {e}")
    
    def backfill_stats(self, season: str, team_id: str):
        """Backfill de estatísticas de equipa."""
        # Implementação similar para stats
        pass
```

---

## 9. INTEGRAÇÃO COM O SISTEMA

### 9.1 Pipeline de Ingestão Unificado

```python
# vbq/data/pipeline.py
class UnifiedDataPipeline:
    """Pipeline unificado de ingestão multi-source."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ingesters = {
            'nba_api': NBAAPIIngester(db),
            'espn': ESPNIngester(db),
            'basketball_reference': BasketballReferenceIngester(db)
        }
        self.deduplicator = DataDeduplicator(db)
        self.quality_scorer = QualityScorer()
        self.prioritizer = DataPrioritizer(db)
    
    def ingest_daily(self, date: datetime):
        """
        Ingesta dados de todas as fontes para uma data.
        
        Pipeline:
        1. Ingestar de todas as fontes
        2. Deduplicar
        3. Calcular quality scores
        4. Persistir no PostgreSQL
        5. Cache no Redis
        """
        all_games = []
        
        # Ingestar de todas as fontes
        for source, ingester in self.ingesters.items():
            try:
                games = ingester.ingest_games(date)
                all_games.extend(games)
                log_info(f"Ingestados {len(games)} jogos de {source}")
            except Exception as e:
                log_error(f"Falha na ingestão de {source}: {e}")
        
        # Deduplicar
        deduplicated = self.deduplicator.deduplicate_games(all_games)
        log_info(f"Deduplicados: {len(deduplicated)} jogos únicos")
        
        # Calcular quality scores
        for game in deduplicated:
            game.data_quality_score = self.quality_scorer.calculate_game_quality(game)
        
        # Persistir
        self._persist_games(deduplicated)
        
        # Cache
        for game in deduplicated:
            self._cache_game(game)
        
        log_info(f"Ingestão diária concluída: {len(deduplicated)} jogos")
        
        return deduplicated
```

---

## 10. MONITORIZAÇÃO DE QUALIDADE

### 10.1 Métricas de Qualidade

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| data_quality_avg | Score médio de qualidade | > 0.8 |
| data_quality_min | Score mínimo de qualidade | > 0.5 |
| source_availability | Disponibilidade por fonte | > 90% |
| deduplication_rate | Taxa de deduplicação | > 10% |

### 10.2 Dashboard de Qualidade

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA QUALITY DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 QUALIDADE GERAL:
- Score médio: 0.92 ✅
- Score mínimo: 0.78 ✅
- Registros: 1,234

📊 POR FONTE:
- NBA API: 0.95 (456 registros) ✅
- ESPN: 0.89 (312 registros) ✅
- Basketball-Reference: 0.91 (466 registros) ✅

📊 DEDUPLICAÇÃO:
- Duplicadas removidas: 234 (16%)
- Conflitos resolvidos: 45

⚠️ ALERTAS:
- Nenhum

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 11. EXEMPLOS DE CÓDIGO

### 11.1 CLI Integration

```bash
# Comando CLI para ingestão multi-source
vbq-cli data ingest-multi --date 2024-01-15

# Backfill de época
vbq-cli data backfill --season 2023-24

# Ver qualidade dos dados
vbq-cli data quality-report --days 30
```

---

## 12. TROUBLESHOOTING

### 12.1 Dados Inconsistentes

```bash
# Verificar qualidade dos dados
vbq-cli data quality-report --detailed

# Forçar re-ingestão de uma fonte
vbq-cli data ingest --source nba_api --date 2024-01-15 --force

# Verificar conflitos
vbq-cli data conflicts --date 2024-01-15
```

### 12.2 Fonte Down

```bash
# Verificar status das fontes
vbq-cli data sources-status

# Se NBA API está down, usar fallback automático
# (já implementado no DataPrioritizer)
```

---

## 13. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Pipeline ETL NBA
- [[04_Data_Engineering/INGESTAO_ODDS]] → Ingestão de odds
- [[14_APIs/INDEX]] → APIs externas
- [[31_Data_Validation/INDEX]] → Validação de dados

---

**Custo de implementação:** 0€ (todas as APIs são públicas)  
**Tempo estimado de implementação:** 2 semanas  
**Prioridade:** ALTA (fundamental para qualidade de dados)
