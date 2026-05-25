# IMPLEMENTACAO_META — Pipeline Completo

**ID:** `MLAB-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. PIPELINE DE TREINO

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split

# Dados: previsoes do modelo primario em dados historicos
# Target: 1 se CLV_expost > 0, 0 caso contrario

def train_meta_model(X_meta, y_meta):
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        max_depth=3,
        learning_rate=0.03,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=50,
        seed=42
    )
    
    model.fit(X_meta, y_meta)
    return model
```

---

## 2. FEATURES META

```python
meta_features = {
    'prob_primario': float,
    'edge_estimado': float,
    'entropy': float,
    'regime': categorical,
    'is_home': bool,
    'is_back_to_back': bool,
    'rest_days': int,
    'liquidez': float,
    'odd': float,
    'prob_publico': float,
    'spread_prob': float
}
```

---

## 3. THRESHOLD OTIMIZACAO

```python
def optimize_threshold(meta_model, X_val, y_val):
    best_threshold = 0.60
    best_sharpe = -999
    
    for threshold in np.linspace(0.50, 0.75, 26):
        probs = meta_model.predict_proba(X_val)[:, 1]
        selected = probs >= threshold
        
        if selected.sum() < 10:
            continue
        
        returns = calculate_returns(X_val[selected], y_val[selected])
        sharpe = returns.mean() / returns.std()
        
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_threshold = threshold
    
    return best_threshold
```

---

## 4. BACKLOG

- [ ] Treinar meta-modelo com 2+ epocas
- [ ] Medir impacto no Sharpe Ratio
- [ ] Documentar ganho de CLV com vs sem meta-labeling

---

## 5. LINKS CRUZADOS

- [[46_Meta_Labeling/INDEX]] ← Secao mae
- [[05_Machine_Learning/INDEX]] → Modelo primario
