# Optuna Integration

**ID:** MLOPS-006 | **Fase:** #phase/2-15 | **Owner:** MLOps Engineer + Quant | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Integração de Optuna para otimização de hiperparâmetros com MLflow callbacks. Optuna fornece otimização automática de hiperparâmetros com logging automático no MLflow.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Otimização de hiperparâmetros com Optuna |
| **Stack** | Optuna, MLflow, XGBoost |
| **Custo** | 0€ (open source) |

---

## 2. ARQUITETURA DE OTIMIZAÇÃO

### 2.1 Fluxo de Otimização

```
┌─────────────────────────────────────────────────────────────┐
│ OPTUNA + MLFLOW                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. DEFINIÇÃO DO ESPAÇO DE BUSCA                    │   │
│  │    - Hiperparâmetros a otimizar                      │   │
│  │    - Ranges de valores                               │   │
│  │    - Tipo de distribuição                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. FUNÇÃO OBJETIVO                                  │   │
│  │    - Treinar modelo com parâmetros                  │   │
│  │    - Avaliar modelo                                 │   │
│  │    - Retornar métrica a otimizar                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. MLFLOW CALLBACK                                  │   │
│  │    - Log parâmetros automaticamente                  │   │
│  │    - Log métricas automaticamente                    │   │
│  │    - Log modelo automaticamente                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. OTIMIZAÇÃO                                       │   │
│  │    - Optuna seleciona próximos parâmetros          │   │
│  │    - Usa TPE (Tree-structured Parzen Estimator)    │   │
│  │    - Converge para ótimo                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. RESULTADOS                                       │   │
│  │    - Melhores parâmetros                            │   │
│  │    - Histórico de trials                            │   │
│  │    - Visualizações                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO OPTUNA

### 3.1 Instalação

```bash
pip install optuna optuna-integration
```

### 3.2 Setup do Study

```python
# vbq/mlops/optuna/study.py
import optuna

def create_study(study_name: str = "xgboost_optimization"):
    """Cria study Optuna"""
    
    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",  # Maximizar CLV
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner()
    )
    
    return study
```

---

## 4. DEFINIÇÃO DO ESPAÇO DE BUSCA

### 4.1 Espaço XGBoost

```python
# vbq/mlops/optuna/search_space.py
def define_xgboost_search_space(trial):
    """Define espaço de busca para XGBoost"""
    
    params = {
        # Número de árvores
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        
        # Profundidade máxima
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        
        # Learning rate
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        
        # Subsample
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        
        # Colsample_bytree
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        
        # Min_child_weight
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        
        # Gamma
        'gamma': trial.suggest_float('gamma', 0, 5),
        
        # Reg_alpha
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
        
        # Reg_lambda
        'reg_lambda': trial.suggest_float('reg_lambda', 0, 1)
    }
    
    return params
```

---

## 5. FUNÇÃO OBJETIVO

### 5.1 Implementação

```python
# vbq/mlops/optuna/objective.py
import mlflow
from optuna.integration.mlflow import MLflowCallback
from vbq.models.xgboost import XGBoostModel
from vbq.data.loader import load_training_data

def objective(trial, data):
    """Função objetivo para otimização"""
    
    # Definir parâmetros
    params = define_xgboost_search_space(trial)
    
    # Iniciar run MLflow
    with mlflow.start_run(run_name=f"trial_{trial.number}"):
        
        # Log parâmetros
        mlflow.log_params(params)
        
        # Treinar modelo
        model = XGBoostModel(params)
        model.train(data['X_train'], data['y_train'])
        
        # Avaliar modelo
        metrics = evaluate_model(model, data)
        
        # Log métricas
        mlflow.log_metrics(metrics)
        
        # Log modelo
        mlflow.sklearn.log_model(model.model, "model")
        
        # Retornar valor a otimizar (CLV)
        return metrics['clv_mean']
```

---

## 6. MLFLOW CALLBACK

### 6.1 Configuração

```python
# vbq/mlops/optuna/mlflow_callback.py
from optuna.integration.mlflow import MLflowCallback

def get_mlflow_callback():
    """Retorna callback MLflow para Optuna"""
    
    mlflow_callback = MLflowCallback(
        tracking_uri="postgresql://user:password@localhost:5432/mlflow",
        metric_for_best_trial="clv_mean",
        mlflow_kwargs={
            "experiment_name": "xgboost_optimization"
        }
    )
    
    return mlflow_callback
```

---

## 7. EXECUÇÃO DA OTIMIZAÇÃO

### 7.1 Otimização Completa

```python
# vbq/mlops/optuna/optimize.py
from vbq.mlops.optuna.study import create_study
from vbq.mlops.optuna.objective import objective
from vbq.mlops.optuna.mlflow_callback import get_mlflow_callback
from vbq.data.loader import load_training_data

def run_optimization(n_trials: int = 100):
    """Executa otimização de hiperparâmetros"""
    
    # Carregar dados
    data = load_training_data(feature_set='full', train_period='2023-2025')
    
    # Criar study
    study = create_study()
    
    # Obter callback MLflow
    mlflow_callback = get_mlflow_callback()
    
    # Executar otimização
    study.optimize(
        lambda trial: objective(trial, data),
        n_trials=n_trials,
        callbacks=[mlflow_callback]
    )
    
    return study
```

### 7.2 Otimização com Pruning

```python
def run_optimization_with_pruning(n_trials: int = 100):
    """Executa otimização com pruning"""
    
    study = optuna.create_study(
        study_name="xgboost_optimization",
        direction="maximize",
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_warmup_steps=10,
            interval_steps=1
        )
    )
    
    study.optimize(
        lambda trial: objective(trial, data),
        n_trials=n_trials,
        callbacks=[mlflow_callback]
    )
    
    return study
```

---

## 8. ANÁLISE DE RESULTADOS

### 8.1 Melhores Parâmetros

```python
def get_best_params(study):
    """Obtém melhores parâmetros"""
    
    best_trial = study.best_trial
    best_params = best_trial.params
    
    print(f"Best trial: {best_trial.number}")
    print(f"Best value (CLV): {best_trial.value}")
    print(f"Best params: {best_params}")
    
    return best_params
```

### 8.2 Histórico de Trials

```python
def get_trials_history(study):
    """Obtém histórico de trials"""
    
    trials_df = study.trials_dataframe()
    
    return trials_df
```

### 8.3 Visualizações

```python
import optuna.visualization as vis

def plot_optimization_history(study):
    """Plota histórico de otimização"""
    fig = vis.plot_optimization_history(study)
    fig.write_html("optimization_history.html")

def plot_param_importances(study):
    """Plota importância de parâmetros"""
    fig = vis.plot_param_importances(study)
    fig.write_html("param_importances.html")

def plot_parallel_coordinate(study):
    """Plota coordenadas paralelas"""
    fig = vis.plot_parallel_coordinate(study)
    fig.write_html("parallel_coordinate.html")
```

---

## 9. INTEGRAÇÃO COM PIPELINES

### 9.1 Pipeline de Otimização

```python
# vbq/mlops/pipelines/optimization_pipeline.py
from prefect import flow, task

@task
def optimization_task(n_trials: int = 100):
    """Tarefa de otimização"""
    
    study = run_optimization(n_trials)
    
    best_params = get_best_params(study)
    
    return best_params

@flow(name="optimization_pipeline")
def optimization_pipeline(n_trials: int = 100):
    """Pipeline de otimização"""
    
    best_params = optimization_task(n_trials)
    
    # Treinar modelo final com melhores parâmetros
    final_model = train_final_model(best_params)
    
    return final_model
```

---

## 10. CONFIGURAÇÃO

### 10.1 Variáveis de Ambiente

```bash
# .env
MLFLOW_TRACKING_URI=postgresql://user:password@localhost:5432/mlflow
OPTUNA_STORAGE=sqlite:///optuna.db
```

### 10.2 Configuração do Optuna

```python
# vbq/mlops/optuna/config.py
import os

OPTUNA_CONFIG = {
    'storage': os.getenv('OPTUNA_STORAGE', 'sqlite:///optuna.db'),
    'n_trials': 100,
    'timeout': 3600,  # 1 hora
    'n_jobs': 1
}
```

---

## 11. LINKS CRUZADOS

- [[29_Experiment_Tracking/INDEX]] ← Secção mãe
- [[29_Experiment_Tracking/MLFLOW_CONFIG]] → Config MLflow
- [[30_Model_Registry/INDEX]] → Model registry
- [[11_MLOps/INDEX]] → MLOps geral

---

**Custo de implementação:** 0€ (open source)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (útil para otimização)
