# SINAI_GENERATION — Geração de Sinais de Apostas

**ID:** `OP-001` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerar sinais de apostas (quando apostar, quanto apostar) baseados em probabilidades do modelo e odds do mercado.

---

## 2. PIPELINE DE GERAÇÃO

```python
def generate_signals(model, features_df, odds_df, bankroll):
    """
    Gera sinais para todos os jogos disponíveis.
    
    Returns:
        DataFrame com sinais (game_id, prob, odd, edge, stake)
    """
    # 1. Prever probabilidades
    probs = model.predict_proba(features_df)[:, 1]
    
    # 2. Calcular edge
    signals = pd.DataFrame({
        'game_id': features_df['game_id'],
        'prob': probs,
        'odd': odds_df['odd'],
    })
    
    signals['edge'] = (signals['prob'] * signals['odd']) - 1
    
    # 3. Filtrar por edge mínimo
    signals = signals[signals['edge'] > 0.04]
    
    # 4. Calcular stake (Kelly)
    signals['stake_pct'] = signals.apply(
        lambda row: fractional_kelly(row['prob'], row['odd'], 0.5),
        axis=1
    )
    
    # 5. Aplicar limites
    signals['stake_pct'] = signals['stake_pct'].clip(upper=0.05)
    
    # 6. Calcular stake absoluto
    signals['stake'] = signals['stake_pct'] * bankroll
    
    return signals
```

---

## 3. FILTROS DE QUALIDADE

```python
def apply_quality_filters(signals):
    """Aplica filtros de qualidade aos sinais."""
    # Filtro 1: Edge mínimo
    signals = signals[signals['edge'] > 0.04]
    
    # Filtro 2: Odds dentro de range
    signals = signals[(signals['odd'] >= 1.20) & (signals['odd'] <= 10.0)]
    
    # Filtro 3: Probabilidade não extrema
    signals = signals[(signals['prob'] >= 0.10) & (signals['prob'] <= 0.90)]
    
    # Filtro 4: Limite de exposição por dia
    daily_exposure = signals.groupby('date')['stake'].sum()
    valid_dates = daily_exposure[daily_exposure <= bankroll * 0.10].index
    signals = signals[signals['date'].isin(valid_dates)]
    
    return signals
```

---

## 4. META-FILTRO (Meta-Labeling)

```python
def apply_meta_filter(signals, meta_model, meta_features):
    """
    Usa meta-modelo para filtrar falsos positivos.
    """
    meta_probs = meta_model.predict_proba(meta_features)[:, 1]
    
    # Filtro: apenas sinais com meta-prob > 0.60
    signals = signals[meta_probs > 0.60]
    
    return signals
```

---

## 5. ORDENAÇÃO

```python
def order_signals(signals):
    """Ordena sinais por prioridade."""
    signals['priority'] = (
        signals['edge'] * 0.5 + 
        signals['prob'] * 0.3 + 
        (1 / signals['odd']) * 0.2
    )
    
    signals = signals.sort_values('priority', ascending=False)
    return signals
```

---

## 6. CRITÉRIOS

- **Edge mínimo 4%** para gerar sinal
- **Stake máximo 5%** por aposta
- **Exposição máxima 10%** por dia
- **Meta-prob > 60%** se meta-modelo ativo

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[STAKE_CALCULATOR]]
