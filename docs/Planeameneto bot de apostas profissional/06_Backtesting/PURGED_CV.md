# PURGED_CV — Walk-Forward Cross-Validation

**ID:** `BT-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar a implementacao completa do purged walk-forward cross-validation com embargo periods.

---

## 2. PORQUE PURGED CV

Backtest tradicional com train/test shuffle:
- Quebra dependencia temporal
- Permite leakage de eventos proximos
- Optimista demais

Purged walk-forward:
- Mantem ordem temporal
- Embargo evita correlacao entre treino e validacao
- Estima performance realista

---

## 3. PARAMETROS

| Parametro | Valor | Justificacao |
|-----------|-------|--------------|
| Janela de treino | 36 meses | 3 epocas NBA completas |
| Janela de validacao | 1 mes | Significancia estatistica minima |
| Embargo | 2 dias | Evita correlacao de jogos proximos |
| Folds | 12 | Um por mes de validacao |

---

## 4. IMPLEMENTACAO DETALHADA

```python
import pandas as pd
import numpy as np

def create_purged_folds(df, train_months=36, val_months=1, embargo_days=2):
    """
    Cria folds de walk-forward com embargo.
    
    Returns: lista de (train_idx, val_idx) para cada fold
    """
    df = df.sort_values('game_date').copy()
    df['year_month'] = df['game_date'].dt.to_period('M')
    
    unique_months = df['year_month'].unique()
    folds = []
    
    for i in range(train_months, len(unique_months) - val_months + 1):
        train_end_month = unique_months[i - 1]
        val_month = unique_months[i]
        
        # Treino: ate ao fim do mes anterior ao embargo
        embargo_cutoff = val_month.start_time - pd.Timedelta(days=embargo_days)
        train_mask = df['game_date'] < embargo_cutoff
        
        # Validacao: mes actual
        val_mask = df['year_month'] == val_month
        
        train_idx = df[train_mask].index.tolist()
        val_idx = df[val_mask].index.tolist()
        
        # Validar que nao ha overlap
        assert len(set(train_idx) & set(val_idx)) == 0, "Overlap detectado!"
        
        folds.append((train_idx, val_idx))
    
    return folds
```

---

## 5. METRICAS POR FOLD

```python
def evaluate_fold(model, X_val, y_val, odds_val):
    probs = model.predict_proba(X_val)[:, 1]
    
    # Simular apostas com edge > 4%
    edges = probs * odds_val - 1
    bets = edges > 0.04
    
    returns = np.where(
        y_val[bets] == 1,
        (odds_val[bets] - 1) * 0.95,  # Comissao 5%
        -1.0
    )
    
    return {
        'n_bets': bets.sum(),
        'clv': edges[bets].mean(),
        'roi': returns.mean(),
        'sharpe': returns.mean() / returns.std() if returns.std() > 0 else 0,
        'win_rate': (y_val[bets] == 1).mean()
    }
```

---

## 6. BACKLOG

- [ ] Implementar e testar com dados historicos
- [ ] Validar que embargo de 2 dias e suficiente (analisar autocorrelacao)
- [ ] Criar visualizacao dos folds (timeline)

---

## 7. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secao mae
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Implementacao no sklearn
