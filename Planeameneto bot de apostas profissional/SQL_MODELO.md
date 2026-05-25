# SQL_MODELO — Modelo SQL

**ID:** `DB-003` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar modelo de dados SQL do sistema.

---

## 2. TABELAS PRINCIPAIS

### 2.1 Tabela de Apostas

```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    market VARCHAR(20) NOT NULL,
    selection VARCHAR(50) NOT NULL,
    prob DECIMAL(5,4) NOT NULL,
    odd DECIMAL(10,2) NOT NULL,
    edge DECIMAL(5,4) NOT NULL,
    stake DECIMAL(10,2) NOT NULL,
    outcome INTEGER,  -- 0=loss, 1=win, NULL=pending
    pnl DECIMAL(10,2),
    status VARCHAR(20) NOT NULL,  -- pending, executed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP
);
```

### 2.2 Tabela de Features

```sql
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    feature_name VARCHAR(50) NOT NULL,
    feature_value DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, feature_name)
);
```

### 2.3 Tabela de Odds

```sql
CREATE TABLE odds (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    market VARCHAR(20) NOT NULL,
    selection VARCHAR(50) NOT NULL,
    odd DECIMAL(10,2) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 3. ÍNDICES

```sql
CREATE INDEX idx_bets_game_id ON bets(game_id);
CREATE INDEX idx_bets_created_at ON bets(created_at);
CREATE INDEX idx_features_game_id ON features(game_id);
CREATE INDEX idx_odds_game_id ON odds(game_id);
```

---

## 4. CRITÉRIOS

- **Normalização 3NF**
- **Índices** em colunas frequentemente consultadas
- **Partitioning** por data para tabelas grandes

---

## 5. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[SCHEMA_EVOLUTION]]
