# FEATURE_SELECTION — Seleção de Features

**ID:** `ML-011` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Selecionar features mais informativas para reduzir overfitting e melhorar generalização.

---

## 2. MÉTODO: FEATURE IMPORTANCE

```python
def select_by_importance(model, X, threshold=0.01):
    """Seleciona features baseado em importance do XGBoost."""
    importance = model.get_booster().get_score(importance_type='gain')
    importance_normalized = {k: v/sum(importance.values()) for k, v in importance.items()}
    
    selected = [k for k, v in importance_normalized.items() if v > threshold]
    return selected
```

---

## 3. REMOÇÃO DE COLINEARIDADE

```python
def remove_collinear(X, threshold=0.9):
    """Remove features altamente correlacionadas."""
    corr_matrix = X.corr().abs()
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [c for c in upper_tri.columns if any(upper_tri[c] > threshold)]
    
    return X.drop(columns=to_drop)
```

---

## 4. CRITÉRIOS

- **Máximo 50 features**
- **Correlação entre features < 0.9**
- **Top 10 estáveis em ≥ 8 folds**

---

## 5. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[SELECAO_VARIANTEIS]]
