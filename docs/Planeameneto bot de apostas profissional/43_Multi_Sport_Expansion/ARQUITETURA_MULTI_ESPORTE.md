# ARQUITETURA_MULTI_ESPORTE — Sistema Multi-Desporto

**ID:** `MSE-005` | **Fase:** #phase/7-12 | **Owner:** Chief Systems Architect | **Status:** #status/active | **Versão:** `2.0.0-VBQ-002`

---

## 1. OBJETIVO

Definir a arquitetura técnica para suportar múltiplos desportos no sistema de value betting, maximizando a reutilização de componentes enquanto permitindo customização específica por desporto.

---

## 2. PRINCÍPIOS ARQUITETURAIS

### 2.1 Principio da Separação
Cada desporto é um **sistema independente** com o seu próprio pipeline de dados, modelo e validação. Não há partilha de modelos entre desportos.

### 2.2 Principio da Reutilização
Componentes genéricos (infraestrutura, monitoring, risk management) são compartilhados entre todos os desportos.

### 2.3 Principio da Isolamento
Falhas em um desporto não devem afetar outros desportos. Circuit breakers por desporto são obrigatórios.

### 2.4 Principio da Progressão
Novos desportos são adicionados sequencialmente, um de cada vez, após validação completa do anterior.

---

## 3. ARQUITETURA EM CAMADAS

```
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 1: SHARED                          │
│  Infraestrutura, Monitoring, Logging, Config Management     │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 2: SEMI-SHARED                     │
│  Data Engineering (ETL framework), Feature Store base,       │
│  Model Registry, Risk Management, Execution Engine          │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                     LAYER 3: SPORT-SPECIFIC                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   NBA    │  │ Football │  │   MMA    │  │   NFL    │    │
│  │ Pipeline │  │ Pipeline │  │ Pipeline │  │ Pipeline │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   NBA    │  │ Football │  │   MMA    │  │   NFL    │    │
│  │  Model   │  │  Model   │  │  Model   │  │  Model   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   NBA    │  │ Football │  │   MMA    │  │   NFL    │    │
│  │  Config  │  │  Config  │  │  Config  │  │  Config  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Nota:** NBA + Football + MMA = VBQ-002 (Fase 7-12). NFL = VBQ-003 (Fase 13+).

---

## 4. COMPONENTES COMPARTILHADOS (SHARED)

### 4.1 Infraestrutura Base
- **VPS/Cloud:** Mesma infraestrutura para todos os desportos
- **Database:** PostgreSQL único com schemas separados por desporto
- **Cache:** Redis compartilhado com namespacing por desporto
- **Message Queue:** RabbitMQ/Redis Pub/Sub para comunicação assíncrona

### 4.2 Monitoring & Observability
- **Logging:** Structured logging com tags por desporto
- **Metrics:** Prometheus + Grafana com dashboards por desporto
- **Alerting:** Alertas específicos por desporto + alertas agregados
- **Tracing:** Distributed tracing com spans por desporto

### 4.3 Configuration Management
- **Config Store:** Centralizado com environment-specific configs
- **Feature Flags:** Ativação/desativação de features por desporto
- **Secrets Management:** HashiCorp Vault ou similar para API keys

### 4.4 Deployment & CI/CD
- **Pipeline Único:** CI/CD reutilizável para todos os desportos
- **Environment Management:** Dev/Stage/Prod com configs por desporto
- **Version Control:** Git com branches por feature/desporto

---

## 5. COMPONENTES SEMI-COMPARTILHADOS (SEMI-SHARED)

### 5.1 Data Engineering Framework
**Compartilhado:**
- ETL framework base (Airflow/Dagster templates)
- Data quality checks genéricos
- Schema validation framework
- Data lineage tracking

**Específico por Desporto:**
- Ingestão connectors (APIs diferentes por desporto)
- Data transformation logic (features específicas)
- Schema definitions (tabelas diferentes por desporto)

### 5.2 Feature Store Base
**Compartilhado:**
- Feature store infrastructure (Feast/Featureform)
- Feature versioning
- Feature serving API
- Feature monitoring

**Específico por Desporto:**
- Feature definitions (features diferentes por desporto)
- Feature computation logic
- Feature groups (separados por desporto)

### 5.3 Model Registry
**Compartilhado:**
- Registry infrastructure (MLflow)
- Model versioning
- Model metadata tracking
- Model deployment pipeline

**Específico por Desporto:**
- Model artifacts (modelos diferentes por desporto)
- Model schemas (inputs/outputs diferentes)
- Model performance metrics (métricas específicas)

### 5.4 Risk Management
**Compartilhado:**
- Kelly criterion calculator
- Position sizing logic
- Circuit breaker framework
- Exposure tracking

**Específico por Desporto:**
- Risk parameters (diferentes por desporto)
- Exposure limits (separados por desporto)
- Circuit breaker thresholds (ajustados por volatilidade)

### 5.5 Execution Engine
**Compartilhado:**
- Order management system
- Bet placement logic
- Execution monitoring
- Slippage tracking

**Específico por Desporto:**
- Betfair/Broker API integration (mercados diferentes)
- Order types específicos (se aplicável)
- Market data subscriptions (diferentes por desporto)

---

## 6. COMPONENTES ESPECÍFICOS POR DESPORTO (SPORT-SPECIFIC)

### 6.1 Data Pipeline por Desporto
Cada desporto tem o seu próprio pipeline:
- **NBA Pipeline:** ingestão NBA API, scraping de odds, feature engineering NBA
- **NFL Pipeline:** ingestão NFL data, feature engineering NFL
- **Tennis Pipeline:** ingestão Tennis Abstract, feature engineering tennis
- **LoL Pipeline:** ingestão Oracle's Elixir, feature engineering LoL

### 6.2 Modelos por Desporto
Cada desporto tem o seu próprio modelo:
- **NBA Model:** XGBoost treinado em dados NBA
- **NFL Model:** XGBoost treinado em dados NFL
- **Tennis Model:** XGBoost treinado em dados tennis
- **LoL Model:** XGBoost treinado em dados LoL

**Importante:** NÃO há transfer learning entre desportos. Cada modelo é independente.

### 6.3 Configuração por Desporto
Cada desporto tem a sua própria configuração:
- **NBA Config:** mercados, limites, parâmetros de risco
- **NFL Config:** mercados, limites, parâmetros de risco
- **Tennis Config:** mercados, limites, parâmetros de risco
- **LoL Config:** mercados, limites, parâmetros de risco

---

## 7. DATABASE SCHEMA

### 7.1 Schemas por Desporto
```sql
-- Schema genérico compartilhado
CREATE SCHEMA shared;
-- Tabelas: users, permissions, audit_log, system_config

-- Schema específico por desporto
CREATE SCHEMA nba;
-- Tabelas: nba_games, nba_odds, nba_features, nba_predictions, nba_bets

CREATE SCHEMA nfl;
-- Tabelas: nfl_games, nfl_odds, nfl_features, nfl_predictions, nfl_bets

CREATE SCHEMA tennis;
-- Tabelas: tennis_matches, tennis_odds, tennis_features, tennis_predictions, tennis_bets

CREATE SCHEMA lol;
-- Tabelas: lol_matches, lol_odds, lol_features, lol_predictions, lol_bets
```

### 7.2 Tabelas Compartilhadas
```sql
-- shared.bets (agregado de todos os desportos)
CREATE TABLE shared.bets (
    id UUID PRIMARY KEY,
    sport VARCHAR(10) NOT NULL,  -- 'nba', 'nfl', 'tennis', 'lol'
    bet_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    odds DECIMAL(5,2) NOT NULL,
    result VARCHAR(10),
    profit_loss DECIMAL(10,2),
    INDEX idx_sport (sport),
    INDEX idx_timestamp (timestamp)
);

-- shared.portfolio (exposição agregada)
CREATE TABLE shared.portfolio (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    sport VARCHAR(10),
    total_exposure DECIMAL(10,2),
    open_bets INTEGER,
    INDEX idx_timestamp (timestamp)
);
```

---

## 8. API DESIGN

### 8.1 APIs Compartilhadas
```python
# API genérica para obter predições
GET /api/v1/predictions?sport={sport}&date={date}

# API genérica para obter bets
GET /api/v1/bets?sport={sport}&start_date={start}&end_date={end}

# API genérica para obter portfolio
GET /api/v1/portfolio?sport={sport}
```

### 8.2 APIs Específicas por Desporto
```python
# Endpoints específicos podem ser adicionados se necessário
GET /api/v1/nba/predictions
GET /api/v1/nfl/predictions
GET /api/v1/tennis/predictions
GET /api/v1/lol/predictions
```

---

## 9. ISOLAMENTO DE FALHAS

### 9.1 Circuit Breakers por Desporto
Cada desporto tem o seu próprio circuit breaker:
- Se NBA model drift > threshold → desativa NBA bets
- NFL bets continuam normais
- Tennis bets continuam normais

### 9.2 Rate Limiting por Desporto
Cada desporto tem rate limiting independente:
- NBA API calls: limitado a X/min
- NFL API calls: limitado a Y/min
- Tennis API calls: limitado a Z/min

### 9.3 Resource Allocation
Cada desporto tem recursos dedicados:
- CPU quotas por desporto
- Memory limits por desporto
- Database connection pools separadas

---

## 10. DEPLOYMENT STRATEGY

### 10.1 Progressive Rollout
1. **Fase 1:** Deploy NBA (baseline)
2. **Fase 2:** Deploy NFL (após NBA validado)
3. **Fase 3:** Deploy Tennis (após NFL validado)
4. **Fase 4:** Deploy LoL (após Tennis validado)

### 10.2 Blue-Green Deployment
Cada desporto é deployado independentemente:
- NBA v2 em green, NBA v1 em blue
- Switch quando validado
- Rollback instantâneo se problemas

### 10.3 Feature Flags
Ativação de novos desportos via feature flags:
```yaml
features:
  nba_enabled: true
  nfl_enabled: false  # Ativar após validação NBA
  tennis_enabled: false
  lol_enabled: false
```

---

## 11. MONITORING AGREGADO

### 11.1 Dashboards por Desporto
- **NBA Dashboard:** ROI, CLV, drawdown, number of bets
- **NFL Dashboard:** ROI, CLV, drawdown, number of bets
- **Tennis Dashboard:** ROI, CLV, drawdown, number of bets
- **LoL Dashboard:** ROI, CLV, drawdown, number of bets

### 11.2 Dashboard Agregado
- **Portfolio Dashboard:** ROI agregado, drawdown agregado, exposure por desporto
- **System Dashboard:** Health check de todos os componentes
- **Business Dashboard:** P&L total, growth trajectory

---

## 12. RISCOS E MITIGAÇÃO

### 12.1 Risco: Complexidade Crescente
**Mitigação:**
- Manter arquitetura modular
- Documentação rigorosa
- Code reviews obrigatórios
- Testing automatizado

### 12.2 Risco: Resource Contention
**Mitigação:**
- Resource quotas por desporto
- Monitoring de resource usage
- Auto-scaling configurável
- Priority queuing

### 12.3 Risco: Data Corruption Cross-Sport
**Mitigação:**
- Schemas separados por desporto
- Strict type checking
- Data validation por schema
- Regular backups

### 12.4 Risco: Cascade Failures
**Mitigação:**
- Circuit breakers por desporto
- Isolation de processos
- Graceful degradation
- Fallback mechanisms

---

## 13. FUTURO EVOLUTION

### 13.1 Adição de Novos Esportes
Processo padrão para adicionar novo desporto:
1. Criar schema no database
2. Implementar data pipeline específico
3. Treinar modelo específico
4. Implementar configuração específica
5. Validar em paper trading
6. Ativar via feature flag

### 13.2 Multi-Model por Esporte
Futuro: múltiplos modelos por desporto (ensemble):
- NBA Model 1 (baseline)
- NBA Model 2 (advanced features)
- NBA Ensemble (combinação)

### 13.3 Cross-Sport Features
Futuro: features que cruzam desportos (raro, mas possível):
- Sentiment analysis de notícias (aplica a todos)
- Macroeconomic factors (afeta volume geral)

---

## 14. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/EXPANSAO_NFL]] → Implementação NFL
- [[43_Multi_Sport_Expansion/EXPANSAO_TENNIS_ATP]] → Implementação Tennis
- [[43_Multi_Sport_Expansion/EXPANSAO_ESPORTS_LOL]] → Implementação LoL
- [[43_Multi_Sport_Expansion/EXPANSAO_SOCCER_EPL]] → Implementação Soccer
- [[04_Data_Engineering/ESQUEMA_BASE_DADOS]] → Schema detalhado
- [[13_Infrastructure/ESCALABILIDADE]] → Escalabilidade da arquitetura
- [[12_DevOps/INFRASTRUCTURE_AS_CODE]] → IaC para multi-esporte

---

**Data de Criação:** 2026-05-13
**Revisão Obrigatória:** Após adição de segundo esporte (NFL)
**Owner:** Chief Systems Architect