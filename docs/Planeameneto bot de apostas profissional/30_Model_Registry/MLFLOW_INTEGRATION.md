# MLflow Integration

**ID:** MLOPS-003 | **Fase:** #phase/2-15 | **Owner:** MLOps Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Integração detalhada de MLflow com o projeto para tracking de experimentos, model registry, e artifact management. MLflow fornece uma plataforma completa para o ciclo de vida de ML.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Integração completa com MLflow |
| **Stack** | MLflow, PostgreSQL, MinIO/S3 |
| **Custo** | 0€ (self-hosted) |

---

## 2. ARQUITETURA MLFLOW

### 2.1 Componentes

```
┌─────────────────────────────────────────────────────────────┐
│ MLFLOW STACK                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. MLFLOW TRACKING SERVER                            │   │
│  │    - Tracking de experimentos                         │   │
│  │    - Métricas e parâmetros                           │   │
│  │    - Artifacts (modelos, gráficos)                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. MLFLOW MODEL REGISTRY                             │   │
│  │    - Gestão de versões de modelos                   │   │
│  │    - Promoção staging → production                   │   │
│  │    - Rollback                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. POSTGRESQL (Backend)                            │   │
│  │    - Armazenamento de runs                           │   │
│  │    - Model registry metadata                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. MINIO/S3 (Artifacts)                              │   │
│  │    - Armazenamento de modelos                        │   │
│  │    - Gráficos e artefatos                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO MLFLOW

### 3.1 Instalação

```bash
pip install mlflow psycopg2-binary minio
```

### 3.2 Configuração do Servidor

```python
# vbq/mlops/mlflow/config.py
import os

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "postgresql://user:password@localhost:5432/mlflow")
MLFLOW_S3_ENDPOINT_URL = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
MLFLOW_ARTIFACT_ROOT = os.getenv("MLFLOW_ARTIFACT_ROOT", "s3://mlflow-artifacts")
```

### 3.3 Inicialização do Servidor

```bash
# Iniciar servidor MLflow
mlflow server \
  --backend-store-uri postgresql://user:password@localhost:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000
```

---

## 4. TRACKING DE EXPERIMENTOS

### 4.1 Iniciar Run

```python
# vbq/mlops/mlflow/tracking.py
import mlflow
from vbq.models.xgboost import XGBoostModel

def train_and_log(params: dict):
    """Treina modelo e regista com MLflow"""
    
    # Iniciar run
    with mlflow.start_run(run_name=f"xgboost_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
        
        # Log parâmetros
        mlflow.log_params(params)
        
        # Treinar modelo
        model = XGBoostModel(params)
        model.train()
        
        # Log métricas
        metrics = model.evaluate()
        mlflow.log_metrics(metrics)
        
        # Log modelo
        mlflow.sklearn.log_model(
            model.model,
            "model",
            registered_model_name="nba_value_model"
        )
        
        # Log artefatos
        mlflow.log_artifact("features_importance.png")
        mlflow.log_artifact("confusion_matrix.png")
        
        return run.info.run_id
```

### 4.2 Log Métricas Customizadas

```python
def log_custom_metrics(metrics: dict):
    """Loga métricas customizadas"""
    
    # Métricas de performance
    mlflow.log_metric("clv_mean", metrics['clv_mean'])
    mlflow.log_metric("roi_mean", metrics['roi_mean'])
    mlflow.log_metric("sharpe_ratio", metrics['sharpe_ratio'])
    
    # Métricas de calibração
    mlflow.log_metric("brier_score", metrics['brier_score'])
    mlflow.log_metric("ece", metrics['ece'])
    
    # Métricas de validação
    mlflow.log_metric("purged_cv_score", metrics['purged_cv_score'])
    mlflow.log_metric("bootstrap_ci_lower", metrics['bootstrap_ci_lower'])
    mlflow.log_metric("bootstrap_ci_upper", metrics['bootstrap_ci_upper'])
```

---

## 5. MODEL REGISTRY

### 5.1 Promoção de Modelo

```python
# vbq/mlops/mlflow/registry.py
from mlflow.tracking import MlflowClient

client = MlflowClient()

def promote_model_to_staging(run_id: str):
    """Promove modelo para staging"""
    
    # Registrar modelo
    model_uri = f"runs:/{run_id}/model"
    model_version = mlflow.register_model(
        model_uri,
        "nba_value_model"
    )
    
    # Promover para staging
    client.transition_model_version_stage(
        name="nba_value_model",
        version=model_version.version,
        stage="Staging"
    )
    
    return model_version.version

def promote_model_to_production(version: str):
    """Promove modelo para produção"""
    
    client.transition_model_version_stage(
        name="nba_value_model",
        version=version,
        stage="Production"
    )
```

### 5.2 Rollback

```python
def rollback_model(target_version: str):
    """Rollback para versão anterior"""
    
    client.transition_model_version_stage(
        name="nba_value_model",
        version=target_version,
        stage="Production",
        archive_existing_versions=True
    )
```

---

## 6. INTEGRAÇÃO COM PIPELINES

### 6.1 Pipeline com MLflow

```python
# vbq/mlops/pipelines/training_pipeline.py
from prefect import flow, task
import mlflow

@task
def train_model(params: dict):
    """Treina modelo com MLflow tracking"""
    
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        
        model = XGBoostModel(params)
        model.train()
        
        metrics = model.evaluate()
        mlflow.log_metrics(metrics)
        
        mlflow.sklearn.log_model(model.model, "model")
        
        return run.info.run_id

@flow(name="training_pipeline")
def training_pipeline(params: dict):
    """Pipeline de treino com MLflow"""
    
    run_id = train_model(params)
    
    # Promover para staging se métricas forem boas
    # (verificar critérios)
    
    return run_id
```

---

## 7. CONFIGURAÇÃO DE ARTIFACTS

### 7.1 MinIO (S3-compatible)

```bash
# docker-compose.yml
services:
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  minio_data:
```

### 7.2 Configuração MLflow para MinIO

```python
# vbq/mlops/mlflow/minio_config.py
import os

os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
```

---

## 8. MONITORIZAÇÃO

### 8.1 Dashboard MLflow

O MLflow fornece um dashboard web em `http://localhost:5000` com:
- Lista de experimentos e runs
- Métricas e parâmetros
- Comparação de runs
- Artifacts e modelos

### 8.2 Métricas de Uso

```python
# vbq/mlops/mlflow/usage_metrics.py
def get_mlflow_usage_metrics():
    """Obtém métricas de uso do MLflow"""
    
    client = MlflowClient()
    
    # Número de experimentos
    experiments = client.search_experiments()
    
    # Número de runs
    runs = client.search_runs(experiment_ids=[e.experiment_id for e in experiments])
    
    # Espaço usado
    # (requer integração com MinIO)
    
    return {
        'num_experiments': len(experiments),
        'num_runs': len(runs),
        'storage_used': 'TODO'
    }
```

---

## 9. AUTOMAÇÃO

### 9.1 Auto-Registro

```python
# vbq/mlops/mlflow/auto_register.py
def auto_register_best_model():
    """Registra automaticamente o melhor modelo"""
    
    client = MlflowClient()
    
    # Buscar runs do experimento
    runs = client.search_runs(
        experiment_ids=["1"],
        order_by=["metrics.clv_mean DESC"]
    )
    
    # Pegar o melhor run
    best_run = runs[0]
    
    # Registrar modelo
    model_uri = f"runs:/{best_run.info.run_id}/model"
    mlflow.register_model(model_uri, "nba_value_model")
```

---

## 10. LINKS CRUZADOS

- [[30_Model_Registry/INDEX]] ← Secção mãe
- [[30_Model_Registry/REGISTRY_GESTAO]] → Gestão de registry
- [[29_Experiment_Tracking/INDEX]] → Tracking de experimentos
- [[11_MLOps/INDEX]] → MLOps geral

---

**Custo de implementação:** 0€ (self-hosted)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (importante para MLOps)
