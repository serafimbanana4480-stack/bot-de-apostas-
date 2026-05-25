# 05_Machine_Learning — INDEX

**ID:** `SEC-05` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer + MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Construir, validar, calibrar e manter os modelos preditivos que estimam probabilidades de outcomes. O objetivo não é precisão absoluta, mas **vantagem matemática consistente sobre o mercado**.

---

## 2. NOTAS FUNDAMENTAIS

- [[XGBoost_BASELINE]] — Configuração do modelo primário, hiperparâmetros, treino
- [[AUTOML_FRAMEWORK]] — Framework de AutoML com Optuna para tuning automático
- [[META_LABELING_MODELO]] — Modelo secundário para filtrar falsos positivos
- [[CALIBRACAO_ISOTONICA]] — Calibração de probabilidades por regime
- [[WALK_FORWARD_CV]] — Validação temporal purged com embargo
- [[OPTUNA_TUNING]] — Otimização de hiperparâmetros com múltiplas janelas
- [[FEATURE_SELECTION]] — Seleção de features com significância estatística
- [[RETRAINING_STRATEGY]] — Quando e como retreinar; triggered vs scheduled
- [[MODEL_REGISTRY]] — Versioning, staging, promoção, rollback
- [[REPRODUCIBILITY]] — Seeds, ambientes, version locking
- [[LEAKAGE_PREVENTION]] — Como garantir zero leakage temporal e de dados

---

## 3. ARQUITETURA DE MODELOS (ENSEMBLE STACKING)

```
┌──────────────────────────────────────────────────────────────┐
│                      FEATURES (80-100)                        │
│  Forma │ Mercado │ Contexto │ Interações │ On/Off │ Micro  │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│   XGBoost       │ │  LightGBM    │ │  CatBoost    │
│  (gradient)     │ │  (gradient) │ │  (gradient) │
└────────┬────────┘ └──────┬──────┘ └──────┬──────┘
         │                │                │
         └────────────────┼────────────────┘
                          ▼
         ┌──────────────────────────────────┐
         │  META-MODELO LINEAR (Logistic)   │
         │  Stacking das previsões base     │
         └────────────────┬─────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                CALIBRAÇÃO ISOTÓNICA POR REGIME               │
│  Regimes: Favorito │ Equilibrado │ Underdog                  │
│  Output: Probabilidade calibrada                             │
└────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    CÁLCULO DE EDGE                             │
│  edge = (prob_calibrada * odd_mercado) - 1                   │
│  Filtro: edge > 0.04                                         │
└────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                  META-MODELO (XGBoost)                         │
│  Target: P(CLV_expost > 0 | edge, confiança, regime, incerteza)│
│  Filtro: prob_meta > 0.60                                    │
│  Output: SINAL APROVADO / REJEITADO                          │
└────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              GESTÃO DE RISCO (Kelly + Limites)                 │
│  Stake = f(bankroll, edge, confiança, limites de exposição) │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. CONFIGURAÇÃO DOS MODELOS BASE (ENSEMBLE)

### 4.1 XGBoost (Gradient Boosting)

```python
import xgboost as xgb

xgb_config = {
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "auc"],
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 50,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "scale_pos_weight": 1.0,
    "tree_method": "hist",
    "seed": 42,
    "n_estimators": 1000,
}
```

### 4.2 LightGBM (Gradient Boosting)

```python
import lightgbm as lgb

lgb_config = {
    "objective": "binary",
    "metric": ["binary_logloss", "auc"],
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 50,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "bagging_freq": 5,
    "verbosity": -1,
    "seed": 42,
    "n_estimators": 1000,
}
```

### 4.3 CatBoost (Gradient Boosting)

```python
import catboost as cb

cat_config = {
    "loss_function": "Logloss",
    "eval_metric": ["Logloss", "AUC"],
    "depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bylevel": 0.8,
    "min_data_in_leaf": 50,
    "l2_leaf_reg": 1.0,
    "random_seed": 42,
    "n_estimators": 1000,
    "verbose": False,
}
```

### 4.4 Meta-Modelo Linear (Stacking)

```python
from sklearn.linear_model import LogisticRegression

meta_config = {
    "C": 1.0,              # Regularização inversa
    "penalty": "l2",
    "solver": "lbfgs",
    "max_iter": 1000,
    "random_state": 42,
}
```

**Early Stopping:**
- `early_stopping_rounds = 50`
- Métrica de validação: `logloss` no set de validação temporal
- Nunca usar accuracy como métrica de early stopping (enviesada)

---

## 5. VALIDAÇÃO: PURGED WALK-FORWARD

```
Épocas: 2019-20, 2020-21, 2021-22 (TREINO)
        2022-23 (VALIDAÇÃO — com embargo de 2 dias)
        2023-24 (TESTE FINAL — nunca usado para otimização)

Janela deslizante (mensal):
  Treino: últimos 36 meses
  Validação: próximo mês
  Embargo: 2 dias entre treino e validação

Número de folds: 12 (um por mês de validação)
```

**Regra crítica:** Se houver jogos adiados ou adicionados, o embargo deve ser recalculado para garantir que nenhum evento próximo no tempo apareça em ambos os sets.

---

## 6. CRITÉRIOS DE SUCESSO DO MODELO

Antes de promover para staging, o modelo deve satisfazer TODOS os critérios:

| Critério | Threshold | Como Testar |
|----------|-----------|-------------|
| CLV médio | > 2.0% | Métrica no set de teste final |
| Brier Score | < Brier_mercado | Comparar previsões vs probabilidades implícitas |
| ECE | < 0.05 | Reliability diagram por regime |
| ROI simulado | > 5% | Backtest com comissões 5% + slippage 0.5% |
| Sharpe Ratio | > 0.5 | ROI médio / desvio padrão dos retornos |
| Feature importance stability | top 10 features estáveis em ≥ 8 folds | Análise de variância de importância |
| Nenhum leakage temporal | Passar audit de data leakage | Verificar que todas as features são conhecidas antes do jogo |

---

## 7. MLFLOW INTEGRAÇÃO (C-011)

### 7.1 Configuração do MLflow

O sistema usa MLflow 2.12+ para experiment tracking, model registry e artifact management.

**Endpoint:** `http://mlflow:5000` (container docker)
**Backend Store:** PostgreSQL (mesmo DB do sistema)
**Artifact Root:** `/mlflow/artifacts` (volume docker)

### 7.2 Logging de Experimentos

```python
import mlflow
import mlflow.xgboost
import mlflow.sklearn

def train_and_log_model(X_train, y_train, X_val, y_val, params):
    """
    Treina modelo e registra no MLflow.
    """
    with mlflow.start_run(run_name=f"xgboost_{datetime.now().strftime('%Y%m%d_%H%M')}"):
        # Log hiperparâmetros
        mlflow.log_params(params)
        
        # Treinar modelo
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train, 
                 eval_set=[(X_val, y_val)],
                 early_stopping_rounds=50,
                 verbose=False)
        
        # Log métricas
        y_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_pred)
        brier = brier_score_loss(y_val, y_pred)
        mlflow.log_metrics({"auc": auc, "brier": brier})
        
        # Log modelo
        mlflow.xgboost.log_model(model, "model")
        
        # Log artefatos adicionais
        mlflow.log_artifact("feature_importance.png")
        mlflow.log_artifact("calibration_plot.png")
        
        return mlflow.active_run().info.run_id
```

### 7.3 Model Registry

**Fluxo de Promoção:**
1. **Development** → Modelos em experimentação
2. **Staging** → Modelos validados em shadow mode
3. **Production** → Modelos ativos em produção

```python
def promote_to_production(run_id, model_name="value_betting_model"):
    """
    Promove modelo para produção no MLflow Model Registry.
    """
    client = mlflow.tracking.MlflowClient()
    
    # Registrar modelo
    model_uri = f"runs:/{run_id}/model"
    mlflow.register_model(model_uri, model_name)
    
    # Transicionar para Production
    client.transition_model_version_stage(
        name=model_name,
        version=client.get_latest_versions(model_name)[0].version,
        stage="Production"
    )
```

### 7.4 Métricas Tracking Automático

MLflow tracking automático para:
- Hiperparâmetros do modelo
- Métricas de validação (AUC, Brier, ECE)
- Feature importance
- Calibração plots
- Artefatos de código (requirements.txt, git commit)

### 7.5 Comparações de Experimentos

Usar MLflow UI para:
- Comparar runs lado a lado
- Identificar melhores hiperparâmetros
- Visualizar evolução de métricas ao longo do tempo
- Analisar feature importance stability

---

## 8. BACKLOG TÉCNICO
x] Documentar AutoML framework com Optuna
- [
- [ ] Implementar pipeline de treino XGBoost com purged CV
- [ ] Integrar Optuna para tuning de hiperparâmetros
- [ ] Implementar calibração isotónica por regime
- [ ] Criar meta-modelo de filtragem de sinais
- [ ] Construir sistema de experiment tracking com MLflow/Optuna artifacts
- [ ] Criar model registry com staging (dev → staging → prod)
- [ ] Implementar testes de leakage automatizados
- [ ] Documentar reprodutibilidade (requirements freeze, seeds, ambiente)

---

## 8. IMPLEMENTAÇÃO COMPLETA

### 8.1 Script Robusto de ML Pipeline
```python
"""
Pipeline completo de Machine Learning para value betting
Inclui XGBoost, Optuna tuning, MLflow tracking, e validação walk-forward
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import joblib

from sklearn.model_selection import TimeSeriesSplit, PurgedKFold
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import xgboost as xgb
import optuna
import mlflow
import mlflow.xgboost

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLPipeline:
    """Pipeline completo de ML para value betting"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = None
        self.calibrator = None
        self.feature_names = None
        self.training_history = []
        
        logger.info("🤖 MLPipeline inicializado")
    
    def prepare_data(self, df: pd.DataFrame, target_col: str, 
                    date_col: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepara dados para treino com validação temporal
        """
        logger.info("📊 Preparando dados para treino...")
        
        # Ordenar por data
        df = df.sort_values(date_col).reset_index(drop=True)
        
        # Separar features e target
        X = df.drop(columns=[target_col, date_col])
        y = df[target_col]
        
        # Guardar nomes das features
        self.feature_names = X.columns.tolist()
        
        logger.info(f"   Features: {len(self.feature_names)}")
        logger.info(f"   Amostras: {len(X)}")
        
        return X, y
    
    def purged_walk_forward_cv(self, X: pd.DataFrame, y: pd.Series,
                              n_splits: int = 5, embargo_days: int = 2) -> List[Tuple]:
        """
        Validação walk-forward com purged CV e embargo temporal
        """
        logger.info(f"🔄 Iniciando purged walk-forward CV ({n_splits} folds, embargo {embargo_days} dias)...")
        
        cv = TimeSeriesSplit(n_splits=n_splits)
        splits = []
        
        for fold, (train_idx, val_idx) in enumerate(cv.split(X)):
            # Aplicar embargo: remover amostras próximas ao limite
            train_end = train_idx[-1]
            val_start = val_idx[0]
            
            # Remover amostras de treino próximas ao início da validação
            embargo_start = max(train_end - embargo_days, 0)
            train_idx_purged = train_idx[train_idx <= embargo_start]
            
            # Remover amostras de validação próximas ao fim do treino
            embargo_end = train_end + embargo_days
            val_idx_purged = val_idx[val_idx > embargo_end]
            
            if len(train_idx_purged) > 0 and len(val_idx_purged) > 0:
                splits.append((train_idx_purged, val_idx_purged))
                logger.info(f"   Fold {fold + 1}: Train={len(train_idx_purged)}, Val={len(val_idx_purged)}")
        
        return splits
    
    def train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series,
                     X_val: pd.DataFrame, y_val: pd.Series,
                     params: Optional[Dict] = None) -> xgb.XGBClassifier:
        """
        Treina modelo XGBoost com early stopping
        """
        logger.info("🎯 Treinando modelo XGBoost...")
        
        if params is None:
            params = self.config.get('xgb_params', self._get_default_xgb_params())
        
        model = xgb.XGBClassifier(**params)
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
        
        logger.info(f"✅ Modelo treinado (best iteration: {model.best_iteration})")
        
        return model
    
    def calibrate_model(self, model: xgb.XGBClassifier, X: pd.DataFrame, 
                      y: pd.Series, method: str = 'isotonic') -> CalibratedClassifierCV:
        """
        Calibra probabilidades do modelo
        """
        logger.info(f"🎚️  Calibrando modelo ({method})...")
        
        calibrator = CalibratedClassifierCV(
            model,
            method=method,
            cv='prefit'
        )
        
        calibrator.fit(X, y)
        
        logger.info("✅ Modelo calibrado")
        
        return calibrator
    
    def evaluate_model(self, model: xgb.XGBClassifier, X: pd.DataFrame, 
                     y: pd.Series) -> Dict[str, float]:
        """
        Avalia modelo com múltiplas métricas
        """
        logger.info("📈 Avaliando modelo...")
        
        y_pred_proba = model.predict_proba(X)[:, 1]
        y_pred = model.predict(X)
        
        metrics = {
            'auc': roc_auc_score(y, y_pred_proba),
            'brier': brier_score_loss(y, y_pred_proba),
            'logloss': log_loss(y, y_pred_proba),
            'accuracy': (y_pred == y).mean()
        }
        
        logger.info(f"   AUC: {metrics['auc']:.4f}")
        logger.info(f"   Brier: {metrics['brier']:.4f}")
        logger.info(f"   LogLoss: {metrics['logloss']:.4f}")
        
        return metrics
    
    def calculate_clv(self, y_true: pd.Series, y_pred_proba: pd.Series,
                     odds: pd.Series) -> float:
        """
        Calcula CLV (Closing Line Value) médio
        """
        logger.info("💰 Calculando CLV...")
        
        # CLV = (pred_prob * odd) - 1
        clv = (y_pred_proba * odds) - 1
        
        # CLV médio para jogos onde apostaríamos
        avg_clv = clv.mean()
        
        logger.info(f"   CLV médio: {avg_clv:.4f}")
        
        return avg_clv
    
    def objective_optuna(self, trial: optuna.Trial, X_train: pd.DataFrame,
                        y_train: pd.Series, X_val: pd.DataFrame,
                        y_val: pd.Series) -> float:
        """
        Função objetivo para Optuna tuning
        """
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': trial.suggest_int('max_depth', 3, 8),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 10, 100),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
            'n_estimators': 1000,
            'tree_method': 'hist',
            'random_state': 42
        }
        
        model = xgb.XGBClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
        
        y_pred_proba = model.predict_proba(X_val)[:, 1]
        brier = brier_score_loss(y_val, y_pred_proba)
        
        return brier
    
    def optimize_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series,
                               X_val: pd.DataFrame, y_val: pd.Series,
                               n_trials: int = 100) -> Dict:
        """
        Otimiza hiperparâmetros com Optuna
        """
        logger.info(f"🔍 Otimizando hiperparâmetros ({n_trials} trials)...")
        
        study = optuna.create_study(direction='minimize')
        study.optimize(
            lambda trial: self.objective_optuna(trial, X_train, y_train, X_val, y_val),
            n_trials=n_trials,
            show_progress_bar=True
        )
        
        best_params = study.best_params
        logger.info(f"✅ Melhores parâmetros: {best_params}")
        
        return best_params
    
    def run_pipeline(self, df: pd.DataFrame, target_col: str, date_col: str,
                    optimize: bool = False, n_trials: int = 50) -> Dict:
        """
        Executa pipeline completo de ML
        """
        logger.info("🚀 Iniciando pipeline completo...")
        
        # Preparar dados
        X, y = self.prepare_data(df, target_col, date_col)
        
        # Obter splits de validação
        splits = self.purged_walk_forward_cv(X, y, n_splits=5)
        
        # Usar último split para treino final
        train_idx, val_idx = splits[-1]
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Otimizar hiperparâmetros se solicitado
        if optimize:
            best_params = self.optimize_hyperparameters(X_train, y_train, X_val, y_val, n_trials)
            params = {**self._get_default_xgb_params(), **best_params}
        else:
            params = self._get_default_xgb_params()
        
        # Treinar modelo
        self.model = self.train_xgboost(X_train, y_train, X_val, y_val, params)
        
        # Calibrar modelo
        self.calibrator = self.calibrate_model(self.model, X_val, y_val)
        
        # Avaliar modelo
        metrics = self.evaluate_model(self.model, X_val, y_val)
        
        # Guardar histórico
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'metrics': metrics,
            'n_train': len(X_train),
            'n_val': len(X_val)
        })
        
        logger.info("✅ Pipeline completo")
        
        return {
            'model': self.model,
            'calibrator': self.calibrator,
            'metrics': metrics,
            'params': params
        }
    
    def save_model(self, filepath: str):
        """Salva modelo calibrado"""
        logger.info(f"💾 Salvando modelo em {filepath}...")
        
        model_data = {
            'model': self.model,
            'calibrator': self.calibrator,
            'feature_names': self.feature_names,
            'config': self.config,
            'training_history': self.training_history
        }
        
        joblib.dump(model_data, filepath)
        logger.info("✅ Modelo salvo")
    
    def load_model(self, filepath: str):
        """Carrega modelo calibrado"""
        logger.info(f"📂 Carregando modelo de {filepath}...")
        
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.calibrator = model_data['calibrator']
        self.feature_names = model_data['feature_names']
        self.config = model_data['config']
        self.training_history = model_data['training_history']
        
        logger.info("✅ Modelo carregado")
    
    def predict(self, X: pd.DataFrame, calibrated: bool = True) -> np.ndarray:
        """Faz predições"""
        if calibrated and self.calibrator:
            return self.calibrator.predict_proba(X)[:, 1]
        return self.model.predict_proba(X)[:, 1]
    
    def _get_default_xgb_params(self) -> Dict:
        """Retorna parâmetros padrão do XGBoost"""
        return {
            'objective': 'binary:logistic',
            'eval_metric': ['logloss', 'auc'],
            'max_depth': 4,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 50,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'n_estimators': 1000,
            'tree_method': 'hist',
            'random_state': 42
        }

class MLFlowTracker:
    """Tracker de experimentos com MLflow"""
    
    def __init__(self, tracking_uri: str = "http://mlflow:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        logger.info("📊 MLflow tracker inicializado")
    
    def log_experiment(self, pipeline: MLPipeline, experiment_name: str,
                      metrics: Dict, params: Dict, artifacts: List[str] = None):
        """Registra experimento no MLflow"""
        logger.info(f"📝 Registrando experimento: {experiment_name}")
        
        with mlflow.start_run(run_name=f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"):
            # Log parâmetros
            mlflow.log_params(params)
            
            # Log métricas
            mlflow.log_metrics(metrics)
            
            # Log modelo
            mlflow.xgboost.log_model(pipeline.model, "model")
            
            # Log artefatos
            if artifacts:
                for artifact in artifacts:
                    mlflow.log_artifact(artifact)
            
            logger.info(f"✅ Experimento registrado: {mlflow.active_run().info.run_id}")
    
    def register_model(self, run_id: str, model_name: str, stage: str = "Staging"):
        """Registra modelo no MLflow Model Registry"""
        logger.info(f"📦 Registrando modelo: {model_name} ({stage})...")
        
        client = mlflow.tracking.MlflowClient()
        
        # Registrar modelo
        model_uri = f"runs:/{run_id}/model"
        mlflow.register_model(model_uri, model_name)
        
        # Transicionar para stage
        version = client.get_latest_versions(model_name)[0].version
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage
        )
        
        logger.info(f"✅ Modelo registrado: {model_name} v{version} ({stage})")

# Uso
if __name__ == "__main__":
    # Configuração
    config = {
        'xgb_params': None  # Será definido via Optuna
        'target_col': 'target',
        'date_col': 'game_date'
    }
    
    # Criar pipeline
    pipeline = MLPipeline(config)
    
    # Criar tracker
    tracker = MLFlowTracker()
    
    # Dados exemplo (substituir com dados reais)
    df = pd.DataFrame({
        'feature1': np.random.rand(1000),
        'feature2': np.random.rand(1000),
        'feature3': np.random.rand(1000),
        'target': np.random.randint(0, 2, 1000),
        'game_date': pd.date_range('2023-01-01', periods=1000)
    })
    
    # Executar pipeline
    result = pipeline.run_pipeline(
        df,
        target_col='target',
        date_col='game_date',
        optimize=True,
        n_trials=20
    )
    
    # Log experimento
    tracker.log_experiment(
        pipeline,
        experiment_name="value_betting_xgboost",
        metrics=result['metrics'],
        params=result['params']
    )
    
    # Salvar modelo
    pipeline.save_model("models/xgboost_model.joblib")
```

---

## 9. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[03_Quant_Research/INDEX]] → Fundamentos matemáticos
- [[06_Backtesting/INDEX]] → Validação temporal rigorosa
- [[29_Experiment_Tracking/INDEX]] → Tracking de experimentos
- [[30_Model_Registry/INDEX]] → Gestão de modelos em produção
- [[46_Meta_Labeling/INDEX]] → Meta-labeling e filtro de qualidade
- [[32_Feature_Store/INDEX]] → Features de entrada
