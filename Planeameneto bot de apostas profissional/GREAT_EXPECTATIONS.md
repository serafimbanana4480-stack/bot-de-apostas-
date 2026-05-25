# GREAT_EXPECTATIONS — Great Expectations

**ID:** `DE-008` | **Fase:** #phase/2 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar Great Expectations para validação de dados.

---

## 2. SUITES DE EXPECTATIONS

| Suite | Camada | Expectativas |
|-------|-------|--------------|
| Bronze | Raw | Schema, tipos, nulos |
| Silver | Cleaned | Uniquidade, sequência temporal |
| Gold | Features | Distribuição, correlação |

---

## 3. IMPLEMENTAÇÃO

```python
import great_expectations as ge

def setup_expectations():
    """Configura Great Expectations."""
    context = ge.get_context()
    
    # Criar data source
    datasource = context.data_sources.add_postgresql("bets_db")
    
    # Criar expectation suite
    suite = context.suites.add(ge.ExpectationSuite(name="bets_suite"))
    
    # Adicionar expectations
    suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="odd",
            min_value=1.01,
            max_value=100
        )
    )
    
    suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="prob",
            min_value=0.0,
            max_value=1.0
        )
    )
    
    return suite

def validate_data(df, suite):
    """
    Valida dados contra expectation suite.
    
    Args:
        df: DataFrame a validar
        suite: Expectation suite
    
    Returns:
        Resultado da validação
    """
    batch = ge.dataframe.PandasDataset(df)
    results = batch.validate(suite)
    
    if not results.success:
        logger.error(f"Validação falhou: {results}")
        send_alert("🚨 Validação de dados falhou")
    
    return results
```

---

## 4. AUTOMAÇÃO

```python
def run_expectations_pipeline(layer):
    """
    Executa validation pipeline para uma camada.
    
    Args:
        layer: Nome da camada (bronze/silver/gold)
    """
    # Obter dados
    data = get_layer_data(layer)
    
    # Obter suite
    suite = get_suite(layer)
    
    # Validar
    results = validate_data(data, suite)
    
    # Log resultados
    log_validation_results(layer, results)
    
    return results.success
```

---

## 5. CRITÉRIOS

- **Validar** em cada camada
- **Falha = bloqueio** do pipeline
- **Alerta imediato** se falha

---

## 6. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[REGRAS_VALIDACAO]]
