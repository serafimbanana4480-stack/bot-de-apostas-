# OPTUNA_TUNING — Otimizacao de Hiperparametros

**ID:** `ML-003` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Otimizar hiperparametros do XGBoost sem overfitting, usando o set de validacao dentro do purged CV.

---

## 2. IMPLEMENTACAO

```python
import optuna
import xgboost as xgb
from sklearn.metrics import log_loss

def objective(trial, X_train, y_train, X_val, y_val):
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'logloss',
        'max_depth': trial.suggest_int('max_depth', 3, 6),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 10, 100),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 1.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 1.0, log=True),
        'n_estimators': 1000,
        'early_stopping_rounds': 50,
        'tree_method': 'hist',
        'seed': 42
    }
    
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    probs = model.predict_proba(X_val)[:, 1]
    return log_loss(y_val, probs)

# Estudo Optuna (maximizar = False porque queremos minimizar logloss)
study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(lambda trial: objective(trial, X_train, y_train, X_val, y_val), n_trials=100)

print(f"Melhores parametros: {study.best_params}")
print(f"Melhor logloss: {study.best_value}")
```

---

## 3. REGRAS ANTI-OVERFITTING

1. **Nunca usar o set de TESTE FINAL para tuning.** So o set de validacao.
2. **Limitar n_trials:** Max 100-200. Mais que isso = overfitting de hiperparametros.
3. **Fixar seed:** Reprodutibilidade absoluta.
4. **Documentar:** Guardar todos os trials em MLflow.

---

## 4. BACKLOG

- [ ] Rodar tuning inicial para modelo Moneyline
- [ ] Rodar tuning para modelo Spread
- [ ] Documentar distribuicao de parametros vs performance
- [ ] Implementar prunning (early stopping de trials ruins)

---

## 5. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secao mae
- [[29_Experiment_Tracking/INDEX]] → Guardar resultados Optuna
