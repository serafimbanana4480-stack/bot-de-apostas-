# Data Validation Automation

**ID:** AUTO-005 | **Fase:** #phase/6-12 | **Owner:** DevOps + Operations Lead | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Sistema de validação automatizada de dados usando Great Expectations. Validação ocorre automaticamente após ingestão de dados, garantindo qualidade e consistência.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Validação automatizada de dados |
| **Stack** | Great Expectations, PostgreSQL |
| **Custo** | 0€ (open source) |

---

## 2. ARQUITETURA DE VALIDAÇÃO

### 2.1 Fluxo de Validação

```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO DE VALIDAÇÃO AUTOMATIZADA                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. INGESTÃO DE DADOS                                  │   │
│  │    - Dados NBA ingeridos                              │   │
│  │    - Armazenados em camada bronze                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. VALIDAÇÃO AUTOMÁTICA                             │   │
│  │    - Expectations rodam automaticamente              │   │
│  │    - Valida schema, tipos, ranges                   │   │
│  │    - Deteta anomalias                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. RESULTADO DE VALIDAÇÃO                           │   │
│  │    - Se PASS: Dados → camada silver                 │   │
│  │    - Se FAIL: Alerta + bloqueio                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. RELATÓRIO DE VALIDAÇÃO                           │   │
│  │    - Gerado automaticamente                          │   │
│  │    - Enviado para Telegram                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO GREAT EXPECTATIONS

### 3.1 Instalação

```bash
pip install great_expectations psycopg2
```

### 3.2 Inicialização

```bash
cd vbq
great_expectations init
```

### 3.3 Configuração do Data Context

```python
# vbq/validation/gx_config.py
from great_expectations.data_context import DataContext

context = DataContext(
    project_root_dir="./vbq/validation"
)
```

---

## 4. EXPECTATIONS

### 4.1 Expectation Suite NBA

```python
# vbq/validation/expectations/nba_suite.py
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.expectations import ExpectationSuite

def create_nba_expectation_suite():
    """Cria expectation suite para dados NBA"""
    suite = ExpectationSuite(
        expectation_suite_name="nba_suite"
    )
    
    # Schema expectations
    suite.add_expectation(
        "expect_column_to_exist",
        column="game_id"
    )
    suite.add_expectation(
        "expect_column_to_exist",
        column="date"
    )
    suite.add_expectation(
        "expect_column_to_exist",
        column="home_team"
    )
    suite.add_expectation(
        "expect_column_to_exist",
        column="away_team"
    )
    
    # Type expectations
    suite.add_expectation(
        "expect_column_values_to_be_of_type",
        column="game_id",
        type_="str"
    )
    suite.add_expectation(
        "expect_column_values_to_be_of_type",
        column="date",
        type_="datetime"
    )
    
    # Range expectations
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
    
    # Uniqueness expectations
    suite.add_expectation(
        "expect_column_values_to_be_unique",
        column="game_id"
    )
    
    # Null expectations
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="game_id"
    )
    suite.add_expectation(
        "expect_column_values_to_not_be_null",
        column="date"
    )
    
    return suite
```

### 4.2 Expectation Suite Odds

```python
# vbq/validation/expectations/odds_suite.py
def create_odds_expectation_suite():
    """Cria expectation suite para dados de odds"""
    suite = ExpectationSuite(
        expectation_suite_name="odds_suite"
    )
    
    # Schema expectations
    suite.add_expectation(
        "expect_column_to_exist",
        column="game_id"
    )
    suite.add_expectation(
        "expect_column_to_exist",
        column="bookmaker"
    )
    suite.add_expectation(
        "expect_column_to_exist",
        column="odd"
    )
    
    # Range expectations
    suite.add_expectation(
        "expect_column_values_to_be_between",
        column="odd",
        min_value=1.01,
        max_value=100.0
    )
    
    # Value set expectations
    suite.add_expectation(
        "expect_column_values_to_be_in_set",
        column="bookmaker",
        value_set=["betfair", "pinnacle", "smarkets"]
    )
    
    return suite
```

---

## 5. VALIDAÇÃO AUTOMATIZADA

### 5.1 Função de Validação

```python
# vbq/validation/validator.py
from great_expectations.data_context import DataContext
from vbq.alerts.telegram_client import TelegramClient

context = DataContext()
telegram = TelegramClient(
    token=TELEGRAM_BOT_TOKEN,
    chat_id=TELEGRAM_CHAT_ID
)

def validate_data(batch_request: RuntimeBatchRequest, suite_name: str):
    """Valida dados automaticamente"""
    
    # Obter expectation suite
    suite = context.get_expectation_suite(suite_name)
    
    # Validar
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite=suite
    )
    
    results = validator.validate()
    
    # Verificar resultados
    if results.success:
        # Dados válidos
        telegram.send_alert(
            level="INFO",
            title="Validação Concluída",
            message=f"Suite {suite_name}: PASS"
        )
        return True
    else:
        # Dados inválidos
        failed_expectations = [
            f"{exp.expectation_type}: {exp.exception['message']}"
            for exp in results.failed_expectations
        ]
        
        telegram.send_alert(
            level="CRITICAL",
            title=f"Validação Falhou: {suite_name}",
            message=f"Failed: {len(results.failed_expectations)}\n\n" +
                   "\n".join(failed_expectations[:5])
        )
        
        return False
```

### 5.2 Integração com Pipeline

```python
# vbq/prefect/pipelines/daily_pipeline.py
from prefect import flow, task
from vbq.validation.validator import validate_data
from great_expectations.core.batch import RuntimeBatchRequest

@task
def validate_ingested_data(data):
    """Valida dados após ingestão"""
    batch_request = RuntimeBatchRequest(
        datasource_name="postgresql",
        data_connector_name="nba_data",
        data_asset_name="nba_games",
        batch_identifiers={"date": data['date']}
    )
    
    return validate_data(batch_request, "nba_suite")

@flow(name="daily_pipeline_with_validation")
def daily_pipeline_with_validation(date: str):
    """Pipeline diário com validação"""
    # Ingestão
    data = ingest_nba_data(date)
    
    # Validação
    is_valid = validate_ingested_data(data, wait_for=[data])
    
    # Se inválido, parar pipeline
    if not is_valid:
        raise Exception("Validação falhou - pipeline parado")
    
    # Continuar pipeline...
    snapshots = create_snapshots(data, wait_for=[is_valid])
    
    return snapshots
```

---

## 6. CHECKPOINTS DE QUALIDADE

### 6.1 Checklist de Validação

- [ ] Schema correto (colunas, tipos)
- [ ] Sem valores nulos em colunas críticas
- [ ] Valores dentro de ranges válidos
- [ ] Valores únicos em colunas únicas
- [ ] Consistência de data/hora
- [ ] Sem duplicatas
- [ ] Referências externas válidas

### 6.2 Métricas de Qualidade

```python
# vbq/validation/metrics.py
def calculate_quality_metrics(results):
    """Calcula métricas de qualidade"""
    return {
        'total_expectations': len(results.results),
        'passed_expectations': len([r for r in results.results if r.success]),
        'failed_expectations': len([r for r in results.results if not r.success]),
        'success_rate': len([r for r in results.results if r.success]) / len(results.results)
    }
```

---

## 7. RELATÓRIOS

### 7.1 Relatório HTML

```python
# vbq/validation/reports.py
def generate_html_report(results, output_path: str):
    """Gera relatório HTML de validação"""
    from great_expectations.render.renderer.html_renderer import HTMLRenderer
    
    renderer = HTMLRenderer()
    html_report = renderer.render(results)
    
    with open(output_path, 'w') as f:
        f.write(html_report)
    
    return output_path
```

### 7.2 Relatório Resumido

```python
def generate_summary_report(results):
    """Gera relatório resumido"""
    summary = {
        'suite_name': results.expectation_suite_name,
        'success': results.success,
        'total_expectations': len(results.results),
        'passed': len([r for r in results.results if r.success]),
        'failed': len([r for r in results.results if not r.success]),
        'failed_expectations': [
            {
                'expectation': r.expectation_config['expectation_type'],
                'column': r.expectation_config['kwargs'].get('column'),
                'message': r.exception['message'] if r.exception else None
            }
            for r in results.failed_expectations
        ]
    }
    
    return summary
```

---

## 8. MONITORIZAÇÃO

### 8.1 Dashboard de Validação

```
┌─────────────────────────────────────────────────────────────┐
│ VALIDAÇÃO DE DADOS - ÚLTIMAS 24 HORAS                     │
├─────────────────────────────────────────────────────────────┤
│ NBA Suite:                                                │
│   - Total: 120                                            │
│   - Pass: 118 (98.3%)                                    │
│   - Fail: 2 (1.7%) ⚠️                                    │
├─────────────────────────────────────────────────────────────┤
│ Odds Suite:                                               │
│   - Total: 85                                             │
│   - Pass: 85 (100%) ✅                                    │
│   - Fail: 0                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Alertas de Qualidade

```python
# vbq/validation/alerts.py
def alert_quality_degradation(success_rate: float, threshold: float):
    """Alerta de degradação de qualidade"""
    if success_rate < threshold:
        telegram.send_alert(
            level="WARNING",
            title="Qualidade de Dados Degradada",
            message=f"Success rate: {success_rate:.1%}\nThreshold: {threshold:.1%}"
        )
```

---

## 9. TESTES

### 9.1 Teste de Validação

```python
# vbq/validation/tests/test_validator.py
def test_nba_validation():
    """Teste de validação NBA"""
    batch_request = RuntimeBatchRequest(
        datasource_name="postgresql",
        data_connector_name="nba_data",
        data_asset_name="nba_games",
        batch_identifiers={"date": "2026-05-18"}
    )
    
    result = validate_data(batch_request, "nba_suite")
    assert result == True
```

---

## 10. LINKS CRUZADOS

- [[39_Automation/INDEX]] ← Secção mãe
- [[31_Data_Validation/INDEX]] → Validação de dados
- [[04_Data_Engineering/INDEX]] → Engenharia de dados
- [[33_Alerting/INDEX]] → Sistema de alertas

---

**Custo de implementação:** 0€ (open source)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para qualidade de dados)
