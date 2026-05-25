# MODELACAO_PLAYER_PROPS — Modelagem para Player Props

**ID:** `PP-004` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir a abordagem de modelagem para player props NBA, incluindo escolha entre regressão e classificação, configuração de modelos XGBoost, e estratégias de calibração específicas para mercados de over/under.

---

## 2. ABORDAGEM DE MODELAGEM

### 2.1 Opção A: Regressão (Previsão de Valor Contínuo)

Prever o valor exato da estatística (ex: pontos = 23.5) e converter em probabilidade de over/under.

**Vantagens:**
- Mais informação granular
- Permite calibração por magnitude
- Melhor para entender drivers de performance
- Útil para definir linhas próprias

**Desvantagens:**
- Mais complexo para converter em probabilidade
- Requer modelagem de incerteza (distribuição)
- Erro de previsão pode ser alto em valores extremos

```python
import xgboost as xgb
import numpy as np
from scipy import stats

# Modelo de regressão
regression_model = xgb.XGBRegressor(
    objective='reg:squarederror',
    max_depth=5,
    learning_rate=0.05,
    n_estimators=1000,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=20,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42
)

# Treino
regression_model.fit(X_train, y_train)  # y_train = valor real (ex: 23.5)

# Previsão
pts_predicted = regression_model.predict(X_test)

# Converter em probabilidade de Over
def calculate_over_probability(predicted_value, line, std_dev):
    """
    Calcula probabilidade de passar a linha assumindo distribuição normal.
    
    Args:
        predicted_value: valor previsto pelo modelo
        line: linha do mercado (ex: 22.5)
        std_dev: desvio padrão dos erros de previsão (calculado em validation)
    
    Returns:
        prob_over: probabilidade de passar a linha
    """
    z_score = (line - predicted_value) / std_dev
    prob_over = 1 - stats.norm.cdf(z_score)
    return prob_over

# Exemplo
line = 22.5
std_dev = 4.5  # Calculado em validation set
prob_over = calculate_over_probability(pts_predicted[0], line, std_dev)
```

### 2.2 Opção B: Classificação Binária (Over/Under Direto)

Prever diretamente a probabilidade de passar a linha (over_line = 1/0).

**Vantagens:**
- Direto para betting
- Mais simples de implementar
- Output já é probabilidade
- Métricas alinhadas com objetivo

**Desvantagens:**
- Perde informação de magnitude
- Difícil calibrar para diferentes linhas
- Menos flexível para linhas não padrão

```python
import xgboost as xgb

# Modelo de classificação
classification_model = xgb.XGBClassifier(
    objective='binary:logistic',
    max_depth=4,
    learning_rate=0.05,
    n_estimators=1000,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=30,
    reg_alpha=0.1,
    reg_lambda=1.0,
    scale_pos_weight=1.0,
    eval_metric=['logloss', 'auc'],
    random_state=42
)

# Preparar target (1 se over, 0 se under)
y_train_class = (y_train > line_train).astype(int)

# Treino
classification_model.fit(
    X_train, y_train_class,
    eval_set=[(X_val, y_val_class)],
    early_stopping_rounds=50,
    verbose=False
)

# Previsão
prob_over = classification_model.predict_proba(X_test)[:, 1]
```

### 2.3 Recomendação: Regressão com Calibração

Para player props, **regressão com calibração** é preferível porque:

1. **Mais flexível:** Funciona para qualquer linha
2. **Melhor calibração:** Permite calibrar por magnitude
3. **Mais informação:** Entende se o erro é sistemático
4. **Linha própria:** Pode criar linhas próprias para comparação

---

## 3. CONFIGURAÇÃO XGBOOST PARA PLAYER PROPS

### 3.1 Configuração Base (Regressão)

```python
BASE_CONFIG_REGRESSION = {
    # Objetivo
    "objective": "reg:squarederror",
    "eval_metric": ["rmse", "mae"],
    
    # Estrutura da árvore (conservadora para evitar overfitting)
    "max_depth": 5,              # Profundidade moderada
    "min_child_weight": 25,      # Mínimo de amostras por folha (aumentado)
    "gamma": 0.1,                # Minimum loss reduction
    
    # Amostragem (prevenção de overfitting)
    "subsample": 0.8,            # 80% das linhas por árvore
    "colsample_bytree": 0.8,     # 80% das features por árvore
    "colsample_bylevel": 0.8,    # 80% das features por nível
    
    # Regularização
    "reg_alpha": 0.3,            # L1 regularization (aumentado)
    "reg_lambda": 1.5,           # L2 regularization (aumentado)
    
    # Learning
    "learning_rate": 0.03,       # Learning rate menor
    "n_estimators": 1500,        # Mais árvores com learning rate menor
    
    # Outros
    "tree_method": "hist",
    "seed": 42,
}
```

### 3.2 Configuração Base (Classificação)

```python
BASE_CONFIG_CLASSIFICATION = {
    # Objetivo
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "auc", "error"],
    
    # Estrutura da árvore
    "max_depth": 4,              # Profundidade menor para classificação
    "min_child_weight": 30,      # Mínimo de amostras por folha
    "gamma": 0.1,
    
    # Amostragem
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "colsample_bylevel": 0.8,
    
    # Regularização
    "reg_alpha": 0.3,
    "reg_lambda": 1.5,
    
    # Learning
    "learning_rate": 0.03,
    "n_estimators": 1500,
    
    # Balanceamento de classes
    "scale_pos_weight": 1.0,     # Ajustar se classes desbalanceadas
    
    # Outros
    "tree_method": "hist",
    "seed": 42,
}
```

### 3.3 Configuração por Mercado

Diferentes mercados (PTS/REB/AST) podem requerer configurações diferentes.

```python
# Pontos: mais volátil, requer mais regularização
PTS_CONFIG = {
    **BASE_CONFIG_REGRESSION,
    "max_depth": 4,
    "min_child_weight": 35,
    "reg_alpha": 0.5,
    "reg_lambda": 2.0,
}

# Ressaltos: menos volátil, pode ser menos regularizado
REB_CONFIG = {
    **BASE_CONFIG_REGRESSION,
    "max_depth": 5,
    "min_child_weight": 20,
    "reg_alpha": 0.2,
    "reg_lambda": 1.0,
}

# Assistências: muito volátil, requer regularização forte
AST_CONFIG = {
    **BASE_CONFIG_REGRESSION,
    "max_depth": 4,
    "min_child_weight": 40,
    "reg_alpha": 0.6,
    "reg_lambda": 2.5,
}
```

---

## 4. CALIBRAÇÃO DE PROBABILIDADES

### 4.1 Calibração por Regime de Linha

Player props têm linhas muito variadas (ex: PTS pode variar de 10.5 a 40.5). Calibração deve ser por regime de linha.

```python
from sklearn.calibration import IsotonicRegression
import numpy as np

def calibrate_by_line_regime(y_true, y_pred, lines, n_bins=5):
    """
    Calibra probabilidades por regime de linha.
    
    Args:
        y_true: valores reais
        y_pred: valores previstos
        lines: linhas do mercado
        n_bins: número de bins para dividir as linhas
    
    Returns:
        calibrators: dicionário de calibradores por regime
    """
    # Criar bins de linhas
    line_percentiles = np.percentile(lines, np.linspace(0, 100, n_bins + 1))
    
    calibrators = {}
    
    for i in range(n_bins):
        # Definir regime
        line_min = line_percentiles[i]
        line_max = line_percentiles[i + 1]
        regime_name = f"line_{line_min:.1f}_{line_max:.1f}"
        
        # Filtrar dados deste regime
        mask = (lines >= line_min) & (lines < line_max)
        
        if mask.sum() > 50:  # Mínimo de amostras
            # Calibrar
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[regime_name] = cal
    
    return calibrators

def predict_calibrated(y_pred, lines, calibrators):
    """
    Aplica calibração por regime de linha.
    """
    y_pred_cal = np.zeros_like(y_pred)
    
    for regime_name, cal in calibrators.items():
        # Extrair limites do regime
        line_min = float(regime_name.split('_')[1])
        line_max = float(regime_name.split('_')[2])
        
        # Aplicar calibração
        mask = (lines >= line_min) & (lines < line_max)
        y_pred_cal[mask] = cal.predict(y_pred[mask])
    
    return y_pred_cal
```

### 4.2 Calibração por Tipo de Jogador

Diferentes tipos de jogadores (estrelas vs role players) têm padrões diferentes.

```python
def calibrate_by_player_type(y_true, y_pred, player_types):
    """
    Calibra por tipo de jogador (star/starter/role_player).
    """
    calibrators = {}
    
    for player_type in ['star', 'starter', 'role_player']:
        mask = player_types == player_type
        
        if mask.sum() > 50:
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[player_type] = cal
    
    return calibrators
```

### 4.3 Calibração por Situação de Jogo

```python
def calibrate_by_game_situation(y_true, y_pred, situations):
    """
    Calibra por situação de jogo (blowout/close/overtime).
    """
    calibrators = {}
    
    for situation in ['blowout', 'close', 'overtime']:
        mask = situations == situation
        
        if mask.sum() > 30:
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[situation] = cal
    
    return calibrators
```

---

## 5. VALIDAÇÃO DE MODELO

### 5.1 Métricas de Regressão

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

def evaluate_regression(y_true, y_pred):
    """
    Avalia modelo de regressão.
    """
    metrics = {
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mae': mean_absolute_error(y_true, y_pred),
        'r2': r2_score(y_true, y_pred),
        'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100,
    }
    
    # Métricas específicas para betting
    metrics['bias'] = np.mean(y_pred - y_true)  # Viés médio
    metrics['over_prediction_rate'] = np.mean(y_pred > y_true)  # % de over-prediction
    
    return metrics
```

### 5.2 Métricas de Classificação

```python
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

def evaluate_classification(y_true, probs):
    """
    Avalia modelo de classificação.
    """
    metrics = {
        'logloss': log_loss(y_true, probs),
        'brier': brier_score_loss(y_true, probs),
        'auc': roc_auc_score(y_true, probs),
    }
    
    return metrics
```

### 5.3 Métricas de Betting

```python
def evaluate_betting_performance(y_true, probs_over, lines, odds_over, odds_under):
    """
    Avalia performance de betting simulada.
    """
    # Converter probs em decisões de betting
    # (ex: bet se edge > 2%)
    
    edge_threshold = 0.02
    bets_over = probs_over > (1 / odds_over) + edge_threshold
    bets_under = (1 - probs_over) > (1 / odds_under) + edge_threshold
    
    # Simular resultados
    results_over = (y_true > lines) & bets_over
    results_under = (y_true <= lines) & bets_under
    
    # Calcular ROI
    roi_over = calculate_roi(results_over, odds_over[bets_over])
    roi_under = calculate_roi(results_under, odds_under[bets_under])
    
    metrics = {
        'roi_over': roi_over,
        'roi_under': roi_under,
        'total_bets': bets_over.sum() + bets_under.sum(),
        'win_rate_over': results_over.mean() if bets_over.sum() > 0 else 0,
        'win_rate_under': results_under.mean() if bets_under.sum() > 0 else 0,
    }
    
    return metrics
```

---

## 6. VALIDAÇÃO TEMPORAL

### 6.1 Walk-Forward CV para Player Props

```python
from sklearn.model_selection import TimeSeriesSplit

def walk_forward_cv_player_props(X, y, dates, n_splits=5):
    """
    Walk-forward cross-validation específico para player props.
    
    Diferenças vs team props:
    - Menos dados por jogador (mais esparsos)
    - Requer purging mais agressivo (lesões têm impacto imediato)
    - Val gap maior (evitar leakage de matchup)
    """
    splits = []
    
    # Ordenar por data
    sorted_indices = np.argsort(dates)
    X_sorted = X.iloc[sorted_indices]
    y_sorted = y.iloc[sorted_indices]
    dates_sorted = dates.iloc[sorted_indices]
    
    # Criar splits
    n_samples = len(X_sorted)
    train_size = n_samples // (n_splits + 1)
    
    for i in range(n_splits):
        train_start = 0
        train_end = train_size * (i + 1)
        val_start = train_end + 7  # 7 dias de gap (purging)
        val_end = train_end + train_size
        
        if val_end > n_samples:
            break
        
        train_indices = np.arange(train_start, train_end)
        val_indices = np.arange(val_start, val_end)
        
        splits.append((train_indices, val_indices))
    
    return splits
```

### 6.2 Purging Agressivo

Player props requerem purging mais agressivo devido a lesões e mudanças de lineup.

```python
def aggressive_purging(train_indices, val_indices, dates, player_ids, purge_days=14):
    """
    Remove dados de treino que estão muito próximos de validação.
    
    Para player props, usar 14 dias (vs 7 dias para team props).
    """
    train_dates = dates.iloc[train_indices]
    val_dates = dates.iloc[val_indices]
    train_players = player_ids.iloc[train_indices]
    val_players = player_ids.iloc[val_indices]
    
    # Encontrar data mínima de validação
    min_val_date = val_dates.min()
    
    # Remover treino dentro de purge_days da validação
    purge_threshold = min_val_date - pd.Timedelta(days=purge_days)
    
    valid_train = train_dates < purge_threshold
    purged_train_indices = train_indices[valid_train]
    
    return purged_train_indices, val_indices
```

---

## 7. FEATURE IMPORTANCE

### 7.1 Análise de Importância

```python
def analyze_feature_importance(model, feature_names, top_n=20):
    """
    Analisa feature importance do modelo.
    """
    importance = model.feature_importances_
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    return importance_df.head(top_n)
```

### 7.2 SHAP Values para Interpretação

```python
import shap

def explain_predictions(model, X, sample_size=100):
    """
    Usa SHAP para explicar previsões.
    """
    # Criar explainer
    explainer = shap.TreeExplainer(model)
    
    # Calcular SHAP values para amostra
    sample = X.sample(n=min(sample_size, len(X)), random_state=42)
    shap_values = explainer.shap_values(sample)
    
    # Plot summary
    shap.summary_plot(shap_values, sample, plot_type="bar")
    
    return shap_values
```

---

## 8. MONITORIZAÇÃO DE DRIFT

### 8.1 Feature Drift

```python
from scipy import stats

def detect_feature_drift(reference_features, current_features, threshold=0.05):
    """
    Detecta drift nas features usando Kolmogorov-Smirnov test.
    """
    drift_detected = {}
    
    for col in reference_features.columns:
        ks_stat, p_value = stats.ks_2samp(
            reference_features[col],
            current_features[col]
        )
        
        drift_detected[col] = {
            'ks_stat': ks_stat,
            'p_value': p_value,
            'drift': p_value < threshold
        }
    
    return drift_detected
```

### 8.2 Prediction Drift

```python
def detect_prediction_drift(reference_predictions, current_predictions, threshold=0.05):
    """
    Detecta drift nas previsões.
    """
    ks_stat, p_value = stats.ks_2samp(
        reference_predictions,
        current_predictions
    )
    
    return {
        'ks_stat': ks_stat,
        'p_value': p_value,
        'drift': p_value < threshold
    }
```

---

## 9. BACKLOG

- [ ] Implementar pipeline de treino para regressão
- [ ] Implementar pipeline de treino para classificação
- [ ] Implementar calibração por regime de linha
- [ ] Implementar calibração por tipo de jogador
- [ ] Implementar walk-forward CV com purging agressivo
- [ ] Analisar feature importance em dados históricos
- [ ] Implementar detecção de drift
- [ ] Comparar performance regressão vs classificação
- [ ] Documentar configuração ótima por mercado (PTS/REB/AST)

---

## 10. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/FEATURES_JOGADOR]] → Features usadas no modelo
- [[42_Player_Props/CALIBRACAO_PROBABILIDADES]] → Calibração detalhada
- [[05_Machine_Learning/XGBoost_BASELINE]] → Configuração base XGBoost
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Validação temporal
- [[05_Machine_Learning/CALIBRACAO_ISOTONICA]] → Calibração isotónica