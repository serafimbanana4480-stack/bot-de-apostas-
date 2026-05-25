# OPTUNA_TUNING — Otimização de Hiperparâmetros

**ID:** `ML-002` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Usar Optuna para otimizar hiperparâmetros do XGBoost de forma eficiente, focando em métricas de edge (CLV) em vez de accuracy tradicional.

---

## 2. PORQUÊ OPTUNA?

| Framework | Vantagens | Desvantagens |
|-----------|-----------|--------------|
| Optuna | Bayesian optimization, pruning, eficiente | Curva de aprendizado |
| Hyperopt | Similar, maduro | Menos ativo |
| Grid Search | Simples | Ineficiente |
| Random Search | Melhor que grid | Sem aprendizado |

---

## 3. SPACE DE BUSCA

```python
import optuna

def define_search_space(trial):
    """Define espaço de busca para XGBoost."""
    return {
        'max_depth': trial.suggest_int('max_depth', 3, 6),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 10, 100),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 2.0),
    }
```

---

## 4. OBJECTIVE FUNCTION

```python
def objective(trial, X_train, y_train, X_val, y_val):
    """Função objetivo para Optuna."""
    params = define_search_space(trial)
    
    # Treinar modelo
    model = xgb.XGBClassifier(**params, n_estimators=1000, early_stopping_rounds=50)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    # Prever probabilidades
    probs = model.predict_proba(X_val)[:, 1]
    
    # Calcular CLV (métrica primária)
    clv = calculate_clv(probs, odds_val, outcomes_val)
    
    # Penalizar overfitting
    train_score = model.score(X_train, y_train)
    val_score = model.score(X_val, y_val)
    overfit_penalty = max(0, train_score - val_score) * 10
    
    return clv - overfit_penalty
```

---

## 5. PRUNING (Early Stopping de Trials)

```python
from optuna.pruners import MedianPruner

pruner = MedianPruner(
    n_startup_trials=5,    # Não prunar primeiros 5 trials
    n_warmup_steps=10,     # Não prunar primeiros 10 iterações
    interval_steps=1       # Checar a cada iteração
)

study = optuna.create_study(direction='maximize', pruner=pruner)
```

---

## 6. EXECUÇÃO DO ESTUDO

```python
def run_optuna_study(X_train, y_train, X_val, y_val, n_trials=50):
    """Executa estudo Optuna."""
    study = optuna.create_study(direction='maximize', pruner=MedianPruner())
    
    study.optimize(
        lambda trial: objective(trial, X_train, y_train, X_val, y_val),
        n_trials=n_trials,
        show_progress_bar=True
    )
    
    return study
```

---

## 7. ANÁLISE DE RESULTADOS

```python
# Melhores parâmetros
best_params = study.best_params
best_clv = study.best_value

# Histórico de trials
trials_df = study.trials_dataframe()

# Importância de hiperparâmetros
optuna.visualization.plot_param_importances(study)
```

---

## 8. CRITÉRIOS DE SELEÇÃO

- CLV médio no set de validação > 2%
- Diferença train-val < 0.05 (sem overfitting)
- Brier Score < mercado
- Sharpe Ratio > 0.5

---

## 9. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[XGBoost_BASELINE]] → Configuração base
