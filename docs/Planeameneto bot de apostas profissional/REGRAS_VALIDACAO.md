# REGRAS_VALIDACAO — Regras de Validação

**ID:** `DE-007` | **Fase:** #phase/2 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir regras de validação para dados do sistema.

---

## 2. REGRAS POR CAMADA

### Bronze (Raw)
- Odds > 1.0
- Probabilidade entre 0 e 1
- Data não nula
- Game ID não vazio

### Silver (Cleaned)
- Sem valores nulos
- Tipos consistentes
- Sem duplicados
- Sequência temporal correta

### Gold (Features)
- Features normalizadas (0-1 ou z-score)
- Sem valores infinitos
- Variância > 0
- Correlação < 0.95 entre features

---

## 3. IMPLEMENTAÇÃO

```python
def validate_bronze_data(data):
    """
    Valida dados da camada Bronze.
    
    Args:
        data: DataFrame a validar
    
    Returns:
        Boolean se válido
    """
    # Odds > 1.0
    if (data['odd'] <= 1.0).any():
        raise ValueError("Odds deve ser > 1.0")
    
    # Probabilidade entre 0 e 1
    if ((data['prob'] < 0) | (data['prob'] > 1)).any():
        raise ValueError("Probabilidade deve estar entre 0 e 1")
    
    # Data não nula
    if data['date'].isnull().any():
        raise ValueError("Data não pode ser nula")
    
    return True

def validate_gold_features(features):
    """
    Valida features da camada Gold.
    
    Args:
        features: DataFrame de features
    
    Returns:
        Boolean se válido
    """
    # Sem valores infinitos
    if np.isinf(features).any().any():
        raise ValueError("Features não podem ter valores infinitos")
    
    # Variância > 0
    if (features.var() == 0).any():
        raise ValueError("Features devem ter variância > 0")
    
    # Correlação < 0.95
    corr_matrix = features.corr()
    high_corr = (corr_matrix.abs() > 0.95) & (corr_matrix != 1.0)
    if high_corr.any().any():
        logger.warning("Alta correlação detetada entre features")
    
    return True
```

---

## 4. AUTOMAÇÃO

```python
def run_validation_rules(layer, data):
    """
    Executa regras de validação para uma camada.
    
    Args:
        layer: Nome da camada
        data: Dados a validar
    
    Returns:
        Resultado da validação
    """
    if layer == 'bronze':
        result = validate_bronze_data(data)
    elif layer == 'silver':
        result = validate_silver_data(data)
    elif layer == 'gold':
        result = validate_gold_features(data)
    
    if not result:
        send_alert(f"🚨 Validação falhou na camada {layer}")
    
    return result
```

---

## 5. CRITÉRIOS

- **Validar** em cada camada
- **Falha = bloqueio** do pipeline
- **Alerta imediato** se falha

---

## 6. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[VALIDACAO_DADOS]]
