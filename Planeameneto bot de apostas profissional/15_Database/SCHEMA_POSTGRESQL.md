# SCHEMA_POSTGRESQL — DDL Completo

**ID:** `DB-001` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. SETUP INICIAL

```sql
-- Database e roles
CREATE DATABASE valuebetting OWNER vb_admin;
\c valuebetting

-- Schemas por camada
CREATE SCHEMA bronze;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
CREATE SCHEMA meta;
CREATE SCHEMA audit;
```

---

## 2. TABELAS BRONZE (RAW)

```sql
CREATE TABLE bronze.raw_nba_games (
    raw_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    season VARCHAR(10),
    game_date DATE,
    home_team_id INT,
    away_team_id INT,
    home_team_name VARCHAR(100),
    away_team_name VARCHAR(100),
    home_score INT,
    away_score INT,
    status VARCHAR(20),  -- 'Final', 'In Progress', etc.
    raw_json JSONB,
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bronze.raw_nba_boxscores (
    raw_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    team_id INT,
    team_name VARCHAR(100),
    stat_category VARCHAR(50),  -- 'Traditional', 'Advanced', 'Four Factors'
    raw_json JSONB,
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bronze.raw_odds_betfair (
    raw_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20),
    market VARCHAR(50),  -- 'moneyline', 'spread', 'total'
    selection VARCHAR(100),
    odd NUMERIC(10,4),
    volume_available NUMERIC(15,2),
    timestamp TIMESTAMPTZ,
    raw_json JSONB,
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bronze.raw_injuries (
    raw_id BIGSERIAL PRIMARY KEY,
    player_id INT,
    player_name VARCHAR(100),
    team_id INT,
    status VARCHAR(50),  -- 'AVAILABLE', 'QUESTIONABLE', 'DOUBTFUL', 'OUT', 'INJURED'
    description TEXT,
    report_date DATE,
    source VARCHAR(50),  -- 'nba_api', 'espn'
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. TABELAS SILVER (CLEAN)

```sql
CREATE TABLE silver.clean_games (
    game_id VARCHAR(20) PRIMARY KEY,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    home_score INT,
    away_score INT,
    winner_team_id INT,  -- NULL se ainda nao jogado
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE silver.clean_team_game_stats (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    team_id INT NOT NULL,
    is_home BOOLEAN NOT NULL,
    pts INT,
    fgm INT, fga INT,
    fg_pct NUMERIC(5,3),
    fg3m INT, fg3a INT,
    fg3_pct NUMERIC(5,3),
    ftm INT, fta INT,
    ft_pct NUMERIC(5,3),
    oreb INT, dreb INT, reb INT,
    ast INT, stl INT, blk INT,
    tov INT, pf INT,
    plus_minus INT,
    -- Four Factors
    efg_pct NUMERIC(5,3),
    tov_pct NUMERIC(5,3),
    orb_pct NUMERIC(5,3),
    ft_rate NUMERIC(5,3),  -- FT/FGA
    -- Advanced
    off_rating NUMERIC(8,3),
    def_rating NUMERIC(8,3),
    net_rating NUMERIC(8,3),
    pace NUMERIC(6,3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE silver.clean_player_injuries (
    id BIGSERIAL PRIMARY KEY,
    player_id INT NOT NULL,
    player_name VARCHAR(100),
    team_id INT,
    report_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    description TEXT,
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(player_id, report_date)
);

CREATE TABLE silver.clean_odds (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    market VARCHAR(50) NOT NULL,  -- 'moneyline_home', 'moneyline_away', 'spread_home'
    bookmaker VARCHAR(50) NOT NULL,  -- 'betfair', 'pinnacle', 'draftkings'
    odd NUMERIC(10,4) NOT NULL CHECK (odd > 1.0),
    volume_available NUMERIC(15,2),
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE silver.clean_schedules (
    id BIGSERIAL PRIMARY KEY,
    team_id INT NOT NULL,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    game_date DATE NOT NULL,
    is_home BOOLEAN NOT NULL,
    opponent_id INT NOT NULL,
    rest_days INT DEFAULT 99,  -- 99 = unknown
    is_back_to_back BOOLEAN DEFAULT FALSE,
    distance_km NUMERIC(8,2),  -- distancia desde ultimo jogo
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, game_id)
);
```

---

## 4. TABELAS GOLD (FEATURES)

```sql
CREATE TABLE gold.feat_team_form (
    id BIGSERIAL PRIMARY KEY,
    team_id INT NOT NULL,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    game_date DATE NOT NULL,
    -- Rolling windows com decaimento exponencial (halflife=5)
    wins_decay5 NUMERIC(5,3),
    pts_for_decay5 NUMERIC(6,2),
    pts_against_decay5 NUMERIC(6,2),
    efg_pct_decay5 NUMERIC(5,3),
    tov_pct_decay5 NUMERIC(5,3),
    orb_pct_decay5 NUMERIC(5,3),
    ft_rate_decay5 NUMERIC(5,3),
    off_rating_decay5 NUMERIC(8,3),
    def_rating_decay5 NUMERIC(8,3),
    net_rating_decay5 NUMERIC(8,3),
    -- Contexto
    rest_days INT,
    is_back_to_back BOOLEAN,
    is_home BOOLEAN,
    distance_km NUMERIC(8,2),
    -- Lesoes
    n_players_out INT DEFAULT 0,
    n_players_questionable INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, game_id)
);

CREATE TABLE gold.feat_game_context (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    -- Interacoes
    home_off_rating_vs_away_def_rating NUMERIC(8,3),
    away_off_rating_vs_home_def_rating NUMERIC(8,3),
    home_efg_vs_away_def_efg NUMERIC(5,3),
    away_efg_vs_home_def_efg NUMERIC(5,3),
    home_pace_vs_away_pace NUMERIC(6,3),
    -- Contexto calendario
    home_rest_days INT,
    away_rest_days INT,
    home_b2b BOOLEAN,
    away_b2b BOOLEAN,
    home_distance_km NUMERIC(8,2),
    away_distance_km NUMERIC(8,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE gold.feat_market (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    game_date DATE NOT NULL,
    market VARCHAR(50) NOT NULL,
    odd_open NUMERIC(10,4),
    odd_close NUMERIC(10,4),
    odd_movement_pct NUMERIC(6,3),  -- (close-open)/open
    implied_prob NUMERIC(5,3),
    overround NUMERIC(5,3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. TABELAS META

```sql
CREATE TABLE meta.pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20),  -- 'running', 'success', 'failed', 'warning'
    records_processed INT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meta.data_versions (
    version_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    snapshot_date DATE NOT NULL,
    row_count INT,
    checksum VARCHAR(64),
    schema_version VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(table_name, snapshot_date)
);

CREATE TABLE meta.feature_metadata (
    feature_id BIGSERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    data_type VARCHAR(50),
    source_table VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meta.model_registry (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50),
    training_data_start_date DATE,
    training_data_end_date DATE,
    metrics JSONB,
    file_path VARCHAR(255),
    is_deployed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_name, model_version)
);
```

---

## 6. TABELAS AUDIT

```sql
CREATE TABLE audit.audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100),
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    transaction_id UUID DEFAULT gen_random_uuid()
);

CREATE TABLE audit.bet_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    bet_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('created', 'executed', 'settled', 'cancelled')),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE audit.api_access_log (
    access_id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    user_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    status_code INT,
    response_time_ms INT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. TABELAS DE SINAIS E APOSTAS (GOLD)

```sql
CREATE TABLE gold.signals (
    signal_id VARCHAR(50) PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    market VARCHAR(50) NOT NULL,
    selection VARCHAR(100) NOT NULL,
    odd_at_generation NUMERIC(10,4) NOT NULL,
    predicted_prob NUMERIC(5,3) NOT NULL,
    implied_prob NUMERIC(5,3) NOT NULL,
    edge NUMERIC(5,3) NOT NULL,
    kelly_fraction NUMERIC(5,3),
    recommended_stake NUMERIC(10,2),
    model_version VARCHAR(20) NOT NULL,
    model_confidence NUMERIC(5,3),
    is_executed BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE gold.bets (
    bet_id VARCHAR(50) PRIMARY KEY,
    signal_id VARCHAR(50) REFERENCES gold.signals(signal_id),
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    market VARCHAR(50) NOT NULL,
    selection VARCHAR(100) NOT NULL,
    odd_taken NUMERIC(10,4) NOT NULL,
    odd_close NUMERIC(10,4),
    stake NUMERIC(10,2) NOT NULL,
    outcome INT CHECK (outcome IN (-1, 0, 1)),
    pnl NUMERIC(10,2),
    clv NUMERIC(5,3),
    bet_type VARCHAR(20) NOT NULL CHECK (bet_type IN ('real', 'shadow', 'paper')),
    bookmaker VARCHAR(50),
    executed_at TIMESTAMPTZ,
    settled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE gold.predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    market VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    predicted_outcome VARCHAR(100),
    predicted_prob NUMERIC(5,3),
    features_used JSONB,
    prediction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    is_correct BOOLEAN,
    UNIQUE(game_id, market, model_version, prediction_timestamp)
);
```

---

## 8. TABELAS DE EQUIPAS E JOGADORES (SILVER)

```sql
CREATE TABLE silver.teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_abbr VARCHAR(10) NOT NULL,
    city VARCHAR(100),
    conference VARCHAR(20),
    division VARCHAR(20),
    arena VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE silver.players (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    team_id INT REFERENCES silver.teams(team_id),
    position VARCHAR(10),
    height_cm INT,
    weight_kg INT,
    birth_date DATE,
    years_experience INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE silver.player_game_stats (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    player_id INT NOT NULL REFERENCES silver.players(player_id),
    team_id INT NOT NULL,
    is_home BOOLEAN NOT NULL,
    minutes NUMERIC(5,2),
    pts INT,
    fgm INT, fga INT,
    fg3m INT, fg3a INT,
    ftm INT, fta INT,
    oreb INT, dreb INT, reb INT,
    ast INT, stl INT, blk INT,
    tov INT, pf INT,
    plus_minus INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(game_id, player_id)
);
```

---

## 9. RELACIONAMENTOS ENTRE TABELAS

### 9.1 Diagrama de Relacionamentos

```
bronze.* (Raw) → silver.* (Clean) → gold.* (Features/Signals/Bets)
     ↓                ↓                    ↓
  APIs            Validation           ML Models
```

### 9.2 Chaves Estrangeiras Principais

| Tabela | Coluna | Referência | Ação |
|--------|--------|------------|------|
| silver.clean_team_game_stats | game_id | silver.clean_games(game_id) | CASCADE |
| silver.clean_odds | game_id | silver.clean_games(game_id) | CASCADE |
| gold.feat_team_form | game_id | silver.clean_games(game_id) | CASCADE |
| gold.signals | game_id | silver.clean_games(game_id) | CASCADE |
| gold.bets | signal_id | gold.signals(signal_id) | SET NULL |
| gold.bets | game_id | silver.clean_games(game_id) | CASCADE |

---

## 10. INDICES

### 10.1 Índices Bronze

```sql
CREATE INDEX idx_raw_nba_games_game_id ON bronze.raw_nba_games(game_id);
CREATE INDEX idx_raw_nba_games_date ON bronze.raw_nba_games(game_date);
CREATE INDEX idx_raw_nba_boxscores_game_id ON bronze.raw_nba_boxscores(game_id);
CREATE INDEX idx_raw_odds_betfair_game_id ON bronze.raw_odds_betfair(game_id);
CREATE INDEX idx_raw_odds_betfair_timestamp ON bronze.raw_odds_betfair(timestamp);
CREATE INDEX idx_raw_injuries_report_date ON bronze.raw_injuries(report_date);
```

### 10.2 Índices Silver

```sql
CREATE INDEX idx_clean_games_date ON silver.clean_games(game_date);
CREATE INDEX idx_clean_games_season ON silver.clean_games(season);
CREATE INDEX idx_clean_games_status ON silver.clean_games(status);
CREATE INDEX idx_clean_team_stats_game ON silver.clean_team_game_stats(game_id, team_id);
CREATE INDEX idx_clean_odds_game ON silver.clean_odds(game_id, market, bookmaker);
CREATE INDEX idx_clean_odds_recorded_at ON silver.clean_odds(recorded_at);
```

### 10.3 Índices Gold

```sql
CREATE INDEX idx_feat_team_game ON gold.feat_team_form(team_id, game_id);
CREATE INDEX idx_feat_team_date ON gold.feat_team_form(team_id, game_date);
CREATE INDEX idx_feat_game_date ON gold.feat_game_context(game_id, game_date);
CREATE INDEX idx_feat_market_game ON gold.feat_market(game_id, market);
CREATE INDEX idx_signals_game ON gold.signals(game_id);
CREATE INDEX idx_signals_created ON gold.signals(created_at);
CREATE INDEX idx_signals_executed ON gold.signals(is_executed, created_at);
CREATE INDEX idx_bets_game ON gold.bets(game_id);
CREATE INDEX idx_bets_executed ON gold.bets(executed_at);
CREATE INDEX idx_bets_outcome ON gold.bets(outcome);
```

### 10.4 Índices Meta e Audit

```sql
CREATE INDEX idx_pipeline_runs_name ON meta.pipeline_runs(pipeline_name);
CREATE INDEX idx_pipeline_runs_status ON meta.pipeline_runs(status);
CREATE INDEX idx_pipeline_runs_started ON meta.pipeline_runs(started_at);
CREATE INDEX idx_data_versions_table ON meta.data_versions(table_name);
CREATE INDEX idx_model_registry_deployed ON meta.model_registry(is_deployed);
CREATE INDEX idx_audit_log_table ON audit.audit_log(table_name);
CREATE INDEX idx_audit_log_changed_at ON audit.audit_log(changed_at);
CREATE INDEX idx_api_access_timestamp ON audit.api_access_log(timestamp);
```

---

## 11. LINKS CRUZADOS

- [[15_Database/INDEX]] ← Secao mae
- [[04_Data_Engineering/ESQUEMA_BASE_DADOS]] → Visao conceptual
- [[15_Database/PERFORMANCE_TUNING]] → Otimização de performance
- [[15_Database/BACKUP_STRATEGY]] → Estratégia de backup
- [[13_Infrastructure/POSTGRES_CONFIG]] → Configuração PostgreSQL
