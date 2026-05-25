# 15_Database — INDEX

**ID:** `SEC-15` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Especificar o schema, índices, constraints, e operações da base de dados PostgreSQL. Garantir integridade referencial, performance de queries analíticas, e audit trail completo.

---

## 2. NOTAS FUNDAMENTAIS

- [[SCHEMA_POSTGRESQL]] — Schema completo com todas as tabelas e relacionamentos
- [[PERFORMANCE_TUNING]] — Índices, partitioning, query optimization
- [[BACKUP_STRATEGY]] — Backup, retention, restore, disaster recovery

---

## 3. SCHEMA CORE — TABELAS PRINCIPAIS

```sql
-- Jogos NBA
CREATE TABLE games (
    game_id UUID PRIMARY KEY,
    season VARCHAR(9) NOT NULL,  -- '2019-20'
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    home_score INT,
    away_score INT,
    spread DECIMAL(5,2),
    total DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (game_date);

-- Odds históricas
CREATE TABLE odds (
    odd_id BIGSERIAL PRIMARY KEY,
    game_id UUID REFERENCES games(game_id),
    bookmaker VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,  -- 'moneyline', 'spread'
    selection VARCHAR(100) NOT NULL,
    odd DECIMAL(8,4) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    is_closing BOOLEAN DEFAULT FALSE,
    volume_available DECIMAL(12,2)
);

-- Apostas (reais e shadow)
CREATE TABLE bets (
    bet_id BIGSERIAL PRIMARY KEY,
    signal_id VARCHAR(50) UNIQUE,
    game_id UUID REFERENCES games(game_id),
    market VARCHAR(50) NOT NULL,
    selection VARCHAR(100) NOT NULL,
    odd_taken DECIMAL(8,4) NOT NULL,
    odd_close DECIMAL(8,4),
    stake DECIMAL(10,2) NOT NULL,
    outcome INT,  -- 1=win, 0=loss, NULL=pending
    pnl DECIMAL(10,2),
    clv DECIMAL(8,4),
    bet_type VARCHAR(20),  -- 'real', 'shadow', 'paper'
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Features (feature store)
CREATE TABLE features (
    feature_id BIGSERIAL PRIMARY KEY,
    game_id UUID REFERENCES games(game_id),
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(12,6),
    feature_version VARCHAR(10) DEFAULT '1.0',
    computed_at TIMESTAMP DEFAULT NOW()
);

-- Audit log
CREATE TABLE audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    record_id VARCHAR(100),
    action VARCHAR(20),  -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. IMPLEMENTAÇÃO COMPLETA

### 4.1 Script Robusto de Database PostgreSQL
```python
"""
Gestão completa de database PostgreSQL para value betting
Inclui schema, triggers, índices, e operações Python
"""

import logging
import asyncpg
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuração da database"""
    host: str = "localhost"
    port: int = 5432
    database: str = "valuebetting"
    user: str = "vb_admin"
    password: str = ""
    min_pool_size: int = 5
    max_pool_size: int = 20

class DatabaseManager:
    """Gestor de database PostgreSQL"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.dsn = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
        
        logger.info("🗄️  DatabaseManager inicializado")
    
    async def connect(self):
        """Conecta ao PostgreSQL"""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.config.min_pool_size,
            max_size=self.config.max_pool_size
        )
        logger.info("✅ Conectado ao PostgreSQL")
    
    async def disconnect(self):
        """Desconecta do PostgreSQL"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Desconectado do PostgreSQL")
    
    async def execute_schema(self):
        """Executa schema inicial"""
        logger.info("🏗️  Criando schema...")
        
        schema_sql = """
        -- Jogos NBA
        CREATE TABLE IF NOT EXISTS games (
            game_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            season VARCHAR(9) NOT NULL,
            game_date DATE NOT NULL,
            home_team_id INT NOT NULL,
            away_team_id INT NOT NULL,
            home_score INT,
            away_score INT,
            spread DECIMAL(5,2),
            total DECIMAL(5,2),
            status VARCHAR(20) DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        ) PARTITION BY RANGE (game_date);
        
        -- Odds históricas
        CREATE TABLE IF NOT EXISTS odds (
            odd_id BIGSERIAL PRIMARY KEY,
            game_id UUID REFERENCES games(game_id),
            bookmaker VARCHAR(50) NOT NULL,
            market VARCHAR(50) NOT NULL,
            selection VARCHAR(100) NOT NULL,
            odd DECIMAL(8,4) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            is_closing BOOLEAN DEFAULT FALSE,
            volume_available DECIMAL(12,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Apostas
        CREATE TABLE IF NOT EXISTS bets (
            bet_id BIGSERIAL PRIMARY KEY,
            signal_id VARCHAR(50) UNIQUE,
            game_id UUID REFERENCES games(game_id),
            market VARCHAR(50) NOT NULL,
            selection VARCHAR(100) NOT NULL,
            odd_taken DECIMAL(8,4) NOT NULL,
            odd_close DECIMAL(8,4),
            stake DECIMAL(10,2) NOT NULL,
            outcome INT CHECK (outcome IN (0, 1, NULL)),
            pnl DECIMAL(10,2),
            clv DECIMAL(8,4),
            bet_type VARCHAR(20) CHECK (bet_type IN ('real', 'shadow', 'paper')),
            executed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Features
        CREATE TABLE IF NOT EXISTS features (
            feature_id BIGSERIAL PRIMARY KEY,
            game_id UUID REFERENCES games(game_id),
            feature_name VARCHAR(100) NOT NULL,
            feature_value DECIMAL(12,6),
            feature_version VARCHAR(10) DEFAULT '1.0',
            computed_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Subscritores
        CREATE TABLE IF NOT EXISTS subscribers (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            email VARCHAR(255),
            subscription_tier VARCHAR(50) DEFAULT 'base',
            subscription_status VARCHAR(50) DEFAULT 'active',
            subscription_start_date DATE,
            subscription_end_date DATE,
            stripe_customer_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Sinais enviados
        CREATE TABLE IF NOT EXISTS signals_sent (
            id SERIAL PRIMARY KEY,
            signal_id VARCHAR(255) UNIQUE NOT NULL,
            sent_at TIMESTAMP DEFAULT NOW(),
            game_id VARCHAR(255),
            team VARCHAR(255),
            market VARCHAR(255),
            odd DECIMAL(10, 2),
            edge DECIMAL(5, 4),
            stake DECIMAL(10, 2),
            subscribers_count INTEGER
        );
        
        -- Audit log
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id BIGSERIAL PRIMARY KEY,
            table_name VARCHAR(50),
            record_id VARCHAR(100),
            action VARCHAR(20),
            old_values JSONB,
            new_values JSONB,
            changed_by VARCHAR(100),
            changed_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        logger.info("✅ Schema criado")
    
    async def create_indexes(self):
        """Cria índices para performance"""
        logger.info("🔍 Criando índices...")
        
        indexes_sql = """
        -- Índices para games
        CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
        CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
        CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team_id, away_team_id);
        
        -- Índices para odds
        CREATE INDEX IF NOT EXISTS idx_odds_game ON odds(game_id);
        CREATE INDEX IF NOT EXISTS idx_odds_timestamp ON odds(timestamp);
        CREATE INDEX IF NOT EXISTS idx_odds_bookmaker ON odds(bookmaker);
        
        -- Índices para bets
        CREATE INDEX IF NOT EXISTS idx_bets_game ON bets(game_id);
        CREATE INDEX IF NOT EXISTS idx_bets_executed ON bets(executed_at);
        CREATE INDEX IF NOT EXISTS idx_bets_type ON bets(bet_type);
        
        -- Índices para features
        CREATE INDEX IF NOT EXISTS idx_features_game ON features(game_id);
        CREATE INDEX IF NOT EXISTS idx_features_name ON features(feature_name);
        
        -- Índices para subscribers
        CREATE INDEX IF NOT EXISTS idx_subscribers_telegram ON subscribers(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(subscription_status);
        
        -- Índices para audit log
        CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(changed_at);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(indexes_sql)
        
        logger.info("✅ Índices criados")
    
    async def create_triggers(self):
        """Cria triggers de audit log"""
        logger.info("⚡ Criando triggers...")
        
        triggers_sql = """
        -- Função de audit log
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                INSERT INTO audit_log (table_name, record_id, action, old_values, changed_by)
                VALUES (TG_TABLE_NAME, OLD::text, 'DELETE', row_to_json(OLD), current_user);
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
                VALUES (TG_TABLE_NAME, NEW::text, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user);
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                INSERT INTO audit_log (table_name, record_id, action, new_values, changed_by)
                VALUES (TG_TABLE_NAME, NEW::text, 'INSERT', row_to_json(NEW), current_user);
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Triggers para tabelas principais
        CREATE TRIGGER IF NOT EXISTS games_audit
        AFTER INSERT OR UPDATE OR DELETE ON games
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER IF NOT EXISTS bets_audit
        AFTER INSERT OR UPDATE OR DELETE ON bets
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        
        CREATE TRIGGER IF NOT EXISTS subscribers_audit
        AFTER INSERT OR UPDATE OR DELETE ON subscribers
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(triggers_sql)
        
        logger.info("✅ Triggers criados")
    
    async def insert_game(self, game_data: Dict) -> str:
        """Insere jogo e retorna UUID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO games (season, game_date, home_team_id, away_team_id)
                VALUES ($1, $2, $3, $4)
                RETURNING game_id
                """,
                game_data['season'], game_data['game_date'],
                game_data['home_team_id'], game_data['away_team_id']
            )
            return str(row['game_id'])
    
    async def insert_bet(self, bet_data: Dict) -> int:
        """Insere aposta e retorna ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO bets (signal_id, game_id, market, selection, odd_taken, stake, bet_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING bet_id
                """,
                bet_data['signal_id'], bet_data['game_id'],
                bet_data['market'], bet_data['selection'],
                bet_data['odd_taken'], bet_data['stake'], bet_data['bet_type']
            )
            return row['bet_id']
    
    async def get_performance_summary(self, days: int = 30) -> Dict:
        """Obtém resumo de performance"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as n_bets,
                    SUM(CASE WHEN outcome = 1 THEN 1 ELSE 0 END) as n_wins,
                    SUM(CASE WHEN outcome = 0 THEN 1 ELSE 0 END) as n_losses,
                    SUM(pnl) as total_pnl,
                    AVG(clv) as avg_clv,
                    AVG(CASE WHEN outcome = 1 THEN 1 ELSE 0 END) as win_rate
                FROM bets
                WHERE executed_at >= NOW() - INTERVAL '%s days'
                AND bet_type = 'real'
                """,
                days
            )
            return dict(row) if row else {}
    
    async def get_games_without_odds(self, days: int = 7) -> List[Dict]:
        """Obtém jogos sem odds registradas"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT g.game_id, g.game_date, g.home_team_id, g.away_team_id
                FROM games g
                LEFT JOIN odds o ON g.game_id = o.game_id
                WHERE o.odd_id IS NULL
                AND g.game_date >= NOW() - INTERVAL '%s days'
                AND g.game_date <= NOW() + INTERVAL '1 day'
                """,
                days
            )
            return [dict(row) for row in rows]

# Uso
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Configuração
        config = DatabaseConfig(password="your_password")
        
        # Criar gestor
        db = DatabaseManager(config)
        
        # Conectar
        await db.connect()
        
        # Criar schema
        await db.execute_schema()
        
        # Criar índices
        await db.create_indexes()
        
        # Criar triggers
        await db.create_triggers()
        
        # Exemplo: inserir jogo
        game_id = await db.insert_game({
            'season': '2023-24',
            'game_date': '2024-01-15',
            'home_team_id': 1610612738,  # Celtics
            'away_team_id': 1610612747   # Lakers
        })
        
        print(f"Game ID: {game_id}")
        
        # Exemplo: resumo de performance
        summary = await db.get_performance_summary(days=30)
        print(f"Performance: {summary}")
        
        # Desconectar
        await db.disconnect()
    
    asyncio.run(main())
```

---

## 5. BACKLOG TÉCNICO

- [ ] Criar schema inicial em PostgreSQL
- [ ] Implementar triggers de audit log
- [ ] Criar índices para queries frequentes
- [ ] Configurar partitioning mensal em games
- [ ] Criar scripts de backup diário
- [ ] Documentar todas as relações e constraints

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[04_Data_Engineering/INDEX]] → Pipelines que alimentam a BD
- [[32_Feature_Store/INDEX]] → Features armazenadas
