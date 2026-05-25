# METRICAS_NEGOCIO — Métricas de Negócio

**ID:** `BM-001` | **Fase:** #phase/3 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir métricas chave de negócio para monitorizar saúde financeira do sistema.

---

## 2. MÉTRICAS PRINCIPAIS

| Métrica | Fórmula | Target |
|---------|---------|--------|
| ROI | PnL / Stake Total | > 5% |
| CLV Médio | Média de (prob * odd - 1) | > 2% |
| Sharpe Ratio | ROI médio / std(ROI) | > 0.5 |
| Win Rate | Vitórias / Total Apostas | > 52% |
| Max Drawdown | Maior queda de bankroll | < 20% |

---

## 3. CÁLCULO DE ROI

```python
def calculate_roi(pnl, total_staked):
    """Calcula ROI."""
    return pnl / total_staked if total_staked > 0 else 0

# Exemplo
pnl = 500
staked = 10000
roi = calculate_roi(pnl, staked)  # 0.05 = 5%
```

---

## 4. CLV MÉDIO

```python
def calculate_clv(probs, odds, outcomes):
    """Calcula CLV médio."""
    edges = (probs * odds) - 1
    clv = np.where(outcomes == 1, edges, -1)
    return np.mean(clv)
```

---

## 5. SHARPE RATIO

```python
def calculate_sharpe(roi_series, risk_free_rate=0.02):
    """
    Calcula Sharpe Ratio anualizado.
    
    Args:
        roi_series: Série de retornos por aposta
        risk_free_rate: Taxa livre de risco (anual)
    """
    excess_returns = roi_series - risk_free_rate / len(roi_series)
    sharpe = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    return sharpe * np.sqrt(252)  # Anualizar (252 dias de apostas)
```

---

## 6. WIN RATE

```python
def calculate_win_rate(outcomes):
    """Calcula taxa de vitória."""
    return np.mean(outcomes)
```

---

## 7. MAX DRAWDOWN

```python
def calculate_max_drawdown(pnl_series):
    """Calcula drawdown máximo."""
    cumulative = pnl_series.cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    
    return drawdown.min()
```

---

## 8. DASHBOARD

Métricas devem ser visualizadas em dashboard atualizado diariamente.

---

## 9. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[09_Monitoring/INDEX]]
