# INTEGRACAO_ML — Pipeline de Features com ML Models

**ID:** `FEAT-006` | **Fase:** #phase/1-6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir o pipeline de integração entre o Feature Store e os modelos de machine learning, garantindo que as features usadas no treino são idênticas às usadas em produção. O pipeline deve automatizar a extração, transformação e entrega de features para treino, validação e inferência.

---

## 2. CONTEXTO

O gap entre treino e produção é uma das principais causas de falhas em sistemas de ML. Sem integração adequada:

- **Inconsistência:** Features calculadas diferentemente em treino vs produção
- **Data leakage:** Features do futuro usadas no treino
- **Version mismatch:** Modelos treinados com features antigas
- **Reproducibility:** Impossível reproduzir resultados históricos
- **Debugging:** Difícil identificar origem de problemas

Em value betting, onde pequenas inconsistências podem levar a perdas financeiras significativas, a integração rigorosa entre Feature Store e ML é crítica.

---

## 3. ARQUITETURA DE INTEGRAÇÃO

### 3.1 Componentes

```
┌─────────────────────────────────────────────────────────────┐
│              ML FEATURE PIPELINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Feature    │───→│  Training   │───→│  Model      │    │
│  │  Store      │    │  Dataset    │    │  Training   │    │
│  │  (Offline)  │    │  Builder    │    │             │    │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘    │
│                            │                  │            │
│                            ▼                  ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Feature    │───→│  Validation │←───│  Model      │    │
│  │  Store      │    │  Dataset    │    │  Evaluation │    │
│  │  (Online)   │    │  Builder    │    │             │    │
│  └─────────────┘    └──────┬──────┘    └─────────────┘    │
│                            │                               │
│                            ▼                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Feature    │───→│  Inference  │←───│  Model      │    │
│  │  Service    │    │  Pipeline   │    │  Serving    │    │
│  │  API        │    │             │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Fluxo de Dados

**Treino:**
```
Offline Store → Feature Selection → Training Set → Model Training → Model Registry
```

**Validação:**
```
Offline Store → Feature Selection → Validation Set → Model Evaluation → Model Approval
```

**Inferência:**
```
Online Store → Feature Service → Inference Pipeline → Prediction → Decision
```

---

## 4. PIPELINE DE TREINO

### 4.1 Extração de Features para Treino

```python
from typing import List, Dict
import pandas as pd
from datetime import datetime, timedelta

class TrainingDataBuilder:
    def __init__(self, feature_store_client):
        self.feature_store = feature_store_client
    
    def build_training_dataset(
        self,
        feature_ids: List[str],
        target_column: str,
        start_date: datetime,
        end_date: datetime,
        feature_versions: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        Constrói dataset de treino com features e target.
        
        Args:
            feature_ids: Lista de IDs das features
            target_column: Nome da coluna target
            start_date: Data inicial do treino
            end_date: Data final do treino
            feature_versions: Versão específica por feature (opcional)
        """
        # Obter features do Offline Store
        features_df = self._extract_features(
            feature_ids=feature_ids,
            start_date=start_date,
            end_date=end_date,
            feature_versions=feature_versions
        )
        
        # Obter target (resultados dos jogos)
        target_df = self._extract_target(
            target_column=target_column,
            start_date=start_date,
            end_date=end_date
        )
        
        # Join features com target (temporal join)
        training_df = self._temporal_join(features_df, target_df)
        
        # Validar integridade temporal (no data leakage)
        self._validate_temporal_integrity(training_df, feature_ids)
        
        # Adicionar metadados de features
        training_df = self._add_feature_metadata(training_df, feature_ids)
        
        return training_df
    
    def _extract_features(
        self,
        feature_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        feature_versions: Dict[str, str] = None
    ) -> pd.DataFrame:
        """Extrai features do Offline Store."""
        feature_versions = feature_versions or {}
        
        dfs = []
        for feature_id in feature_ids:
            version = feature_versions.get(feature_id, "latest")
            
            # Query feature store
            df = self.feature_store.query_offline_store(
                feature_id=feature_id,
                version=version,
                start_date=start_date,
                end_date=end_date
            )
            
            # Rename columns para evitar conflitos
            df = df.rename(columns={"value": feature_id})
            dfs.append(df)
        
        # Merge todas as features
        result = dfs[0]
        for df in dfs[1:]:
            result = result.merge(df, on=["entity_id", "timestamp"], how="outer")
        
        return result
    
    def _extract_target(
        self,
        target_column: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Extrai target (resultados dos jogos)."""
        # Query tabela de jogos
        query = f"""
            SELECT 
                game_id as entity_id,
                game_date as timestamp,
                {target_column} as target
            FROM clean_games
            WHERE game_date BETWEEN '{start_date}' AND '{end_date}'
        """
        return pd.read_sql(query, self.feature_store.db_conn)
    
    def _temporal_join(self, features_df: pd.DataFrame, target_df: pd.DataFrame) -> pd.DataFrame:
        """
        Faz join temporal garantindo que features são de antes do jogo.
        
        Importante: Features devem ser de antes do timestamp do target
        para evitar data leakage.
        """
        # Para cada jogo, buscar features do timestamp anterior
        result = []
        
        for _, game in target_df.iterrows():
            game_time = game["timestamp"]
            
            # Buscar features mais recentes antes do jogo
            game_features = features_df[
                (features_df["entity_id"] == game["entity_id"]) &
                (features_df["timestamp"] < game_time)
            ].sort_values("timestamp").tail(1)
            
            if not game_features.empty:
                row = game_features.iloc[0].to_dict()
                row["target"] = game["target"]
                result.append(row)
        
        return pd.DataFrame(result)
    
    def _validate_temporal_integrity(self, df: pd.DataFrame, feature_ids: List[str]):
        """Valida que não há data leakage."""
        # Verificar se todas as features têm timestamp antes do target
        # (Esta validação depende da estrutura do seu dataset)
        pass
    
    def _add_feature_metadata(self, df: pd.DataFrame, feature_ids: List[str]) -> pd.DataFrame:
        """Adiciona metadados de features ao dataset."""
        metadata = {}
        for feature_id in feature_ids:
            feature_meta = self.feature_store.get_feature_metadata(feature_id)
            metadata[feature_id] = {
                "version": feature_meta["current_version"],
                "formula": feature_meta["formula"],
                "source": feature_meta["source_tables"]
            }
        
        # Guardar metadata como atributo do DataFrame
        df.attrs["feature_metadata"] = metadata
        
        return df
```

### 4.2 Feature Selection

```python
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class FeatureSelector:
    def __init__(self, feature_store_client):
        self.feature_store = feature_store_client
    
    def select_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        method: str = "importance",
        k: int = 20
    ) -> List[str]:
        """
        Seleciona features baseado em diferentes critérios.
        
        Args:
            X: DataFrame de features
            y: Series de target
            method: Método de seleção (importance, mutual_info, correlation)
            k: Número de features a selecionar
        """
        if method == "importance":
            return self._select_by_importance(X, y, k)
        elif method == "mutual_info":
            return self._select_by_mutual_info(X, y, k)
        elif method == "correlation":
            return self._select_by_correlation(X, y, k)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _select_by_importance(self, X: pd.DataFrame, y: pd.Series, k: int) -> List[str]:
        """Seleciona features por importância usando Random Forest."""
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        importances = pd.DataFrame({
            "feature": X.columns,
            "importance": rf.feature_importances_
        }).sort_values("importance", ascending=False)
        
        selected = importances.head(k)["feature"].tolist()
        
        # Log feature importance
        self._log_feature_importance(importances)
        
        return selected
    
    def _select_by_mutual_info(self, X: pd.DataFrame, y: pd.Series, k: int) -> List[str]:
        """Seleciona features por mutual information."""
        mi = mutual_info_classif(X, y, random_state=42)
        
        importances = pd.DataFrame({
            "feature": X.columns,
            "importance": mi
        }).sort_values("importance", ascending=False)
        
        return importances.head(k)["feature"].tolist()
    
    def _select_by_correlation(self, X: pd.DataFrame, y: pd.Series, k: int) -> List[str]:
        """Seleciona features por correlação com target."""
        correlations = X.corrwith(y).abs().sort_values(ascending=False)
        
        return correlations.head(k).index.tolist()
    
    def _log_feature_importance(self, importances: pd.DataFrame):
        """Registra feature importance para análise posterior."""
        # Guardar no Feature Store ou sistema de logging
        pass
```

---

## 5. PIPELINE DE INFERÊNCIA

### 5.1 Feature Extraction em Tempo Real

```python
class InferencePipeline:
    def __init__(
        self,
        model,
        feature_store_client: FeatureStoreClient,
        feature_ids: List[str],
        feature_versions: Dict[str, str] = None
    ):
        self.model = model
        self.feature_store = feature_store_client
        self.feature_ids = feature_ids
        self.feature_versions = feature_versions or {}
        
        # Validar que o modelo foi treinado com as features corretas
        self._validate_model_features()
    
    def _validate_model_features(self):
        """Valida que as features do pipeline correspondem às do modelo."""
        model_features = getattr(self.model, "feature_names_in_", None)
        
        if model_features is not None:
            missing_features = set(model_features) - set(self.feature_ids)
            extra_features = set(self.feature_ids) - set(model_features)
            
            if missing_features:
                raise ValueError(f"Modelo requer features que não estão no pipeline: {missing_features}")
            
            if extra_features:
                logger.warning(f"Pipeline tem features que o modelo não usa: {extra_features}")
    
    async def predict(
        self,
        entity_id: str,
        entity_type: str,
        timestamp: datetime = None
    ) -> Dict:
        """
        Faz previsão para uma entidade.
        
        Args:
            entity_id: ID da entidade (game_id, team_id, etc.)
            entity_type: Tipo de entidade
            timestamp: Timestamp para features (default: agora)
        """
        timestamp = timestamp or datetime.now()
        
        # Obter features do Feature Store
        features = await self.feature_store.get_features(
            feature_ids=self.feature_ids,
            entity_id=entity_id,
            entity_type=entity_type,
            timestamp=timestamp,
            version=self.feature_versions
        )
        
        # Preparar input para modelo
        X = self._prepare_model_input(features)
        
        # Fazer previsão
        prediction = self.model.predict(X)
        probability = self.model.predict_proba(X)
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "timestamp": timestamp.isoformat(),
            "prediction": prediction[0],
            "probability": probability[0].tolist(),
            "features": features,
            "feature_versions": self.feature_versions
        }
    
    def _prepare_model_input(self, features: Dict) -> pd.DataFrame:
        """Prepara input para o modelo."""
        # Extrair valores das features
        feature_values = {
            feature_id: features[feature_id]["value"]
            for feature_id in self.feature_ids
            if feature_id in features and features[feature_id] is not None
        }
        
        # Criar DataFrame
        X = pd.DataFrame([feature_values])
        
        # Garantir ordem das features igual ao treino
        if hasattr(self.model, "feature_names_in_"):
            X = X[self.model.feature_names_in_]
        
        # Tratar missing values
        X = X.fillna(0)  # Ou usar imputer treinado
        
        return X
    
    async def predict_batch(
        self,
        entity_ids: List[str],
        entity_type: str,
        timestamp: datetime = None
    ) -> List[Dict]:
        """Faz previsões em batch para múltiplas entidades."""
        predictions = []
        
        for entity_id in entity_ids:
            prediction = await self.predict(entity_id, entity_type, timestamp)
            predictions.append(prediction)
        
        return predictions
```

### 5.2 Consistência Treino ↔ Produção

```python
class ConsistencyChecker:
    def __init__(self, feature_store_client):
        self.feature_store = feature_store_client
    
    def check_training_production_consistency(
        self,
        model_metadata: Dict,
        production_timestamp: datetime
    ) -> Dict:
        """
        Verifica consistência entre features de treino e produção.
        """
        feature_versions = model_metadata["feature_versions"]
        feature_ids = list(feature_versions.keys())
        
        # Obter features de produção
        production_features = self.feature_store.get_features(
            feature_ids=feature_ids,
            entity_id="sample_entity",  # Usar entidade de exemplo
            entity_type="game",
            timestamp=production_timestamp,
            version=feature_versions
        )
        
        # Obter metadados de features
        feature_metadata = {}
        for feature_id in feature_ids:
            meta = self.feature_store.get_feature_metadata(
                feature_id,
                version=feature_versions[feature_id]
            )
            feature_metadata[feature_id] = meta
        
        # Comparar
        inconsistencies = []
        
        for feature_id in feature_ids:
            # Verificar versão
            if feature_metadata[feature_id]["current_version"] != feature_versions[feature_id]:
                inconsistencies.append({
                    "feature_id": feature_id,
                    "type": "version_mismatch",
                    "training_version": feature_versions[feature_id],
                    "current_version": feature_metadata[feature_id]["current_version"]
                })
            
            # Verificar fórmula
            training_formula = model_metadata.get("feature_formulas", {}).get(feature_id)
            current_formula = feature_metadata[feature_id]["formula"]
            
            if training_formula != current_formula:
                inconsistencies.append({
                    "feature_id": feature_id,
                    "type": "formula_mismatch",
                    "training_formula": training_formula,
                    "current_formula": current_formula
                })
        
        return {
            "consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies
        }
```

---

## 6. MODEL REGISTRY

### 6.1 Armazenamento de Metadados de Modelos

```python
from dataclasses import dataclass
from typing import Dict, List
import joblib
import json

@dataclass
class ModelMetadata:
    model_id: str
    model_name: str
    version: str
    training_date: datetime
    feature_ids: List[str]
    feature_versions: Dict[str, str]
    feature_formulas: Dict[str, str]
    performance_metrics: Dict[str, float]
    hyperparameters: Dict
    training_data_range: Dict[str, datetime]
    model_path: str

class ModelRegistry:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
    
    def register_model(
        self,
        model,
        metadata: ModelMetadata
    ) -> str:
        """
        Registra um modelo no registry.
        """
        # Guardar modelo
        model_filename = f"{metadata.model_id}_{metadata.version}.pkl"
        model_path = f"{self.storage_path}/models/{model_filename}"
        joblib.dump(model, model_path)
        
        # Guardar metadados
        metadata.model_path = model_path
        metadata_path = f"{self.storage_path}/metadata/{model_filename}.json"
        
        with open(metadata_path, "w") as f:
            json.dump(asdict(metadata), f, default=str)
        
        # Atualizar índice
        self._update_index(metadata)
        
        return metadata.model_id
    
    def load_model(self, model_id: str, version: str = None):
        """Carrega um modelo do registry."""
        if version is None:
            version = self._get_latest_version(model_id)
        
        model_filename = f"{model_id}_{version}.pkl"
        model_path = f"{self.storage_path}/models/{model_filename}"
        
        model = joblib.load(model_path)
        
        # Carregar metadados
        metadata_path = f"{self.storage_path}/metadata/{model_filename}.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Anexar metadados ao modelo
        model.metadata = metadata
        
        return model
    
    def _update_index(self, metadata: ModelMetadata):
        """Atualiza índice de modelos."""
        index_path = f"{self.storage_path}/index.json"
        
        try:
            with open(index_path, "r") as f:
                index = json.load(f)
        except FileNotFoundError:
            index = {"models": {}}
        
        if metadata.model_id not in index["models"]:
            index["models"][metadata.model_id] = {}
        
        index["models"][metadata.model_id][metadata.version] = asdict(metadata)
        
        with open(index_path, "w") as f:
            json.dump(index, f, default=str)
    
    def _get_latest_version(self, model_id: str) -> str:
        """Obtém a versão mais recente de um modelo."""
        index_path = f"{self.storage_path}/index.json"
        
        with open(index_path, "r") as f:
            index = json.load(f)
        
        versions = list(index["models"][model_id].keys())
        versions.sort(reverse=True)
        
        return versions[0]
```

---

## 7. VALIDAÇÃO DE MODELOS

### 7.1 Validação de Features

```python
class ModelValidator:
    def __init__(self, feature_store_client):
        self.feature_store = feature_store_client
    
    def validate_model_before_deployment(
        self,
        model,
        validation_data: pd.DataFrame
    ) -> Dict:
        """
        Valida modelo antes de deployment.
        """
        results = {
            "feature_validation": self._validate_features(validation_data),
            "performance_validation": self._validate_performance(model, validation_data),
            "consistency_validation": self._validate_consistency(model)
        }
        
        results["overall_valid"] = all(
            v["valid"] for v in results.values()
        )
        
        return results
    
    def _validate_features(self, data: pd.DataFrame) -> Dict:
        """Valida que features estão dentro de ranges esperados."""
        issues = []
        
        for column in data.columns:
            if column == "target":
                continue
            
            # Verificar missing values
            missing_rate = data[column].isnull().sum() / len(data)
            if missing_rate > 0.05:
                issues.append({
                    "feature": column,
                    "type": "high_missing_rate",
                    "value": missing_rate
                })
            
            # Verificar outliers
            q25, q75 = data[column].quantile([0.25, 0.75])
            iqr = q75 - q25
            lower_bound = q25 - 3 * iqr
            upper_bound = q75 + 3 * iqr
            
            outliers = ((data[column] < lower_bound) | (data[column] > upper_bound)).sum()
            if outliers / len(data) > 0.01:
                issues.append({
                    "feature": column,
                    "type": "high_outlier_rate",
                    "value": outliers / len(data)
                })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _validate_performance(self, model, data: pd.DataFrame) -> Dict:
        """Valida performance do modelo."""
        X = data.drop("target", axis=1)
        y = data["target"]
        
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        # Calcular métricas
        from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
        
        metrics = {
            "accuracy": accuracy_score(y, predictions),
            "roc_auc": roc_auc_score(y, probabilities[:, 1]),
            "log_loss": log_loss(y, probabilities)
        }
        
        # Comparar com thresholds
        thresholds = {
            "accuracy": 0.55,
            "roc_auc": 0.60,
            "log_loss": 0.69
        }
        
        issues = []
        for metric, value in metrics.items():
            if metric == "log_loss":
                if value > thresholds[metric]:
                    issues.append({
                        "metric": metric,
                        "type": "below_threshold",
                        "value": value,
                        "threshold": thresholds[metric]
                    })
            else:
                if value < thresholds[metric]:
                    issues.append({
                        "metric": metric,
                        "type": "below_threshold",
                        "value": value,
                        "threshold": thresholds[metric]
                    })
        
        return {
            "valid": len(issues) == 0,
            "metrics": metrics,
            "issues": issues
        }
    
    def _validate_consistency(self, model) -> Dict:
        """Valida consistência de features do modelo."""
        # Verificar que o modelo tem metadados de features
        if not hasattr(model, "metadata"):
            return {
                "valid": False,
                "issues": [{"type": "missing_metadata"}]
            }
        
        # Verificar que feature_versions está presente
        if "feature_versions" not in model.metadata:
            return {
                "valid": False,
                "issues": [{"type": "missing_feature_versions"}]
            }
        
        return {
            "valid": True,
            "issues": []
        }
```

---

## 8. AUTOMAÇÃO DE PIPELINE

### 8.1 End-to-End Pipeline

```python
from prefect import flow, task

@task
def extract_training_data(feature_ids, start_date, end_date):
    """Extrai dados de treino."""
    builder = TrainingDataBuilder(feature_store_client)
    return builder.build_training_dataset(feature_ids, "target", start_date, end_date)

@task
def select_features(X, y, method="importance", k=20):
    """Seleciona features."""
    selector = FeatureSelector(feature_store_client)
    return selector.select_features(X, y, method, k)

@task
def train_model(X, y, hyperparameters):
    """Treina modelo."""
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(**hyperparameters)
    model.fit(X, y)
    return model

@task
def validate_model(model, validation_data):
    """Valida modelo."""
    validator = ModelValidator(feature_store_client)
    return validator.validate_model_before_deployment(model, validation_data)

@task
def register_model(model, metadata):
    """Registra modelo."""
    registry = ModelRegistry("./model_registry")
    return registry.register_model(model, metadata)

@flow(name="ml_training_pipeline")
def ml_training_pipeline(
    feature_ids: List[str],
    start_date: datetime,
    end_date: datetime,
    hyperparameters: Dict
):
    """Pipeline completo de treino de ML."""
    
    # 1. Extrair dados
    training_data = extract_training_data(feature_ids, start_date, end_date)
    
    # 2. Selecionar features
    X = training_data.drop("target", axis=1)
    y = training_data["target"]
    selected_features = select_features(X, y)
    
    # 3. Treinar modelo
    X_selected = X[selected_features]
    model = train_model(X_selected, y, hyperparameters)
    
    # 4. Validar modelo
    validation_results = validate_model(model, training_data)
    
    if not validation_results["overall_valid"]:
        raise ValueError("Model validation failed")
    
    # 5. Registrar modelo
    metadata = ModelMetadata(
        model_id="betting_model_v1",
        model_name="Betting Model",
        version="1.0",
        training_date=datetime.now(),
        feature_ids=selected_features,
        feature_versions={fid: "latest" for fid in selected_features},
        feature_formulas={},  # Preencher com fórmulas reais
        performance_metrics={},
        hyperparameters=hyperparameters,
        training_data_range={"start": start_date, "end": end_date},
        model_path=""
    )
    
    model_id = register_model(model, metadata)
    
    return model_id
```

---

## 9. BOAS PRÁTICAS

### 9.1 Prevenção de Data Leakage

- **Sempre usar temporal join:** Features devem ser de antes do target
- **Validar timestamps:** Verificar que features não são do futuro
- **Documentar known_at:** Cada feature deve ter timestamp de conhecimento
- **Testar com holdout:** Validar em dados futuros não usados no treino

### 9.2 Reproducibilidade

- **Versionar tudo:** Features, código, dados, hiperparâmetros
- **Usar seeds:** Para qualquer operação aleatória
- **Guardar metadados:** De features, modelo, pipeline
- **Automatizar pipeline:** Sem passos manuais

### 9.3 Monitorização

- **Track feature drift:** Monitorizar mudanças nas features
- **Track model drift:** Monitorizar performance ao longo do tempo
- **Log predictions:** Guardar todas as previsões com features
- **Alert on degradation:** Alertar se performance cai abaixo de threshold

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar TrainingDataBuilder
- [ ] Implementar FeatureSelector
- [ ] Implementar InferencePipeline
- [ ] Criar ModelRegistry
- [ ] Implementar ModelValidator
- [ ] Criar pipeline automatizado com Prefect
- [ ] Implementar validação de consistência treino/produção
- [ ] Adicionar logging de features usadas em previsões
- [ ] Implementar sistema de rollback de modelos
- [ ] Criar dashboard de performance de modelos

---

## 11. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secção mãe
- [[32_Feature_Store/ARQUITETURA_FEATURE_STORE]] → Arquitetura geral
- [[32_Feature_Store/SERVICO_FEATURES]] → API de serviço de features
- [[32_Feature_Store/MONITORIZACAO_FEATURES]] → Monitorização de qualidade
- [[05_Machine_Learning/INDEX]] → Modelos e treinamento
- [[05_Machine_Learning/MODEL_REGISTRY]] → Registry de modelos
- [[31_Data_Validation/INDEX]] → Validação de dados