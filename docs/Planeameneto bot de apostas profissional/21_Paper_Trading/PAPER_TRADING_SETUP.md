# PAPER_TRADING_SETUP — Configuração e Ambiente

**ID:** `PT-SETUP-001` | **Fase:** #phase/3 | **Owner:** DevOps + Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir a configuração técnica, ambiente e ferramentas necessárias para executar o paper trading de forma robusta e confiável.

---

## 2. REQUISITOS DE SISTEMA

### 2.1 Hardware Mínimo

| Componente | Mínimo | Recomendado | Justificação |
|------------|--------|-------------|--------------|
| CPU | 2 vCPU | 4 vCPU | Processamento de sinais em tempo real |
| RAM | 4 GB | 8 GB | Cache de dados em memória |
| Armazenamento | 50 GB SSD | 100 GB SSD | Histórico de dados e logs |
| Rede | 10 Mbps | 100 Mbps | Latência crítica para captura de odds |

### 2.2 Software

| Componente | Versão Mínima | Recomendado | Justificação |
|------------|---------------|-------------|--------------|
| Python | 3.9 | 3.11 | Compatibilidade com bibliotecas |
| PostgreSQL | 13 | 15 | Performance de queries |
| Redis | 6.0 | 7.0 | Cache de odds em tempo real |
| Docker | 20.10 | 24.0 | Isolamento de ambiente |
| Git | 2.30 | 2.40 | Controle de versão |

---

## 3. ARQUITETURA DO AMBIENTE

### 3.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        VPS / Servidor                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Data        │    │  Signal      │    │  Paper       │       │
│  │  Pipeline    │───→│  Engine      │───→│  Trading     │       │
│  │  (Docker)    │    │  (Docker)    │    │  Module      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ↓                   ↓                   ↓                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  PostgreSQL  │    │  Redis       │    │  Reporting   │       │
│  │  (Docker)    │    │  (Docker)    │    │  (Docker)    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  API Odds    │    │  API Result  │    │  Monitoring  │
│  (External)  │    │  (External)  │    │  (Grafana)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 3.2 Estrutura de Diretórios

```
/paper_trading/
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.data
│   ├── Dockerfile.signal
│   └── Dockerfile.paper
├── config/
│   ├── config.yaml
│   ├── logging.yaml
│   └── database.yaml
├── scripts/
│   ├── setup.sh
│   ├── backup.sh
│   └── health_check.sh
├── src/
│   ├── data_pipeline/
│   ├── signal_engine/
│   ├── paper_trading/
│   └── reporting/
├── logs/
│   ├── data_pipeline.log
│   ├── signal_engine.log
│   └── paper_trading.log
└── tests/
    ├── test_pipeline.py
    ├── test_signals.py
    └── test_paper_trading.py
```

---

## 4. CONFIGURAÇÃO DE BASE DE DADOS

### 4.1 Schema PostgreSQL

```sql
-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Tabela de sinais paper trading
CREATE TABLE paper_trading_signals (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(50) UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    
    -- Identificação do jogo
    game_id VARCHAR(50) NOT NULL,
    game_date TIMESTAMP NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    
    -- Mercado
    market_type VARCHAR(20) NOT NULL, -- 'moneyline', 'spread', 'totals'
    selection_id VARCHAR(50) NOT NULL,
    selection_name VARCHAR(100) NOT NULL,
    bet_type VARCHAR(20) NOT NULL,
    
    -- Sinal
    signal_timestamp TIMESTAMP NOT NULL,
    signal_odds DECIMAL(10,4) NOT NULL,
    signal_stake DECIMAL(10,2) NOT NULL,
    kelly_fraction DECIMAL(5,4) NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    expected_value DECIMAL(5,4) NOT NULL,
    
    -- Execução simulada
    execution_timestamp TIMESTAMP,
    execution_odds DECIMAL(10,4),
    execution_status VARCHAR(20), -- 'FILLED', 'CANCELLED_TIMEOUT', 'REJECTED'
    slippage_pct DECIMAL(5,4),
    fill_reason TEXT,
    
    -- Resultado
    closing_odds DECIMAL(10,4),
    game_result VARCHAR(20), -- 'WIN', 'LOSS', 'VOID', 'PENDING'
    pnl DECIMAL(10,2),
    clv_expost DECIMAL(5,4),
    
    -- Metadados
    mode VARCHAR(10) NOT NULL DEFAULT 'paper',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_execution_status CHECK (execution_status IN ('FILLED', 'CANCELLED_TIMEOUT', 'REJECTED', 'PENDING')),
    CONSTRAINT valid_game_result CHECK (game_result IN ('WIN', 'LOSS', 'VOID', 'PENDING'))
);

-- Índices para performance
CREATE INDEX idx_paper_signals_game ON paper_trading_signals(game_id);
CREATE INDEX idx_paper_signals_date ON paper_trading_signals(signal_timestamp);
CREATE INDEX idx_paper_signals_status ON paper_trading_signals(execution_status);
CREATE INDEX idx_paper_signals_result ON paper_trading_signals(game_result);

-- Tabela de logs de execução
CREATE TABLE paper_trading_logs (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(50) REFERENCES paper_trading_signals(signal_id),
    log_timestamp TIMESTAMP DEFAULT NOW(),
    log_level VARCHAR(10) NOT NULL, -- 'INFO', 'WARNING', 'ERROR'
    log_message TEXT NOT NULL,
    log_data JSONB
);

CREATE INDEX idx_paper_logs_signal ON paper_trading_logs(signal_id);
CREATE INDEX idx_paper_logs_timestamp ON paper_trading_logs(log_timestamp);

-- Tabela de métricas diárias
CREATE TABLE paper_trading_daily_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE UNIQUE NOT NULL,
    
    -- Volume
    total_signals INT DEFAULT 0,
    filled_bets INT DEFAULT 0,
    cancelled_bets INT DEFAULT 0,
    fill_rate DECIMAL(5,4) DEFAULT 0,
    
    -- Performance
    total_pnl DECIMAL(10,2) DEFAULT 0,
    roi DECIMAL(5,4) DEFAULT 0,
    avg_clv DECIMAL(5,4) DEFAULT 0,
    sharpe_ratio DECIMAL(5,4) DEFAULT 0,
    max_drawdown DECIMAL(5,4) DEFAULT 0,
    
    -- Operacional
    uptime_pct DECIMAL(5,4) DEFAULT 0,
    avg_latency_seconds DECIMAL(10,4) DEFAULT 0,
    circuit_breakers_triggered INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_paper_trading_signals_updated_at BEFORE UPDATE ON paper_trading_signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paper_trading_daily_metrics_updated_at BEFORE UPDATE ON paper_trading_daily_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 4.2 Configuração de Conexão

```yaml
# config/database.yaml
database:
  host: localhost
  port: 5432
  name: paper_trading_db
  user: paper_trading_user
  password: ${DB_PASSWORD}  # Variável de ambiente
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600
  
redis:
  host: localhost
  port: 6379
  db: 0
  password: ${REDIS_PASSWORD}
  max_connections: 50
  socket_timeout: 5
  socket_connect_timeout: 5
```

---

## 5. CONFIGURAÇÃO DE APLICAÇÃO

### 5.1 Configuração Principal

```yaml
# config/config.yaml
paper_trading:
  mode: paper
  
  # Validação de sinais
  validation:
    min_confidence: 0.6
    min_expected_value: 0.02
    max_stake: 100
    max_exposure_daily: 500
  
  # Simulação de execução
  execution:
    timeout_seconds: 60
    min_liquidity: 100
    slippage_tolerance: 0.02
    simulate_fill: true
  
  # Captura de odds
  odds_capture:
    enabled: true
    sources:
      - betfair
      - pinnacle
    capture_interval_seconds: 30
    retry_attempts: 3
    retry_delay_seconds: 5
  
  # Captura de resultados
  results_capture:
    enabled: true
    sources:
      - api_sports
    check_interval_minutes: 15
    max_attempts: 10
  
  # Relatórios
  reporting:
    enabled: true
    schedule: "0 23 * * *"  # 23:00 UTC diário
    output_formats:
      - json
      - csv
      - html
    email_recipients:
      - ops@example.com
  
  # Alertas
  alerts:
    enabled: true
    channels:
      - email
      - telegram
    alert_on:
      - system_error
      - fill_rate_low
      - clv_negative
      - drawdown_high
```

### 5.2 Configuração de Logging

```yaml
# config/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/paper_trading.log
    maxBytes: 10485760  # 10MB
    backupCount: 10
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/paper_trading_errors.log
    maxBytes: 10485760  # 10MB
    backupCount: 10

loggers:
  paper_trading:
    level: DEBUG
    handlers: [console, file, error_file]
    propagate: false
  
  data_pipeline:
    level: INFO
    handlers: [console, file]
    propagate: false
  
  signal_engine:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: WARNING
  handlers: [console]
```

---

## 6. DOCKER COMPOSE

### 6.1 docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: paper_trading_db
    environment:
      POSTGRES_DB: paper_trading_db
      POSTGRES_USER: paper_trading_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paper_trading_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: paper_trading_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  data_pipeline:
    build:
      context: .
      dockerfile: docker/Dockerfile.data
    container_name: paper_trading_pipeline
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=paper_trading_db
      - DB_USER=paper_trading_user
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./src/data_pipeline:/app/src
    restart: unless-stopped

  signal_engine:
    build:
      context: .
      dockerfile: docker/Dockerfile.signal
    container_name: paper_trading_signal
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      data_pipeline:
        condition: service_started
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=paper_trading_db
      - DB_USER=paper_trading_user
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./src/signal_engine:/app/src
    restart: unless-stopped

  paper_trading:
    build:
      context: .
      dockerfile: docker/Dockerfile.paper
    container_name: paper_trading_module
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      signal_engine:
        condition: service_started
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=paper_trading_db
      - DB_USER=paper_trading_user
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./src/paper_trading:/app/src
    restart: unless-stopped

  reporting:
    build:
      context: .
      dockerfile: docker/Dockerfile.reporting
    container_name: paper_trading_reporting
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=paper_trading_db
      - DB_USER=paper_trading_user
      - DB_PASSWORD=${DB_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./reports:/app/reports
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## 7. SCRIPTS DE SETUP

### 7.1 Script de Inicialização

```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "=== Paper Trading Setup ==="

# Verificar dependências
echo "Verificando dependências..."
command -v docker >/dev/null 2>&1 || { echo "Docker não instalado"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose não instalado"; exit 1; }

# Criar diretórios
echo "Criando diretórios..."
mkdir -p logs reports config sql

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "Criando arquivo .env..."
    cat > .env << EOF
DB_PASSWORD=change_this_password
REDIS_PASSWORD=change_this_password
EOF
    echo "AVISO: Por favor, edite .env e altere as senhas!"
fi

# Copiar arquivos de configuração
echo "Copiando arquivos de configuração..."
cp config/config.yaml.example config/config.yaml 2>/dev/null || true
cp config/database.yaml.example config/database.yaml 2>/dev/null || true
cp config/logging.yaml.example config/logging.yaml 2>/dev/null || true

# Iniciar containers
echo "Iniciando containers Docker..."
docker-compose up -d

# Aguardar PostgreSQL estar pronto
echo "Aguardando PostgreSQL..."
sleep 10

# Executar migrações
echo "Executando migrações de banco de dados..."
docker-compose exec postgres psql -U paper_trading_user -d paper_trading_db -f /docker-entrypoint-initdb.d/init.sql

echo "=== Setup concluído ==="
echo "Verifique os logs com: docker-compose logs -f"
```

### 7.2 Script de Health Check

```bash
#!/bin/bash
# scripts/health_check.sh

echo "=== Paper Trading Health Check ==="

# Verificar se containers estão rodando
echo "Verificando containers..."
docker-compose ps

# Verificar PostgreSQL
echo "Verificando PostgreSQL..."
docker-compose exec postgres pg_isready -U paper_trading_user

# Verificar Redis
echo "Verificando Redis..."
docker-compose exec redis redis-cli ping

# Verificar logs recentes
echo "Logs recentes (últimas 20 linhas):"
docker-compose logs --tail=20

echo "=== Health check concluído ==="
```

---

## 8. VALIDAÇÃO DE AMBIENTE

### 8.1 Checklist de Validação

Antes de iniciar o paper trading, validar:

- [ ] Docker e Docker Compose instalados
- [ ] Todos os containers iniciados sem erros
- [ ] PostgreSQL acessível e schema criado
- [ ] Redis acessível
- [ ] Variáveis de ambiente configuradas
- [ ] Arquivos de configuração validados
- [ ] APIs externas acessíveis (odds, resultados)
- [ ] Logs sem erros críticos
- [ ] Backup configurado
- [ ] Monitorização configurada

### 8.2 Testes de Integração

```python
# tests/test_paper_trading_setup.py
import pytest
import psycopg2
import redis
from datetime import datetime

def test_database_connection():
    """Testa conexão com PostgreSQL"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="paper_trading_db",
        user="paper_trading_user",
        password="change_this_password"
    )
    assert conn is not None
    conn.close()

def test_redis_connection():
    """Testa conexão com Redis"""
    r = redis.Redis(
        host="localhost",
        port=6379,
        password="change_this_password",
        decode_responses=True
    )
    assert r.ping() == True

def test_database_schema():
    """Testa se schema foi criado corretamente"""
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    
    # Verificar tabelas
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    assert 'paper_trading_signals' in tables
    assert 'paper_trading_logs' in tables
    assert 'paper_trading_daily_metrics' in tables
    
    conn.close()

def test_config_files():
    """Testa se arquivos de configuração existem"""
    import os
    assert os.path.exists('config/config.yaml')
    assert os.path.exists('config/database.yaml')
    assert os.path.exists('config/logging.yaml')
```

---

## 9. MONITORIZAÇÃO

### 9.1 Métricas a Monitorizar

| Métrica | Ferramenta | Alerta se |
|---------|------------|-----------|
| CPU do servidor | Prometheus/Grafana | > 80% por 5 min |
| RAM do servidor | Prometheus/Grafana | > 85% por 5 min |
| Espaço em disco | Prometheus/Grafana | > 80% |
| Latência de BD | PostgreSQL stats | > 100ms |
| Conexões ativas | PostgreSQL stats | > 80% do pool |
| Taxa de erros de API | Custom logs | > 5% |
| Uptime do sistema | Custom script | < 95% |

### 9.2 Dashboard Grafana (Sugestão)

```json
{
  "dashboard": {
    "title": "Paper Trading Monitoring",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [{"expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"}]
      },
      {
        "title": "Memory Usage",
        "targets": [{"expr": "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"}]
      },
      {
        "title": "Signals per Hour",
        "targets": [{"expr": "rate(paper_trading_signals_total[1h])"}]
      },
      {
        "title": "Fill Rate",
        "targets": [{"expr": "paper_trading_fill_rate"}]
      },
      {
        "title": "Database Latency",
        "targets": [{"expr": "pg_stat_statement_mean_exec_time"}]
      }
    ]
  }
}
```

---

## 10. BACKUP E RECUPERAÇÃO

### 10.1 Estratégia de Backup

```bash
# scripts/backup.sh
#!/bin/bash

BACKUP_DIR="/backups/paper_trading"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U paper_trading_user paper_trading_db > $BACKUP_DIR/db_$DATE.sql

# Backup Redis
docker-compose exec redis redis-cli --rdb /data/dump_$DATE.rdb
docker cp paper_trading_redis:/data/dump_$DATE.rdb $BACKUP_DIR/

# Backup configurações
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 10.2 Recuperação

```bash
# scripts/restore.sh
#!/bin/bash

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: ./restore.sh <arquivo_backup>"
    exit 1
fi

# Restaurar PostgreSQL
docker-compose exec -T postgres psql -U paper_trading_user paper_trading_db < $BACKUP_FILE

echo "Backup restaurado com sucesso"
```

---

## 11. LINKS CRUZADOS

- [[21_Paper_Trading/INDEX]] ← Secao mae
- [[21_Paper_Trading/PROTOCOLO_PAPER]] ← Protocolo operacional
- [[14_APIs/BETFAIR_API]] → Configuração de API Betfair
- [[10_Infrastructure/INDEX]] → Infraestrutura geral