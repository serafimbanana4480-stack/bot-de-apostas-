# WALK_FORWARD_CV — Validacao Temporal Purged

**ID:** `ML-002` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar purged walk-forward cross-validation que evita look-ahead bias e overfitting temporal.

---

## 2. CONCEITO

```
Epoca 1-3: TREINO
Epoca 4: VALIDACAO (com embargo 2 dias)
Epoca 5: TESTE FINAL (nunca tocar durante desenvolvimento)
```

---

## 3. IMPLEMENTACAO

```python
import pandas as pd
from sklearn.model_selection import BaseCrossValidator

class PurgedWalkForwardCV(BaseCrossValidator):
    """
    Walk-forward com embargo entre treino e validacao.
    """
    def __init__(self, n_splits=12, embargo_days=2):
        self.n_splits = n_splits
        self.embargo_days = embargo_days
    
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits
    
    def split(self, X, y=None, groups=None):
        df = X.copy()
        df = df.sort_values('game_date')
        
        # Divisao por meses
        df['year_month'] = df['game_date'].dt.to_period('M')
        unique_months = df['year_month'].unique()
        
        # Ultimos n meses sao para validacao
        train_months = unique_months[:-self.n_splits]
        
        for i in range(self.n_splits):
            val_month = unique_months[-self.n_splits + i]
            
            # Treino: todos os meses ate ao mes de validacao (com embargo)
            embargo_cutoff = val_month.start_time - pd.Timedelta(days=self.embargo_days)
            train_mask = df['game_date'] < embargo_cutoff
            val_mask = df['year_month'] == val_month
            
            train_idx = df[train_mask].index
            val_idx = df[val_mask].index
            
            yield train_idx, val_idx
```

---

## 4. EXEMPLO DE USO

```python
from sklearn.model_selection import cross_val_score

cv = PurgedWalkForwardCV(n_splits=12, embargo_days=2)
scores = []

for train_idx, val_idx in cv.split(df_features):
    X_train, X_val = df_features.iloc[train_idx], df_features.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    
    model = train_primary_model(X_train, y_train, X_val, y_val)
    probs = model.predict_proba(X_val)[:, 1]
    
    # Calcular CLV e ROI neste fold
    fold_metrics = evaluate_fold(X_val, y_val, probs)
    scores.append(fold_metrics)
```

---

## 5. BACKLOG

- [ ] Implementar testes unitarios para o splitter
- [ ] Verificar que nenhum jogo do treino esta dentro do embargo do validacao
- [ ] Documentar distribuicao de folds por epoca

---

## 6. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secao mae
- [[06_Backtesting/INDEX]] → Backtest que usa este CV
