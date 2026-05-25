# AutoML Framework

**ID:** `AUTOML-001` | **Fase:** #phase/2-6 | **Owner:** ML Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Framework de AutoML para tuning automático de hiperparâmetros de modelos de Machine Learning usando Optuna, com Purged Walk-Forward Cross-Validation, early stopping, e integração com MLflow para experiment tracking. Baseado na implementação do projeto NBA-Betting/NBA_Betting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Tuning automático de hiperparâmetros sem intervenção manual |
| **Framework** | Optuna (Bayesian optimization) |
| **CV Strategy** | Purged Walk-Forward (anti-leakage temporal) |
| **Early Stopping** | Pruning de trials sem melhoria |
| **Experiment Tracking** | MLflow |
| **Custo** | 0€ (Optuna é open-source) |

---

## 2. OVERVIEW DO AUTOML FRAMEWORK

### 2.1 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    OPTUNA STUDY                            │
│  (Coordena otimização bayesiana de hiperparâmetros)       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              OBJECTIVE FUNCTION                             │
│  (Treina modelo com hiperparâmetros e retorna score)       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│          PURGED WALK-FORWARD CV                             │
│  (Validação temporal sem leakage)                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MODEL TRAINING                                 │
│  (XGBoost, LightGBM, CatBoost, etc.)                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MLflow TRACKING                                │
│  (Registra métricas, artefactos, modelos)                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Componentes

| Componente | Descrição | Tecnologia |
|-------------|-----------|------------|
| **Optuna Study** | Otimização bayesiana | Optuna |
| **Objective Function** | Função a minimizar | Custom Python |
| **CV Strategy** | Validação temporal | Purged Walk-Forward |
| **Pruning** | Early stopping de trials | Optuna Pruning |
| **Tracking** | Experiment tracking | MLflow |
| **Search Space** | Espaço de hiperparâmetros | Por modelo |

---

## 3. SEARCH SPACE POR MODELO

### 3.1 XGBoost

```python
def xgboost_search_space(trial):
    """
    Espaço de busca para XGBoost.
    """
    return {
        # Hiperparâmetros de árvore
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=50),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        
        # Regularização
        'gamma': trial.suggest_float('gamma', 0.0, 0.5, step=0.01),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0, step=0.05),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0, step=0.05),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0, step=0.01),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0, step=0.01),
        
        # Learning rate
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, step=0.01),
        
        # Balanceamento de classes
        'scale_pos_weight': trial.suggest_float('scale_pos_weight', 0.5, 2.0, step=0.1)
    }
```

### 3.2 LightGBM

```python
def lightgbm_search_space(trial):
    """
    Espaço de busca para LightGBM.
    """
    return {
        # Hiperparâmetros de árvore
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=50),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'num_leaves': trial.suggest_int('num_leaves', 20, 200, step=10),
        
        # Regularização
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0, step=0.05),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0, step=0.05),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0, step=0.01),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0, step=0.01),
        
        # Learning rate
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, step=0.01),
        
        # Feature sampling
        'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0, step=0.05),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0, step=0.05),
        'bagging_freq': trial.suggest_int('bagging_freq', 1, 10)
    }
```

### 3.3 CatBoost

```python
def catboost_search_space(trial):
    """
    Espaço de busca para CatBoost.
    """
    return {
        # Hiperparâmetros de árvore
        'iterations': trial.suggest_int('iterations', 100, 1000, step=50),
        'depth': trial.suggest_int('depth', 4, 12),
        
        # Regularização
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0, step=0.5),
        'random_strength': trial.suggest_float('random_strength', 0.0, 1.0, step=0.1),
        
        # Learning rate
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, step=0.01),
        
        # Bagging
        'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0, step=0.1),
        
        # Border count
        'border_count': trial.suggest_int('border_count', 32, 256, step=32)
    }
```

---

## 4. PIPELINE DE TUNING AUTOMÁTICO

### 4.1 Objective Function

```python
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

def objective(trial, X_train, y_train, model_type='xgboost'):
    """
    Função objetivo para Optuna.
    
    Args:
        trial: Trial Optuna
        X_train: Features de treino
        y_train: Target de treino
        model_type: Tipo de modelo (xgboost, lightgbm, catboost)
    
    Returns:
        float: Score a minimizar (ex: -log_loss)
    """
    # Obter hiperparâmetros do search space
    if model_type == 'xgboost':
        params = xgboost_search_space(trial)
        model = XGBClassifier(**params)
    elif model_type == 'lightgbm':
        params = lightgbm_search_space(trial)
        model = LGBMClassifier(**params)
    elif model_type == 'catboost':
        params = catboost_search_space(trial)
        model = CatBoostClassifier(**params, verbose=False)
    
    # Purged Walk-Forward CV
    cv_scores = purged_walk_forward_cv(
        model, X_train, y_train,
        n_splits=5,
        purge_gap=30,  # 30 dias de gap
        trial=trial  # Para pruning
    )
    
    # Retornar score médio negativo (Optuna minimiza)
    return -np.mean(cv_scores)
```

### 4.2 Purged Walk-Forward CV

```python
from sklearn.model_selection import TimeSeriesSplit
import numpy as np
from datetime import datetime, timedelta

def purged_walk_forward_cv(model, X, y, n_splits=5, purge_gap=30, trial=None):
    """
    Cross-validation temporal com purged gaps para evitar leakage.
    
    Args:
        model: Modelo a treinar
        X: Features
        y: Target
        n_splits: Número de splits
        purge_gap: Dias de gap entre treino e teste
        trial: Trial Optuna para pruning
    
    Returns:
        list: Scores de cada fold
    """
    scores = []
    
    # Assumir que X tem índice temporal
    dates = X.index if hasattr(X, 'index') else range(len(X))
    
    # Criar splits temporais
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=len(X)//(n_splits+1))
    
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        # Aplicar purged gap
        train_end = train_idx[-1]
        test_start = train_end + purge_gap
        
        if test_start >= len(X):
            continue
        
        test_idx_purged = range(test_start, min(test_start + len(test_idx), len(X)))
        
        if len(test_idx_purged) == 0:
            continue
        
        # Treinar modelo
        X_train_fold = X.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        X_test_fold = X.iloc[test_idx_purged]
        y_test_fold = y.iloc[test_idx_purged]
        
        model.fit(X_train_fold, y_train_fold)
        
        # Prever e calcular score
        y_pred = model.predict_proba(X_test_fold)[:, 1]
        score = log_loss(y_test_fold, y_pred)
        scores.append(score)
        
        # Pruning: reportar score intermediário para Optuna
        if trial is not None:
            trial.report(score, fold)
            
            # Se trial não está a melhorar, parar
            if trial.should_prune():
                raise optuna.TrialPruned()
    
    return scores
```

---

## 5. EARLY STOPPING E PRUNING

### 5.1 Optuna Pruning

```python
from optuna.pruners import MedianPruner
from optuna.pruners import HyperbandPruner

# Configurar pruner
pruner = MedianPruner(
    n_startup_trials=10,      # Não prunar nos primeiros 10 trials
    n_warmup_steps=30,        # Não prunar nos primeiros 30 steps
    interval_steps=10         # Verificar a cada 10 steps
)

# Ou usar Hyperband (mais agressivo)
pruner = HyperbandPruner(
    min_resource=100,          # Mínimo de iterações
    max_resource=1000,         # Máximo de iterações
    reduction_factor=3         # Fator de redução
)
```

### 5.2 Early Stopping no Modelo

```python
# XGBoost com early stopping
model = XGBClassifier(
    **params,
    early_stopping_rounds=50,  # Parar se não melhorar em 50 rounds
    eval_metric='logloss'
)

# LightGBM com early stopping
model = LGBMClassifier(
    **params,
    early_stopping_rounds=50,
    verbose=-1
)

# CatBoost com early stopping
model = CatBoostClassifier(
    **params,
    early_stopping_rounds=50,
    verbose=False
)
```

---

## 6. MODEL SELECTION E ENSEMBLE

### 6.1 AutoML Study

```python
def run_automl_study(X, y, n_trials=100, model_type='xgboost'):
    """
    Executa estudo Optuna para AutoML.
    
    Args:
        X: Features
        y: Target
        n_trials: Número de trials
        model_type: Tipo de modelo
    
    Returns:
        Optuna study com melhores hiperparâmetros
    """
    # Criar estudo
    study = optuna.create_study(
        direction='minimize',  # Minimizar log_loss
        sampler=TPESampler(seed=42),  # Bayesian optimization
        pruner=MedianPruner()
    )
    
    # Definir objective function parcial
    objective_func = lambda trial: objective(trial, X, y, model_type)
    
    # Executar otimização
    study.optimize(
        objective_func,
        n_trials=n_trials,
        timeout=3600,  # Timeout de 1 hora
        show_progress_bar=True
    )
    
    return study
```

### 6.2 Ensemble de Modelos

```python
def ensemble_automl(X_train, y_train, X_test, n_trials_per_model=50):
    """
    Treina ensemble de múltiplos modelos com AutoML.
    
    Args:
        X_train: Features de treino
        y_train: Target de treino
        X_test: Features de teste
        n_trials_per_model: Trials por modelo
    
    Returns:
        dict: {model_name: model, predictions}
    """
    models = {}
    predictions = {}
    
    # Treinar XGBoost
    study_xgb = run_automl_study(X_train, y_train, n_trials_per_model, 'xgboost')
    best_params_xgb = study_xgb.best_params
    models['xgboost'] = XGBClassifier(**best_params_xgb)
    models['xgboost'].fit(X_train, y_train)
    predictions['xgboost'] = models['xgboost'].predict_proba(X_test)[:, 1]
    
    # Treinar LightGBM
    study_lgb = run_automl_study(X_train, y_train, n_trials_per_model, 'lightgbm')
    best_params_lgb = study_lgb.best_params
    models['lightgbm'] = LGBMClassifier(**best_params_lgb)
    models['lightgbm'].fit(X_train, y_train)
    predictions['lightgbm'] = models['lightgbm'].predict_proba(X_test)[:, 1]
    
    # Treinar CatBoost
    study_cat = run_automl_study(X_train, y_train, n_trials_per_model, 'catboost')
    best_params_cat = study_cat.best_params
    models['catboost'] = CatBoostClassifier(**best_params_cat, verbose=False)
    models['catboost'].fit(X_train, y_train)
    predictions['catboost'] = models['catboost'].predict_proba(X_test)[:, 1]
    
    # Ensemble simples (média)
    predictions['ensemble'] = np.mean([
        predictions['xgboost'],
        predictions['lightgbm'],
        predictions['catboost']
    ], axis=0)
    
    return models, predictions
```

---

## 7. INTEGRAÇÃO COM MLFLOW

### 7.1 MLflow Tracking

```python
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.lightgbm

def objective_with_mlflow(trial, X_train, y_train, model_type='xgboost'):
    """
    Objective function com MLflow tracking.
    """
    # Iniciar run MLflow
    with mlflow.start_run(nested=True):
        # Log hiperparâmetros
        if model_type == 'xgboost':
            params = xgboost_search_space(trial)
            mlflow.log_params(params)
            model = XGBClassifier(**params)
        elif model_type == 'lightgbm':
            params = lightgbm_search_space(trial)
            mlflow.log_params(params)
            model = LGBMClassifier(**params)
        
        # Treinar modelo
        cv_scores = purged_walk_forward_cv(model, X_train, y_train, trial=trial)
        mean_score = np.mean(cv_scores)
        
        # Log métricas
        mlflow.log_metric('log_loss', mean_score)
        mlflow.log_metric('log_loss_std', np.std(cv_scores))
        
        # Log modelo
        mlflow.sklearn.log_model(model, 'model')
        
        return mean_score
```

### 7.2 MLflow Experiment

```python
# Criar experimento
mlflow.set_experiment('vbq-automl')

# Executar estudo com MLflow
study = optuna.create_study(direction='minimize')
study.optimize(
    lambda trial: objective_with_mlflow(trial, X, y),
    n_trials=100
)

# Log melhores resultados no MLflow
with mlflow.start_run():
    mlflow.log_params(study.best_params)
    mlflow.log_metric('best_log_loss', study.best_value)
    
    # Treinar modelo final com melhores params
    best_model = XGBClassifier(**study.best_params)
    best_model.fit(X, y)
    mlflow.xgboost.log_model(best_model, 'best_model')
```

---

## 8. CLI INTEGRATION

### 8.1 Comando AutoML

```bash
vbq-cli automl tune [OPTIONS]

Options:
  --model TEXT          Modelo a tunar (xgboost/lightgbm/catboost/ensemble). Default: xgboost
  --trials INTEGER      Número de trials. Default: 100
  --timeout INTEGER     Timeout em segundos. Default: 3600
  --mlflow              Habilitar MLflow tracking
  --output FILE         Output dos melhores parâmetros
  --verbose             Output detalhado

Examples:
  # Tuning XGBoost com 100 trials
  vbq-cli automl tune --model xgboost --trials 100

  # Tuning ensemble com MLflow
  vbq-cli automl tune --model ensemble --trials 50 --mlflow

  # Tuning com timeout de 2 horas
  vbq-cli automl tune --model lightgbm --timeout 7200
```

### 8.2 Output Esperado

```
✅ AutoML iniciado às 2024-01-15 14:00:00
📊 Modelo: XGBoost
🔬 Trials: 100
⏱️  Timeout: 3600s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPTIMIZAÇÃO EM PROGRESSO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trial 10/100: log_loss = 0.6234 (best: 0.6189)
Trial 20/100: log_loss = 0.6156 (best: 0.6156) ✅
Trial 30/100: log_loss = 0.6189 (best: 0.6156)
Trial 40/100: log_loss = 0.6123 (best: 0.6123) ✅
...
Trial 100/100: log_loss = 0.6101 (best: 0.6101) ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MELHORES HIPERPARÂMETROS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
n_estimators: 750
max_depth: 6
min_child_weight: 3
gamma: 0.15
subsample: 0.85
colsample_bytree: 0.90
learning_rate: 0.05
reg_alpha: 0.10
reg_lambda: 0.20
scale_pos_weight: 0.9

MELHOR SCORE: log_loss = 0.6101

⏱️  Duração: 58m 32s
💾 Modelo guardado em: /opt/vbq/models/xgboost_automl_20240115.pkl
📝 Log: /var/log/vbq/automl_tune_20240115.log
```

---

## 9. MONITORIZAÇÃO

### 9.1 Métricas AutoML

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| automl_trials_completed | Trials completados | > 80% |
| automl_best_score | Melhor score atingido | < target |
| automl_improvement_rate | Taxa de melhoria | > 5% |
| automl_pruning_rate | Taxa de pruning | < 30% |

### 9.2 Dashboard AutoML

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTOML DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ESTUDO ATUAL:
- Modelo: XGBoost
- Trials: 87/100 (87%)
- Melhor score: 0.6101
- Target score: 0.6200 ✅
- Tempo decorrido: 52m 18s

📈 PROGRESSO:
- Melhoria: 5.3% vs baseline (0.6432)
- Trials pruned: 23 (26%)
- Tempo estimado restante: 8m 42s

🎯 TOP 5 TRIALS:
1. Trial #78: 0.6101 ✅
2. Trial #65: 0.6105
3. Trial #52: 0.6112
4. Trial #41: 0.6118
5. Trial #33: 0.6123

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 10. EXEMPLOS DE CÓDIGO

### 10.1 Script de Tuning Completo

```python
# scripts/automl_tune.py
import optuna
from vbq.data.loader import load_training_data
from vbq.automl.objective import objective_with_mlflow
from vbq.database import SessionLocal

def main():
    # Carregar dados
    db = SessionLocal()
    X, y = load_training_data(db)
    db.close()
    
    # Criar estudo
    study = optuna.create_study(
        direction='minimize',
        sampler=TPESampler(seed=42),
        pruner=MedianPruner()
    )
    
    # Configurar MLflow
    mlflow.set_experiment('vbq-automl')
    
    # Executar otimização
    study.optimize(
        lambda trial: objective_with_mlflow(trial, X, y, 'xgboost'),
        n_trials=100,
        timeout=3600,
        show_progress_bar=True
    )
    
    # Guardar melhores parâmetros
    best_params = study.best_params
    with open('best_params.json', 'w') as f:
        json.dump(best_params, f)
    
    print(f"✅ Melhor score: {study.best_value:.4f}")
    print(f"📊 Melhores parâmetros: {best_params}")

if __name__ == '__main__':
    main()
```

---

## 11. TROUBLESHOOTING

### 11.1 AutoML Converge para Mau Score

```bash
# Verificar qualidade dos dados
vbq-cli report data-quality

# Aumentar número de trials
vbq-cli automl tune --trials 200

# Ajustar search space (expandir)
# Editar automl/search_spaces.py
```

### 11.2 AutoML Muito Lento

```bash
# Reduzir número de trials
vbq-cli automl tune --trials 50

# Adicionar pruning mais agressivo
# Editar config.yaml: automl.pruner = hyperband

# Reduzir timeout
vbq-cli automl tune --timeout 1800
```

### 11.3 Overfitting no AutoML

```bash
# Aumentar purge gap no CV
# Editar config.yaml: automl.purge_gap_days = 60

# Aumentar regularização no search space
# Editar automl/search_spaces.py (aumentar reg_alpha, reg_lambda)

# Usar mais folds no CV
vbq-cli automl tune --cv-splits 10
```

---

## 12. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secção mãe
- [[05_Machine_Learning/OPTUNA_TUNING]] → Documentação Optuna existente
- [[05_Machine_Learning/XGBoost_BASELINE]] → Modelo base
- [[06_Backtesting/INDEX]] → Validação de modelos
- [[30_Model_Registry/INDEX]] → Registro de modelos
- [[29_Experiment_Tracking/INDEX]] → Tracking de experimentos

---

**Custo de implementação:** 0€ (Optuna e MLflow são open-source)  
**Tempo estimado de implementação:** 2 semanas  
**Prioridade:** ALTA (fundamental para performance de modelos)
