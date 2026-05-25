# XGBoost_BASELINE — Configuração do Modelo Primário

**ID:** `ML-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar a configuração base do modelo XGBoost utilizado para prever probabilidades de outcomes em jogos NBA. Este modelo é o coração do sistema de value betting e deve ser rigorosamente validado antes de produção.

---

## 2. PORQUÊ XGBOOST?

| Critério | XGBoost | Alternativas Rejeitadas |
|----------|---------|-------------------------|
| Performance em dados tabulares | Superior | LightGBM (menos estável), Neural Networks (overkill) |
| Velocidade de treino | Rápido | Deep Learning (muito lento) |
| Interpretabilidade | Feature importance clara | Black-box models |
| Robustez a outliers | Built-in handling | Regressão linear (sensível) |
| Suporte a regularização | L1 + L2 integradas | Random Forest (limitado) |

---

## 3. CONFIGURAÇÃO PADRÃO (Moneyline)

```python
import xgboost as xgb

model_config = {
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

**Early Stopping:** `early_stopping_rounds = 50` com métrica `logloss` no set de validação temporal.

---

## 4. VALIDAÇÃO DE HIPERPARÂMETROS

Otimizar para CLV médio no set de validação (primário), Brier Score (secundário), Sharpe Ratio (terciário). NUNCA otimizar para accuracy isoladamente.

---

## 5. DIAGNÓSTICO DE OVERFITTING

Sinais: logloss train << logloss val (delta > 0.1), feature importance instável, performance cai no teste.

---

## 6. INFERÊNCIA EM PRODUÇÃO

```python
def predict_proba(model, features_df):
    assert list(features_df.columns) == model.get_booster().feature_names
    probas = model.predict_proba(features_df)[:, 1]
    return probas
```

---

## 7. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[06_Backtesting/INDEX]]
- [[CALIBRACAO_ISOTONICA]]
