# ENSEMBLE STACKING — Implementação Detalhada

**ID:** `SEC-05-01` | **Status:** #status/pending | **Versão:** `2.0.0-ENSEMBLE`

---

## 1. OBJETIVO

Implementar ensemble stacking com XGBoost, LightGBM e CatBoost como modelos base e Logistic Regression como meta-modelo para combinar as previsões. Esta arquitetura reduz variância e melhora robustez do modelo.

---

## 2. ARQUITETURA DE TREINO

```python
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import PurgedKFold
from sklearn.calibration import CalibratedClassifierCV

class EnsembleStacking:
    """
    Ensemble stacking com 3 modelos base + meta-modelo linear.
    """
    def __init__(self, xgb_config, lgb_config, cat_config, meta_config):
        self.xgb_model = XGBClassifier(**xgb_config)
        self.lgb_model = LGBMClassifier(**lgb_config)
        self.cat_model = CatBoostClassifier(**cat_config)
        self.meta_model = LogisticRegression(**meta_config)
        
        self.base_models = {
            'xgb': self.xgb_model,
            'lgb': self.lgb_model,
            'cat': self.cat_model
        }
        
    def fit_base_models(self, X_train, y_train, X_val, y_val):
        """
        Treina os 3 modelos base no set de treino.
        """
        base_predictions = {}
        
        for name, model in self.base_models.items():
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=50,
                verbose=False
            )
            # Obter previsões no validation set
            base_predictions[name] = model.predict_proba(X_val)[:, 1]
        
        return base_predictions
    
    def fit_meta_model(self, base_predictions, y_val):
        """
        Treina meta-modelo nas previsões dos modelos base.
        """
        # Criar feature matrix com previsões dos 3 modelos
        X_meta = np.column_stack([
            base_predictions['xgb'],
            base_predictions['lgb'],
            base_predictions['cat']
        ])
        
        self.meta_model.fit(X_meta, y_val)
        
        return X_meta
    
    def predict(self, X):
        """
        Faz previsão usando ensemble completo.
        """
        # Obter previsões dos modelos base
        base_preds = np.column_stack([
            self.xgb_model.predict_proba(X)[:, 1],
            self.lgb_model.predict_proba(X)[:, 1],
            self.cat_model.predict_proba(X)[:, 1]
        ])
        
        # Meta-modelo combina as previsões
        ensemble_pred = self.meta_model.predict_proba(base_preds)[:, 1]
        
        return ensemble_pred
    
    def predict_with_uncertainty(self, X):
        """
        Retorna previsão e incerteza (desvio padrão dos modelos base).
        """
        base_preds = np.column_stack([
            self.xgb_model.predict_proba(X)[:, 1],
            self.lgb_model.predict_proba(X)[:, 1],
            self.cat_model.predict_proba(X)[:, 1]
        ])
        
        ensemble_pred = self.meta_model.predict_proba(base_preds)[:, 1]
        uncertainty = np.std(base_preds, axis=1)  # Desvio padrão entre modelos
        
        return ensemble_pred, uncertainty
```

---

## 3. VALIDAÇÃO PURGED WALK-FORWARD PARA ENSEMBLE

```python
def purged_walk_forward_ensemble(X, y, dates, embargo_days=2):
    """
    Validação temporal purged para ensemble stacking.
    """
    # Ordenar por data
    sorted_indices = np.argsort(dates)
    X_sorted = X.iloc[sorted_indices]
    y_sorted = y.iloc[sorted_indices]
    dates_sorted = dates.iloc[sorted_indices]
    
    # Definir janelas de treino/validação/teste
    n_splits = 12
    ensemble_performance = []
    
    for i in range(n_splits):
        # Janela deslizante
        train_start = i * 3  # 3 meses por fold
        train_end = train_start + 36  # 36 meses de treino
        val_start = train_end + embargo_days
        val_end = val_start + 1  # 1 mês de validação
        
        # Aplicar embargo
        train_mask = (dates_sorted >= dates_sorted.iloc[train_start]) & \
                     (dates_sorted < dates_sorted.iloc[train_end])
        val_mask = (dates_sorted >= dates_sorted.iloc[val_start]) & \
                   (dates_sorted < dates_sorted.iloc[val_end])
        
        X_train, X_val = X_sorted[train_mask], X_sorted[val_mask]
        y_train, y_val = y_sorted[train_mask], y_sorted[val_mask]
        
        # Treinar ensemble
        ensemble = EnsembleStacking(xgb_config, lgb_config, cat_config, meta_config)
        ensemble.fit_base_models(X_train, y_train, X_val, y_val)
        ensemble.fit_meta_model(ensemble.fit_base_models(X_train, y_train, X_val, y_val), y_val)
        
        # Avaliar
        val_pred = ensemble.predict(X_val)
        clv = calculate_clv(val_pred, get_market_odds(val_mask))
        ensemble_performance.append(clv)
    
    return ensemble_performance
```

---

## 4. BENEFÍCIOS DO ENSEMBLE

**Redução de Variância:**
- 3 modelos independentes reduzem overfitting específico de um algoritmo
- Meta-modelo linear captura padrões de erro dos modelos base

**Robustez:**
- Se um modelo falhar em um regime específico, os outros compensam
- Diferentes algoritmos capturam diferentes padrões nos dados

**Performance:**
- Esperado: +1-2% de CLV adicional vs modelo único XGBoost
- Melhor generalização para novos dados

---

## 5. DEPENDÊNCIAS

```txt
xgboost>=2.0.0
lightgbm>=4.0.0
catboost>=1.2.0
scikit-learn>=1.3.0
```

---

## 6. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| CLV médio ensemble | > 2.5% (vs 2.0% modelo único) |
| Variância entre folds | < 0.5% (mais estável que modelo único) |
| Correlação entre modelos base | < 0.85 (diversidade suficiente) |
| Tempo de inferência | < 100ms por aposta |
