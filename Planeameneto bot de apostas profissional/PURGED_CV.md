# PURGED_CV — Cross-Validation com Embargo

**ID:** `ML-009` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar purged walk-forward cross-validation, que remove dados próximos temporalmente entre treino e validação para evitar data leakage.

---

## 2. PROBLEMA DO CV TRADICIONAL

K-fold tradicional não preserva estrutura temporal - dados de treino podem estar muito próximos de validação, causando leakage.

---

## 3. PURGED WALK-FORWARD CV

```python
def purged_walk_forward_cv(data, date_col, n_folds=12, embargo_days=2):
    """
    Gera folds com embargo temporal.
    
    Args:
        data: DataFrame com coluna de data
        date_col: Nome da coluna de data
        n_folds: Número de folds
        embargo_days: Dias de exclusão entre treino e validação
    
    Returns:
        Lista de (train_idx, val_idx)
    """
    data_sorted = data.sort_values(date_col)
    unique_dates = sorted(data_sorted[date_col].unique())
    
    folds = []
    fold_size = len(unique_dates) // n_folds
    
    for i in range(n_folds - 1):
        # Treino: épocas anteriores
        train_end_date = unique_dates[i * fold_size]
        train_mask = data_sorted[date_col] < train_end_date
        
        # Validação: próxima época
        val_start_date = unique_dates[(i + 1) * fold_size]
        val_end_date = unique_dates[(i + 2) * fold_size] if i + 2 < n_folds else unique_dates[-1]
        
        # Embargo: excluir dias entre treino e validação
        embargo_end = val_start_date - timedelta(days=embargo_days)
        
        val_mask = (data_sorted[date_col] >= embargo_end) & (data_sorted[date_col] < val_end_date)
        
        folds.append((train_mask, val_mask))
    
    return folds
```

---

## 4. EMBARGO

Embargo remove dias adjacentes entre treino e validação:

```python
# Exemplo: embargo de 2 dias
# Treino: até 2023-01-15
# Embargo: 2023-01-16 a 2023-01-17 (excluídos)
# Validação: a partir de 2023-01-18
```

---

## 5. CRITÉRIOS

- **Embargo mínimo 2 dias** para NBA
- **12 folds** (um por mês) para validação robusta
- **Test set lockado** - nunca usado em CV

---

## 6. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[LEAKAGE_PREVENTION]]
