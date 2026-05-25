# MODEL_REGISTRY_GESTAO — Gestão do Registry de Modelos

**ID:** `ML-017` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerir registry de modelos para versionamento e tracking.

---

## 2. ESTRUTURA DO REGISTRY

```
models/
├── v1.0/
│   ├── model.pkl
│   ├── config.json
│   └── metrics.json
├── v1.1/
│   ├── model.pkl
│   ├── config.json
│   └── metrics.json
└── current -> v1.1
```

---

## 3. REGISTRO DE MODELO

```python
def register_model(model, config, metrics, version):
    """
    Registra novo modelo no registry.
    
    Args:
        model: Modelo treinado
        config: Configuração do modelo
        metrics: Métricas de validação
        version: Versão do modelo
    
    Returns:
        Caminho do modelo registado
    """
    import mlflow
    
    # Iniciar run
    with mlflow.start_run():
        # Log modelo
        mlflow.sklearn.log_model(model, "model")
        
        # Log parâmetros
        mlflow.log_params(config)
        
        # Log métricas
        mlflow.log_metrics(metrics)
        
        # Tag com versão
        mlflow.set_tag("version", version)
    
    return f"models/{version}"
```

---

## 4. CARREGAMENTO DE MODELO

```python
def load_model(version="current"):
    """
    Carrega modelo do registry.
    
    Args:
        version: Versão do modelo (default: current)
    
    Returns:
        Modelo carregado
    """
    import mlflow
    
    if version == "current":
        # Obter versão atual
        version = get_current_version()
    
    model_uri = f"models:/{version}"
    model = mlflow.sklearn.load_model(model_uri)
    
    return model
```

---

## 5. CRITÉRIOS

- **Versionamento semântico** (major.minor.patch)
- **Metadados completos** para cada versão
- **Link "current"** para versão ativa

---

## 6. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[SOP_DEPLOY_MODELO]]
