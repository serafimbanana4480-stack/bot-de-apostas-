# MODEL_REGISTRY — Registro de Modelos ML

**ID:** `ML-REG-001` | **Fase:** #phase/2 | **Owner:** ML Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Centralizar o registro, versionamento e gestão de todos os modelos de machine learning do sistema, garantindo reproducibilidade, audit trail e rollback seguro.

---

## 2. ARQUITETURA

### 2.1 Componentes

| Componente | Função | Tecnologia |
|------------|--------|------------|
| MLflow Tracking | Registro de experimentos | MLflow |
| Model Store | Armazenamento de artefactos | MLflow + S3/Local |
| Model Registry | Versionamento e staging | MLflow Registry |
| Serving API | Inferência em produção | FastAPI + MLflow |

### 2.2 Fluxo de Vida de um Modelo

```
Desenvolvimento → Experimento → Registro → Staging → Production → Retirement
```

---

## 3. REGISTRO DE EXPERIMENTOS

### 3.1 Tracking com MLflow

```python
import mlflow
import mlflow.xgboost
from sklearn.metrics import log_loss, roc_auc_score

class ModelExperiment:
    """Registra um experimento de treino no MLflow."""
    
    def __init__(self, experiment_name: str):
        mlflow.set_experiment(experiment_name)
    
    def run(self, model, X_train, y_train, X_val, y_val, params: dict):
        """Executa treino e registra tudo no MLflow."""
        with mlflow.start_run() as run:
            # Logar parâmetros
            mlflow.log_params(params)
            
            # Treinar modelo
            model.fit(X_train, y_train)
            
            # Predições
            probs = model.predict_proba(X_val)[:, 1]
            
            # Métricas
            metrics = {
                'roc_auc': roc_auc_score(y_val, probs),
                'log_loss': log_loss(y_val, probs),
                'brier_score': brier_score_loss(y_val, probs),
                'ece': self.calculate_ece(y_val, probs),
            }
            mlflow.log_metrics(metrics)
            
            # Logar modelo
            mlflow.xgboost.log_model(model, "model")
            
            # Logar artefactos (gráficos, relatórios)
            mlflow.log_artifact("calibration_plot.png")
            
            return run.info.run_id, metrics
```

### 3.2 Estrutura de Experimento

Cada experimento deve conter:
- **Params:** Todos os hiperparâmetros usados
- **Metrics:** ROC-AUC, Brier, ECE, CLV simulado, ROI simulado
- **Tags:** Tipo de modelo, época, versão de dados
- **Artefacts:** Gráficos de calibração, feature importance, relatório de backtest

---

## 4. MODEL REGISTRY

### 4.1 Stages

| Stage | Descrição | Quem Promove |
|-------|-----------|--------------|
| None | Experimento recente, não validado | — |
| Staging | Validado em backtest, aguardando paper | ML Engineer |
| Production | Aprovado em paper trading, ativo em produção | CTO + ML Lead |
| Archived | Substituído por versão mais recente | Automático |

### 4.2 Promoção de Modelo

```python
def promote_model(model_name: str, version: str, stage: str):
    """Promove modelo para novo stage com validação."""
    
    client = mlflow.tracking.MlflowClient()
    
    # Verificar se métricas atingem critérios
    model_version = client.get_model_version(model_name, version)
    metrics = get_model_metrics(model_name, version)
    
    if stage == 'Production':
        # Critérios rigorosos para produção
        assert metrics['roc_auc'] > 0.55, "AUC insuficiente"
        assert metrics['ece'] < 0.10, "Calibração inadequada"
        assert metrics['clv_simulated'] > 0.02, "CLV insuficiente"
    
    # Promover
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=stage
    )
    
    logger.info(f"Modelo {model_name} v{version} promovido para {stage}")
```

### 4.3 Rollback de Modelo

```python
def rollback_model(model_name: str):
    """Reverte para versão anterior em produção."""
    
    client = mlflow.tracking.MlflowClient()
    
    # Obter versão atual em produção
    current = client.get_latest_versions(model_name, stages=['Production'])[0]
    
    # Obter versões anteriores
    versions = client.search_model_versions(f"name='{model_name}'")
    previous = [v for v in versions if v.version < current.version]
    
    if not previous:
        raise ValueError("Não há versão anterior para rollback")
    
    # Promover versão anterior
    rollback_to = max(previous, key=lambda x: int(x.version))
    client.transition_model_version_stage(
        name=model_name,
        version=rollback_to.version,
        stage='Production'
    )
    
    # Arquivar versão atual
    client.transition_model_version_stage(
        name=model_name,
        version=current.version,
        stage='Archived'
    )
    
    logger.critical(f"Rollback executado: {current.version} → {rollback_to.version}")
```

---

## 5. SERVING DE MODELOS

### 5.1 API de Inferência

```python
from fastapi import FastAPI
import mlflow.pyfunc

app = FastAPI()

class ModelServer:
    """Servidor de inferência com hot-swap de modelos."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.version = None
        self.load_model()
    
    def load_model(self):
        """Carrega modelo mais recente em produção."""
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions(self.model_name, stages=['Production'])
        
        if not versions:
            raise ValueError("Nenhum modelo em produção")
        
        latest = versions[0]
        self.model = mlflow.pyfunc.load_model(f"models:/{self.model_name}/Production")
        self.version = latest.version
        
        logger.info(f"Modelo carregado: {self.model_name} v{self.version}")
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Executa predição."""
        return self.model.predict(features)

# Endpoint FastAPI
model_server = ModelServer("nba_value_model")

@app.post("/predict")
async def predict(features: FeatureInput):
    df = pd.DataFrame([features.dict()])
    prob = model_server.predict(df)[0]
    return {
        "probability": float(prob),
        "model_version": model_server.version,
        "timestamp": datetime.now().isoformat()
    }
```

### 5.2 Hot-Swap em Produção

```python
@app.post("/reload-model")
async def reload_model():
    """Recarrega modelo sem restart do servidor."""
    try:
        model_server.load_model()
        return {"status": "ok", "version": model_server.version}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

---

## 6. AUDIT E COMPLIANCE

### 6.1 Registro de Uso

```python
def log_prediction(model_version: str, features: dict, prediction: float):
    """Registra cada predição para audit."""
    logger.info(
        "Prediction logged",
        model_version=model_version,
        prediction=prediction,
        timestamp=datetime.now().isoformat(),
        feature_hash=hashlib.md5(str(features).encode()).hexdigest()
    )
```

### 6.2 Retenção

| Tipo | Retenção | Razão |
|------|----------|-------|
| Experimentos | 2 anos | Reproducibilidade |
| Modelos em Produção | Permanente | Rollback |
| Artefactos | 1 ano | Relatórios |
| Logs de predição | 90 dias | Audit |

---

## 7. BACKLOG

- [x] Definir arquitetura de model registry
- [x] Documentar tracking com MLflow
- [x] Documentar stages e promoção
- [x] Implementar rollback automático
- [x] Documentar API de inferência com hot-swap
- [x] Documentar audit e retenção
- [ ] Configurar MLflow server em produção
- [ ] Implementar CI/CD para deploy de modelos

---

## 8. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secção mãe
- [[29_Experiment_Tracking/INDEX]] → Experiment tracking detalhado
- [[12_DevOps/CI_CD_SETUP]] → CI/CD para modelos
- [[05_Machine_Learning/MODELO_XGBOOST]] → Treino do modelo
