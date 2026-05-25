# XGBoost_BASELINE — Modelo Primário

**ID:** `ML-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Construir o modelo primário de estimação de probabilidades de resultado NBA (Moneyline e Spread). XGBoost foi escolhido como algoritmo baseline devido à sua performance robusta em dados tabulares, capacidade de lidar com features não-lineares, e eficiência computacional. O objetivo não é criar o modelo mais complexo possível, mas um baseline sólido e interpretável que possa ser melhorado iterativamente. Este modelo serve como referência para comparação com modelos mais avançados e como ponto de partida para otimização de hiperparâmetros.

---

## 2. POR QUE XGBOOST?

### 2.1 Vantagens do XGBoost

**Performance em Dados Tabulares:**
- XGBoost é state-of-the-art para dados tabulares estruturados
- Lida bem com features numéricas e categóricas
- Captura interações não-lineares entre features automaticamente

**Robustez:**
- Lida bem com missing values (não precisa de imputação prévia)
- Resistente a overfitting com regularização L1/L2
- Estável mesmo com features correlacionadas

**Eficiência:**
- Treino rápido com implementação otimizada em C++
- Suporta treino paralelo e distribuído
- Inferência rápida para produção

**Interpretabilidade:**
- Feature importance global e local
- SHAP values para interpretação de predições individuais
- Visualização de árvores de decisão

### 2.2 Alternativas Consideradas

**Random Forest:**
- Vantagem: Mais simples de interpretar
- Desvantagem: Geralmente menos preciso que XGBoost
- Decisão: XGBoost escolhido por melhor performance

**Logistic Regression:**
- Vantagem: Altamente interpretável
- Desvantagem: Assume linearidade, não captura interações complexas
- Decisão: Usado como baseline simples para comparação

**Neural Networks:**
- Vantagem: Pode capturar padrões muito complexos
- Desvantagem: Requer mais dados, mais difícil de treinar, menos interpretável
- Decisão: Considerado para versões futuras após baseline estabelecido

---

## 3. CONFIGURAÇÃO BASE

### 3.1 Parâmetros Conservadores Iniciais

A configuração base usa valores conservadores para evitar overfitting e garantir estabilidade:

```python
import xgboost as xgb
from sklearn.calibration import IsotonicRegression
import numpy as np

# Configuracao inicial conservadora
BASE_CONFIG = {
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "auc"],
    "max_depth": 4,                    # Profundidade limitada para evitar overfitting
    "learning_rate": 0.05,             # Learning rate baixo para treino estável
    "subsample": 0.8,                  # Subsampling de linhas para regularização
    "colsample_bytree": 0.8,          # Subsampling de colunas para regularização
    "min_child_weight": 50,            # Peso mínimo em nós filhos para evitar overfitting
    "reg_alpha": 0.1,                  # Regularização L1 (Lasso)
    "reg_lambda": 1.0,                 # Regularização L2 (Ridge)
    "scale_pos_weight": 1.0,           # Balanceamento de classes (1 = sem balanceamento)
    "tree_method": "hist",             # Método de construção de árvores (histogram-based)
    "seed": 42,                        # Semente aleatória para reprodutibilidade
    "n_estimators": 1000,              # Número máximo de árvores (early stopping vai parar antes)
}

def train_primary_model(X_train, y_train, X_val, y_val, config=BASE_CONFIG):
    """
    Treina modelo XGBoost com early stopping.
    
    Args:
        X_train: Features de treino
        y_train: Target de treino (0 ou 1)
        X_val: Features de validação
        y_val: Target de validação
        config: Dicionário de configuração XGBoost
    
    Returns:
        Modelo treinado
    """
    model = xgb.XGBClassifier(**config)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=50,      # Para se não houver melhoria em 50 iterações
        verbose=False
    )
    return model
```

### 3.2 Explicação dos Parâmetros

**max_depth = 4:**
- Profundidade máxima de cada árvore
- Valores baixos (3-6) evitam overfitting
- Valores altos permitem capturar padrões mais complexos mas aumentam risco de overfitting

**learning_rate = 0.05:**
- Tamanho do passo na otimização
- Valores baixos (0.01-0.1) requerem mais árvores mas são mais estáveis
- Valores altos (0.1-0.3) convergem mais rápido mas podem ser instáveis

**subsample = 0.8:**
- Percentagem de linhas usadas em cada árvore
- Valores < 1.0 introduzem aleatoriedade e reduzem overfitting
- Valores próximos de 1.0 usam mais dados mas podem overfitar

**colsample_bytree = 0.8:**
- Percentagem de colunas usadas em cada árvore
- Valores < 1.0 introduzem aleatoriedade e reduzem overfitting
- Valores próximos de 1.0 usam mais features mas podem overfitar

**min_child_weight = 50:**
- Soma mínima de pesos em um nó filho
- Valores altos previnem criação de nós com poucas amostras
- Valores baixos permitem árvores mais complexas

**reg_alpha = 0.1 e reg_lambda = 1.0:**
- Regularização L1 e L2
- Penalizam pesos grandes, reduzindo overfitting
- Valores mais altos = mais regularização (modelo mais simples)

**early_stopping_rounds = 50:**
- Para treino se validação não melhorar em 50 iterações
- Evita overfitting parando no ponto ótimo
- Valor depende do learning rate (mais learning rate = menos rounds)

---

## 4. PREPARAÇÃO DE DADOS

### 4.1 Limpeza e Validação

```python
def prepare_training_data(df_features, target_col='home_won'):
    """
    Prepara dados para treino do modelo.
    
    Args:
        df_features: DataFrame com features e target
        target_col: Nome da coluna target (1 se equipa da casa ganhou, 0 caso contrario)
    
    Returns:
        X: Features para treino
        y: Target para treino
    
    Raises:
        AssertionError: Se houver muitos missing values
    """
    # Remover colunas não preditivas
    X = df_features.drop(columns=[target_col, 'game_id', 'game_date'])
    y = df_features[target_col]
    
    # Validar qualidade dos dados
    assert X.isnull().sum().max() < len(X) * 0.05, "Muitos missing values!"
    
    return X, y
```

### 4.2 Tratamento de Missing Values

XGBoost lida nativamente com missing values, mas é importante validar:

**Percentagem de Missing por Feature:**
- Features com > 50% missing devem ser removidas ou revisadas
- Features com 10-50% missing podem ser mantidas se informativas
- Features com < 10% missing são geralmente aceitáveis

**Imputação (Opcional):**
- Para features críticas com missing, considerar imputação
- Imputação por média/mediana para features numéricas
- Imputação por moda para features categóricas
- XGBoost pode usar missing como categoria separada

---

## 5. CALIBRAÇÃO ISOTÔNICA POR REGIME

### 5.1 Por Que Calibrar?

Modelos de machine learning (especialmente gradient boosting) tendem a ser **mal calibrados**: as probabilidades preditas não correspondem às frequências reais de ocorrência. Por exemplo, o modelo pode prever 70% de probabilidade, mas em casos onde o modelo prediz 70%, o resultado ocorre apenas 60% das vezes.

Calibração é crítica para apostas porque:
- Edge é calculado como (prob_predita × odd - 1)
- Se probabilidades não são calibradas, edge é calculado incorretamente
- Stake sizing via Kelly assume probabilidades calibradas

### 5.2 Calibração por Regime

Diferentes regimes (favorito, equilibrado, underdog) podem ter padrões de calibração diferentes:

```python
from sklearn.calibration import IsotonicRegression

def calibrate_by_regime(model, X_val, y_val, regime_col='regime'):
    """
    Treina calibrador separado para cada regime (favorito/equilibrado/underdog).
    
    Args:
        model: Modelo XGBoost treinado
        X_val: Features de validação
        y_val: Target de validação
        regime_col: Nome da coluna de regime
    
    Returns:
        Dicionário de calibradores por regime
    """
    probs_raw = model.predict_proba(X_val)[:, 1]
    
    calibrators = {}
    for regime in ['favorito', 'equilibrado', 'underdog']:
        mask = X_val[regime_col] == regime
        if mask.sum() > 100:  # Minimo de 100 amostras para calibracao estavel
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(probs_raw[mask], y_val[mask])
            calibrators[regime] = cal
    
    return calibrators

def predict_calibrated(model, calibrators, X, regime_col='regime'):
    """
    Faz predições calibradas usando calibradores por regime.
    
    Args:
        model: Modelo XGBoost treinado
        calibrators: Dicionário de calibradores por regime
        X: Features para predição
        regime_col: Nome da coluna de regime
    
    Returns:
        Probabilidades calibradas
    """
    probs_raw = model.predict_proba(X)[:, 1]
    probs_cal = np.zeros_like(probs_raw)
    
    for regime in ['favorito', 'equilibrado', 'underdog']:
        mask = X[regime_col] == regime
        if regime in calibrators:
            probs_cal[mask] = calibrators[regime].predict(probs_raw[mask])
        else:
            probs_cal[mask] = probs_raw[mask]  # Fallback para probabilidade bruta
    
    return probs_cal
```

### 5.3 Validação de Calibração

**Reliability Diagram:**
- Plota probabilidade predita vs frequência real
- Linha diagonal = calibração perfeita
- Desvios da diagonal indicam má calibração

**Expected Calibration Error (ECE):**
- Métrica quantitativa de calibração
- ECE = 0 indica calibração perfeita
- ECE > 0.1 indica má calibração

**Brier Score:**
- Métrica que combina calibração e refinamento
- Valores mais baixos são melhores
- Brier Score = 0.25 para classificação binária aleatória

---

## 6. MÉTRICAS DE AVALIAÇÃO

### 6.1 Métricas de Performance

```python
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

def evaluate_model(y_true, probs, probs_market=None):
    """
    Avalia performance do modelo com múltiplas métricas.
    
    Args:
        y_true: Target verdadeiro (0 ou 1)
        probs: Probabilidades preditas pelo modelo
        probs_market: Probabilidades implícitas das odds de mercado (opcional)
    
    Returns:
        Dicionário com métricas de avaliação
    """
    metrics = {
        'logloss': log_loss(y_true, probs),
        'brier': brier_score_loss(y_true, probs),
        'auc': roc_auc_score(y_true, probs),
    }
    
    # Se probabilidades de mercado disponíveis, calcular melhoria
    if probs_market is not None:
        metrics['brier_market'] = brier_score_loss(y_true, probs_market)
        metrics['brier_improvement'] = metrics['brier_market'] - metrics['brier']
    
    return metrics
```

### 6.2 Interpretação das Métricas

**Log Loss:**
- Mede a qualidade das probabilidades preditas
- Valores mais baixos são melhores
- Log Loss = 0.693 para classificação binária aleatória
- Target: < 0.6 (significativamente melhor que aleatório)

**Brier Score:**
- Similar ao Log Loss mas mais interpretável
- Quadrado do erro de probabilidade
- Valores mais baixos são melhores
- Brier Score = 0.25 para classificação binária aleatória
- Target: < 0.2

**AUC-ROC:**
- Área sob a curva ROC
- Mede capacidade de discriminação (separar classes)
- Valores mais altos são melhores
- AUC = 0.5 para classificação aleatória
- Target: > 0.55 (melhor que aleatório mas modesto)

**Brier Improvement:**
- Diferença entre Brier Score do mercado e do modelo
- Valores positivos indicam que modelo é melhor que odds de mercado
- Target: > 0.01 (1% de melhoria)

---

## 7. FEATURE IMPORTANCE

### 7.1 Feature Importance Global

```python
def get_feature_importance(model, feature_names):
    """
    Extrai feature importance do modelo.
    
    Args:
        model: Modelo XGBoost treinado
        feature_names: Lista de nomes de features
    
    Returns:
        DataFrame com feature importance ordenado
    """
    importance = model.feature_importances_
    df_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    })
    df_importance = df_importance.sort_values('importance', ascending=False)
    return df_importance
```

### 7.2 SHAP Values (Importância Local)

SHAP (SHapley Additive exPlanations) explica predições individuais:

```python
import shap

def explain_prediction(model, X_sample, feature_names):
    """
    Explica predição individual usando SHAP.
    
    Args:
        model: Modelo XGBoost treinado
        X_sample: Amostra para explicar
        feature_names: Lista de nomes de features
    
    Returns:
        Valores SHAP para cada feature
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    df_shap = pd.DataFrame({
        'feature': feature_names,
        'shap_value': shap_values[0]
    })
    df_shap = df_shap.sort_values('shap_value', key=abs, ascending=False)
    return df_shap
```

---

## 8. VALIDAÇÃO TEMPORAL

### 8.1 Walk-Forward Cross-Validation

Não usar random cross-validation (embaralha dados temporais). Usar walk-forward:

```python
from sklearn.model_selection import TimeSeriesSplit

def walk_forward_cv(X, y, n_splits=5, test_size_days=30):
    """
    Cross-validation temporal walk-forward.
    
    Args:
        X: Features ordenadas por data
        y: Target ordenado por data
        n_splits: Número de folds
        test_size_days: Tamanho do conjunto de teste em dias
    
    Returns:
        Gerador de (train_idx, test_idx)
    """
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size_days)
    return tscv.split(X)
```

### 8.2 Embargo

Aplicar embargo entre treino e validação para evitar leakage temporal:

```python
def apply_embargo(train_idx, test_idx, embargo_days=7):
    """
    Remove amostras do treino que estão muito próximas ao teste.
    
    Args:
        train_idx: Índices de treino
        test_idx: Índices de teste
        embargo_days: Dias de embargo entre treino e teste
    
    Returns:
        train_idx ajustado com embargo
    """
    # Implementar lógica de embargo
    # ...
    return train_idx_adjusted
```

---

## 9. BACKLOG TÉCNICO

- [ ] Implementar pipeline completo de treino com walk-forward CV
- [ ] Integrar Optuna para hyperparameter tuning
- [ ] Criar testes de leakage automatizados
- [ ] Documentar feature importance por fold
- [ ] Implementar cross-validation com purged walk-forward
- [ ] Criar sistema de logging de experimentos
- [ ] Implementar monitoramento de drift de features
- [ ] Criar dashboard de performance do modelo

---

## 10. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secção mãe
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Validação temporal detalhada
- [[05_Machine_Learning/OPTUNA_TUNING]] → Otimização de hiperparâmetros
- [[05_Machine_Learning/CALIBRACAO_ISOTONICA]] → Detalhes de calibração
- [[05_Machine_Learning/LEAKAGE_PREVENTION]] → Prevenção de leakage
