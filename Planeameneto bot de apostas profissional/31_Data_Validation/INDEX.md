# 31_Data_Validation — INDEX

**ID:** `SEC-31` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar sistema de validação de dados para garantir que os dados que alimentam o sistema são corretos, completos, e temporalmente válidos. Um modelo quantitativo é tão bom quanto os seus dados - erro de dados é pior que erro de modelo.

---

## 2. PRINCÍPIOS DE VALIDAÇÃO

### 2.1 Regras de Ouro

1. **Nunca assuma que dados estão corretos** - Valide sempre
2. **Nunca processe dados não validados** - Pipeline deve falhar se qualidade < threshold
3. **Sempre documentar violações** - Log detalhado de todas as violações
4. **Sempre alertar em tempo real** - Notificar equipa se qualidade degrada
5. **Sempre ter plano B** - Fallback para dados alternativos se primary falha

### 2.2 Dimensões de Qualidade

| Dimensão | Definição | Threshold |
|----------|-----------|-----------|
| **Completude** | % de valores não-null | > 95% |
| **Consistência** | Valores dentro de ranges esperados | > 95% |
| **Validade Temporal** | Timestamps não são futuros | 100% |
| **Unicidade** | Sem duplicados (game_id único) | 100% |
| **Atualidade** | Dados não são stale (> 24h) | > 99% |

---

## 3. FRAMEWORK DE VALIDAÇÃO

### 3.1 Great Expectations

**Library:** Great Expectations (GX)

**Por que Great Expectations?**
- Declarativo (regras em YAML/Python)
- Integrável com Pandas
- Auto-documentação (data docs)
- Suporte para multiple data sources

**Instalação:**
```bash
pip install great-expectations
```

### 3.2 Configuração Inicial

```bash
# Inicializar Great Expectations
great_expectations init

# Isso cria estrutura:
# great_expectations/
#   ├── great_expectations.yml
#   ├── expectations/
#   ├── plugins/
#   ├── uncommitted/
#   │   ├── data_docs/
#   │   └── expectations/
```

---

## 4. SUITES DE EXPECTATIVAS

### 4.1 Suite 1: Bronze (Raw Data)

**Objetivo:** Validar dados brutos após ingestão

```python
# expectations/bronze_games_expectations.py
from great_expectations.core.batch import RuntimeBatch
from great_expectations.core.expectation_suite import ExpectationSuite

def create_bronze_games_suite():
    suite = ExpectationSuite(name="bronze_games_suite")
    
    # Expectativa 1: game_id é único
    suite.add_expectation(
        "expect_column_values_to_be_unique",
        column="game_id"
    )
    
    # Expectativa 2: game_date não é null
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="game_date"
    )
    
    # Expectativa 3: game_date não é futuro
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="game_date",
        min_value="2020-01-01",
        max_value="2026-12-31"
    )
    
    # Expectativa 4: home_team e away_team não são null
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="home_team"
    )
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="away_team"
    )
    
    # Expectativa 5: home_score e away_score são >= 0
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="home_score",
        min_value=0,
        max_value=200
    )
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="away_score",
        min_value=0,
        max_value=200
    )
    
    # Expectativa 6: season é um dos valores esperados
    suite.add_expectation(
        "expect_column_values_to_be_in_set",
        column="season",
        value_set=["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
    )
    
    return suite
```

### 4.2 Suite 2: Silver (Clean Data)

**Objetivo:** Validar dados após limpeza e transformação

```python
# expectations/silver_games_expectations.py
def create_silver_games_suite():
    suite = ExpectationSuite(name="silver_games_suite")
    
    # Expectativa 1: Não há duplicados
    suite.add_expectation(
        "expect_table_row_count_to_equal_other_table",
        table_name="silver.games_clean",
        other_table_name="bronze.raw_games"
    )
    
    # Expectativa 2: Todos os jogos têm odds
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="home_odds"
    )
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="away_odds"
    )
    
    # Expectativa 3: Odds estão em range razoável
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="home_odds",
        min_value=1.01,
        max_value=10.0
    )
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="away_odds",
        min_value=1.01,
        max_value=10.0
    )
    
    # Expectativa 4: Overround é < 10%
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="overround",
        min_value=0,
        max_value=0.10
    )
    
    return suite
```

### 4.3 Suite 3: Gold (Features)

**Objetivo:** Validar features calculadas

```python
# expectations/gold_features_expectations.py
def create_gold_features_suite():
    suite = ExpectationSuite(name="gold_features_suite")
    
    # Expectativa 1: Não há valores null em features críticas
    critical_features = [
        "feat_team_form_win_rate",
        "feat_market_implied_prob",
        "feat_context_rest_days",
        "feat_players_minutes_projected"
    ]
    
    for feature in critical_features:
        suite.add_expectation(
            "expect_column_values_to_not_be_null",
            column=feature
        )
    
    # Expectativa 2: Features numéricas estão em range
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="feat_team_form_win_rate",
        min_value=0,
        max_value=1
    )
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="feat_market_implied_prob",
        min_value=0,
        max_value=1
    )
    
    # Expectativa 3: Target não é null
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="target"
    )
    
    # Expectativa 4: Target é 0 ou 1
    suite.add_expectation(
        "expect_column_values_to_be_in_set",
        column="target",
        value_set=[0, 1]
    )
    
    return suite
```

---

## 5. PIPELINE DE VALIDAÇÃO

### 5.1 Validação Após Ingestão

```python
# app/validation/pipeline.py
from great_expectations import DataContext
from great_expectations.checkpoint.actions import ValidationAction
import logging

logger = logging.getLogger(__name__)

class ValidationPipeline:
    def __init__(self):
        self.context = DataContext()
    
    def validate_bronze(self, df, table_name="bronze.raw_games"):
        """Valida dados bronze"""
        suite = create_bronze_games_suite()
        
        batch = RuntimeBatch.from_dataframe(df, table_name)
        
        results = self.context.run_validation_operator(
            batch=batch,
            expectation_suite=suite,
            run_name="bronze_validation"
        )
        
        if not results.success:
            logger.error(f"Validação bronze falhou: {results}")
            self._handle_validation_failure(results)
            return False
        
        logger.info(f"Validação bronze passou: {results.statistics}")
        return True
    
    def validate_silver(self, df, table_name="silver.games_clean"):
        """Valida dados silver"""
        suite = create_silver_games_suite()
        
        batch = RuntimeBatch.from_dataframe(df, table_name)
        
        results = self.context.run_validation_operator(
            batch=batch,
            expectation_suite=suite,
            run_name="silver_validation"
        )
        
        if not results.success:
            logger.error(f"Validação silver falhou: {results}")
            self._handle_validation_failure(results)
            return False
        
        logger.info(f"Validação silver passou: {results.statistics}")
        return True
    
    def validate_gold(self, df, table_name="gold.features"):
        """Valida features gold"""
        suite = create_gold_features_suite()
        
        batch = RuntimeBatch.from_dataframe(df, table_name)
        
        results = self.context.run_validation_operator(
            batch=batch,
            expectation_suite=suite,
            run_name="gold_validation"
        )
        
        if not results.success:
            logger.error(f"Validação gold falhou: {results}")
            self._handle_validation_failure(results)
            return False
        
        logger.info(f"Validação gold passou: {results.statistics}")
        return True
    
    def _handle_validation_failure(self, results):
        """Handle falha de validação"""
        # Log detalhes
        for result in results.run_results:
            if not result.success:
                logger.error(f"Expectation falhou: {result.expectation_config}")
        
        # Enviar alerta
        send_alert(
            severity="HIGH",
            message="Validação de dados falhou",
            details=str(results.statistics)
        )
        
        # Pausar pipeline se crítico
        if results.statistics["unsuccessful_percent"] > 0.10:
            pause_pipeline("validation_failed")
```

### 5.2 Integração com Pipeline ETL

```python
# app/data_engineering/ingest.py
from app.validation.pipeline import ValidationPipeline

def ingest_and_validate():
    """Ingesta dados e valida"""
    validator = ValidationPipeline()
    
    # 1. Ingerir dados
    df = ingest_nba_data()
    
    # 2. Validar bronze
    if not validator.validate_bronze(df):
        raise ValueError("Validação bronze falhou, abortando ingestão")
    
    # 3. Salvar no bronze
    save_to_bronze(df)
    
    # 4. Limpar e transformar
    df_clean = clean_and_transform(df)
    
    # 5. Validar silver
    if not validator.validate_silver(df_clean):
        raise ValueError("Validação silver falhou, abortando transformação")
    
    # 6. Salvar no silver
    save_to_silver(df_clean)
    
    # 7. Calcular features
    df_features = calculate_features(df_clean)
    
    # 8. Validar gold
    if not validator.validate_gold(df_features):
        raise ValueError("Validação gold falhou, abortando feature engineering")
    
    # 9. Salvar no gold
    save_to_gold(df_features)
    
    logger.info("Pipeline ETL completado com validação bem-sucedida")
```

---

## 6. MONITORIZAÇÃO DE QUALIDADE DE DADOS

### 6.1 Métricas

| Métrica | Descrição | Target |
|---------|-----------|--------|
| **Validação Pass Rate** | % de validações que passam | > 95% |
| **Null Rate** | % de valores null | < 5% |
| **Duplicate Rate** | % de duplicados | 0% |
| **Stale Data Rate** | % de dados > 24h | < 1% |
| **Range Violation Rate** | % de valores fora de range | < 5% |

### 6.2 Dashboard Grafana

**Painel: Data Quality**

**Gráficos:**
- Validation Pass Rate (últimos 30 dias)
- Null Rate por tabela (bronze, silver, gold)
- Duplicate Rate por tabela
- Stale Data Rate
- Range Violation Rate
- Tempo de validação (ms)

**Alertas:**
- Se Validation Pass Rate < 90% (HIGH)
- Se Null Rate > 10% (HIGH)
- Se Stale Data Rate > 5% (CRITICAL)

---

## 7. LATE ARRIVING DATA

### 7.1 Problema

Dados podem chegar atrasados (ex: jogo adiado, estatísticas atualizadas tarde). Se não tratados, podem causar leakage temporal.

### 7.2 Solução

**Timestamps:**
- `ingested_at` - Quando dado foi ingerido
- `game_date` - Data do jogo
- `last_updated_at` - Última atualização

**Validação:**
```python
# Verificar se há late arriving data
def check_late_arriving_data():
    query = """
    SELECT game_id, game_date, ingested_at, last_updated_at
    FROM bronze.raw_games
    WHERE last_updated_at > ingested_at + INTERVAL '1 hour'
    """
    
    late_arrivals = execute_query(query)
    
    if late_arrivals:
        logger.warning(f"Encontrados {len(late_arrivals)} jogos com late arriving data")
        # Re-processar esses jogos
        for game in late_arrivals:
            reprocess_game(game['game_id'])
```

---

## 8. RECONCILIAÇÃO DE DADOS

### 8.1 Verificação de Contagens

```python
def verify_row_counts():
    """Verifica se contagens de linhas são consistentes"""
    
    bronze_count = count_rows("bronze.raw_games")
    silver_count = count_rows("silver.games_clean")
    gold_count = count_rows("gold.features")
    
    # Bronze e Silver devem ter mesma contagem
    if bronze_count != silver_count:
        logger.error(f"Bronze ({bronze_count}) != Silver ({silver_count})")
        send_alert("Row count mismatch between bronze and silver")
    
    # Gold deve ter mesma contagem
    if silver_count != gold_count:
        logger.error(f"Silver ({silver_count}) != Gold ({gold_count})")
        send_alert("Row count mismatch between silver and gold")
    
    return {
        "bronze": bronze_count,
        "silver": silver_count,
        "gold": gold_count
    }
```

---

## 9. BACKLOG DE VALIDAÇÃO

- [ ] Configurar Great Expectations
- [ ] Criar suites de expectativas para bronze
- [ ] Criar suites de expectativas para silver
- [ ] Criar suites de expectativas para gold
- [ ] Implementar pipeline de validação
- [ ] Integrar com pipeline ETL
- [ ] Configurar monitorização de qualidade
- [ ] Implementar late arriving data detection
- [ ] Implementar reconciliação de contagens
- [ ] Criar dashboard de qualidade de dados

---

## 10. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[04_Data_Engineering/INDEX]] → Pipeline de dados
- [[10_Monitoring/INDEX]] → Monitorização e alertas
- [[48_Data_Drift/INDEX]] → Deteção de drift
