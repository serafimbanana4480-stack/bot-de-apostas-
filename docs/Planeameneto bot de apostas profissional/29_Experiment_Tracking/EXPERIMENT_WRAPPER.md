# Experiment Wrapper

**ID:** MLOPS-005 | **Fase:** #phase/2-15 | **Owner:** MLOps Engineer + Quant | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Wrapper padronizado para experimentos de ML que garante consistência, reprodutibilidade, e logging automático de todos os experimentos.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Wrapper padronizado para experimentos |
| **Stack** | Python, MLflow, Git |
| **Custo** | 0€ (open source) |

---

## 2. ARQUITETURA DO WRAPPER

### 2.1 Estrutura

```
┌─────────────────────────────────────────────────────────────┐
│ EXPERIMENT WRAPPER                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. INICIALIZAÇÃO                                     │   │
│  │    - Validação de parâmetros                         │   │
│  │    - Setup MLflow                                    │   │
│  │    - Log Git hash                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. TREINO                                           │   │
│  │    - Carregar dados                                  │   │
│  │    - Treinar modelo                                 │   │
│  │    - Validar modelo                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. AVALIAÇÃO                                        │   │
│  │    - Calcular métricas                              │   │
│  │    - Gerar artefatos                                │   │
│  │    - Log resultados                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. FINALIZAÇÃO                                      │   │
│  │    - Log modelo                                      │   │
│  │    - Gerar relatório                                │   │
│  │    - Retornar resultados                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. IMPLEMENTAÇÃO

### 3.1 Classe Base

```python
# vbq/mlops/experiments/wrapper.py
import mlflow
import hashlib
from datetime import datetime
from typing import Dict, Any
import git

class ExperimentWrapper:
    """Wrapper padronizado para experimentos"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.git_hash = self._get_git_hash()
        
    def _get_git_hash(self) -> str:
        """Obtém hash do Git"""
        try:
            repo = git.Repo(search_parent_directories=True)
            return repo.head.commit.hexsha
        except:
            return "unknown"
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa experimento"""
        
        # Validar parâmetros
        self._validate_params(params)
        
        # Iniciar run MLflow
        with mlflow.start_run(
            run_name=self._generate_run_name(),
            experiment_id=self._get_or_create_experiment()
        ) as run:
            
            # Log parâmetros
            mlflow.log_params(params)
            mlflow.log_param("git_hash", self.git_hash)
            
            # Executar experimento
            results = self._execute_experiment(params)
            
            # Log métricas
            mlflow.log_metrics(results['metrics'])
            
            # Log modelo
            mlflow.sklearn.log_model(
                results['model'],
                "model"
            )
            
            # Log artefatos
            for artifact in results.get('artifacts', []):
                mlflow.log_artifact(artifact)
            
            # Log decisão
            mlflow.log_param("decision", results['decision'])
            
            return results
    
    def _validate_params(self, params: Dict[str, Any]):
        """Valida parâmetros"""
        required_params = ['model_type', 'feature_set', 'train_period']
        
        for param in required_params:
            if param not in params:
                raise ValueError(f"Parâmetro obrigatório: {param}")
    
    def _generate_run_name(self) -> str:
        """Gera nome de run único"""
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        hash_str = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"{self.experiment_name}_{date_str}_{hash_str}"
    
    def _get_or_create_experiment(self) -> str:
        """Obtém ou cria experimento"""
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        
        if experiment is None:
            experiment_id = mlflow.create_experiment(self.experiment_name)
        else:
            experiment_id = experiment.experiment_id
        
        return experiment_id
    
    def _execute_experiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa experimento (implementar em subclasses)"""
        raise NotImplementedError("Implementar em subclasses")
```

---

## 4. EXPERIMENTO XGBOOST

### 4.1 Implementação Específica

```python
# vbq/mlops/experiments/xgboost_experiment.py
from vbq.mlops.experiments.wrapper import ExperimentWrapper
from vbq.models.xgboost import XGBoostModel

class XGBoostExperiment(ExperimentWrapper):
    """Experimento XGBoost"""
    
    def __init__(self):
        super().__init__("xgboost_experiment")
    
    def _execute_experiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa experimento XGBoost"""
        
        # Carregar dados
        data = self._load_data(params)
        
        # Treinar modelo
        model = XGBoostModel(params)
        model.train(data['X_train'], data['y_train'])
        
        # Validar modelo
        metrics = self._evaluate_model(model, data)
        
        # Gerar artefatos
        artifacts = self._generate_artifacts(model, metrics)
        
        # Decisão
        decision = self._make_decision(metrics)
        
        return {
            'model': model,
            'metrics': metrics,
            'artifacts': artifacts,
            'decision': decision
        }
    
    def _load_data(self, params: Dict[str, Any]):
        """Carrega dados para treino"""
        from vbq.data.loader import load_training_data
        
        return load_training_data(
            feature_set=params['feature_set'],
            train_period=params['train_period']
        )
    
    def _evaluate_model(self, model, data):
        """Avalia modelo"""
        from vbq.models.evaluation import evaluate_model
        
        return evaluate_model(
            model,
            data['X_test'],
            data['y_test'],
            data['odds_test']
        )
    
    def _generate_artifacts(self, model, metrics):
        """Gera artefatos"""
        artifacts = []
        
        # Feature importance
        model.plot_feature_importance("feature_importance.png")
        artifacts.append("feature_importance.png")
        
        # Confusion matrix
        model.plot_confusion_matrix("confusion_matrix.png")
        artifacts.append("confusion_matrix.png")
        
        return artifacts
    
    def _make_decision(self, metrics: Dict[str, Any]) -> str:
        """Toma decisão sobre o experimento"""
        
        if metrics['clv_mean'] > 0.01 and metrics['roi_mean'] > 0:
            return "PROMOTE_TO_STAGING"
        elif metrics['clv_mean'] > 0.005:
            return "KEEP_EXPERIMENTING"
        else:
            return "DISCARD"
```

---

## 5. USO

### 5.1 Executar Experimento

```python
# vbq/mlops/experiments/run_experiment.py
from vbq.mlops.experiments.xgboost_experiment import XGBoostExperiment

def run_xgboost_experiment():
    """Executa experimento XGBoost"""
    
    experiment = XGBoostExperiment()
    
    params = {
        'model_type': 'xgboost',
        'feature_set': 'full',
        'train_period': '2023-2025',
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1
    }
    
    results = experiment.run(params)
    
    print(f"Experimento concluído: {results['decision']}")
    print(f"Métricas: {results['metrics']}")
    
    return results
```

### 5.2 Batch de Experimentos

```python
def run_hyperparameter_search():
    """Executa grid search de hiperparâmetros"""
    
    experiment = XGBoostExperiment()
    
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1, 0.2]
    }
    
    results = []
    
    for n_estimators in param_grid['n_estimators']:
        for max_depth in param_grid['max_depth']:
            for learning_rate in param_grid['learning_rate']:
                
                params = {
                    'model_type': 'xgboost',
                    'feature_set': 'full',
                    'train_period': '2023-2025',
                    'n_estimators': n_estimators,
                    'max_depth': max_depth,
                    'learning_rate': learning_rate
                }
                
                result = experiment.run(params)
                results.append(result)
    
    return results
```

---

## 6. REPRODUTIBILIDADE

### 6.1 Seed Fixo

```python
import random
import numpy as np

def set_seed(seed: int = 42):
    """Fixa seed para reprodutibilidade"""
    random.seed(seed)
    np.random.seed(seed)
```

### 6.2 Logging de Ambiente

```python
def log_environment():
    """Loga informações do ambiente"""
    import platform
    import mlflow
    
    env_info = {
        'python_version': platform.python_version(),
        'os': platform.system(),
        'mlflow_version': mlflow.__version__,
        'numpy_version': np.__version__
    }
    
    mlflow.log_params(env_info)
```

---

## 7. RELATÓRIOS

### 7.1 Relatório de Experimento

```python
def generate_experiment_report(results: Dict[str, Any]) -> str:
    """Gera relatório de experimento"""
    
    report = f"""
# Experimento XGBoost

## Parâmetros
{json.dumps(results['params'], indent=2)}

## Métricas
{json.dumps(results['metrics'], indent=2)}

## Decisão
{results['decision']}

## Git Hash
{results['git_hash']}
"""
    
    return report
```

---

## 8. LINKS CRUZADOS

- [[29_Experiment_Tracking/INDEX]] ← Secção mãe
- [[29_Experiment_Tracking/MLFLOW_SETUP]] → Setup MLflow
- [[30_Model_Registry/INDEX]] → Model registry
- [[11_MLOps/INDEX]] → MLOps geral

---

**Custo de implementação:** 0€ (open source)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (importante para consistência)
