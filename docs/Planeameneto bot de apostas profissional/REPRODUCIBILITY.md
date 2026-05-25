# REPRODUCIBILITY — Reprodutibilidade de Experimentos

**ID:** `ML-004` | **Fase:** #phase/2 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Garantir que qualquer experimento pode ser reproduzido exatamente, usando os mesmos dados, código e ambiente.

---

## 2. PILARES DA REPRODUTIBILIDADE

| Pilar | Implementação |
|-------|---------------|
| **Dados** | Snapshots versionados, seeds fixos |
| **Código** | Git versioning, requirements.txt |
| **Ambiente** | Docker, versões fixas de Python/pacotes |
| **Randomness** | Seeds fixos em todos os lugares |
| **Logging** | Registro completo de metadados |

---

## 3. SEEDS

```python
import random
import numpy as np

def set_global_seed(seed=42):
    """Fixa seeds para reproducibilidade."""
    random.seed(seed)
    np.random.seed(seed)
    # XGBoost seed configurado no model_config
```

**Importante:** Setar seed antes de qualquer operação estocástica.

---

## 4. REQUIREMENTS FREEZE

```bash
# requirements.txt com versões fixas
xgboost==2.0.0
scikit-learn==1.3.0
pandas==2.0.0
numpy==1.24.0
optuna==3.3.0
```

Usar `pip freeze > requirements.txt` após instalar versões específicas.

---

## 5. DOCKER

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "train_model.py"]
```

Garante ambiente idêntico em qualquer máquina.

---

## 6. DATA SNAPSHOTS

```python
def create_training_snapshot(data, features_config):
    """Cria snapshot imutável de dados de treino."""
    snapshot = {
        'data': data,
        'features_config': features_config,
        'timestamp': datetime.now(),
        'git_commit': get_git_commit(),
        'requirements': get_installed_packages()
    }
    
    filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
    joblib.dump(snapshot, f"data/snapshots/{filename}")
    
    return filename
```

---

## 7. MLflow TRACKING

```python
import mlflow

def train_with_tracking(params, X_train, y_train):
    """Treina com MLflow tracking."""
    with mlflow.start_run():
        # Log parâmetros
        mlflow.log_params(params)
        
        # Treinar
        model = train_model(params, X_train, y_train)
        
        # Log métricas
        mlflow.log_metrics({'clv': clv, 'brier': brier})
        
        # Log modelo
        mlflow.xgboost.log_model(model, "model")
        
        # Log artifacts
        mlflow.log_artifact("features_config.json")
    
    return model
```

---

## 8. CHECKLIST DE REPRODUTIBILIDADE

Antes de promover modelo:

- [ ] Seeds fixos em todo o código
- [ ] Requirements.txt com versões fixas
- [ ] Git commit hash registrado
- [ ] Data snapshot criado e salvo
- [ ] MLflow run registrado
- [ ] Random state documentado
- [ ] Feature config versionado

---

## 9. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[29_Experiment_Tracking/INDEX]]
