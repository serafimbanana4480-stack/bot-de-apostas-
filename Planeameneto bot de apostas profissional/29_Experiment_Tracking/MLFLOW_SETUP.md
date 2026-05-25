# MLFLOW_SETUP — Tracking de Experimentos

**ID:** `ET-001` | **Fase:** #phase/2 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Registar todos os experimentos de ML: parametros, metricas, artifacts, e modelos.

---

## 2. INSTALACAO

```bash
pip install mlflow

# Iniciar servidor (em producao, usar PostgreSQL como backend)
mlflow server \
  --backend-store-uri postgresql://user:pass@localhost/mlflow \
  --default-artifact-root /mlflow/artifacts \
  --host 0.0.0.0 \
  --port 5000
```

---

## 3. USO NO CODIGO

```python
import mlflow
import mlflow.xgboost

mlflow.set_experiment("nba_moneyline_v1")

with mlflow.start_run():
    # Parametros
    mlflow.log_params({
        "max_depth": 4,
        "learning_rate": 0.05,
        "n_estimators": 1000
    })
    
    # Metricas
    mlflow.log_metrics({
        "clv": 0.025,
        "roi": 0.065,
        "sharpe": 0.62
    })
    
    # Modelo
    mlflow.xgboost.log_model(model, "model")
```

---

## 4. WRAPPER PADRONIZADO DE EXPERIMENTO

```python
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional
import mlflow
import mlflow.xgboost

@dataclass
class ExperimentConfig:
    experiment_name: str       # e.g. "nba_moneyline_v2"
    run_name: str              # e.g. "EXP-2026-001_xgb_depth4"
    hypothesis: str            # O que estamos a testar
    dataset_seasons: list      # e.g. [2020, 2021, 2022, 2023, 2024]
    features_version: str      # e.g. "v1.2"
    cv_n_splits: int = 5
    cv_embargo_days: int = 2


@contextmanager
def track_experiment(config: ExperimentConfig):
    """
    Context manager que garante logging consistente de todos os experimentos.
    Uso:
        with track_experiment(config) as run:
            model.fit(X_train, y_train)
            mlflow.xgboost.log_model(model, "model")
    """
    mlflow.set_experiment(config.experiment_name)

    with mlflow.start_run(run_name=config.run_name) as run:
        # Tags obrigatórias
        mlflow.set_tags({
            "hypothesis": config.hypothesis,
            "dataset.seasons": str(config.dataset_seasons),
            "features.version": config.features_version,
            "cv.n_splits": config.cv_n_splits,
            "cv.embargo_days": config.cv_embargo_days,
            "project": "VBQ-001",
        })
        yield run
        # Logging automático de metadata no final
        mlflow.set_tag("status", "completed")
```

---

## 5. CONVENÇÕES DE NAMING

| Campo | Formato | Exemplo |
|-------|---------|---------|
| Experiment name | `{desporto}_{mercado}_v{versao}` | `nba_moneyline_v1` |
| Run name | `EXP-{YYYY}-{NNN}_{modelo}_{tag}` | `EXP-2026-001_xgb_depth4` |
| Model artifact | `model` (fixo) | `mlflow/model` |
| Dataset artifact | `dataset_{layer}_{date}` | `dataset_gold_2026-05-01` |

---

## 6. MÉTRICAS OBRIGATÓRIAS POR EXPERIMENTO

```python
REQUIRED_METRICS = {
    # Performance de betting
    "clv_mean":         float,  # CLV médio nas predições (%)
    "clv_std":          float,  # Desvio padrão do CLV
    "roi":              float,  # ROI total (%)
    "sharpe_ratio":     float,  # Sharpe ratio anualizado
    "n_bets":           int,    # Número de apostas geradas

    # Qualidade do modelo
    "brier_score":      float,  # Brier Score (< 0.25 target)
    "ece":              float,  # Expected Calibration Error (< 0.05 target)
    "log_loss":         float,  # Log loss
    "auc_roc":          float,  # AUC-ROC

    # Validação
    "cv_mean_clv":      float,  # CLV médio nos folds de CV
    "cv_std_clv":       float,  # Variabilidade entre folds
    "cv_t_stat":        float,  # t-statistic: CLV significativamente > 0?
}
```

---

## 7. DOCKER COMPOSE (PRODUÇÃO)

```yaml
# docker-compose.mlflow.yml
services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    ports:
      - "5000:5000"
    environment:
      MLFLOW_BACKEND_STORE_URI: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/mlflow
      MLFLOW_ARTIFACT_ROOT: /mlflow/artifacts
    volumes:
      - mlflow_artifacts:/mlflow/artifacts
    command: >
      mlflow server
        --backend-store-uri postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/mlflow
        --default-artifact-root /mlflow/artifacts
        --host 0.0.0.0
        --port 5000
    depends_on:
      - db

volumes:
  mlflow_artifacts:
```

---

## 8. BACKLOG

- [ ] Configurar MLflow server via Docker Compose (Fase 2, Semana 1)
- [ ] Criar tabela `mlflow` no PostgreSQL
- [ ] Implementar `track_experiment` wrapper em todos os scripts de treino
- [ ] Documentar convenção de naming para a equipa
- [ ] Configurar acesso externo (porta 5000) com autenticação básica
- [ ] Integrar Optuna com MLflow callbacks para hyperparameter search

---

## 9. LINKS CRUZADOS

- [[29_Experiment_Tracking/INDEX]] ← Secção mãe
- [[30_Model_Registry/INDEX]] → Promoção de modelos
- [[05_Machine_Learning/INDEX]] → Scripts de treino que usam MLflow
- [[12_DevOps/INDEX]] → Docker Compose setup
