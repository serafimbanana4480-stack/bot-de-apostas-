# 46_Meta_Labeling — INDEX

**ID:** `SEC-46` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar um sistema de meta-labeling que usa um modelo secundário para filtrar falsos positivos do modelo primário. O meta-modelo aprende a prever se uma aposta terá CLV positivo ex-post, reduzindo o número de apostas ruins enquanto mantém o edge.

---

## 2. CONCEITO DE META-LABELING

### 2.1 Problema

O modelo primário (XGBoost + LightGBM + CatBoost) prevê a probabilidade de vitória de uma equipa. No entanto:

- **Nem todas as previsões de alta probabilidade têm edge real**
- **O mercado pode estar eficiente em certos contextos**
- **O modelo pode overfit em certos regimes**
- **Fatores não capturados pelo modelo podem afetar o outcome**

### 2.2 Solução: Meta-Modelo

O meta-modelo é um modelo secundário que:

- **Input:** Features do modelo primário + edge calculado + contexto adicional
- **Target:** CLV ex-post > 0 (1 se positivo, 0 se negativo)
- **Output:** Probabilidade de que a aposta terá CLV positivo
- **Decisão:** Apenas aprovar aposta se prob_meta > 0.60

### 2.3 Por Que Funciona

O meta-modelo captura:
- **Regime dependence:** Edge funciona melhor em certos contextos (ex: playoffs vs regular season)
- **Market efficiency:** O mercado pode estar mais eficiente em certos jogos (ex: jogos de alto perfil)
- **Model confidence:** O modelo primário pode ter baixa confiança em certas previsões
- **Non-linear interactions:** Interações entre features que o modelo primário não captura

---

## 3. ARQUITETURA DO META-MODELO

```
┌─────────────────────────────────────────────────────────────┐
│                    MODELO PRIMÁRIO                           │
│  (XGBoost + LightGBM + CatBoost → Ensemble)               │
│  Input: 80 features                                        │
│  Output: Probabilidade calibrada (P_cal)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    CÁLCULO DE EDGE                           │
│  edge = (P_cal * odd_mercado) - 1                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FEATURES PARA META-MODELO                      │
│  ├─ Edge calculado                                           │
│  ├─ P_cal (probabilidade calibrada)                        │
│  ├─ Confiança do modelo (variação entre ensemble)          │
│  ├─ Regime (favorito/equilibrado/underdog)                 │
│  ├─ Contexto (back-to-back, travel distance, rest days)    │
│  ├─ Movimento de odds (opening vs closing)                │
│  ├─ Volume de apostas (liquidez do mercado)                │
│  └─ Features do modelo primário (80 features)             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  META-MODELO (XGBoost)                       │
│  Input: ~90 features (80 + 10 adicionais)                 │
│  Target: CLV_expost > 0 (binary)                           │
│  Output: P(CLV > 0 | edge, contexto)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   DECISÃO FINAL                              │
│  Se prob_meta > 0.60 → APROVAR aposta                      │
│  Se prob_meta < 0.60 → REJEITAR aposta                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. IMPLEMENTAÇÃO

### 4.1 Features Adicionais para Meta-Modelo

```python
# app/models/meta_features.py
from typing import Dict
import numpy as np

def generate_meta_features(primary_features: Dict, edge: float, 
                          market_context: Dict) -> Dict:
    """
    Gera features adicionais para o meta-modelo.
    """
    meta_features = {}
    
    # Edge calculado
    meta_features["edge"] = edge
    
    # Probabilidade calibrada do modelo primário
    meta_features["prob_calibrated"] = primary_features["prob_cal"]
    
    # Confiança do modelo (desvio padrão entre ensemble)
    meta_features["model_confidence"] = primary_features["ensemble_std"]
    
    # Regime
    meta_features["regime_favorite"] = 1 if primary_features["prob_cal"] > 0.6 else 0
    meta_features["regime_underdog"] = 1 if primary_features["prob_cal"] < 0.4 else 0
    meta_features["regime_balanced"] = 1 if 0.4 <= primary_features["prob_cal"] <= 0.6 else 0
    
    # Contexto
    meta_features["is_back_to_back"] = market_context["is_back_to_back"]
    meta_features["travel_distance"] = market_context["travel_distance"]
    meta_features["rest_days"] = market_context["rest_days"]
    
    # Movimento de odds
    meta_features["odds_movement_pct"] = market_context["odds_movement_pct"]
    meta_features["odds_volatility"] = market_context["odds_volatility"]
    
    # Volume de apostas (liquidez)
    meta_features["betting_volume"] = market_context["betting_volume"]
    
    # Interações
    meta_features["edge_x_confidence"] = edge * primary_features["ensemble_std"]
    meta_features["edge_x_regime_favorite"] = edge * meta_features["regime_favorite"]
    
    return meta_features
```

### 4.2 Treino do Meta-Modelo

```python
# app/models/meta_model.py
import xgboost as xgb
import pandas as pd
from sklearn.model_selection import PurgedKFold
from sklearn.metrics import roc_auc_score, brier_score_loss

class MetaModel:
    def __init__(self):
        self.model = None
        self.threshold = 0.60
        
    def train(self, X: pd.DataFrame, y: pd.Series, 
              dates: pd.Series, n_folds: int = 12):
        """
        Treina o meta-modelo usando Purged Walk-Forward CV.
        
        Args:
            X: Features (incluindo features do modelo primário + meta features)
            y: Target (CLV_expost > 0)
            dates: Datas dos jogos (para purged CV)
            n_folds: Número de folds para CV
        """
        # Configuração XGBoost
        params = {
            "objective": "binary:logistic",
            "eval_metric": ["logloss", "auc"],
            "max_depth": 3,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 30,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "scale_pos_weight": 1.0,
            "tree_method": "hist",
            "seed": 42,
            "n_estimators": 500,
        }
        
        # Purged Walk-Forward CV
        purged_cv = PurgedKFold(n_splits=n_folds, embargo_days=2)
        
        scores = []
        for train_idx, val_idx in purged_cv.split(X, dates):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Treinar fold
            model = xgb.XGBClassifier(**params)
            model.fit(X_train, y_train, 
                     eval_set=[(X_val, y_val)],
                     early_stopping_rounds=50,
                     verbose=False)
            
            # Avaliar fold
            y_pred = model.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, y_pred)
            brier = brier_score_loss(y_val, y_pred)
            scores.append({"auc": auc, "brier": brier})
        
        # Treinar modelo final com todos os dados
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(X, y)
        
        # Otimizar threshold
        self._optimize_threshold(X, y)
        
        return scores
    
    def _optimize_threshold(self, X: pd.DataFrame, y: pd.Series):
        """
        Otimiza o threshold de decisão para maximizar F1 score.
        """
        y_pred_proba = self.model.predict_proba(X)[:, 1]
        
        # Testar thresholds de 0.40 a 0.80
        thresholds = np.arange(0.40, 0.81, 0.05)
        best_threshold = 0.60
        best_f1 = 0
        
        for threshold in thresholds:
            y_pred = (y_pred_proba >= threshold).astype(int)
            # Calcular F1 (ou outra métrica)
            f1 = self._calculate_f1(y, y_pred)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        self.threshold = best_threshold
    
    def predict(self, X: pd.DataFrame) -> float:
        """
        Prediz probabilidade de CLV > 0.
        
        Returns:
            Probabilidade (0-1)
        """
        if self.model is None:
            raise ValueError("Model not trained")
        
        return self.model.predict_proba(X)[0, 1]
    
    def approve_bet(self, X: pd.DataFrame) -> bool:
        """
        Decide se aprova ou rejeita aposta.
        
        Returns:
            True se aprovar, False se rejeitar
        """
        prob = self.predict(X)
        return prob >= self.threshold
    
    def _calculate_f1(self, y_true, y_pred):
        """Calcula F1 score (simplificado)."""
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        if (precision + recall) == 0:
            return 0
        
        return 2 * (precision * recall) / (precision + recall)
```

### 4.3 Integração com Pipeline Principal

```python
# app/pipeline/signal_generation.py
from app.models.meta_model import MetaModel
from app.models.meta_features import generate_meta_features

class SignalGenerator:
    def __init__(self, primary_model, meta_model: MetaModel):
        self.primary_model = primary_model
        self.meta_model = meta_model
    
    def generate_signal(self, game_id: str, features: Dict, 
                       market_context: Dict) -> Dict:
        """
        Gera sinal de aposta com meta-labeling.
        """
        # 1. Obter predição do modelo primário
        primary_pred = self.primary_model.predict(features)
        prob_cal = primary_pred["prob_calibrated"]
        
        # 2. Calcular edge
        odd = market_context["current_odd"]
        edge = (prob_cal * odd) - 1
        
        # 3. Se edge < 4%, rejeitar imediatamente
        if edge < 0.04:
            return {
                "approved": False,
                "reason": "edge_below_threshold",
                "edge": edge,
                "prob_cal": prob_cal
            }
        
        # 4. Gerar features para meta-modelo
        meta_features = generate_meta_features(
            primary_features=primary_pred,
            edge=edge,
            market_context=market_context
        )
        
        # 5. Obter predição do meta-modelo
        prob_meta = self.meta_model.predict(meta_features)
        
        # 6. Decisão final
        approved = self.meta_model.approve_bet(meta_features)
        
        return {
            "approved": approved,
            "reason": "meta_model" if not approved else "all_checks_passed",
            "edge": edge,
            "prob_cal": prob_cal,
            "prob_meta": prob_meta,
            "threshold": self.meta_model.threshold
        }
```

---

## 5. CRITÉRIOS DE SUCESSO DO META-MODELO

### 5.1 Métricas de Validação

| Métrica | Threshold | Como Medir |
|---------|-----------|-------------|
| ROC-AUC | > 0.60 | Meta-modelo vs baseline (random) |
| F1 Score | > 0.70 | Threshold otimizado |
| Reduction de Falsos Positivos | > 20% | Comparado com modelo primário |
| Retenção de True Positivos | > 80% | CLV positivo mantido |
| CLV Médio (pós-filtro) | > 3.0% | Edge real mantido |

### 5.2 Critérios de Promoção

O meta-modelo é promovido para produção se:

1. ✅ ROC-AUC > 0.60 em Purged CV
2. ✅ F1 Score > 0.70
3. ✅ Redução de falsos positivos > 20%
4. ✅ Retenção de true positives > 80%
5. ✅ CLV médio pós-filtro > 3.0%
6. ✅ Threshold otimizado entre 0.50-0.70

---

## 6. MONITORIZAÇÃO DO META-MODELO

### 6.1 Métricas a Monitorizar

- **Taxa de aprovação:** % de sinais aprovados pelo meta-modelo
- **Taxa de rejeição:** % de sinais rejeitados pelo meta-modelo
- **Prob_meta médio:** Probabilidade média dos sinais aprovados
- **CLV pós-filtro:** CLV médio dos sinais aprovados
- **Drift do meta-modelo:** Mudança na distribuição de prob_meta

### 6.2 Alertas

- Se taxa de aprovação < 30% (meta-modelo muito restritivo)
- Se taxa de aprovação > 80% (meta-modelo muito permissivo)
- Se CLV pós-filtro < 2.0% (meta-modelo não está funcionando)
- Se drift > 0.20 (meta-modelo precisa de re-treino)

---

## 7. RETRAINING DO META-MODELO

### 7.1 Quando Retreinar

- **Mensal:** Retreinar com dados dos últimos 30 dias
- **Se drift > 0.20:** Retreinar imediatamente
- **Se CLV pós-filtro < 2.0%:** Retreinar e investigar

### 7.2 Procedimento de Retraining

1. Coletar dados históricos (features + CLV ex-post)
2. Treinar novo meta-modelo com Purged CV
3. Validar novo modelo (critérios de sucesso)
4. Comparar com modelo atual
5. Se novo modelo é melhor, promover para produção
6. Se novo modelo é pior, manter modelo atual e investigar

---

## 8. EXPERIMENTAÇÃO

### 8.1 Teste A/B

Para validar o meta-modelo antes de produção:

- **Grupo A:** Sinais do modelo primário (sem meta-modelo)
- **Grupo B:** Sinais filtrados pelo meta-modelo
- **Duração:** 1 mês
- **Métrica:** Comparar CLV médio entre grupos

Se Grupo B tem CLV significativamente maior (test estatístico), meta-modelo é validado.

### 8.2 Shadow Mode

Antes de produção:

- Executar meta-modelo em shadow mode (não afeta decisões reais)
- Registar decisões do meta-modelo
- Comparar com decisões reais
- Analisar se meta-modelo teria evitado apostas ruins

---

## 9. BACKLOG DE META-LABELING

- [ ] Implementar MetaModel class
- [ ] Implementar generate_meta_features
- [ ] Treinar meta-modelo com dados históricos
- [ ] Integrar meta-modelo no pipeline de sinais
- [ ] Configurar monitorização do meta-modelo
- [ ] Implementar retraining automático
- [ ] Configurar alertas para meta-modelo
- [ ] Executar teste A/B
- [ ] Executar shadow mode
- [ ] Promover para produção

---

## 10. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos primários
- [[07_Value_Detection/INDEX]] → Motor de edge que consome meta-modelo
- [[06_Backtesting/INDEX]] → Validação do meta-modelo
