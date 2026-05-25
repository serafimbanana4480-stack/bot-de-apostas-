# ARQUITETURA_FEATURE_STORE — Arquitetura do Sistema de Features

**ID:** `FEAT-001` | **Fase:** #phase/1-6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir a arquitetura do Feature Store para armazenar, versionar e servir features de forma centralizada. O sistema deve suportar tanto treino de modelos (histórico) como inferência em tempo real (online), garantindo consistência entre ambos.

---

## 2. CONTEXTO

Um Feature Store é o componente crítico que conecta engenharia de dados com machine learning. Sem um Feature Store, cada equipe recria features, há inconsistências entre treino e produção, e não há rastreabilidade. Em value betting, onde a precisão é crítica, um Feature Store robusto é essencial para:

- Garantir que as features usadas no treino são idênticas às usadas em produção
- Evitar data leakage através de versionamento temporal
- Permitir reutilização de features entre múltiplos modelos
- Facilitar debugging e auditabilidade

---

## 3. ARQUITETURA GERAL

### 3.1 Componentes Principais

```
┌─────────────────────────────────────────────────────────────────┐
│                      FEATURE STORE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              OFFLINE STORE (Histórico)                   │   │
│  │  • PostgreSQL + Parquet                                  │   │
│  │  • Features para treino de modelos                       │   │
│  │  • Acesso via SQL/Python                                 │   │
│  │  • Escalável para TB de dados                            │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                        │
│                        │ Sincronização                          │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ONLINE STORE (Tempo Real)                   │   │
│  │  • Redis (ou PostgreSQL com cache)                       │   │
│  │  • Features para inferência em produção                  │   │
│  │  • Baixa latência (<10ms)                                │   │
│  │  • TTL automático                                        │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                        │
└────────────────────────┼────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌─────────────────┐           ┌─────────────────┐
│  Feature API    │           │  Feature CLI    │
│  (REST/GraphQL) │           │  (Admin tools)  │
└─────────────────┘           └─────────────────┘
```

### 3.2 Fluxo de Dados

```
Fontes de Dados (Bronze/Silver)
    │
    ▼
Pipeline de Feature Engineering
    │
    ├─→ Offline Store (PostgreSQL)
    │       │
    │       ├─→ Treino de Modelos (Batch)
    │       └─→ Backtests
    │
    └─→ Online Store (Redis)
            │
            ├─→ Inferência em Tempo Real
            └─→ API de Predição
```

---

## 4. OFFLINE STORE

### 4.1 Propósito

Armazenar features históricas para:
- Treino de modelos de machine learning
- Backtesting de estratégias
- Análise exploratória
- Validação de features

### 4.2 Implementação

**Tecnologia:** PostgreSQL 15 com extensão TimescaleDB (opcional para time-series)

**Schema:**
```sql
-- Tabela principal de features
CREATE TABLE feature_store.features (
    feature_id VARCHAR(50) NOT NULL,
    feature_version INT NOT NULL,
    entity_id VARCHAR(50) NOT NULL,  -- team_id, game_id, etc.
    timestamp TIMESTAMP NOT NULL,
    value DOUBLE PRECISION,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (feature_id, feature_version, entity_id, timestamp)
);

-- Índices para performance
CREATE INDEX idx_feature_entity_time 
    ON feature_store.features (feature_id, entity_id, timestamp);
    
CREATE INDEX idx_feature_time 
    ON feature_store.features (feature_id, timestamp);

-- Partitioning por timestamp (opcional para escalabilidade)
```

**Tabela de metadados de features:**
```sql
CREATE TABLE feature_store.feature_metadata (
    feature_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    data_type VARCHAR(20),  -- float, int, bool, string
    source_table VARCHAR(100),
    source_column VARCHAR(100),
    transformation_logic TEXT,
    current_version INT DEFAULT 1,
    owner VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4.3 Vantagens

- **Consistência ACID:** Transações garantem integridade
- **SQL nativo:** Fácil de consultar com ferramentas existentes
- **Joins complexos:** Possível combinar features de múltiplas fontes
- **Time travel:** Query features em qualquer ponto no tempo
- **Escalabilidade:** Partitioning e índices para grandes volumes

### 4.4 Limitações

- **Latência:** Consultas podem demorar 100ms-1s (dependendo do volume)
- **Custo:** Armazenamento em disco é mais caro que memória
- **Não ideal para inferência em tempo real:** Requer cache adicional

---

## 5. ONLINE STORE

### 5.1 Propósito

Armazenar features recentes para:
- Inferência em tempo real (previsões antes do jogo)
- Serviço de features com baixa latência
- Cache de features frequentemente acessadas

### 5.2 Implementação

**Tecnologia:** Redis 7.x (ou PostgreSQL com pg_cache)

**Schema (Redis):**
```
# Key pattern: feature:{feature_id}:v{version}:{entity_id}
# Value: JSON com timestamp e valor

feature:home_win_rate_decay5:v1:BOS:2024-01-15
{
    "value": 0.65,
    "timestamp": "2024-01-15T10:00:00Z",
    "version": 1,
    "ttl": 86400  # 24 horas
}

# Para batch get de múltiplas features:
entity:features:{entity_id}:{timestamp}
{
    "home_win_rate_decay5": 0.65,
    "away_win_rate_decay5": 0.58,
    "home_efg_pct_decay5": 0.52,
    ...
}
```

**Configuração Redis:**
```python
# Exemplo de configuração
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": True,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True,
    "max_connections": 50
}

# TTL por tipo de feature
FEATURE_TTL = {
    "rolling_stats": 86400,      # 24 horas
    "market_odds": 3600,         # 1 hora
    "injury_status": 1800,       # 30 minutos
    "schedule_context": 604800   # 7 dias
}
```

### 5.3 Vantagens

- **Baixa latência:** <10ms para get simples
- **Alta throughput:** Milhares de ops/segundo
- **TTL automático:** Expiração natural de features antigas
- **In-memory:** Performance otimizada para leituras frequentes

### 5.4 Limitações

- **Sem joins:** Cada feature é uma key separada
- **Memória volátil:** Dados perdidos se Redis crash (mitigado com persistência)
- **Custo:** RAM é mais cara que disco
- **Sem time travel complexo:** Apenas versão atual

---

## 6. SINCRONIZAÇÃO OFFLINE ↔ ONLINE

### 6.1 Estratégia de Sincronização

**Batch Sync (diário):**
```python
def sync_features_to_online():
    """
    Sincroniza features calculadas no dia para Online Store.
    Executa: 1x/dia após pipeline de feature engineering.
    """
    # 1. Buscar features atualizadas nas últimas 24h
    recent_features = query_offline_store(
        "SELECT * FROM features WHERE created_at > NOW() - INTERVAL '24 hours'"
    )
    
    # 2. Agrupar por entity
    entity_features = group_by_entity(recent_features)
    
    # 3. Escrever para Redis em pipeline
    redis_pipeline = redis_client.pipeline()
    for entity_id, features in entity_features.items():
        key = f"entity:features:{entity_id}:{features[0].timestamp}"
        redis_pipeline.setex(
            key,
            FEATURE_TTL.get(features[0].type, 86400),
            json.dumps(features)
        )
    redis_pipeline.execute()
```

**Real-time Sync (opcional):**
```python
def on_feature_computed(feature):
    """
    Triggered quando uma feature é computada.
    Atualiza Online Store imediatamente.
    """
    redis_key = f"feature:{feature.id}:v{feature.version}:{feature.entity_id}"
    redis_client.setex(
        redis_key,
        FEATURE_TTL.get(feature.type, 86400),
        json.dumps({
            "value": feature.value,
            "timestamp": feature.timestamp,
            "version": feature.version
        })
    )
```

### 6.2 Consistência

- **Eventual consistency:** Offline Store é fonte de verdade
- **Reconciliation:** Job diário verifica diferenças entre stores
- **Fallback:** Se feature não está em Online Store, busca no Offline Store

---

## 7. FEATURE REGISTRY

### 7.1 Propósito

Catálogo central de todas as features disponíveis, incluindo:
- Metadados (nome, descrição, tipo)
- Lineage (origem dos dados)
- Versões atuais e históricas
- Estatísticas (distribuição, missing rate)
- Owners e responsáveis

### 7.2 Implementação

**Tabela de registry (PostgreSQL):**
```sql
CREATE TABLE feature_store.feature_registry (
    feature_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    data_type VARCHAR(20) NOT NULL,
    category VARCHAR(50),  -- rolling, market, context, interaction
    source_tables TEXT[],   -- Tabelas de origem
    transformation_logic TEXT,
    current_version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active',  -- active, deprecated, experimental
    owner VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    tags TEXT[]
);
```

**API de registry:**
```python
class FeatureRegistry:
    def register_feature(self, feature: FeatureMetadata):
        """Registra nova feature no catálogo."""
        
    def get_feature(self, feature_id: str) -> FeatureMetadata:
        """Busca metadados de uma feature."""
        
    def list_features(self, category: str = None, status: str = None) -> List[FeatureMetadata]:
        """Lista features com filtros."""
        
    def update_feature_version(self, feature_id: str, new_version: int):
        """Atualiza versão de uma feature."""
        
    def deprecate_feature(self, feature_id: str):
        """Marca feature como deprecated."""
```

---

## 8. BOAS PRÁTICAS

### 8.1 Nomenclatura

- **Feature ID:** Prefixo descritivo + nome curto
  - Ex: `home_win_rate_decay5`, `clv_implied`, `away_is_b2b`
- **Versões:** Numéricas incrementais (1.0, 1.1, 2.0)
- **Entity IDs:** Consistentes com fontes de dados
  - `team_id`, `game_id`, `player_id`

### 8.2 Imutabilidade

- Features históricas nunca são modificadas
- Mudanças requerem nova versão
- Versões antigas permanecem para reprodução

### 8.3 Documentação

- Cada feature tem descrição clara
- Lógica de transformação documentada
- Exemplos de uso fornecidos
- Owner identificado para suporte

### 8.4 Testes

- Testes unitários para lógica de transformação
- Testes de integridade (range, tipo)
- Testes de leakage (timestamp validation)
- Testes de performance (latência)

---

## 9. ESCALABILIDADE

### 9.1 Volume de Dados

**Estimativa inicial:**
- 30 features × 30 equipas × 1230 jogos/época × 5 épocas = ~5.5M linhas
- Com histórico de 10 épocas: ~11M linhas
- Tamanho estimado: 2-5 GB (offline), 500 MB (online)

**Estratégias de escalabilidade:**
- Partitioning por timestamp (mensal)
- Índices compostos para queries frequentes
- Arquivamento de features antigas (cold storage)
- Compressão (TOAST no PostgreSQL)

### 9.2 Performance

**Queries otimizadas:**
```sql
-- Ruim: Scan completo
SELECT * FROM features WHERE feature_id = 'home_win_rate_decay5';

-- Bom: Índice composto
SELECT value FROM features 
WHERE feature_id = 'home_win_rate_decay5' 
  AND entity_id = 'BOS' 
  AND timestamp <= '2024-01-15'
ORDER BY timestamp DESC 
LIMIT 1;
```

**Cache de queries frequentes:**
- Materialized views para agregações
- Pre-computed joins para feature groups
- Query result caching (PostgreSQL)

---

## 10. MONITORIZAÇÃO

### 10.1 Métricas de Sistema

- **Latência:** Tempo médio de get/set features
- **Throughput:** Ops/segundo em Online Store
- **Storage:** Uso de disco (offline) e memória (online)
- **Cache hit rate:** % de features servidas do cache

### 10.2 Métricas de Qualidade

- **Feature freshness:** Idade da feature mais recente
- **Missing rate:** % de valores nulos por feature
- **Outlier rate:** % de valores fora de range esperado
- **Drift score:** Mudança na distribuição ao longo do tempo

---

## 11. SEGURANÇA

### 11.1 Controlo de Acesso

- **RBAC:** Roles por função (admin, engineer, analyst)
- **Feature-level ACL:** Permissões por feature
- **Audit log:** Registo de todas as operações

### 11.2 Dados Sensíveis

- **PII:** Não armazenar dados pessoais identificáveis
- **Odds:** Considerar sensibilidade comercial
- **Encryption:** At-rest e in-transit

---

## 12. BACKLOG TÉCNICO

- [ ] Implementar schema PostgreSQL para Offline Store
- [ ] Configurar Redis para Online Store
- [ ] Criar pipeline de sincronização offline→online
- [ ] Implementar Feature Registry API
- [ ] Adicionar partitioning por timestamp
- [ ] Criar materialized views para queries frequentes
- [ ] Implementar cache hit rate monitoring
- [ ] Adicionar RBAC para feature access
- [ ] Criar backup automático de Offline Store
- [ ] Implementar feature lineage tracking

---

## 13. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secção mãe
- [[04_Data_Engineering/ESQUEMA_BASE_DADOS]] → Schema detalhado PostgreSQL
- [[32_Feature_Store/FEATURES_COMPLETAS]] → Catálogo de features específicas
- [[32_Feature_Store/GESTAO_VERSOES]] → Gestão de versões de features
- [[32_Feature_Store/COMPUTACAO_FEATURES]] → Pipeline de computação
- [[32_Feature_Store/SERVICO_FEATURES]] → API de serviço de features
- [[32_Feature_Store/MONITORIZACAO_FEATURES]] → Monitorização de qualidade
- [[32_Feature_Store/INTEGRACAO_ML]] → Integração com ML models
- [[05_Machine_Learning/INDEX]] → Consumidores das features