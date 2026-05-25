# FALSE_POSITIVE_FILTER — Meta-Labeling

**ID:** `ML-012` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Usar meta-modelo para filtrar sinais falsos positivos - apostas com edge positivo mas que historicamente não geram CLV.

---

## 2. CONCEITO

Meta-labeling é uma técnica onde treinamos um segundo modelo para prever se o edge real foi positivo após o jogo.

---

## 3. META-TARGET

```python
def create_meta_target(probs, odds, outcomes):
    """
    Cria meta-target: CLV ex-post > 0.
    
    Args:
        probs: Probabilidades previstas
        odds: Odds reais
        outcomes: Resultados reais (0 ou 1)
    
    Returns:
        Meta-target (0 ou 1)
    """
    edge = (probs * odds) - 1
    clv = np.where(outcomes == 1, edge, -1)
    meta_target = (clv > 0).astype(int)
    
    return meta_target
```

---

## 4. META-FEATURES

```python
def create_meta_features(probs, odds, context_features):
    """
    Cria features para meta-modelo.
    """
    meta_features = pd.DataFrame({
        'edge': (probs * odds) - 1,
        'prob': probs,
        'odd': odds,
        'regime': context_features['regime'],  # favorite/balanced/underdog
        'hours_before_game': context_features['hours_before']
    })
    
    return meta_features
```

---

## 5. TREINO DO META-MODELO

```python
def train_meta_model(X_meta, y_meta):
    """Treina meta-modelo XGBoost."""
    meta_model = xgb.XGBClassifier(
        max_depth=3,
        learning_rate=0.1,
        n_estimators=100,
        objective='binary:logistic'
    )
    
    meta_model.fit(X_meta, y_meta)
    return meta_model
```

---

## 6. APLICAÇÃO EM PRODUÇÃO

```python
def apply_meta_filter(signals, meta_model, meta_features):
    """
    Filtra sinais usando meta-modelo.
    
    Args:
        signals: DataFrame com sinais
        meta_model: Meta-modelo treinado
        meta_features: Features meta para os sinais
    
    Returns:
        Sinais filtrados
    """
    meta_probs = meta_model.predict_proba(meta_features)[:, 1]
    
    # Apenas sinais com meta-prob > 0.60
    filtered_signals = signals[meta_probs > 0.60]
    
    return filtered_signals
```

---

## 7. CRITÉRIOS

- **Meta-prob > 60%** para aprovar sinal
- **Meta-modelo validado** com CLV > 2%
- **Filtro opcional** - pode ser desativado se reduz muito volume

---

## 8. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[46_Meta_Labeling/INDEX]]
