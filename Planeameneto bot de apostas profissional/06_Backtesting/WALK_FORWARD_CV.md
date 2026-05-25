# WALK_FORWARD_CV — Walk-Forward Cross-Validation

**ID:** `QR-024` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar walk-forward CV para validação temporal de modelos.

---

## 2. CONCEITO

Walk-forward CV simula operação real treinando em dados passados e testando em dados futuros, re-treino em intervalos regulares.

---

## 3. IMPLEMENTAÇÃO

```python
def walk_forward_cv(data, train_size, test_size, step):
    """
    Walk-forward cross-validation.
    
    Args:
        data: Dataset temporal
        train_size: Tamanho da janela de treino
        test_size: Tamanho da janela de teste
        step: Passo entre janelas
    
    Returns:
        Lista de scores por fold
    """
    scores = []
    
    start = 0
    while start + train_size + test_size <= len(data):
        # Janela de treino
        train_start = start
        train_end = start + train_size
        
        # Janela de teste
        test_start = train_end
        test_end = test_start + test_size
        
        # Treinar
        train_data = data.iloc[train_start:train_end]
        model = train_model(train_data)
        
        # Testar
        test_data = data.iloc[test_start:test_end]
        score = evaluate_model(model, test_data)
        
        scores.append(score)
        
        # Próxima janela
        start += step
    
    return scores
```

---

## 4. PARÂMETROS TÍPICOS

| Parâmetro | Valor |
|-----------|-------|
| Train size | 90 dias |
| Test size | 30 dias |
| Step | 30 dias |

---

## 5. PURGED WALK-FORWARD

```python
def purged_walk_forward_cv(data, train_size, test_size, step, purge_days=1):
    """
    Walk-forward CV com purged data.
    
    Args:
        data: Dataset temporal
        train_size: Tamanho da janela de treino
        test_size: Tamanho da janela de teste
        step: Passo entre janelas
        purge_days: Dias a purgar
    
    Returns:
        Lista de scores por fold
    """
    scores = []
    
    start = 0
    while start + train_size + test_size + purge_days <= len(data):
        # Janela de treino
        train_start = start
        train_end = start + train_size
        
        # Purge
        purge_end = train_end + purge_days
        
        # Janela de teste (após purge)
        test_start = purge_end
        test_end = test_start + test_size
        
        # Treinar
        train_data = data.iloc[train_start:train_end]
        model = train_model(train_data)
        
        # Testar
        test_data = data.iloc[test_start:test_end]
        score = evaluate_model(model, test_data)
        
        scores.append(score)
        
        # Próxima janela
        start += step
    
    return scores
```

---

## 6. CRITÉRIOS

- **Purged CV** obrigatório para evitar leakage
- **Mínimo 5 folds** para validação estatística
- **Janelas sobrepostas** para mais dados

---

## 7. LINKS CRUZADOS

- [[06_Backtesting/INDEX]]
- [[LEAKAGE_TEMPORAL]]
