# SELECAO_MODELOS — Seleção de Modelos

**ID:** `ML-015` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir processo de seleção entre múltiplos modelos candidatos.

---

## 2. CRITÉRIOS DE SELEÇÃO

| Critério | Peso | Threshold |
|----------|------|-----------|
| CLV | 40% | > 2% |
| Sharpe | 30% | > 0.5 |
| Calibração | 20% | ECE < 0.05 |
| Estabilidade | 10% | Variância < 10% |

---

## 3. PROCESSO DE SELEÇÃO

```python
def select_model(candidate_models, validation_data):
    """
    Seleciona melhor modelo entre candidatos.
    
    Args:
        candidate_models: Lista de modelos candidatos
        validation_data: Dados de validação
    
    Returns:
        Melhor modelo
    """
    scores = []
    
    for model in candidate_models:
        # Avaliar modelo
        metrics = evaluate_model(model, validation_data)
        
        # Calcular score ponderado
        score = (
            metrics['clv'] * 0.4 +
            metrics['sharpe'] * 0.3 +
            (1 - metrics['ece']) * 0.2 +
            (1 - metrics['instability']) * 0.1
        )
        
        scores.append({'model': model, 'score': score, 'metrics': metrics})
    
    # Selecionar com maior score
    best = max(scores, key=lambda x: x['score'])
    
    return best['model']
```

---

## 4. VALIDAÇÃO

```python
def evaluate_model(model, data):
    """
    Avalia modelo em dados de validação.
    
    Args:
        model: Modelo a avaliar
        data: Dados de validação
    
    Returns:
        Métricas do modelo
    """
    predictions = model.predict_proba(data['features'])
    
    clv = calculate_clv(predictions, data['odds'], data['outcomes'])
    sharpe = calculate_sharpe(predictions, data['outcomes'])
    ece = calculate_ece(predictions, data['outcomes'])
    instability = calculate_instability(model, data)
    
    return {
        'clv': clv,
        'sharpe': sharpe,
        'ece': ece,
        'instability': instability
    }
```

---

## 5. CRITÉRIOS

- **Mínimo 3 modelos** candidatos
- **Validação purged walk-forward**
- **Score ponderado** para seleção

---

## 6. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[OPTUNA_TUNING]]
