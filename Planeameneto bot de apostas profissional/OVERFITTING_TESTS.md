# OVERFITTING_TESTS — Detecção de Overfitting

**ID:** `ML-008` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Detectar overfitting no modelo para garantir generalização para dados não vistos.

---

## 2. SINAIS DE OVERFITTING

| Sinal | Threshold | Ação |
|-------|-----------|------|
| Logloss train << logloss val | Delta > 0.1 | Aumentar regularização |
| Accuracy train >> accuracy val | Delta > 0.15 | Reduzir profundidade |
| Feature importance instável | Top 10 variam > 50% | Aumentar min_child_weight |
| Performance cai no teste | ROI val > ROI test + 10% | Revisar features |

---

## 3. TESTE 1: GAP TREINO-VALIDAÇÃO

```python
def train_val_gap(model, X_train, y_train, X_val, y_val):
    """
    Calcula gap entre treino e validação.
    """
    train_loss = model.score(X_train, y_train)
    val_loss = model.score(X_val, y_val)
    
    gap = train_loss - val_loss
    
    if gap > 0.1:
        print(f"Overfitting detectado! Gap: {gap:.3f}")
        return False
    
    return True
```

---

## 4. TESTE 2: FEATURE IMPORTANCE STABILITY

```python
def feature_importance_stability(importances_by_fold):
    """
    Verifica estabilidade de feature importance.
    
    Args:
        importances_by_fold: Lista de dicts de importance por fold
    
    Returns:
        Boolean se estável
    """
    # Encontrar top 10 features no fold 0
    fold_0 = importances_by_fold[0]
    top_10 = sorted(fold_0.items(), key=lambda x: x[1], reverse=True)[:10]
    top_10_features = [f[0] for f in top_10]
    
    # Verificar quantas estão no top 10 de outros folds
    stable_count = 0
    for fold in importances_by_fold[1:]:
        fold_top_10 = sorted(fold.items(), key=lambda x: x[1], reverse=True)[:10]
        fold_top_10_features = [f[0] for f in fold_top_10]
        
        overlap = len(set(top_10_features) & set(fold_top_10_features))
        stable_count += overlap
    
    # Se top 10 está em ≥ 8 folds, estável
    return stable_count >= 8
```

---

## 5. TESTE 3: PERFORMANCE NO TESTE

```python
def test_set_performance(model, X_val, X_test, y_val, y_test):
    """
    Compara performance validação vs teste.
    """
    val_score = model.score(X_val, y_val)
    test_score = model.score(X_test, y_test)
    
    drop = val_score - test_score
    
    if drop > 0.1:
        print(f"Performance cai drasticamente no teste! Drop: {drop:.3f}")
        return False
    
    return True
```

---

## 6. MITIGAÇÕES

Se overfitting detectado:

```python
def mitigate_overfitting(config):
    """
    Ajusta configuração para reduzir overfitting.
    """
    mitigated = config.copy()
    mitigated.update({
        'max_depth': max(2, config['max_depth'] - 1),
        'min_child_weight': config['min_child_weight'] * 2,
        'reg_alpha': config['reg_alpha'] + 0.5,
        'reg_lambda': config['reg_lambda'] + 1.0,
        'subsample': max(0.5, config['subsample'] - 0.1)
    })
    
    return mitigated
```

---

## 7. CHECKLIST

Antes de promover modelo:
- [ ] Gap train-val < 0.1
- [ ] Top 10 features estáveis em ≥ 8 folds
- [ ] Performance teste ≥ performance val - 0.1
- [ ] Brier Score teste < Brier Score treino + 0.05

---

## 8. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[LEAKAGE_PREVENTION]]
