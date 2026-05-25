# LEAKAGE_PREVENTION — Prevenção de Data Leakage

**ID:** `ML-005` | **Fase:** #phase/1-2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Garantir zero data leakage temporal - nenhuma informação do futuro pode ser usada para prever o passado. Leakage é a causa #1 de modelos falsamente "bons" em backtest.

---

## 2. TIPOS DE LEAKAGE

| Tipo | Exemplo | Como prevenir |
|------|---------|--------------|
| **Temporal** | Usar odds de fecho para prever antes do jogo | Purged CV com embargo |
| **Target** | Feature derivada do outcome | Remover features correlacionadas com target |
| **Data Snooping** | Ajustar thresholds após ver test set | Lock test set |
| **Normalization** | Normalizar com stats globais | Normalizar apenas com treino |

---

## 3. PURGED WALK-FORWARD CV

```python
def purged_walk_forward_cv(data, embargo_days=2):
    """
    Gera folds com embargo temporal.
    
    Args:
        data: DataFrame com coluna 'date'
        embargo_days: Dias de exclusão entre treino e validação
    
    Returns:
        Lista de (train_idx, val_idx)
    """
    unique_dates = sorted(data['date'].unique())
    folds = []
    
    for i in range(len(unique_dates) - 12):  # 12 folds
        # Treino: épocas anteriores
        train_end = unique_dates[i]
        train_mask = data['date'] < train_end
        
        # Validação: próxima época
        val_start = unique_dates[i]
        val_end = unique_dates[i+1]
        
        # Embargo: excluir dias entre treino e validação
        embargo_start = train_end
        embargo_end = val_start - timedelta(days=embargo_days)
        
        val_mask = (data['date'] >= embargo_end) & (data['date'] < val_end)
        
        folds.append((train_mask, val_mask))
    
    return folds
```

---

## 4. AUDIT DE FEATURES

```python
def audit_feature_leakage(features_df, target, date_col):
    """Audita features para leakage temporal."""
    issues = []
    
    for col in features_df.columns:
        # Verificar correlação com target
        corr = features_df[col].corr(target)
        if abs(corr) > 0.9:
            issues.append(f"{col}: correlação muito alta com target ({corr:.2f})")
        
        # Verificar se feature usa dados futuros
        # (ex: média de 5 jogos incluindo jogo atual)
        if 'rolling' in col.lower():
            issues.append(f"{col}: verificar se inclui dado atual")
    
    return issues
```

---

## 5. REGRAS DE OURO

1. **Nunca usar dados do jogo atual** em features pré-jogo
2. **Sempre usar embargo** entre treino e validação
3. **Normalizar apenas com treino** - aplicar transformação a validação/teste
4. **Lock test set** - nunca ajustar após ver performance
5. **Documentar timestamp** de cada feature

---

## 6. VALIDAÇÃO AUTOMATIZADA

```python
def validate_no_leakage(X_train, X_val, X_test):
    """Valida que não há leakage."""
    checks = {
        'train_val_overlap': check_temporal_overlap(X_train, X_val),
        'train_test_overlap': check_temporal_overlap(X_train, X_test),
        'future_data_in_train': check_future_dates(X_train),
    }
    
    if any(checks.values()):
        raise ValueError("Leakage detectado!")
    
    return True
```

---

## 7. CRITICAL CHECKLIST

Antes de treinar:
- [ ] Test set nunca usado em qualquer fase
- [ ] Features calculadas apenas com dados até timestamp do jogo
- [ ] Normalização fit apenas em treino
- [ ] Embargo aplicado entre folds
- [ ] Sem look-ahead em rolling features

---

## 8. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[06_Backtesting/INDEX]] → Validação temporal
