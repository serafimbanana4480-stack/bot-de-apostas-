# GESTAO_VERSOES — Gestão de Versões e Metadados de Features

**ID:** `FEAT-002` | **Fase:** #phase/1-6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer um sistema robusto de versionamento para features, garantindo que mudanças nas definições de features são rastreáveis, reversíveis e não quebram modelos em produção. Cada versão deve ter metadados completos e ser imutável após criação.

---

## 2. CONTEXTO

Em sistemas de machine learning, features evoluem constantemente:
- Fórmulas são melhoradas
- Janelas de tempo são ajustadas
- Fontes de dados mudam
- Bugs são corrigidos

Sem versionamento adequado:
- Modelos treinados com features antigas quebram em produção
- Impossível reproduzir resultados históricos
- Não há rastreabilidade de decisões
- Rollbacks são difíceis ou impossíveis

Em value betting, onde pequenas mudanças podem impactar significativamente a precisão das previsões, o versionamento é crítico para confiança e auditabilidade.

---

## 3. POLÍTICA DE VERSIONAMENTO

### 3.1 Quando Criar Nova Versão

**Obrigatório criar nova versão quando:**
- Fórmula de cálculo muda
- Janela de tempo (window) é alterada
- Fonte de dados muda
- Tipo de dado muda (ex: float → int)
- Lógica de tratamento de missing values muda

**Opcional (pode manter mesma versão):**
- Correção de bugs em código de ingestão (sem mudar fórmula)
- Melhorias de performance (sem mudar resultado)
- Atualização de metadados (documentação, owner)

**Exemplos:**

| Mudança | Nova Versão? | Justificação |
|---------|--------------|--------------|
| Mudar window de 5 para 10 jogos | ✅ Sim | Fórmula alterada |
| Corrigir bug em cálculo de média | ✅ Sim | Resultado alterado |
| Adicionar índice para performance | ❌ Não | Resultado inalterado |
| Mudar nome da feature | ✅ Sim | Breaking change |
| Atualizar descrição | ❌ Não | Metadado apenas |

### 3.2 Esquema de Versionamento

**Formato:** `MAJOR.MINOR` (semântico)

- **MAJOR (X.0):** Mudanças breaking que alteram significativamente o valor
  - Mudança de fórmula
  - Mudança de janela de tempo
  - Mudança de fonte de dados
  
- **MINOR (X.Y):** Mudanças não-breaking
  - Correções de bugs menores
  - Melhorias de precisão numérica
  - Adição de validações

**Exemplos:**
- `1.0` → `2.0`: Mudança de window de 5 para 10 jogos
- `1.0` → `1.1`: Correção de arredondamento
- `2.0` → `2.1`: Adição de validação de range

---

## 4. METADADOS DE FEATURES

### 4.1 Metadados Obrigatórios

Cada versão de feature deve ter:

```sql
CREATE TABLE feature_store.feature_versions (
    feature_id VARCHAR(50) NOT NULL,
    version VARCHAR(10) NOT NULL,  -- MAJOR.MINOR
    name VARCHAR(100) NOT NULL,
    description TEXT,
    data_type VARCHAR(20) NOT NULL,  -- float, int, bool, string
    category VARCHAR(50),  -- rolling, market, context, interaction
    
    -- Lógica de cálculo
    formula TEXT NOT NULL,  -- Fórmula matemática ou pseudocódigo
    transformation_logic TEXT,  -- Código de transformação detalhado
    parameters JSONB,  -- Parâmetros configuráveis (window, halflife, etc.)
    
    -- Fonte de dados
    source_tables TEXT[] NOT NULL,
    source_columns TEXT[] NOT NULL,
    source_system VARCHAR(50),  -- nba_api, odds_portal, etc.
    
    -- Timestamps
    known_at_timestamp VARCHAR(100),  -- Quando a feature era conhecida
    effective_from TIMESTAMP NOT NULL,  -- Quando esta versão tornou-se ativa
    effective_to TIMESTAMP,  -- Quando esta versão foi desativada (NULL se ativa)
    
    -- Validação
    validation_rules JSONB,  -- Regras de validação (range, not_null, etc.)
    adf_test_result VARCHAR(20),  -- Pass, Fail, N/A
    
    -- Estatísticas
    mean DOUBLE PRECISION,
    std DOUBLE PRECISION,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    missing_rate DOUBLE PRECISION,
    
    -- Gestão
    owner VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',  -- active, deprecated, experimental
    change_reason TEXT,  -- Por que esta versão foi criada
    parent_version VARCHAR(10),  -- Versão anterior (para lineage)
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(50) NOT NULL,
    
    PRIMARY KEY (feature_id, version)
);
```

### 4.2 Exemplo de Metadados Completos

```json
{
    "feature_id": "home_win_rate_decay5",
    "version": "2.0",
    "name": "Home Win Rate with Exponential Decay (Halflife=5)",
    "description": "Taxa de vitórias em casa com decaimento exponencial dos últimos 20 jogos",
    "data_type": "float",
    "category": "rolling",
    "formula": "Σ(win_i * 0.5^(i/5)) / Σ(0.5^(i/5)) para i=0..19",
    "transformation_logic": "Calcular média ponderada com pesos exponenciais onde jogos recentes têm peso maior",
    "parameters": {
        "window": 20,
        "halflife": 5,
        "min_games": 5
    },
    "source_tables": ["clean_games"],
    "source_columns": ["game_date", "home_team", "away_team", "home_score", "away_score"],
    "source_system": "nba_api",
    "known_at_timestamp": "game_date - 1 day",
    "effective_from": "2024-01-15T00:00:00Z",
    "effective_to": null,
    "validation_rules": {
        "min_value": 0.0,
        "max_value": 1.0,
        "not_null": true,
        "allowed_null_rate": 0.0
    },
    "adf_test_result": "Pass",
    "mean": 0.62,
    "std": 0.12,
    "min_value": 0.25,
    "max_value": 0.95,
    "missing_rate": 0.0,
    "owner": "joao.silva",
    "status": "active",
    "change_reason": "Mudança de window de 10 para 20 jogos para capturar tendências de longo prazo",
    "parent_version": "1.0",
    "created_at": "2024-01-15T10:30:00Z",
    "created_by": "joao.silva"
}
```

---

## 5. LINEAGE DE FEATURES

### 5.1 Propósito

Rastrear a origem de cada feature desde os dados brutos até ao valor final. Isso permite:
- Debugging de features com problemas
- Impact analysis de mudanças em fontes de dados
- Compliance e auditabilidade
- Reprodução de resultados

### 5.2 Estrutura de Lineage

```sql
CREATE TABLE feature_store.feature_lineage (
    id SERIAL PRIMARY KEY,
    feature_id VARCHAR(50) NOT NULL,
    version VARCHAR(10) NOT NULL,
    
    -- Nível 1: Feature atual
    feature_name VARCHAR(100) NOT NULL,
    
    -- Nível 2: Tabelas fonte
    source_table VARCHAR(100) NOT NULL,
    source_column VARCHAR(100) NOT NULL,
    
    -- Nível 3: Tabelas raw (se aplicável)
    raw_table VARCHAR(100),
    raw_column VARCHAR(100),
    
    -- Nível 4: Sistema externo
    external_system VARCHAR(100),
    external_endpoint VARCHAR(255),
    
    -- Relacionamento
    transformation_type VARCHAR(50),  -- aggregation, calculation, join, filter
    transformation_details TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (feature_id, version) REFERENCES feature_store.feature_versions(feature_id, version)
);
```

### 5.3 Exemplo de Lineage

```
home_win_rate_decay5 (v2.0)
  ├─→ clean_games.game_date
  │     └─→ raw_nba_games.game_date
  │           └─→ nba_api.stats.endpoints.leaguegamefinder
  │
  ├─→ clean_games.home_team
  │     └─→ raw_nba_games.home_team
  │           └─→ nba_api.stats.endpoints.leaguegamefinder
  │
  ├─→ clean_games.home_score
  │     └─→ raw_nba_games.home_score
  │           └─→ nba_api.stats.endpoints.leaguegamefinder
  │
  └─→ clean_games.away_score
        └─→ raw_nba_games.away_score
              └─→ nba_api.stats.endpoints.leaguegamefinder
```

### 5.4 API de Lineage

```python
class FeatureLineage:
    def get_lineage(self, feature_id: str, version: str) -> LineageGraph:
        """Retorna grafo completo de lineage para uma feature."""
        
    def trace_to_source(self, feature_id: str, version: str) -> SourceInfo:
        """Rastreia até à fonte de dados externa."""
        
    def get_impact_analysis(self, source_table: str) -> List[FeatureInfo]:
        """Lista todas as features impactadas por uma mudança numa fonte."""
        
    def visualize_lineage(self, feature_id: str, version: str) -> str:
        """Gera representação visual do lineage (DOT/GraphViz)."""
```

---

## 6. CICLO DE VIDA DE VERSÕES

### 6.1 Estados de Versão

```
┌─────────┐
│ DRAFT   │ ← Versão em desenvolvimento
└────┬────┘
     │
     ▼
┌─────────┐
│ TESTING │ ← Versão em teste (validação, QA)
└────┬────┘
     │
     ▼
┌─────────┐
│ ACTIVE  │ ← Versão em produção (padrão)
└────┬────┘
     │
     ▼
┌─────────┐
│DEPRECATED│ ← Versão antiga, ainda disponível para backtest
└────┬────┘
     │
     ▼
┌─────────┐
│ARCHIVED │ ← Versão arquivada (não mais acessível via API)
└─────────┘
```

### 6.2 Transições de Estado

**DRAFT → TESTING:**
- Feature implementada
- Testes unitários passando
- Pronta para validação

**TESTING → ACTIVE:**
- Validação de qualidade passou
- ADF/KPSS test passaram
- Revisão de código aprovada
- Documentação completa

**ACTIVE → DEPRECATED:**
- Nova versão criada
- Modelos atualizados para usar nova versão
- Período de grace period (ex: 30 dias)

**DEPRECATED → ARCHIVED:**
- Nenhum modelo usando esta versão
- Mais de 90 dias desde deprecation
- Backup criado antes de arquivar

### 6.3 Política de Manutenção

- **Versões ativas:** Mantidas em produção
- **Versões deprecated:** Disponíveis para backtest por 90 dias
- **Versões archived:** Removidas de Online Store, mantidas em Offline Store com flag
- **Versões experimentais:** Prefixo `exp_`, não usadas em produção

---

## 7. MIGRAÇÃO ENTRE VERSÕES

### 7.1 Estratégia de Rollout

**Blue-Green Deployment:**
```python
def rollout_new_version(feature_id: str, new_version: str):
    """
    Implementa nova versão sem downtime.
    """
    # 1. Validar nova versão
    validate_feature_version(feature_id, new_version)
    
    # 2. Calcular features com nova versão em background
    compute_features_async(feature_id, new_version)
    
    # 3. Atualizar metadados (versão ativa ainda é a antiga)
    update_metadata(feature_id, new_version, status='testing')
    
    # 4. Atualizar modelos para usar nova versão (gradual)
    for model in get_models_using_feature(feature_id):
        update_model_config(model, feature_id, new_version)
    
    # 5. Monitorizar performance por 7 dias
    monitor_rollback_window(feature_id, new_version, days=7)
    
    # 6. Se OK, marcar versão antiga como deprecated
    if performance_ok:
        deprecate_version(feature_id, old_version)
    else:
        rollback_to_old_version(feature_id, old_version)
```

### 7.2 Rollback

```python
def rollback_version(feature_id: str, from_version: str, to_version: str):
    """
    Reverte para versão anterior em caso de problemas.
    """
    # 1. Parar computação da nova versão
    stop_feature_computation(feature_id, from_version)
    
    # 2. Restaurar versão antiga como ativa
    set_active_version(feature_id, to_version)
    
    # 3. Reverter configurações de modelos
    for model in get_models_using_feature(feature_id):
        update_model_config(model, feature_id, to_version)
    
    # 4. Marcar nova versão como experimental
    update_metadata(feature_id, from_version, status='experimental')
    
    # 5. Log rollback para análise
    log_rollback(feature_id, from_version, to_version, reason)
```

---

## 8. COMPARAÇÃO DE VERSÕES

### 8.1 Diff de Versões

```python
def compare_versions(feature_id: str, version_a: str, version_b: str) -> VersionDiff:
    """
    Compara duas versões de uma feature.
    """
    meta_a = get_feature_metadata(feature_id, version_a)
    meta_b = get_feature_metadata(feature_id, version_b)
    
    return {
        "formula_changed": meta_a.formula != meta_b.formula,
        "parameters_changed": meta_a.parameters != meta_b.parameters,
        "source_changed": meta_a.source_tables != meta_b.source_tables,
        "window_changed": meta_a.parameters.window != meta_b.parameters.window,
        "performance_impact": estimate_performance_impact(meta_a, meta_b),
        "breaking_change": is_breaking_change(meta_a, meta_b)
    }
```

### 8.2 Análise de Impacto

```python
def assess_impact(feature_id: str, new_version: str) -> ImpactReport:
    """
    Avalia impacto de mudança de versão em modelos e sistemas.
    """
    affected_models = get_models_using_feature(feature_id)
    affected_pipelines = get_pipelines_using_feature(feature_id)
    
    # Estimar mudança na distribuição
    old_dist = get_distribution(feature_id, current_version)
    new_dist = get_distribution(feature_id, new_version)
    distribution_shift = calculate_kl_divergence(old_dist, new_dist)
    
    return {
        "affected_models": len(affected_models),
        "affected_pipelines": len(affected_pipelines),
        "distribution_shift": distribution_shift,
        "risk_level": "HIGH" if distribution_shift > 0.3 else "MEDIUM" if distribution_shift > 0.1 else "LOW",
        "recommendation": get_recommendation(distribution_shift)
    }
```

---

## 9. TAGS E CLASSIFICAÇÃO

### 9.1 Sistema de Tags

Tags permitem organizar e filtrar features:

```sql
CREATE TABLE feature_store.feature_tags (
    feature_id VARCHAR(50) NOT NULL,
    version VARCHAR(10) NOT NULL,
    tag VARCHAR(50) NOT NULL,
    tag_value VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (feature_id, version, tag),
    FOREIGN KEY (feature_id, version) REFERENCES feature_store.feature_versions(feature_id, version)
);
```

**Tags padrão:**
- `category`: rolling, market, context, interaction
- `stability`: stable, experimental, volatile
- `computation_cost`: low, medium, high
- `latency_requirement`: real_time, batch, offline
- `domain`: offense, defense, scheduling, market
- `importance`: critical, high, medium, low

**Exemplos:**
```sql
INSERT INTO feature_store.feature_tags VALUES
('home_win_rate_decay5', '2.0', 'category', 'rolling'),
('home_win_rate_decay5', '2.0', 'stability', 'stable'),
('home_win_rate_decay5', '2.0', 'computation_cost', 'medium'),
('home_win_rate_decay5', '2.0', 'domain', 'offense'),
('home_win_rate_decay5', '2.0', 'importance', 'high');
```

### 9.2 Busca por Tags

```python
def search_features(tags: Dict[str, str]) -> List[FeatureInfo]:
    """
    Busca features por tags.
    """
    query = """
        SELECT DISTINCT f.feature_id, f.version, f.name
        FROM feature_store.feature_versions f
        JOIN feature_store.feature_tags t ON f.feature_id = t.feature_id AND f.version = t.version
        WHERE 1=1
    """
    
    for tag, value in tags.items():
        query += f" AND (t.tag = '{tag}' AND t.tag_value = '{value}')"
    
    return execute_query(query)
```

---

## 10. AUDITORIA E COMPLIANCE

### 10.1 Audit Log

```sql
CREATE TABLE feature_store.audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- create, update, deprecate, archive
    feature_id VARCHAR(50),
    version VARCHAR(10),
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    ip_address INET,
    user_agent TEXT
);
```

**Ações auditadas:**
- Criação de nova versão
- Mudança de status
- Atualização de metadados
- Deprecation/Archival
- Acesso a features sensíveis

### 10.2 Relatórios de Compliance

```python
def generate_compliance_report(date_range: DateRange) -> ComplianceReport:
    """
    Gera relatório de compliance para auditoria.
    """
    return {
        "total_versions_created": count_versions_created(date_range),
        "versions_deprecated": count_versions_deprecated(date_range),
        "unauthorized_changes": detect_unauthorized_changes(date_range),
        "feature_lineage_coverage": calculate_lineage_coverage(),
        "documentation_completeness": calculate_doc_completeness(),
        "validation_failures": get_validation_failures(date_range)
    }
```

---

## 11. BOAS PRÁTICAS

### 11.1 Documentação

- **Sempre documentar o "porquê"** da mudança, não apenas o "o quê"
- **Manter changelog** para cada feature
- **Exemplos de uso** para versões complexas
- **Referências** a papers ou documentação externa

### 11.2 Validação

- **Testar nova versão** em ambiente de staging
- **Comparar distribuições** entre versões
- **Validar em backtest** antes de produção
- **Monitorizar** após rollout

### 11.3 Comunicação

- **Notificar stakeholders** antes de mudanças breaking
- **Documentar impactos** em modelos dependentes
- **Fornecer timeline** de migração
- **Disponibilizar suporte** durante transição

---

## 12. FERRAMENTAS E AUTOMAÇÃO

### 12.1 CLI de Gestão de Versões

```python
# Exemplo de CLI
$ feature version create home_win_rate_decay5 \
    --version 2.0 \
    --formula "Σ(win_i * 0.5^(i/5)) / Σ(0.5^(i/5))" \
    --window 20 \
    --halflife 5 \
    --reason "Mudança de window para capturar tendências de longo prazo"

$ feature version list home_win_rate_decay5
ID: home_win_rate_decay5
  v1.0 (deprecated) - 2023-06-01 to 2024-01-14
  v2.0 (active)    - 2024-01-15 to present

$ feature version compare home_win_rate_decay5 1.0 2.0
Formula changed: Yes
Window changed: 10 → 20
Distribution shift: 0.15 (MEDIUM)
Breaking change: Yes
```

### 12.2 Web UI

Dashboard para:
- Visualizar todas as versões de uma feature
- Comparar versões side-by-side
- Ver lineage visual
- Gerir tags e metadados
- Aprovar/rejeitar mudanças

---

## 13. BACKLOG TÉCNICO

- [ ] Implementar schema de feature_versions
- [ ] Criar sistema de lineage tracking
- [ ] Desenvolver CLI de gestão de versões
- [ ] Implementar pipeline de validação de versões
- [ ] Criar dashboard de comparação de versões
- [ ] Implementar sistema de tags
- [ ] Adicionar audit logging
- [ ] Desenvolver ferramenta de impacto analysis
- [ ] Criar relatórios de compliance
- [ ] Implementar rollback automático
- [ ] Adicionar integração com Git (versionar metadados)

---

## 14. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secção mãe
- [[32_Feature_Store/ARQUITETURA_FEATURE_STORE]] → Arquitetura geral
- [[32_Feature_Store/FEATURES_COMPLETAS]] → Catálogo de features específicas
- [[32_Feature_Store/COMPUTACAO_FEATURES]] → Pipeline de computação
- [[04_Data_Engineering/SCHEMA_EVOLUTION]] → Evolução de schema de dados
- [[31_Data_Validation/INDEX]] → Validação de qualidade de dados
- [[05_Machine_Learning/INDEX]] → Modelos que consomem features