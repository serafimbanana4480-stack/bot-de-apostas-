# SEPARACAO_TREINO_TESTE — Split Temporal

**ID:** `ML-006` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir estratégia de split temporal para treino/validação/teste que preserve a estrutura temporal e evite data leakage.

---

## 2. PRINCÍPIOS

1. **Split temporal obrigatório** - nunca random split
2. **Test set lockado** - nunca usado em treino
3. **Embargo entre folds** - evitar leakage temporal
4. **Proporções:** 70% treino, 15% validação, 15% teste

---

## 3. SPLIT TEMPORAL SIMPLES

```python
def temporal_split(data, date_col, train_pct=0.7, val_pct=0.15):
    """
    Split temporal simples.
    
    Args:
        data: DataFrame com coluna de data
        date_col: Nome da coluna de data
        train_pct: % para treino
        val_pct: % para validação
    
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test
    """
    # Ordenar por data
    data_sorted = data.sort_values(date_col)
    
    # Calcular índices
    n = len(data_sorted)
    train_end = int(n * train_pct)
    val_end = int(n * (train_pct + val_pct))
    
    # Split
    train = data_sorted.iloc[:train_end]
    val = data_sorted.iloc[train_end:val_end]
    test = data_sorted.iloc[val_end:]
    
    return train, val, test
```

---

## 4. PURGED WALK-FORWARD CV

```python
def purged_walk_forward(data, date_col, n_folds=12, embargo_days=2):
    """
    Gera folds para walk-forward CV com embargo.
    
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
        embargo_start = train_end_date
        embargo_end = val_start_date - timedelta(days=embargo_days)
        
        val_mask = (data_sorted[date_col] >= embargo_end) & (data_sorted[date_col] < val_end_date)
        
        folds.append((train_mask, val_mask))
    
    return folds
```

---

## 5. TEST SET LOCK

```python
# Lock test set - nunca usar em treino
TEST_SET_LOCKED = True
TEST_SET_START_DATE = "2023-10-01"

def is_in_test_set(date):
    """Verifica se data está no test set."""
    return date >= TEST_SET_START_DATE
```

---

## 6. CRITÉRIOS

- **Test set nunca usado** em qualquer fase de desenvolvimento
- **Embargo mínimo 2 dias** entre folds
- **Split sempre temporal** - nunca random
- **Reproduzível** com seeds fixos

---

## 7. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[LEAKAGE_PREVENTION]]
