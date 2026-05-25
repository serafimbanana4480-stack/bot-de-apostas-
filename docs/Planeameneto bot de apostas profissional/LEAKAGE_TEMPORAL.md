# LEAKAGE_TEMPORAL — Leakage Temporal

**ID:** `QR-020` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Prevenir leakage temporal (data leakage) no backtesting.

---

## 2. TIPOS DE LEAKAGE

| Tipo | Descrição | Prevenção |
|------|-----------|-----------|
| Look-ahead | Usar dados futuros | Purged CV |
| Target leakage | Feature correlacionada com target | Análise de correlação |
| Data leakage | Usar data do jogo na feature | Remover data |

---

## 3. PREVENÇÃO COM PURGED CV

```python
def purged_cross_validation(data, purge_days=1):
    """
    Cross-validation com purged data.
    
    Args:
        data: Dataset completo
        purge_days: Dias a purgar entre treino e teste
    
    Returns:
        Scores de CV
    """
    scores = []
    
    for train_idx, test_idx in time_series_split(data):
        # Identificar data limite
        train_dates = data.iloc[train_idx]['date']
        cutoff_date = train_dates.max()
        
        # Purgar dados após cutoff
        purge_date = cutoff_date + timedelta(days=purge_days)
        
        # Filtrar teste para após purga
        test_idx_purged = [
            i for i in test_idx 
            if data.iloc[i]['date'] > purge_date
        ]
        
        # Treinar e avaliar
        model = train_model(data.iloc[train_idx])
        score = evaluate_model(model, data.iloc[test_idx_purged])
        scores.append(score)
    
    return scores
```

---

## 4. DETEÇÃO DE LEAKAGE

```python
def detect_target_leakage(features, target):
    """
    Deteta features com alta correlação com target.
    
    Args:
        features: DataFrame de features
        target: Série de target
    
    Returns:
        Features suspeitas de leakage
    """
    suspicious = []
    
    for col in features.columns:
        corr = features[col].corr(target)
        
        if abs(corr) > 0.95:
            suspicious.append({
                'feature': col,
                'correlation': corr
            })
    
    return suspicious
```

---

## 5. CRITÉRIOS

- **Purged CV** obrigatório para backtesting
- **Remover features** com correlação > 0.95 com target
- **Revisar manualmente** features suspeitas

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[BACKTESTING_VALIDATION]]
