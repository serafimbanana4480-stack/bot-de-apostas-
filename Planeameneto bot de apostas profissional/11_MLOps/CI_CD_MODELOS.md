# CI_CD_MODELOS — Pipeline CI/CD para Modelos

**ID:** `MLO-002` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Automatizar o ciclo de vida completo dos modelos de machine learning: desde o treino até ao deploy em produção, garantindo que cada versão é testada, validada e promovida de forma controlada. O pipeline CI/CD de modelos é diferente do pipeline de código da aplicação porque envolve treino, validação de métricas e testes específicos de ML.

---

## 2. ARQUITETURA DO PIPELINE

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE CI/CD DE MODELOS                    │
└─────────────────────────────────────────────────────────────────┘

1. TRIGGER
   ├── Scheduled (cron semanal - segunda 04:00)
   ├── Triggered (drift detectado ou CLV < 0%)
   └── Manual (git push para branch feature/model-XXX)

2. TREINO (Prefect Flow)
   ├── Pull dados históricos (últimos 3 anos)
   ├── Feature engineering reprodutível
   ├── Split treino/validação/teste (temporal)
   ├── Treino modelo com hiperparâmetros fixos
   ├── Logging de métricas no MLflow
   └── Registo do modelo no MLflow Registry

3. VALIDAÇÃO AUTOMÁTICA
   ├── Testes de qualidade de dados (pytest)
   ├── Testes de performance (backtest hold-out)
   ├── Comparação com modelo em produção
   └── Validação de drift (PSI, KS test)

4. PROMOÇÃO
   ├── Se métricas > threshold → Promove para STAGING
   ├── Se métricas < threshold → Falha pipeline, alerta
   └── Registo no MLflow como "Archived"

5. DEPLOY STAGING
   ├── Docker build com novo modelo
   ├── Deploy em ambiente staging (shadow mode)
   ├── Execução por 7 dias sem apostas reais
   ├── Monitorização de CLV shadow
   └── Se CLV shadow > CLV prod → Promove para PROD

6. DEPLOY PRODUÇÃO
   ├── Blue-green deployment
   ├── Modelo novo serve 10% do tráfego (canary)
   ├── Monitorização contínua por 48h
   ├── Se performance estável → 100% do tráfego
   └── Se performance degrada → Rollback automático

7. MONITORIZAÇÃO CONTÍNUA
   ├── Métricas de drift (PSI, KS)
   ├── Métricas de performance (CLV, accuracy)
   ├── Alertas automáticos
   └── Trigger de retraining se necessário
```

---

## 3. IMPLEMENTAÇÃO COM PREFECT

### 3.1 Flow Principal de Retraining

```python
# flows/model_retraining.py
from prefect import flow, task
from prefect.artifacts import create_markdown_artifact
import mlflow
from mlflow.tracking import MlflowClient

@task
def prepare_training_data():
    """Prepara dados de treino com split temporal"""
    from src.data.data_loader import load_historical_data
    from src.features.feature_engineering import create_features
    
    df = load_historical_data(years=3)
    df = create_features(df)
    
    # Split temporal para evitar leakage
    train = df[df['date'] < '2024-01-01']
    val = df[(df['date'] >= '2024-01-01') & (df['date'] < '2024-07-01')]
    test = df[df['date'] >= '2024-07-01']
    
    return train, val, test

@task
def train_model(train_data, val_data):
    """Treina modelo e regista no MLflow"""
    from src.models.model_trainer import ModelTrainer
    
    mlflow.set_experiment("value-betting-retraining")
    
    with mlflow.start_run():
        trainer = ModelTrainer()
        model = trainer.train(train_data, val_data)
        
        # Logging de métricas
        metrics = trainer.evaluate(model, val_data)
        mlflow.log_metrics(metrics)
        
        # Logging de parâmetros
        mlflow.log_params(trainer.get_params())
        
        # Registo do modelo
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="value-betting-model"
        )
        
        return model, metrics

@task
def validate_model(model, test_data):
    """Valida modelo contra modelo em produção"""
    from src.models.model_validator import ModelValidator
    
    validator = ModelValidator()
    
    # Comparar com modelo em produção
    prod_model = mlflow.sklearn.load_model("models:/value-betting-model/Production")
    prod_metrics = validator.evaluate(prod_model, test_data)
    new_metrics = validator.evaluate(model, test_data)
    
    # Criar artifact de comparação
    comparison = f"""
    # Comparação de Modelos
    
    | Métrica | Modelo Produção | Novo Modelo | Delta |
    |---------|----------------|-------------|-------|
    | CLV     | {prod_metrics['clv']:.2%} | {new_metrics['clv']:.2%} | {new_metrics['clv'] - prod_metrics['clv']:.2%} |
    | Accuracy| {prod_metrics['accuracy']:.2%} | {new_metrics['accuracy']:.2%} | {new_metrics['accuracy'] - prod_metrics['accuracy']:.2%} |
    | Precision| {prod_metrics['precision']:.2%} | {new_metrics['precision']:.2%} | {new_metrics['precision'] - prod_metrics['precision']:.2%} |
    """
    
    create_markdown_artifact(
        key="model-comparison",
        markdown=comparison
    )
    
    # Validar se novo modelo é superior
    improvement = new_metrics['clv'] - prod_metrics['clv']
    return improvement > 0.02  # 2% de melhoria mínima

@task
def promote_to_staging(model):
    """Promove modelo para staging no MLflow Registry"""
    client = MlflowClient()
    
    # Obter última versão
    latest_version = client.get_latest_versions(
        "value-betting-model",
        stages=["None"]
    )[0].version
    
    # Transicionar para Staging
    client.transition_model_version_stage(
        name="value-betting-model",
        version=latest_version,
        stage="Staging"
    )
    
    return latest_version

@flow(name="model-retraining-pipeline")
def model_retraining_pipeline():
    """Pipeline completo de retraining de modelo"""
    # 1. Preparar dados
    train, val, test = prepare_training_data()
    
    # 2. Treinar modelo
    model, metrics = train_model(train, val)
    
    # 3. Validar modelo
    is_valid = validate_model(model, test)
    
    if not is_valid:
        raise ValueError("Novo modelo não supera modelo em produção")
    
    # 4. Promover para staging
    version = promote_to_staging(model)
    
    return version
```

### 3.2 Configuração de Schedule

```python
# flows/schedule.py
from prefect import flow
from prefect.deployments import Deployment
from prefect.orion.schemas.schedules import IntervalSchedule
from datetime import timedelta, time
from prefect.orion.schemas.schedules import CronSchedule

from flows.model_retraining import model_retraining_pipeline

# Schedule semanal: segunda-feira às 04:00
weekly_schedule = CronSchedule(
    cron="0 4 * * 1",  # Segunda 04:00
    timezone="Europe/Lisbon"
)

deployment = Deployment.build_from_flow(
    flow=model_retraining_pipeline,
    name="weekly-model-retraining",
    schedule=weekly_schedule,
    work_queue_name="ml-queue"
)

if __name__ == "__main__":
    deployment.apply()
```

---

## 4. TESTES AUTOMATIZADOS

### 4.1 Testes de Qualidade de Dados

```python
# tests/data/test_training_data_quality.py
import pytest
import pandas as pd
import numpy as np

def test_no_missing_values(train_data):
    """Verifica que não há valores missing nos dados de treino"""
    assert train_data.isnull().sum().sum() == 0, "Dados de treino contêm missing values"

def test_temporal_split(train_data, val_data, test_data):
    """Verifica que split é temporal e não há leakage"""
    assert train_data['date'].max() < val_data['date'].min(), "Split temporal inválido"
    assert val_data['date'].max() < test_data['date'].min(), "Split temporal inválido"

def test_feature_distribution(train_data, val_data):
    """Verifica que distribuição de features é similar entre treino e validação"""
    from scipy.stats import ks_2samp
    
    for feature in ['odds', 'home_team_strength', 'away_team_strength']:
        statistic, p_value = ks_2samp(
            train_data[feature],
            val_data[feature]
        )
        assert p_value > 0.05, f"Distribuição de {feature} difere significativamente"

def test_class_balance(train_data):
    """Verifica balanceamento de classes"""
    class_counts = train_data['target'].value_counts()
    min_ratio = class_counts.min() / class_counts.max()
    assert min_ratio > 0.3, "Classes desbalanceadas (ratio < 30%)"

def test_no_duplicate_rows(train_data):
    """Verifica que não há linhas duplicadas"""
    assert train_data.duplicated().sum() == 0, "Dados contêm linhas duplicadas"
```

### 4.2 Testes de Performance de Modelo

```python
# tests/models/test_model_performance.py
import pytest
import mlflow

def test_model_accuracy_above_threshold(model, test_data):
    """Verifica que accuracy do modelo está acima do threshold"""
    from sklearn.metrics import accuracy_score
    
    predictions = model.predict(test_data.drop('target', axis=1))
    accuracy = accuracy_score(test_data['target'], predictions)
    
    assert accuracy > 0.55, f"Accuracy {accuracy:.2%} abaixo do threshold 55%"

def test_clv_positive(model, test_data):
    """Verifica que CLV é positivo"""
    from src.models.metrics import calculate_clv
    
    predictions = model.predict_proba(test_data.drop('target', axis=1))[:, 1]
    clv = calculate_clv(predictions, test_data['odds'], test_data['target'])
    
    assert clv > 0, f"CLV negativo: {clv:.2%}"

def test_model_calibration(model, test_data):
    """Verifica que probabilidades são calibradas"""
    from sklearn.calibration import calibration_curve
    from scipy.stats import pearsonr
    
    predictions = model.predict_proba(test_data.drop('target', axis=1))[:, 1]
    prob_true, prob_pred = calibration_curve(
        test_data['target'],
        predictions,
        n_bins=10
    )
    
    correlation, _ = pearsonr(prob_true, prob_pred)
    assert correlation > 0.9, f"Modelo mal calibrado (correlation: {correlation:.2f})"

def test_model_not_overfitting(train_metrics, val_metrics):
    """Verifica que modelo não está overfitting"""
    accuracy_gap = train_metrics['accuracy'] - val_metrics['accuracy']
    assert accuracy_gap < 0.05, f"Modelo overfitting (gap: {accuracy_gap:.2%})"
```

---

## 5. GITHUB ACTIONS WORKFLOW

```yaml
# .github/workflows/model-ci-cd.yml
name: Model CI/CD Pipeline

on:
  schedule:
    - cron: '0 4 * * 1'  # Segunda-feira 04:00
  workflow_dispatch:
  push:
    branches:
      - feature/model-*

jobs:
  train-model:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install prefect mlflow scikit-learn
      
      - name: Start MLflow server
        run: |
          mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlflow-artifacts --host 0.0.0.0 --port 5000 &
          sleep 5
      
      - name: Run model retraining pipeline
        run: |
          python -m flows.model_retraining
        env:
          MLFLOW_TRACKING_URI: http://localhost:5000
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      
      - name: Run data quality tests
        run: pytest tests/data/test_training_data_quality.py -v
      
      - name: Run model performance tests
        run: pytest tests/models/test_model_performance.py -v
      
      - name: Promote to staging
        if: success()
        run: |
          python scripts/promote_to_staging.py
        env:
          MLFLOW_TRACKING_URI: http://localhost:5000
      
      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Model retraining pipeline failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 6. MÉTRICAS E THRESHOLDS

| Métrica | Threshold Mínimo | Threshold Alerta | Ação |
|---------|-----------------|------------------|------|
| Accuracy (hold-out) | 55% | 50% | Retraining se < 50% |
| CLV (hold-out) | 2% | 0% | Retraining se < 0% |
| Improvement vs Prod | 2% | - | Não promove se < 2% |
| PSI (features) | - | 0.20 | Retraining se > 0.20 |
| KS p-value | > 0.05 | < 0.01 | Alerta se < 0.01 |
| Calibration correlation | > 0.90 | < 0.85 | Alerta se < 0.85 |

---

## 7. ROLLBACK AUTOMÁTICO

```python
# scripts/rollback_model.py
from mlflow.tracking import MlflowClient

def rollback_to_previous_model():
    """Rollback para versão anterior do modelo"""
    client = MlflowClient()
    
    # Obter versões em Production
    prod_versions = client.get_latest_versions(
        "value-betting-model",
        stages=["Production"]
    )
    
    if len(prod_versions) > 1:
        # Transicionar versão anterior para Production
        previous_version = prod_versions[1].version
        current_version = prod_versions[0].version
        
        client.transition_model_version_stage(
            name="value-betting-model",
            version=previous_version,
            stage="Production"
        )
        
        # Arquivar versão atual
        client.transition_model_version_stage(
            name="value-betting-model",
            version=current_version,
            stage="Archived"
        )
        
        print(f"Rollback: {current_version} → {previous_version}")
    else:
        print("Não há versão anterior para rollback")

if __name__ == "__main__":
    rollback_to_previous_model()
```

---

## 8. MONITORIZAÇÃO DO PIPELINE

### 8.1 Métricas de Pipeline

- **Duração do treino**: Tempo total do pipeline
- **Sucesso/Falha**: Taxa de sucesso dos pipelines
- **Melhoria de CLV**: Delta entre novo modelo e produção
- **Taxa de promoção**: % de modelos que chegam a produção

### 8.2 Alertas

- Pipeline falha → Alerta Slack imediato
- CLV < 0% em validação → Alerta para revisão
- PSI > 0.20 → Trigger retraining automático
- Modelo não promove → Notificação para MLOps Engineer

---

## 9. BACKLOG TÉCNICO

- [ ] Configurar Prefect server para orquestração
- [ ] Implementar tests de robustez (adversarial examples)
- [ ] Adicionar testes de fairness (bias detection)
- [ ] Criar dashboard de monitorização do pipeline
- [ ] Implementar cache de features para acelerar treino
- [ ] Adicionar testes de escalabilidade (big data)

---

## 10. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[11_MLOps/RETRAINING_AUTO]] → Detalhes de retraining
- [[11_MLOps/SHADOW_DEPLOYMENT]] → Deploy em shadow mode
- [[11_MLOps/MODEL_REGISTRY_GESTAO]] → Gestão do registry
- [[12_DevOps/CI_CD_SETUP]] → CI/CD geral da aplicação
- [[29_Experiment_Tracking/INDEX]] → Tracking de experimentos