# META-LABELING DETALHADA — FILTRO DE QUALIDADE

**ID:** `FEA-002` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar um modelo secundário (meta-modelo) que filtra falsos positivos do modelo primário, aumentando a qualidade dos sinais e reduzindo overfitting.

**Problema:** O modelo primário estima probabilidades, mas nem todos os edges estimados são genuínos. Meta-labeling aprende a distinguir edges que se mantêm vs edges que desaparecem.

---

## 2. CONCEITO DE META-LABELING

### 2.1 O que é Meta-Labeling?

Meta-labeling é uma técnica onde:
- **Modelo Primário:** Estima `P(resultado | features)`
- **Meta-Modelo:** Estima `P(edge é genuíno | P_primário, edge, contexto)`

**Intuição:** O meta-modelo aprende quando confiar no edge estimado pelo modelo primário.

### 2.2 Por que usar Meta-Labeling?

| Benefício | Explicação |
|-----------|------------|
| Filtra falsos positivos | Reduz número de apostas de baixa qualidade |
| Aumenta CLV real | Só aposta quando edge se mantém |
| Reduz overfitting | Meta-modelo generaliza melhor que thresholds fixos |
| Adaptativo | Ajusta automaticamente a mudanças de mercado |

---

## 3. FEATURES DO META-MODELO

### 3.1 Features do Modelo Primário

```python
features_meta = [
    'p_modelo',           # Probabilidade do modelo primário
    'p_modelo_logit',     # Logit da probabilidade
    'confidence',         # Confiança (1 - entropia)
]
```

### 3.2 Features de Edge

```python
features_edge = [
    'edge_estimado',      # P_modelo * odd - 1
    'edge_absoluto',      # |edge_estimado|
    'edge_normalized',    # edge / (odd - 1)
]
```

### 3.3 Features de Confiança

```python
features_confidence = [
    'entropia',           # -P*log(P) - (1-P)*log(1-P)
    'margin',             # |P - 0.5|
    'sharpness',          # 1 / (2 * std(predictions))
]
```

### 3.4 Features de Regime

```python
features_regime = [
    'is_favorite',        # P_modelo >= 0.65
    'is_underdog',        # P_modelo < 0.35
    'is_balanced',        # 0.35 <= P_modelo < 0.65
    'home_game',          # 1 se casa, 0 fora
    'back_to_back',       # 1 se B2B, 0 caso contrário
]
```

### 3.5 Features de Qualidade de Dados

```python
features_quality = [
    'games_history',      # Número de jogos usados no cálculo das features
    'odds_age_minutes',   # Idade da odd em minutos
    'market_liquidity',   # Volume disponível no mercado
]
```

**Total de features:** 15-20 features

---

## 4. TARGET DO META-MODELO

### 4.1 Definição

```python
target = 1 if odds_close_pinnacle > odds_used else 0
```

**Interpretação:**
- `target = 1`: CLV positivo (edge foi genuíno)
- `target = 0`: CLV negativo ou zero (edge desapareceu)

### 4.2 Fonte de Odds de Fecho

- **Backtest:** Odds de fecho do Pinnacle (via repositórios públicos/Kaggle)
- **Produção:** Odds de fecho da Betfair Exchange (armazenadas após o jogo)

---

## 5. ARQUITETURA DO META-MODELO

### 5.1 Configuração XGBoost

```python
meta_model_config = {
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "auc"],
    "max_depth": 3,                  # Mais shallow que modelo primário
    "learning_rate": 0.03,           # Mais conservador
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
```

### 5.2 Diferenças vs Modelo Primário

| Aspecto | Modelo Primário | Meta-Modelo |
|---------|-----------------|-------------|
| Profundidade | max_depth = 4 | max_depth = 3 |
| Learning rate | 0.05 | 0.03 |
| N_estimators | 1000 | 500 |
| Objetivo | Prever resultado | Prever qualidade do edge |

**Justificação:** Meta-modelo deve ser mais simples para evitar overfitting em dados de edge.

---

## 6. VALIDAÇÃO DO META-MODELO

### 6.1 Purged Walk-Forward CV

Mesma estrutura que modelo primário:
- 3 épocas treino, 1 validação, 1 teste
- Embargo de 2 dias
- Iteração mensal

### 6.2 Métricas de Avaliação

| Métrica | Target | Como Medir |
|---------|--------|------------|
| AUC | > 0.55 | Capacidade de discriminar CLV positivo vs negativo |
| Precision @ P_meta > 0.6 | > 0.60 | % de sinais filtrados que têm CLV positivo |
| Recall @ P_meta > 0.6 | > 0.40 | % de CLV positivos capturados |
| F1 Score | > 0.50 | Balance entre precision e recall |

### 6.3 Análise de Regimes

Separar métricas por:
- Favorito vs Underdog
- Casa vs Fora
- Back-to-Back vs Normal

**Justificação:** Meta-modelo pode ter performance diferente por regime.

---

## 7. REGRAS DE APOSTA COM META-LABELING

### 7.1 Regra Principal

```python
edge = p_modelo * odd_betfair - 1
p_meta = meta_model.predict(features_meta)

if edge > 0.04 and p_meta > 0.60:
    gerar_sinal()
else:
    rejeitar_sinal()
```

### 7.2 Thresholds Dinâmicos (Opcional)

```python
# Ajustar threshold de P_meta por regime
if is_favorite:
    p_meta_threshold = 0.55  # Mais liberal para favoritos
elif is_underdog:
    p_meta_threshold = 0.65  # Mais conservador para underdogs
else:
    p_meta_threshold = 0.60  # Padrão para equilibrados
```

---

## 8. TREINAMENTO DO META-MODELO

### 8.1 Pipeline de Treino

```python
def train_meta_model(X_train, y_train, X_val, y_val):
    # 1. Treinar modelo primário
    primary_model = train_primary_model(X_train_features, y_train)
    
    # 2. Gerar predictions do modelo primário
    p_modelo_train = primary_model.predict_proba(X_train_features)[:, 1]
    p_modelo_val = primary_model.predict_proba(X_val_features)[:, 1]
    
    # 3. Calcular edge e features meta
    X_meta_train = build_meta_features(X_train, p_modelo_train, odds_train)
    X_meta_val = build_meta_features(X_val, p_modelo_val, odds_val)
    
    # 4. Treinar meta-modelo
    meta_model = xgb.XGBClassifier(**meta_model_config)
    meta_model.fit(
        X_meta_train, y_train,
        eval_set=[(X_meta_val, y_val)],
        early_stopping_rounds=30,
        verbose=False
    )
    
    return meta_model
```

### 8.2 Frequência de Retreino

- **Inicial:** Treinar a cada mês durante backtest
- **Produção:** Retreinar semanalmente (segunda-feira)
- **Trigger:** Se drift no meta-modelo (AUC cai < 0.52)

---

## 9. MONITORIZAÇÃO DO META-MODELO

### 9.1 Métricas em Produção

| Métrica | Frequência | Alerta se |
|---------|------------|-----------|
| AUC (rolling 7 dias) | Diário | < 0.52 |
| Precision @ P_meta > 0.6 | Diário | < 0.55 |
| % sinais filtrados | Diário | < 20% ou > 80% |
| CLV dos sinais aprovados | Diário | < 0% |

### 9.2 Diagnóstico de Problemas

**Se AUC cai drasticamente:**
1. Verificar se features do meta-modelo têm drift
2. Verificar se odds de fecho estão corretas
3. Verificar se há mudanças de regime (nova temporada, regras)

**Se % sinais filtrados muito baixo (< 20%):**
1. Meta-modelo pode estar muito conservador
2. Ajustar threshold de P_meta para 0.55
3. Verificar se features de qualidade estão corretas

**Se % sinais filtrados muito alto (> 80%):**
1. Meta-modelo pode estar muito liberal
2. Ajustar threshold de P_meta para 0.65
3. Verificar se há sobreposição com modelo primário

---

## 10. BACKLOG

- [ ] Implementar pipeline de treino do meta-modelo
- [ ] Adicionar testes de AUC por regime
- [ ] Implementar thresholds dinâmicos por regime
- [ ] Criar dashboard de monitorização do meta-modelo
- [ ] Implementar auto-retreino se drift detectado
- [ ] Adicionar feature importance do meta-modelo

---

## 11. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelo primário
- [[06_Backtesting/INDEX]] → Validação do meta-modelo
- [[48_Data_Drift/INDEX]] → Monitorização de drift
