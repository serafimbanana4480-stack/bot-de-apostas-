# 🤖 Machine Learning

**Componente:** Machine Learning  
**Status:** 🚧 Em desenvolvimento (70%)  
**Responsável:** Principal Quant Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Desenvolver modelos preditivos de alta precisão para prever resultados de jogos NBA, utilizando técnicas avançadas de ensemble learning, calibração probabilística e validação rigorosa.

---

## 🏗️ Arquitetura

### Stack de ML

| Componente | Tecnologia | Versão | Propósito |
|------------|-----------|--------|-----------|
| **Modelos Base** | XGBoost | 2.0.3 | Gradient boosting |
| | LightGBM | 4.3.0 | Gradient boosting otimizado |
| | CatBoost | 1.2.3 | Gradient boosting com categorical features |
| **Ensemble** | Custom Stacking | - | Combinação de modelos |
| **Calibração** | Isotonic Regression | scikit-learn | Calibração probabilística |
| **Otimização** | Optuna | 3.5.0 | Hyperparameter tuning |
| **Tracking** | MLflow | 2.12.1 | Experiment tracking |
| **Meta-labeling** | XGBoost | 2.0.3 | Filtro de falsos positivos |

---

## 🔧 Componentes Técnicos

### 1. Modelos Base

**Arquivo:** `src/models/ensemble.py`

#### XGBoost Baseline

**Hyperparâmetros:**
```python
xgb_params = {
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'max_depth': 6,
    'learning_rate': 0.01,
    'n_estimators': 1000,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'min_child_weight': 3
}
```

#### LightGBM

**Hyperparâmetros:**
```python
lgb_params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'max_depth': 6,
    'learning_rate': 0.01,
    'n_estimators': 1000,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'min_child_samples': 20
}
```

#### CatBoost

**Hyperparâmetros:**
```python
cat_params = {
    'loss_function': 'Logloss',
    'eval_metric': 'Logloss',
    'depth': 6,
    'learning_rate': 0.01,
    'iterations': 1000,
    'l2_leaf_reg': 3.0,
    'subsample': 0.8,
    'colsample_bylevel': 0.8
}
```

### 2. Ensemble Stacking

**Arquivo:** `src/models/ensemble.py`

**Arquitetura:**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   XGBoost   │  │  LightGBM   │  │  CatBoost   │
│   Base      │  │   Base      │  │   Base      │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌─────────────────┐
              │ Meta-Model      │
              │ (Logistic Reg)  │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Final Prediction│
              └─────────────────┘
```

**Implementação:**
```python
class StackingEnsemble:
    def __init__(self):
        self.base_models = {
            'xgb': XGBClassifier(**xgb_params),
            'lgb': LGBMClassifier(**lgb_params),
            'cat': CatBoostClassifier(**cat_params)
        }
        self.meta_model = LogisticRegression()
    
    def fit(self, X, y):
        # Train base models
        base_predictions = {}
        for name, model in self.base_models.items():
            model.fit(X, y)
            base_predictions[name] = model.predict_proba(X)[:, 1]
        
        # Create meta-features
        meta_features = pd.DataFrame(base_predictions)
        
        # Train meta-model
        self.meta_model.fit(meta_features, y)
    
    def predict_proba(self, X):
        # Get base predictions
        base_predictions = {}
        for name, model in self.base_models.items():
            base_predictions[name] = model.predict_proba(X)[:, 1]
        
        # Create meta-features
        meta_features = pd.DataFrame(base_predictions)
        
        # Meta prediction
        return self.meta_model.predict_proba(meta_features)[:, 1]
```

### 3. Calibração Isotônica

**Arquivo:** `05_Machine_Learning/CALIBRACAO_ISOTONICA.md`

**Objetivo:** Calibrar probabilidades para refletir verdadeiras frequências

**Implementação:**
```python
from sklearn.isotonic import IsotonicRegression

class CalibratedModel:
    def __init__(self, base_model):
        self.base_model = base_model
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
    
    def fit(self, X, y):
        # Train base model
        self.base_model.fit(X, y)
        
        # Get uncalibrated probabilities
        uncalibrated_probs = self.base_model.predict_proba(X)[:, 1]
        
        # Fit calibrator
        self.calibrator.fit(uncalibrated_probs, y)
    
    def predict_proba(self, X):
        # Get uncalibrated probabilities
        uncalibrated_probs = self.base_model.predict_proba(X)[:, 1]
        
        # Calibrate
        calibrated_probs = self.calibrator.predict(uncalibrated_probs)
        
        return calibrated_probs
```

**Métricas de Calibração:**
- **Brier Score:** < 0.25
- **Expected Calibration Error:** < 0.05
- **Reliability Diagram:** Próximo da diagonal

### 4. Meta-labeling

**Arquivo:** `src/models/meta_model.py`

**Objetivo:** Filtrar falsos positivos do modelo primário

**Arquitetura:**
```
┌─────────────┐
│ Primary     │
│ Model       │
│ (XGBoost)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Edge        │
│ Calculation │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Meta-Model  │
│ (Filter)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Final       │
│ Decision    │
└─────────────┘
```

**Implementação:**
```python
class MetaLabelingModel:
    def __init__(self):
        self.primary_model = XGBClassifier(**xgb_params)
        self.meta_model = XGBClassifier(**meta_params)
    
    def fit(self, X, y, odds):
        # Train primary model
        self.primary_model.fit(X, y)
        
        # Get primary predictions
        primary_probs = self.primary_model.predict_proba(X)[:, 1]
        
        # Calculate edge
        edge = calculate_edge(primary_probs, odds)
        
        # Create meta-features
        meta_features = pd.DataFrame({
            'primary_prob': primary_probs,
            'edge': edge,
            'odds': odds
        })
        
        # Train meta-model
        # y_meta = 1 se aposta foi lucrativa, 0 caso contrário
        self.meta_model.fit(meta_features, y_meta)
    
    def predict(self, X, odds):
        # Get primary prediction
        primary_probs = self.primary_model.predict_proba(X)[:, 1]
        
        # Calculate edge
        edge = calculate_edge(primary_probs, odds)
        
        # Create meta-features
        meta_features = pd.DataFrame({
            'primary_prob': primary_probs,
            'edge': edge,
            'odds': odds
        })
        
        # Meta prediction
        meta_pred = self.meta_model.predict(meta_features)
        
        # Only bet if meta-model approves
        return meta_pred == 1
```

---

## 🔄 Pipeline de Treino

### Walk-Forward Cross-Validation

**Arquivo:** `05_Machine_Learning/WALK_FORWARD_CV.md`

**Descrição:** Validação temporal que previne data leakage

**Implementação:**
```python
from sklearn.model_selection import TimeSeriesSplit

def walk_forward_validation(X, y, n_splits=5):
    """
    Walk-forward CV com purged periods
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    results = []
    for train_idx, test_idx in tscv.split(X):
        # Purge training data
        train_idx = purge_period(train_idx, test_idx, gap=1)
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train model
        model = StackingEnsemble()
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict_proba(X_test)
        metrics = calculate_metrics(y_test, y_pred)
        
        results.append(metrics)
    
    return results
```

### Purged Cross-Validation

**Descrição:** Remove períodos de embargo para evitar leakage

**Regras:**
- Embargo period: 1 jogo após treino
- Gap period: 1 jogo antes de teste
- Garante independência temporal

### Hyperparameter Tuning

**Arquivo:** `05_Machine_Learning/OPTUNA_TUNING.md`

**Framework:** Optuna

**Implementação:**
```python
import optuna

def objective(trial):
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.1),
        'n_estimators': trial.suggest_int('n_estimators', 100, 2000),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
    }
    
    model = XGBClassifier(**params)
    score = cross_val_score(model, X, y, cv=walk_forward_cv)
    
    return score.mean()

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
```

---

## 📊 Model Registry

**Arquivo:** `30_Model_Registry/INDEX.md`

**Funcionalidades:**
- Versionamento de modelos
- Staging (dev, staging, prod)
- Rollback automático
- Metadata tracking

**Implementação:**
```python
class ModelRegistry:
    def __init__(self, mlflow_client):
        self.client = mlflow_client
    
    def register_model(self, model, model_name, metrics):
        with mlflow.start_run():
            mlflow.log_params(model.get_params())
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(model, "model")
            
            model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
            mlflow.register_model(model_uri, model_name)
    
    def promote_model(self, model_name, version, stage):
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage
        )
    
    def rollback_model(self, model_name, to_version):
        client.transition_model_version_stage(
            name=model_name,
            version=to_version,
            stage="Production"
        )
```

---

## 🧪 Validação e Testes

### Métricas de Performance

**Classificação:**
- **Log Loss:** Minimizar
- **AUC-ROC:** > 0.65
- **Brier Score:** < 0.25
- **Accuracy:** > 55%

**Calibração:**
- **Expected Calibration Error:** < 0.05
- **Brier Score:** < 0.25
- **Reliability Diagram:** Próximo da diagonal

**Negócio:**
- **ROI:** > 3% (simulado)
- **CLV:** > 2% (simulado)
- **Sharpe Ratio:** > 1.0

### Overfitting Tests

**Arquivo:** `06_Backtesting/OVERFITTING_TESTS.md`

**Testes:**
1. **Train-Test Split Temporal:** Garantir separação temporal
2. **Walk-Forward CV:** Validação robusta
3. **Purged CV:** Evitar leakage
4. **Feature Importance Stability:** Consistência entre folds
5. **Prediction Drift:** Monitorizar drift ao longo do tempo

---

## 📈 Monitorização

### Métricas em Produção

**Model Metrics:**
- Latência de predição
- Volume de predições
- Taxa de erro
- Drift de features

**Business Metrics:**
- ROI real
- CLV real
- Win rate
- Drawdown

### Drift Detection

**Arquivo:** `05_Machine_Learning/MONITORIZACAO_DRIFT.md`

**Implementação:**
```python
from scipy.stats import ks_2samp

def detect_drift(reference_data, current_data, threshold=0.05):
    """
    Deteta drift usando Kolmogorov-Smirnov test
    """
    drift_detected = False
    drift_report = {}
    
    for feature in reference_data.columns:
        statistic, p_value = ks_2samp(
            reference_data[feature],
            current_data[feature]
        )
        
        if p_value < threshold:
            drift_detected = True
            drift_report[feature] = {
                'statistic': statistic,
                'p_value': p_value,
                'drift': True
            }
    
    return drift_detected, drift_report
```

---

## 🚀 Performance e Otimização

### Model Optimization

**Técnicas:**
- Early stopping
- Feature selection
- Model quantization
- Batch inference

### Inference Optimization

**Implementação:**
```python
class ModelOptimizer:
    def __init__(self, model):
        self.model = model
    
    def optimize_for_inference(self):
        # Quantization
        self.model = quantize_model(self.model)
        
        # Pruning
        self.model = prune_model(self.model)
        
        # Compilation
        self.model = compile_model(self.model)
        
        return self.model
```

---

## 📝 Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Completar ensemble stacking
- [ ] Implementar calibração isotônica
- [ ] Adicionar meta-labeling
- [ ] Otimizar hyperparameters

### Médio Prazo (1-2 meses)
- [ ] Implementar online learning
- [ ] Adicionar deep learning models
- [ ] Criar autoML pipeline
- [ ] Implementar model compression

### Longo Prazo (3-6 meses)
- [ ] Multi-desporto models
- [ ] Real-time inference
- [ ] Automated retraining
- [ ] Model marketplace

---

## 🔗 Links Relacionados

- [[Feature Engineering]] - Features para treino
- [[Backtesting]] - Validação histórica
- [[Model Registry]] - Gestão de modelos
- [[Pesquisa Avançada e Validação]] - RAG, RLHF e Auto-avaliação do modelo
- [[Índice Mestre]] - Documentação completa

---

**Última atualização:** 2026-05-19  
**Responsável:** Principal Quant Engineer  
**Status:** 🚧 Em desenvolvimento