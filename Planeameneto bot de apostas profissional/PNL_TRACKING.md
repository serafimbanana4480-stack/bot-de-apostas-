# PNL_TRACKING — Tracking de Lucro e Prejuízo

**ID:** `OP-003` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Rastrear PnL (Profit and Loss) em tempo real para monitorizar performance do sistema.

---

## 2. CÁLCULO DE PNL

```python
def calculate_pnl(bets):
    """
    Calcula PnL total, por dia, por aposta.
    
    Args:
        bets: DataFrame com colunas [stake, odds, outcome]
    
    Returns:
        PnL total
    """
    # PnL por aposta
    bets['pnl'] = np.where(
        bets['outcome'] == 1,
        bets['stake'] * (bets['odds'] - 1),
        -bets['stake']
    )
    
    total_pnl = bets['pnl'].sum()
    return total_pnl
```

---

## 3. PNL POR DIA

```python
def daily_pnl(bets):
    """Calcula PnL diário."""
    daily = bets.groupby('date')['pnl'].sum()
    return daily
```

---

## 4. PNL ACUMULADO

```python
def cumulative_pnl(bets):
    """Calcula PnL acumulado."""
    bets_sorted = bets.sort_values('date')
    bets_sorted['cumulative_pnl'] = bets_sorted['pnl'].cumsum()
    return bets_sorted
```

---

## 5. MÉTRICAS DERIVADAS

```python
def calculate_pnl_metrics(bets):
    """Calcula métricas derivadas de PnL."""
    total_pnl = calculate_pnl(bets)
    total_staked = bets['stake'].sum()
    
    metrics = {
        'total_pnl': total_pnl,
        'roi': total_pnl / total_staked if total_staked > 0 else 0,
        'n_bets': len(bets),
        'win_rate': np.mean(bets['outcome']),
        'avg_stake': total_staked / len(bets)
    }
    
    return metrics
```

---

## 6. ALERTAS DE PNL

```python
def check_pnl_alerts(current_pnl, initial_bankroll):
    """Verifica alertas de PnL."""
    drawdown_pct = 1 - (initial_bankroll + current_pnl) / initial_bankroll
    
    if drawdown_pct > 0.10:
        send_alert(f"⚠️ Drawdown de {drawdown_pct:.1%} detetado")
    
    if current_pnl < -initial_bankroll * 0.20:
        send_alert("🚨 Drawdown crítico - parar operações")
```

---

## 7. CRITÉRIOS

- **PnL atualizado em tempo real**
- **Alertas se drawdown > 10%**
- **Parar se drawdown > 20%**

---

## 8. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[09_Monitoring/INDEX]]
