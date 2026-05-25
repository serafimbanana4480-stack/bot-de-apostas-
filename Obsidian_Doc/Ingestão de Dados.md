# 📊 Ingestão de Dados

**Componente:** Data Engineering  
**Status:** 🚧 Em desenvolvimento (78%)  
**Responsável:** Data Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Coletar, processar e armazenar dados de jogos NBA e odds de múltiplas casas de apostas, garantindo qualidade, consistência e disponibilidade para os modelos de ML.

---

## 🏗️ Arquitetura

### Fontes de Dados

| Fonte | Tipo | Dados | Rate Limit | Custo |
|-------|------|-------|------------|-------|
| **NBA API** | Oficial | Jogos, estatísticas, jogadores | 1 req/s | Grátis |
| **Betfair API** | Exchange | Odds em tempo real, volume | 5 req/s | Pago |
| **Odds API** | Agregador | Odds de múltiplas casas | 500 req/mês | Grátis (tier free) |
| **Basketball-Reference** | Scraping | Estatísticas históricas | Manual | Grátis |

### Pipeline ETL

```
┌─────────────────┐
│  Data Sources   │
│  (APIs + Web)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ingestion      │
│  Orchestrator   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validation     │
│  + Cleaning     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deduplication  │
│  + Merging      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  (Raw Layer)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Feature Store  │
│  (Processed)    │
└─────────────────┘
```

---

## 🔧 Componentes Técnicos

### 1. NBA API Integration

**Arquivo:** `src/ingestion/nba_api.py`

**Funcionalidades:**
- Coleta de dados de jogos (past, current, future)
- Estatísticas de jogadores e equipas
- Play-by-play data
- Injury reports

**Endpoints utilizados:**
- `leaguestandings` - Classificação
- `playergamelog` - Histórico de jogadores
- `teamgamelog` - Histórico de equipas
- `commonplayerinfo` - Info de jogadores
- `scoreboard` - Resultados em tempo real

**Rate Limiting:**
- 1 requisição por segundo
- Cache local de 5 minutos
- Retry automático com exponential backoff

### 2. Betfair API Integration

**Arquivo:** `src/ingestion/betfair_odds.py`

**Funcionalidades:**
- Odds em tempo real
- Volume de mercado
- Depth do mercado
- Movimento de odds

**Mercados monitorizados:**
- NBA Moneyline
- NBA Spread
- NBA Totals (futuro)

**Rate Limiting:**
- 5 requisições por segundo (conta standard)
- Streaming para odds em tempo real
- Cache de 30 segundos

### 3. Odds API Integration

**Arquivo:** `src/ingestion/odds_api.py`

**Funcionalidades:**
- Odds de múltiplas casas
- Comparação de odds
- Fallback para Betfair

**Casas cobertas:**
- Bet365
- DraftKings
- FanDuel
- PointsBet
- William Hill

**Rate Limiting:**
- 500 requisições por mês (tier free)
- Cache de 1 hora
- Prioridade baixa (fallback)

### 4. Scraping Basketball-Reference

**Arquivo:** `scripts/scraping_local.py`

**Funcionalidades:**
- Estatísticas históricas avançadas
- Dados não disponíveis na NBA API
- Backfill de dados históricos

**Tecnologia:**
- BeautifulSoup4
- Selenium (quando necessário)
- Rate limiting respeitoso

---

## 🔄 Pipeline de Ingestão

### Fluxo Diário

```python
# 1. Coleta de dados de jogos
nba_api.fetch_games(date=today)

# 2. Coleta de odds (multi-casa)
betfair.fetch_odds(markets=["moneyline", "spread"])
odds_api.fetch_odds(bookmakers=["bet365", "draftkings"])

# 3. Validação e limpeza
validator.check_schema()
validator.remove_duplicates()
validator.handle_missing_values()

# 4. Deduplicação e merge
deduplicator.merge_sources()
deduplicator.resolve_conflicts()

# 5. Armazenamento
database.store_raw(data)
feature_store.update_features(data)
```

### Orquestração com Prefect

**Arquivo:** `src/pipeline/daily_flow.py`

**Flow:**
```python
@flow(name="daily_ingestion_flow")
def daily_ingestion():
    # 1. Fetch games
    games = fetch_nba_games()
    
    # 2. Fetch odds
    odds = fetch_odds_parallel(games)
    
    # 3. Validate
    validated = validate_data(games, odds)
    
    # 4. Store
    store_raw(validated)
    
    # 5. Update features
    update_features(validated)
```

**Schedule:**
- Execução a cada hora durante temporada
- Execução a cada 15 minutos durante jogos
- Backfill manual disponível

---

## 🧹 Validação e Limpeza

### Validação de Schema

**Arquivo:** `src/database/models.py`

**Regras:**
- Tipos de dados corretos
- Valores dentro de ranges esperados
- Chaves estrangeiras válidas
- Timestamps em UTC

**Exemplo:**
```python
class Game(Base):
    game_id: str  # UUID
    date: datetime  # UTC
    home_team: str  # 3-letter code
    away_team: str  # 3-letter code
    home_score: int  # 0-200
    away_score: int  # 0-200
    status: str  # scheduled, live, final
```

### Deduplicação

**Arquivo:** `04_Data_Engineering/DEDUPLICACAO_E_LIMPEZA.md`

**Estratégia:**
- Chave primária: `(game_id, source, timestamp)`
- Regra mais recente wins
- Detecção de duplicatas exatas
- Resolução de conflitos por prioridade de fonte

### Tratamento de Missing Values

**Estratégias:**
- **Jogos:** Ignorar se > 20% missing
- **Odds:** Interpolação temporal
- **Estatísticas:** Forward fill
- **Jogadores:** Excluir se injured

---

## 📊 Schema de Banco de Dados

### Tabelas Principais

**games**
```sql
CREATE TABLE games (
    game_id VARCHAR(36) PRIMARY KEY,
    game_date TIMESTAMP NOT NULL,
    home_team VARCHAR(3) NOT NULL,
    away_team VARCHAR(3) NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20) NOT NULL,
    season INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**odds**
```sql
CREATE TABLE odds (
    odds_id VARCHAR(36) PRIMARY KEY,
    game_id VARCHAR(36) REFERENCES games(game_id),
    bookmaker VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) NOT NULL,
    home_odds DECIMAL(10, 4),
    away_odds DECIMAL(10, 4),
    draw_odds DECIMAL(10, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**player_stats**
```sql
CREATE TABLE player_stats (
    stat_id VARCHAR(36) PRIMARY KEY,
    game_id VARCHAR(36) REFERENCES games(game_id),
    player_id VARCHAR(36) NOT NULL,
    team VARCHAR(3) NOT NULL,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    minutes_played INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 Performance e Otimização

### Cache Strategy

**Redis Cache:**
- NBA API: 5 minutos
- Betfair API: 30 segundos
- Odds API: 1 hora
- Features: 15 minutos

**Implementação:**
```python
from src.cache.redis_client import redis_client

@redis_client.cache(ttl=300)
def fetch_games(date):
    return nba_api.games(date)
```

### Batch Processing

**Estratégia:**
- Batch size: 1000 registros
- Parallel processing: 4 workers
- Chunk size: 100 registros por worker

### Indexação

**Índices no PostgreSQL:**
```sql
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_odds_game ON odds(game_id);
CREATE INDEX idx_odds_timestamp ON odds(timestamp);
CREATE INDEX idx_player_game ON player_stats(game_id, player_id);
```

---

## 📈 Monitorização

### Métricas

**Pipeline Metrics:**
- Latência de ingestão
- Taxa de sucesso
- Volume de dados
- Taxa de duplicatas

**Data Quality Metrics:**
- % de valores missing
- % de registros fora de schema
- % de conflitos resolvidos
- Freshness dos dados

### Alertas

**Telegram Alerts:**
- Falha na ingestão (> 5 min)
- Schema validation error
- Taxa de duplicatas > 5%
- Missing values > 10%

---

## 🔒 Segurança

### API Keys
- Armazenadas em environment variables
- Nunca commitadas no Git
- Rotation mensal

### Rate Limiting
- Respeito aos limites de cada API
- Implementação com Redis
- Fallback automático

### Data Privacy
- Anonimização de dados pessoais
- Compliance GDPR
- Retention policy: 2 anos

---

## 📝 Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Implementar backfill histórico
- [ ] Otimizar cache strategy
- [ ] Adicionar mais fontes de odds
- [ ] Melhorar error handling

### Médio Prazo (1-2 meses)
- [ ] Implementar streaming de odds
- [ ] Adicionar NFL data
- [ ] Criar data quality dashboard
- [ ] Automatizar schema evolution

### Longo Prazo (3-6 meses)
- [ ] Multi-desporto expansion
- [ ] Real-time processing
- [ ] ML-based anomaly detection
- [ ] Data marketplace integration

---

## 🔗 Links Relacionados

- [[Feature Engineering]] - Próximo passo no pipeline
- [[Machine Learning]] - Consumidor dos dados
- [[Pipeline de Operações]] - Orquestração
- [[Índice Mestre]] - Documentação completa
- [[Schema de Banco de Dados]] - Detalhes técnicos

---

**Última atualização:** 2026-05-19  
**Responsável:** Data Engineer  
**Status:** 🚧 Em desenvolvimento