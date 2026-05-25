# 32_Feature_Store — INDEX

**ID:** `SEC-32` | **Fase:** #phase/2 | **Owner:** Data Engineer + MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar um feature store para gerir, versionar, e servir features de forma eficiente. O feature store permite reutilização de features entre modelos, garantindo consistência e facilitando MLOps.

---

## 2. POR QUE UM FEATURE STORE?

### 2.1 Problemas Sem Feature Store

- **Reinventing the wheel:** Cada modelo recalcula as mesmas features
- **Inconsistência:** Diferentes versões de features entre modelos
- **No lineage:** Impossível rastrear de onde veio cada feature
- **No versioning:** Impossível voltar a versão anterior de feature
- **Lentitude:** Recalcular features em tempo real é lento

### 2.2 Benefícios de Feature Store

- **Reutilização:** Features calculadas uma vez, usadas múltiplas vezes
- **Consistência:** Todos os modelos usam mesma versão de features
- **Lineage:** Rastreabilidade completa de cada feature
- **Versioning:** Voltar a versão anterior se necessário
- **Performance:** Features servidas rapidamente (cache)
- **Reproducibilidade:** Exatamente as mesmas features para reproduzir experimentos

---

## 3. ARQUITETURA DO FEATURE STORE

```
┌─────────────────────────────────────────────────────────────┐
│                    FONTE DE DADOS                           │
│  (NBA API, Basketball-Reference, Odds, etc.)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FEATURE ENGINEERING BATCH                      │
│  (Cálculo de features, transformações, agregações)       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FEATURE STORE                               │
│  ├─ PostgreSQL (armazenamento persistente)                │
│  ├─ Redis (cache para serving rápido)                     │
│  ├─ MLflow (versioning de feature sets)                 │
│  └─ API REST (serving de features)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐
│  MODELO A   │ │ MODELO B │ │  MODELO C   │
│  (XGBoost)  │ │ (LightGBM)│ │ (CatBoost)  │
└─────────────┘ └─────────┘ └─────────────┘
```

---

## 4. COMPONENTES

### 4.1 PostgreSQL (Armazenamento Persistente)

**Schema:**
```sql
CREATE TABLE feature_sets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    metadata JSONB,
    UNIQUE(name, version)
);

CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    feature_set_id INTEGER REFERENCES feature_sets(id),
    game_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    feature_value FLOAT,
    feature_type VARCHAR(50),  -- 'numerical', 'categorical'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feature_set_id, game_id, feature_name)
);

CREATE TABLE feature_lineage (
    id SERIAL PRIMARY KEY,
    feature_set_id INTEGER REFERENCES feature_sets(id),
    source_table VARCHAR(255) NOT NULL,
    source_column VARCHAR(255),
    transformation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Redis (Cache para Serving Rápido)

**Configuração:**
```python
# app/feature_store/cache.py
import redis
import json
from typing import Dict, Any

class FeatureCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hora
    
    def get_features(self, game_id: str, feature_set_id: int) -> Dict[str, Any]:
        """Busca features no cache"""
        key = f"features:{feature_set_id}:{game_id}"
        cached = self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        
        return None
    
    def set_features(self, game_id: str, feature_set_id: int, features: Dict[str, Any]):
        """Armazena features no cache"""
        key = f"features:{feature_set_id}:{game_id}"
        self.redis.setex(key, self.ttl, json.dumps(features))
    
    def invalidate_feature_set(self, feature_set_id: int):
        """Invalida todas as features de um feature set"""
        pattern = f"features:{feature_set_id}:*"
        keys = self.redis.keys(pattern)
        
        if keys:
            self.redis.delete(*keys)
```

### 4.3 MLflow (Versioning de Feature Sets)

**Log de Feature Sets:**
```python
# app/feature_store/mlflow.py
import mlflow
import mlflow.pyfunc

def log_feature_set(feature_set_id: int, metadata: Dict[str, Any]):
    """Registra feature set no MLflow"""
    
    with mlflow.start_run(run_name=f"feature_set_{feature_set_id}"):
        # Log metadata
        mlflow.log_params(metadata)
        
        # Log artefatos (opcional)
        # mlflow.log_artifact("feature_schema.json")
        
        # Log métricas
        mlflow.log_metric("n_features", metadata["n_features"])
        mlflow.log_metric("n_games", metadata["n_games"])
```

### 4.4 API REST (Serving de Features)

```python
# app/feature_store/api.py
from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

class FeatureStoreAPI:
    def __init__(self, db, cache):
        self.db = db
        self.cache = cache
    
    def get_features(self, game_id: str, feature_set_name: str, version: int = None) -> Dict[str, Any]:
        """
        Busca features para um jogo específico.
        
        Args:
            game_id: ID do jogo
            feature_set_name: Nome do feature set
            version: Versão do feature set (opcional, usa latest se None)
        
        Returns:
            Dicionário de features
        """
        # 1. Buscar feature set ID
        if version:
            feature_set_id = self.db.get_feature_set_by_name_and_version(feature_set_name, version)
        else:
            feature_set_id = self.db.get_latest_feature_set(feature_set_name)
        
        if not feature_set_id:
            raise HTTPException(status_code=404, detail="Feature set not found")
        
        # 2. Tentar cache
        cached = self.cache.get_features(game_id, feature_set_id)
        if cached:
            logger.info(f"Features encontradas em cache para {game_id}")
            return cached
        
        # 3. Buscar no PostgreSQL
        features = self.db.get_features(game_id, feature_set_id)
        
        if not features:
            raise HTTPException(status_code=404, detail="Features not found")
        
        # 4. Armazenar no cache
        self.cache.set_features(game_id, feature_set_id, features)
        
        return features
    
    def create_feature_set(self, name: str, features_df, metadata: Dict[str, Any]):
        """
        Cria novo feature set.
        
        Args:
            name: Nome do feature set
            features_df: DataFrame de features (game_id como índice)
            metadata: Metadata do feature set
        """
        # 1. Criar feature set no database
        feature_set_id = self.db.create_feature_set(name, metadata)
        
        # 2. Inserir features no database
        self.db.insert_features(feature_set_id, features_df)
        
        # 3. Registrar lineage
        self.db.register_lineage(feature_set_id, metadata["sources"])
        
        # 4. Log no MLflow
        log_feature_set(feature_set_id, metadata)
        
        # 5. Invalidar cache se existir versão anterior
        old_feature_set_id = self.db.get_previous_feature_set(name)
        if old_feature_set_id:
            self.cache.invalidate_feature_set(old_feature_set_id)
        
        return feature_set_id
```

---

## 5. WORKFLOW DE FEATURE STORE

### 5.1 Criação de Feature Set

```python
# app/feature_store/workflow.py
import pandas as pd
from app.feature_store.api import FeatureStoreAPI

def create_nba_feature_set():
    """Cria feature set NBA completo"""
    
    # 1. Buscar dados limpos
    df = get_clean_games()
    
    # 2. Calcular features
    features_df = calculate_all_features(df)
    
    # 3. Metadata
    metadata = {
        "name": "nba_features_v1",
        "version": 1,
        "description": "Features completas para NBA (80 features)",
        "n_features": 80,
        "n_games": len(features_df),
        "sources": [
            {"table": "silver.games_clean", "columns": ["*"]},
            {"table": "silver.player_stats", "columns": ["*"]}
        ],
        "created_by": "system"
    }
    
    # 4. Criar feature set
    api = FeatureStoreAPI(db, cache)
    feature_set_id = api.create_feature_set(
        name="nba_features_v1",
        features_df=features_df,
        metadata=metadata
    )
    
    logger.info(f"Feature set criado com ID: {feature_set_id}")
    
    return feature_set_id
```

### 5.2 Serving de Features para Modelo

```python
# app/models/inference.py
from app.feature_store.api import FeatureStoreAPI

class ModelInference:
    def __init__(self, model, feature_store_api):
        self.model = model
        self.feature_store = feature_store_api
        self.feature_set_name = "nba_features_v1"
        self.feature_set_version = 1
    
    def predict(self, game_id: str) -> Dict[str, Any]:
        """
        Faz predição para um jogo específico.
        
        Args:
            game_id: ID do jogo
            
        Returns:
            Dicionário com predição e metadados
        """
        # 1. Buscar features do feature store
        features = self.feature_store.get_features(
            game_id=game_id,
            feature_set_name=self.feature_set_name,
            version=self.feature_set_version
        )
        
        if not features:
            raise ValueError(f"Features not found for game {game_id}")
        
        # 2. Converter para formato do modelo
        X = self._prepare_features(features)
        
        # 3. Fazer predição
        prediction = self.model.predict_proba(X)[0, 1]
        
        return {
            "game_id": game_id,
            "prediction": prediction,
            "features": features,
            "feature_set": f"{self.feature_set_name}_v{self.feature_set_version}"
        }
    
    def _prepare_features(self, features: Dict[str, Any]) -> pd.DataFrame:
        """Prepara features para o modelo"""
        # Converter dicionário para DataFrame
        df = pd.DataFrame([features])
        
        # Reordenar colunas para ordem esperada pelo modelo
        df = df[self.model.feature_names]
        
        return df
```

---

## 6. VERSIONING DE FEATURES

### 6.1 Estratégia de Versioning

**Semantic Versioning:** `major.minor.patch`

- **major:** Mudança breaking na definição de features
- **minor:** Adição de novas features (backward compatible)
- **patch:** Correção de bugs em cálculo de features

**Exemplos:**
- `nba_features_v1.0.0` → `nba_features_v1.1.0` (adicionou 5 features)
- `nba_features_v1.1.0` → `nba_features_v2.0.0` (removeu 10 features, mudou definição)

### 6.2 Rollback

```python
# app/feature_store/versioning.py
def rollback_feature_set(name: str, target_version: int):
    """
    Faz rollback para versão específica de feature set.
    
    Args:
        name: Nome do feature set
        target_version: Versão para rollback
    """
    # 1. Validar que versão existe
    feature_set_id = db.get_feature_set_by_name_and_version(name, target_version)
    
    if not feature_set_id:
        raise ValueError(f"Version {target_version} does not exist")
    
    # 2. Atualizar "latest" para apontar para versão alvo
    db.update_latest_feature_set(name, target_version)
    
    # 3. Invalidar cache
    cache.invalidate_all()
    
    # 4. Log rollback
    logger.info(f"Feature set {name} rolled back to v{target_version}")
```

---

## 7. MONITORIZAÇÃO

### 7.1 Métricas

| Métrica | Descrição | Target |
|---------|-----------|--------|
| **Cache Hit Rate** | % de features servidas do cache | > 80% |
| **Feature Serving Latency** | Tempo médio para servir features | < 50ms |
| **Feature Set Age** | Idade do feature set mais recente | < 30 dias |
| **Feature Quality** | % de features sem null | > 95% |

### 7.2 Dashboard Grafana

**Painel: Feature Store**

**Gráficos:**
- Cache Hit Rate (últimos 30 dias)
- Feature Serving Latency (p50, p95, p99)
- Número de feature sets ativos
- Idade de feature sets
- Feature Quality (null rate)

**Alertas:**
- Se Cache Hit Rate < 70% (MEDIUM)
- Se Feature Serving Latency > 100ms (HIGH)
- Se Feature Set Age > 60 dias (HIGH)

---

## 8. BACKLOG DE FEATURE STORE

- [ ] Implementar schema PostgreSQL
- [ ] Implementar cache Redis
- [ ] Implementar API REST
- [ ] Implementar workflow de criação de feature set
- [ ] Implementar versioning de features
- [ ] Implementar rollback de features
- [ ] Integrar com MLflow
- [ ] Configurar monitorização
- [ ] Implementar lineage tracking
- [ ] Documentar feature sets

---

## 9. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[04_Data_Engineering/INDEX]] → Pipeline de dados
- [[05_Machine_Learning/INDEX]] → Modelos que consomem features
- [[11_MLOps/INDEX]] → MLOps e feature management
