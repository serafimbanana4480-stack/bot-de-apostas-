# SELECAO_VARIANTEIS — Seleção de Features

**ID:** `ML-007` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Selecionar features mais informativas para reduzir overfitting e melhorar generalização do modelo.

---

## 2. MÉTODOS DE SELEÇÃO

### 2.1 Feature Importance (XGBoost)

```python
def select_by_importance(model, X, threshold=0.01):
    """
    Seleciona features baseado em importance do XGBoost.
    
    Args:
        model: Modelo XGBoost treinado
        X: DataFrame de features
        threshold: Threshold mínimo de importance
    
    Returns:
        Lista de features selecionadas
    """
    importance = model.get_booster().get_score(importance_type='gain')
    importance_normalized = {k: v/sum(importance.values()) for k, v in importance.items()}
    
    selected = [k for k, v in importance_normalized.items() if v > threshold]
    return selected
```

### 2.2 Correlação com Target

```python
def select_by_correlation(X, y, threshold=0.05):
    """Seleciona features com correlação mínima com target."""
    correlations = X.corrwith(y)
    selected = correlations[abs(correlations) > threshold].index.tolist()
    return selected
```

### 2.3 Recursive Feature Elimination (RFE)

```python
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression

def rfe_selection(X, y, n_features=50):
    """RFE para seleção de features."""
    estimator = LogisticRegression(max_iter=1000)
    selector = RFE(estimator, n_features_to_select=n_features)
    selector.fit(X, y)
    
    return X.columns[selector.support_].tolist()
```

---

## 3. COLINEARIDADE

Remover features altamente correlacionadas:

```python
def remove_collinear_features(X, threshold=0.9):
    """
    Remove features com correlação > threshold.
    """
    corr_matrix = X.corr().abs()
    
    # Encontrar pares com correlação alta
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > threshold)]
    
    return X.drop(columns=to_drop), to_drop
```

---

## 4. ESTRATÉGIA HÍBRIDA

```python
def hybrid_feature_selection(X, y, model):
    """Combina múltiplos métodos."""
    # 1. Correlação com target
    corr_selected = select_by_correlation(X, y, threshold=0.03)
    
    # 2. Feature importance
    imp_selected = select_by_importance(model, X, threshold=0.01)
    
    # 3. Interseção
    final_selected = list(set(corr_selected) & set(imp_selected))
    
    # 4. Remover colinearidade
    X_selected, dropped = remove_collinear_features(X[final_selected])
    
    return X_selected.columns.tolist()
```

---

## 5. CRITÉRIOS

- **Máximo 50 features** para evitar overfitting
- **Correlação com target > 0.03** para incluir
- **Correlação entre features < 0.9** para evitar colinearidade
- **Top 10 features estáveis** em ≥ 8 folds

---

## 6. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[FEATURE_ENGINEERING]]
