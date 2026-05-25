# GREAT_EXPECTATIONS — Implementação de Validação de Dados

**ID:** `VAL-006` | **Fase:** #phase/4 | **Owner:** Data Engineer | **Status:** #status/in_progress

---

## 1. OBJETIVO

Definir a implementação técnica de Great Expectations como framework de validação de dados para o pipeline de value betting. Great Expectations permite definir, testar e documentar expectativas de qualidade de dados de forma automatizada e reutilizável.

---

## 2. CONTEXTO

Great Expectations é um framework open-source para validação de dados que:
- Permite definir expectativas (regras) de forma declarativa
- Gera documentação automática de qualidade de dados
- Integra-se com pipelines de dados (Prefect, Airflow)
- Fornece dashboards interativos de validação
- Suporta versionamento de suites de expectativas

A implementação de Great Expectations complementa as regras de qualidade definidas em [[VAL-005_REGRAS_QUALIDADE]].

---

## 3. ARQUITETURA

### 3.1. Componentes Principais

**Data Context:**
- Ponto de entrada principal do Great Expectations
- Gerencia configurações, datasources e suites
- Localização: `great_expectations/`

**Expectation Suites:**
- Coleções de expectativas para um dataset específico
- Cada tabela tem sua própria suite
- Armazenadas em `great_expectations/expectations/`

**Validation Results:**
- Resultados da validação de um batch
- Incluem estatísticas e detalhes de falhas
- Armazenados em `great_expectations/uncommitted/`

**Data Docs:**
- Documentação HTML gerada automaticamente
- Inclui expectativas, resultados e estatísticas
- Acessível via browser

### 3.2. Estrutura de Diretórios

```
great_expectations/
├── great_expectations.yml          # Configuração principal
├── expectations/                   # Suites de expectativas
│   ├── games_suite.json
│   ├── odds_suite.json
│   ├── player_stats_suite.json
│   ├── team_stats_suite.json
│   ├── features_suite.json
│   └── predictions_suite.json
├── plugins/                        # Plugins customizados
├── uncommitted/                    # Resultados de validação
│   ├── validations/
│   └── data_docs/
└── checkpoints/                    # Checkpoints para validação
    ├── games_checkpoint.yml
    ├── odds_checkpoint.yml
    └── ...
```

---

## 4. CONFIGURAÇÃO

### 4.1. Inicialização

**Instalação:**
```bash
pip install great_expectations
```

**Inicialização do projeto:**
```bash
cd /path/to/project
great_expectations init
```

**Configuração do Data Context:**
- Escolher "I want to use a SQL database for my data"
- Configurar conexão com PostgreSQL
- Definir localização de dados docs

### 4.2. Configuração de Datasources

**PostgreSQL Datasource:**
- Conexão com database de betting
- Schema: `betting_data`
- Tabelas: games, odds, player_stats, team_stats, features, predictions

**Configuração em `great_expectations.yml`:**
```yaml
datasources:
  betting_postgres:
    class_name: SqlAlchemyDatasource
    execution_engine:
      class_name: SqlAlchemyExecutionEngine
      connection_string: postgresql://user:pass@localhost:5432/betting_db
    data_connectors:
      betting_data:
        class_name: RuntimeDataConnector
        batch_identifiers:
          - batch_id
```

### 4.3. Configuração de Stores

**Expectations Store:**
- Local: Sistema de ficheiros
- Caminho: `expectations/`
- Formato: JSON

**Validations Store:**
- Local: Sistema de ficheiros
- Caminho: `uncommitted/validations/`
- Formato: JSON

**Data Docs Store:**
- Local: Sistema de ficheiros
- Caminho: `uncommitted/data_docs/`
- Formato: HTML

---

## 5. SUITES DE EXPECTATIVAS

### 5.1. Suite de Jogos (games_suite)

**Expectativas principais:**
- game_id: não null, único
- game_date: não null, não futuro (para jogos finished)
- home_team_id: não null, ≠ away_team_id
- away_team_id: não null
- status: em conjunto válido
- home_score: ≥ 0, ≤ 200 (se não null)
- away_score: ≥ 0, ≤ 200 (se não null)

**Implementação:**
```python
validator.expect_column_values_to_not_be_null("game_id")
validator.expect_column_values_to_be_unique("game_id")
validator.expect_column_values_to_not_be_null("game_date")
validator.expect_column_values_to_not_be_null("home_team_id")
validator.expect_column_values_to_not_be_null("away_team_id")
validator.expect_column_values_to_not_match_regex("home_team_id", away_team_id)
validator.expect_column_values_to_be_in_set("status", ["scheduled", "in_progress", "finished", "postponed", "cancelled"])
validator.expect_column_values_to_be_between("home_score", min_value=0, max_value=200)
validator.expect_column_values_to_be_between("away_score", min_value=0, max_value=200)
```

### 5.2. Suite de Odds (odds_suite)

**Expectativas principais:**
- market_id: não null, formato válido
- selection_id: não null, formato válido
- odd: não null, > 1.0, < 1000.0
- timestamp: não null, ≤ now, < game_date + 2h
- market: em conjunto válido

**Implementação:**
```python
validator.expect_column_values_to_not_be_null("market_id")
validator.expect_column_values_to_match_regex("market_id", r"^\d+\.\d+$")
validator.expect_column_values_to_not_be_null("selection_id")
validator.expect_column_values_to_match_regex("selection_id", r"^\d+$")
validator.expect_column_values_to_not_be_null("odd")
validator.expect_column_values_to_be_between("odd", min_value=1.01, max_value=1000.0)
validator.expect_column_values_to_not_be_null("timestamp")
validator.expect_column_values_to_be_between("timestamp", max_value="now")
validator.expect_column_values_to_be_in_set("market", ["moneyline_home", "moneyline_away", "spread_home", "spread_away", "total_over", "total_under"])
```

### 5.3. Suite de Estatísticas de Jogadores (player_stats_suite)

**Expectativas principais:**
- player_id: não null, existe na tabela de jogadores
- game_id: não null, existe na tabela de jogos
- team_id: não null, ∈ {home_team_id, away_team_id}
- minutes_played: ∈ [0, 48]
- field_goals_made ≤ field_goals_attempted
- field_goal_percentage: ∈ [0.0, 1.0]
- points: ∈ [0, 100]

**Implementação:**
```python
validator.expect_column_values_to_not_be_null("player_id")
validator.expect_column_values_to_not_be_null("game_id")
validator.expect_column_values_to_not_be_null("team_id")
validator.expect_column_values_to_be_between("minutes_played", min_value=0, max_value=48)
validator.expect_column_values_to_be_between("field_goals_made", max_value="field_goals_attempted")
validator.expect_column_values_to_be_between("field_goal_percentage", min_value=0.0, max_value=1.0)
validator.expect_column_values_to_be_between("points", min_value=0, max_value=100)
validator.expect_column_values_to_be_between("rebounds", min_value=0, max_value=55)
validator.expect_column_values_to_be_between("assists", min_value=0, max_value=30)
```

### 5.4. Suite de Estatísticas de Equipas (team_stats_suite)

**Expectativas principais:**
- team_id: não null, existe na tabela de equipas
- game_id: não null, existe na tabela de jogos
- team_type: ∈ {home, away}
- field_goals_made ≤ field_goals_attempted
- field_goal_percentage: ∈ [0.0, 1.0]
- total_points: consistente com soma de player_pts

**Implementação:**
```python
validator.expect_column_values_to_not_be_null("team_id")
validator.expect_column_values_to_not_be_null("game_id")
validator.expect_column_values_to_be_in_set("team_type", ["home", "away"])
validator.expect_column_values_to_be_between("field_goals_made", max_value="field_goals_attempted")
validator.expect_column_values_to_be_between("field_goal_percentage", min_value=0.0, max_value=1.0)
validator.expect_column_values_to_be_between("total_points", min_value=0, max_value=200)
```

### 5.5. Suite de Features (features_suite)

**Expectativas principais:**
- feature_id: não null, único
- game_id: não null
- computed_at: não null, < game_date (anti-leakage)
- feature_value: não null (para features críticas)
- feature_name: em conjunto válido
- rolling_avg: dentro de limites históricos

**Implementação:**
```python
validator.expect_column_values_to_not_be_null("feature_id")
validator.expect_column_values_to_be_unique("feature_id")
validator.expect_column_values_to_not_be_null("game_id")
validator.expect_column_values_to_not_be_null("computed_at")
validator.expect_column_values_to_be_between("computed_at", max_value="game_date")
validator.expect_column_values_to_not_be_null("feature_value")
validator.expect_column_values_to_be_in_set("feature_name", FEATURE_NAMES_LIST)
```

### 5.6. Suite de Predictions (predictions_suite)

**Expectativas principais:**
- prediction_id: não null, único
- game_id: não null
- model_id: não null
- predicted_at: não null, < game_date
- probability: ∈ [0.0, 1.0], ∉ (0.01, 0.99)
- spread: ∈ [-30, 30]
- total: ∈ [180, 260]
- P(home) + P(away) = 1.0 ± 0.01

**Implementação:**
```python
validator.expect_column_values_to_not_be_null("prediction_id")
validator.expect_column_values_to_be_unique("prediction_id")
validator.expect_column_values_to_not_be_null("game_id")
validator.expect_column_values_to_not_be_null("model_id")
validator.expect_column_values_to_not_be_null("predicted_at")
validator.expect_column_values_to_be_between("predicted_at", max_value="game_date")
validator.expect_column_values_to_be_between("probability", min_value=0.0, max_value=1.0)
validator.expect_column_values_to_be_between("spread", min_value=-30, max_value=30)
validator.expect_column_values_to_be_between("total", min_value=180, max_value=260)
```

---

## 6. CHECKPOINTS

### 6.1. Configuração de Checkpoints

**Checkpoint de Jogos:**
```yaml
name: games_checkpoint
config:
  class_name: SimpleCheckpoint
  run_name_template: "%Y%m%d-%H%M%S-games"
  validation_operator_name: action_list_operator
  batches:
    - batch:
        datasource: betting_postgres
        data_connector: betting_data
        data_asset_name: games
        batch_identifiers:
          batch_id: default_batch_id
      expectation_suite_name: games_suite
```

**Checkpoint de Odds:**
```yaml
name: odds_checkpoint
config:
  class_name: SimpleCheckpoint
  run_name_template: "%Y%m%d-%H%M%S-odds"
  validation_operator_name: action_list_operator
  batches:
    - batch:
        datasource: betting_postgres
        data_connector: betting_data
        data_asset_name: odds
        batch_identifiers:
          batch_id: default_batch_id
      expectation_suite_name: odds_suite
```

### 6.2. Execução de Checkpoints

**Execução via CLI:**
```bash
great_expectations checkpoint run games_checkpoint
great_expectations checkpoint run odds_checkpoint
```

**Execução via Python:**
```python
from great_expectations import get_context

context = get_context()
results = context.run_checkpoint("games_checkpoint")

if not results.success:
    raise DataValidationError(f"Validation failed: {results.statistics}")
```

---

## 7. INTEGRAÇÃO COM PIPELINE

### 7.1. Integração com Prefect

**Task de Validação:**
```python
from prefect import task
from great_expectations import get_context

@task
def validate_games_batch(batch_id: str):
    context = get_context()
    results = context.run_checkpoint(
        checkpoint_name="games_checkpoint",
        batch_identifiers={"batch_id": batch_id}
    )

    if not results.success:
        raise DataValidationError(
            f"Games validation failed: {results.statistics}"
        )

    return results
```

**Flow Completo:**
```python
from prefect import Flow

with Flow("Betting Data Pipeline") as flow:
    # Ingestão
    games = ingest_nba_games()
    odds = ingest_betfair_odds()

    # Validação
    validate_games(games)
    validate_odds(odds)

    # Feature Engineering
    features = compute_features(games)

    # Validação de Features
    validate_features(features)

    # Predictions
    predictions = generate_predictions(features)

    # Validação de Predictions
    validate_predictions(predictions)
```

### 7.2. Integração com Airflow

**Operator Customizado:**
```python
from airflow.providers.postgres.operators.postgres import PostgresOperator
from great_expectations import get_context

class GreatExpectationsOperator(BaseOperator):
    def __init__(self, checkpoint_name, **kwargs):
        super().__init__(**kwargs)
        self.checkpoint_name = checkpoint_name

    def execute(self, context):
        context_ge = get_context()
        results = context_ge.run_checkpoint(self.checkpoint_name)

        if not results.success:
            raise AirflowException(
                f"Validation failed for {self.checkpoint_name}"
            )

        return results
```

**DAG:**
```python
from airflow import DAG

with DAG("betting_pipeline", schedule_interval="0 */6 * * *") as dag:
    ingest_games = PostgresOperator(
        task_id="ingest_games",
        sql="SELECT * FROM nba_games WHERE date = yesterday"
    )

    validate_games = GreatExpectationsOperator(
        task_id="validate_games",
        checkpoint_name="games_checkpoint"
    )

    ingest_games >> validate_games
```

---

## 8. ACTIONS E NOTIFICAÇÕES

### 8.1. Validation Actions

**Action List Operator:**
```yaml
action_list_operator:
  class_name: ActionListValidationOperator
  action_list:
    - name: store_validation_result
      action:
        class_name: StoreValidationResultAction
    - name: update_data_docs
      action:
        class_name: UpdateDataDocsAction
    - name: send_slack_notification
      action:
        class_name: SlackNotificationAction
        slack_webhook_url: ${SLACK_WEBHOOK_URL}
        notify_on: failure
        renderer:
          class_name: SlackRenderer
```

### 8.2. Notificações Customizadas

**Slack Notification:**
- Envia mensagem para #data-quality-alerts
- Inclui estatísticas de validação
- Detalhes de falhas
- Link para data docs

**Email Notification:**
- Envia email para data-team@company.com
- Inclui relatório HTML
- Anexos com resultados detalhados

---

## 9. DATA DOCS

### 9.1. Geração de Data Docs

**Comando:**
```bash
great_expectations docs build
```

**Localização:**
- `uncommitted/data_docs/local_site/index.html`
- Acessível via browser local

### 9.2. Componentes dos Data Docs

**Expectation Suites:**
- Lista de todas as expectativas
- Descrição de cada expectativa
- Exemplos de uso

**Validation Results:**
- Histórico de validações
- Estatísticas de sucesso/falha
- Detalhes de falhas por expectativa

**Profiling Results:**
- Estatísticas descritivas de colunas
- Histogramas
- Distribuições

---

## 10. MANUTENÇÃO

### 10.1. Atualização de Suites

**Adicionar nova expectativa:**
```python
validator.expect_column_values_to_be_between("new_column", min_value=0, max_value=100)
validator.save_expectation_suite(discard_failed_expectations=False)
```

**Remover expectativa obsoleta:**
```python
suite = context.get_expectation_suite("games_suite")
suite.expectations = [e for e in suite.expectations if e.expectation_type != "expect_column_to_exist"]
context.save_expectation_suite(suite)
```

### 10.2. Versionamento

**Git:**
- Adicionar `expectations/` ao Git
- Adicionar `great_expectations.yml` ao Git
- Excluir `uncommitted/` do Git (.gitignore)

**CI/CD:**
- Validar suites em CI
- Testar alterações em staging
- Deploy automático para produção

---

## 11. MELHORES PRÁTICAS

### 11.1. Organização

**Nomes de suites:**
- Usar naming convention: `{table}_suite`
- Ex: `games_suite`, `odds_suite`

**Nomes de checkpoints:**
- Usar naming convention: `{table}_checkpoint`
- Ex: `games_checkpoint`, `odds_checkpoint`

### 11.2. Performance

**Batch size:**
- Validar batches de tamanho razoável (1000-10000 registros)
- Evitar validar datasets inteiros de uma vez

**Caching:**
- Usar caching para expectativas computacionalmente caras
- Ex: expect_column_values_to_be_in_set com conjuntos grandes

### 11.3. Debugging

**Logging:**
- Habilitar logging detalhado para debugging
- Configurar log level em `great_expectations.yml`

**Interactive mode:**
- Usar modo interativo para testar expectativas
- `great_expectations suite edit games_suite`

---

## 12. REFERÊNCIAS CRUZADAS

- [[31_Data_Validation/INDEX]] ← Secção mãe
- [[VAL-005_REGRAS_QUALIDADE]] → Regras implementadas como expectativas
- [[04_Data_Engineering/INDEX]] → Pipeline que usa validação
- [[VAL-004_ALERTAS_MONITORIZACAO]] → Notificações de falhas

---

## 13. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2024-XX-XX | 1.0 | Criação inicial do documento | Data Engineer |
