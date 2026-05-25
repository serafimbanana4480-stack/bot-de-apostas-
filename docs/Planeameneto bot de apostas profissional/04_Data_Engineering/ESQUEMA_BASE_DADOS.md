# ESQUEMA_BASE_DADOS — Visão Conceptual

**ID:** `DE-002` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir a arquitetura conceptual da base de dados que suporta todo o sistema de apostas desportivas. O schema deve ser desenhado para suportar ingestão contínua de dados de múltiplas fontes, transformação progressiva através de camadas de qualidade (Bronze → Silver → Gold), e query eficiente para treino de modelos, backtesting e operação em tempo real. O objetivo não é apenas armazenar dados, mas criar uma estrutura que facilite análise, traceabilidade e qualidade consistente.

---

## 2. PRINCÍPIOS DO SCHEMA

### 2.1 Tudo Tem Timestamp

Cada registo deve ter dois timestamps explícitos:
- **created_at:** Quando o registo foi criado/ingressado no sistema
- **valid_at:** Quando os dados eram válidos no mundo real (ex: data do jogo)

Isto permite:
- Rastrear quando dados foram ingeridos (debugging de ingestão)
- Recriar o estado do sistema em qualquer momento no passado (time travel)
- Detectar dados stale ou desatualizados
- Audit trail completo de todas as alterações

### 2.2 Never Delete (Imutabilidade de Dados Raw)

Dados na camada Bronze (raw) nunca são apagados. Correções são implementadas como novos registos, não como atualizações. Isto garante:
- Preservação histórica completa
- Capacidade de reprocessar dados com novas regras
- Debugging de problemas históricos
- Compliance e auditoria

Apenas camadas derivadas (Silver, Gold) podem ter dados substituídos, mas mesmo assim através de operações append-only com versionamento.

### 2.3 Imutabilidade Pós-Processamento

Tabelas Silver (limpas) e Gold (features) são append-only. Quando dados são atualizados, novos registos são adicionados em vez de modificar existentes. Isto permite:
- Reproduzibilidade de experimentos (sempre usar mesma versão de dados)
- Rollback fácil (reverter para versão anterior)
- Comparação entre versões (A/B testing de features)
- Audit trail completo de transformações

### 2.4 Chaves Naturais

Usar identificadores naturais do domínio como chaves primárias em vez de chaves sintéticas auto-incrementadas:
- game_id da NBA API em vez de id auto-incrementado
- team_id da NBA API em vez de id auto-incrementado

Isto facilita:
- Integração com fontes externas
- Debugging (IDs são reconhecíveis)
- Join com dados externos
- Evita ambiguidade entre sistemas

---

## 3. ARQUITETURA EM CAMADAS

### 3.1 Camada Bronze (Raw)

**Propósito:** Armazenar dados exatamente como recebidos das fontes externas, sem qualquer transformação além de parsing básico.

**Características:**
- Dados não estruturados ou semi-estruturados
- Preservação completa de dados originais
- Alta granularidade temporal (todos os updates)
- Prefixo de tabela: `raw_`

**Tabelas típicas:**
- `raw_nba_games`: Dados brutos da NBA API
- `raw_odds_betfair`: Odds brutas da Betfair
- `raw_stats_basketball_reference`: Estatísticas do Basketball-Reference
- `raw_injuries_espn`: Lesões do ESPN

**Regras:**
- Nunca modificar dados existentes
- Adicionar novos registos para updates
- Manter todos os campos originais, mesmo redundantes
- Incluir metadados de ingestão (source, timestamp, status)

---

### 3.2 Camada Silver (Clean)

**Propósito:** Dados limpos, deduplicados e validados, prontos para consumo por downstream.

**Características:**
- Estrutura consistente e normalizada
- Dados deduplicados (entidades únicas)
- Validações aplicadas e violações corrigidas
- Prefixo de tabela: `clean_`

**Tabelas típicas:**
- `clean_games`: Jogos únicos e validados
- `clean_teams`: Equipas normalizadas
- `clean_odds`: Odds deduplicadas e validadas
- `clean_injuries`: Lesões normalizadas

**Regras:**
- Aplicar todas as regras de deduplicação e limpeza
- Normalizar identificadores (ex: nomes de equipas para team_id)
- Validar ranges e tipos de dados
- Manter versão dos dados (append-only)

---

### 3.3 Camada Gold (Features)

**Propósito:** Features de machine learning calculadas e prontas para treino de modelos.

**Características:**
- Features pré-calculadas e otimizadas para query
- Agregações temporais já aplicadas
- Normalizações e transformações aplicadas
- Prefixo de tabela: `feat_`

**Tabelas típicas:**
- `feat_team_form`: Forma recente de equipas
- `feat_market_metrics`: Métricas de mercado
- `feat_game_context`: Contexto do jogo
- `feat_interactions`: Interações não-lineares entre features

**Regras:**
- Features calculadas deterministicamente
- Lineage documentado (origem de cada feature)
- Versionamento explícito (feat_v1, feat_v2, etc.)
- Otimizadas para leitura (índices apropriados)

---

### 3.4 Camada Meta (Sistema)

**Propósito:** Metadados sobre o próprio sistema — execuções de pipelines, status de jobs, métricas de qualidade.

**Características:**
- Dados operacionais e administrativos
- Alta frequência de escrita
- Queries de monitorização e alerting
- Prefixo de tabela: `meta_`

**Tabelas típicas:**
- `meta_pipeline_runs`: Histórico de execuções de pipelines
- `meta_data_quality`: Métricas de qualidade de dados
- `meta_model_versions`: Versões de modelos em produção
- `meta_alerts`: Histórico de alertas gerados

---

### 3.5 Camada Audit

**Propósito:** Registo completo de todas as correções, modificações e ações manuais no sistema.

**Características:**
- Imutável (append-only)
- Alta granularidade (cada ação registada)
- Query interface para investigação
- Prefixo de tabela: `audit_`

**Tabelas típicas:**
- `audit_corrections`: Correções de dados aplicadas
- `audit_model_updates`: Atualizações de modelos
- `audit_manual_interventions`: Intervenções manuais de operadores
- `audit_access_logs`: Logs de acesso e permissões

---

## 4. DIAGRAMA ENTIDADE-RELACÃO (Simplificado)

```
+----------------+       +------------------+       +-------------------+
|  games         |<----- |  team_stats      |       |  player_injuries  |
+----------------+       +------------------+       +-------------------+
| game_id (PK)   |       | game_id (FK)     |       | player_id (FK)    |
| season         |       | team_id (FK)     |       | date               |
| date           |       | stat_type        |       | status             |
| home_team      |       | value            |       | description        |
| away_team      |       +------------------+       +-------------------+
| home_score     |                ^
| away_score     |                |
| status         |       +------------------+
| created_at     |       |  odds_history    |
| valid_at       |       +------------------+
+----------------+       | game_id (FK)     |
       ^             | market           |
       |             | bookmaker        |
       |             | odd              |
       |             | timestamp        |
       |             +------------------+
       |
+----------------+
|  schedules     |
+----------------+
| team_id (FK)   |
| date           |
| is_home        |
| rest_days      |
| b2b_flag       |
| created_at     |
| valid_at       |
+----------------+
```

**Relações Principais:**
- **games → team_stats:** Um jogo tem múltiplas estatísticas (por equipa, por tipo)
- **games → odds_history:** Um jogo tem histórico de odds (por mercado, por bookmaker)
- **games → player_injuries:** Um jogo tem múltiplos status de lesão (por jogador)
- **games → schedules:** Um jogo tem agendamento (rest days, back-to-back flags)

---

## 5. CONVENÇÕES DE NOMENCLATURA

### 5.1 Prefixos de Camada

| Camada | Prefixo | Exemplo | Propósito |
|--------|---------|---------|-----------|
| Bronze (Raw) | `raw_` | raw_nba_games | Dados brutos não transformados |
| Silver (Clean) | `clean_` | clean_games | Dados limpos e validados |
| Gold (Features) | `feat_` | feat_team_form | Features de ML pré-calculadas |
| Meta (Sistema) | `meta_` | meta_pipeline_runs | Metadados operacionais |
| Audit | `audit_` | audit_corrections | Registo de correções e ações |

### 5.2 Convenções de Colunas

- **IDs:** Usar `_id` sufixo (ex: game_id, team_id, player_id)
- **Timestamps:** Usar `_at` sufixo (ex: created_at, valid_at, updated_at)
- **Flags Booleanos:** Usar `_flag` sufixo (ex: b2b_flag, is_home)
- **Percentagens:** Usar `%` sufixo (ex: eFG%, ORB%)
- **Contadores:** Usar `_count` ou `_num` sufixo (ex: loss_streak_count)

### 5.3 Convenções de Nomes de Tabelas

- Singular (ex: game, não games)
- Snake_case (ex: team_stats, não TeamStats)
- Descritivo (ex: player_injuries_recent, não injuries)
- Sem abreviações não-óbvias (ex: offensive_rebound_pct, não ORB%)

---

## 6. ÍNDICES CRÍTICOS

### 6.1 Índices para Performance de Queries de Treino

Queries de treino de modelos tipicamente precisam de:
- Filtrar por data (ex: jogos dos últimos 12 meses)
- Filtrar por season (ex: temporada 2023-24)
- Join com estatísticas de equipa
- Join com odds históricas

**Índices necessários:**
```sql
-- Filtragem eficiente por data e season
CREATE INDEX idx_games_date ON clean_games(date);
CREATE INDEX idx_games_season ON clean_games(season);

-- Join eficiente com estatísticas
CREATE INDEX idx_team_stats_game ON clean_team_stats(game_id, team_id);

-- Join eficiente com odds
CREATE INDEX idx_odds_game_market ON clean_odds(game_id, market, timestamp);
```

### 6.2 Índices para Backtest Queries

Queries de backtest tipicamente precisam de:
- Filtrar por time e data (trajetória de uma equipa)
- Filtrar por período específico
- Ordenação temporal estrita

**Índices necessários:**
```sql
-- Trajetórias temporais de equipas
CREATE INDEX idx_schedule_team_date ON clean_schedules(team_id, date);

-- Queries temporais ordenadas
CREATE INDEX idx_games_date_season ON clean_games(date, season);
```

### 6.3 Índices para Queries em Tempo Real

Queries em tempo real tipicamente precisam de:
- Lookup rápido por game_id
- Lookup rápido por team_id
- Últimos N registos de odds

**Índices necessários:**
```sql
-- Lookup rápido por ID
CREATE INDEX idx_games_id ON clean_games(game_id);
CREATE INDEX idx_teams_id ON clean_teams(team_id);

-- Últimas odds de um jogo
CREATE INDEX idx_odds_game_timestamp ON clean_odds(game_id, timestamp DESC);
```

---

## 7. PARTICIONAMENTO E OTIMIZAÇÃO

### 7.1 Partitioning por Season

Tabelas grandes (games, odds, stats) devem ser partitionadas por season. Isto permite:
- Queries eficientes que filtram por season (particion pruning)
- Facilita arquivamento de seasons antigas
- Permite drop rápido de seasons específicas se necessário
- Melhora performance de maintenance (vacuum, analyze)

**Implementação:**
```sql
-- Partitioning por season
CREATE TABLE clean_games (
    game_id VARCHAR(20),
    season VARCHAR(10),
    date DATE,
    -- ... outros campos
) PARTITION BY LIST (season);

-- Partitions para cada season
CREATE TABLE clean_games_2023_24 PARTITION OF clean_games
    FOR VALUES IN ('2023-24');
CREATE TABLE clean_games_2022_23 PARTITION OF clean_games
    FOR VALUES IN ('2022-23');
```

### 7.2 Compression

Para tabelas grandes, especialmente camadas Bronze e Gold, usar compression para reduzir espaço de armazenamento:
- Colunas numéricas: usar tipos mais pequenos quando possível (SMALLINT vs INTEGER)
- Colunas de texto: usar VARCHAR com comprimento apropriado
- Compression level: TOAST compression automática do PostgreSQL

### 7.3 Vacuum e Analyze

Configurar autovacuum agressivo para tabelas com alta taxa de escrita:
- Autovacuum mais frequente para tabelas de odds (alta churn)
- Analyze automático após loads大批量
- Monitorização de bloat e reindexação periódica

---

## 8. RELATIONSHIPS E INTEGRIDADE

### 8.1 Foreign Keys

Foreign keys devem ser implementados para garantir integridade referencial:
- team_stats.team_id → teams.team_id
- odds.game_id → games.game_id
- injuries.player_id → players.player_id

No entanto, considerar:
- Desabilitar FKs em camadas Bronze (dados raw podem ter referências inválidas)
- Implementar FKs apenas em camadas Silver e Gold
- Usar ON DELETE CASCADE com cautela (preferir ON DELETE RESTRICT)

### 8.2 Constraints

Implementar constraints para garantir qualidade de dados:
- CHECK constraints para ranges (ex: score >= 0)
- UNIQUE constraints para chaves naturais (ex: (game_id, market, bookmaker, timestamp))
- NOT NULL constraints para campos críticos (ex: game_id, date)

---

## 9. BACKLOG TÉCNICO

- [ ] Criar schema completo em SQL DDL (ver [[15_Database/SCHEMA_POSTGRESQL]])
- [ ] Implementar partitioning por season em tabelas principais
- [ ] Criar tabelas de audit para todas as correções
- [ ] Documentar lineage de cada campo (origem e transformações)
- [ ] Implementar views materializadas para queries frequentes
- [ ] Configurar backups automatizados com point-in-time recovery
- [ ] Implementar monitoring de performance de queries
- [ ] Criar processos de arquivamento para seasons antigas

---

## 10. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[15_Database/INDEX]] → Schema SQL completo e implementação
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Pipeline que popula estas tabelas
- [[04_Data_Engineering/DEDUPLICACAO_E_LIMPEZA]] → Regras aplicadas na camada Silver
