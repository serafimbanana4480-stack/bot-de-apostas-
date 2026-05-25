# THRESHOLD_OPTIMIZATION — Otimização de Thresholds

**ID:** `QR-014` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Otimizar thresholds (edge mínimo, stake máximo) para maximizar ROI enquanto controla risco.

---

## 2. THRESHOLDS PRINCIPAIS

| Threshold | Default | Range |
|-----------|---------|-------|
| Edge mínimo | 4% | 2-6% |
| Stake máximo | 5% | 3-7% |
| Kelly fraction | 0.5 | 0.25-0.75 |

---

## 3. OTIMIZAÇÃO DE EDGE MÍNIMO

```python
def optimize_edge_threshold(backtest_data, thresholds):
    """
    Otimiza edge mínimo baseado em backtest.
    
    Args:
        backtest_data: Dados de backtest
        thresholds: Lista de thresholds a testar
    
    Returns:
        Threshold ótimo
    """
    results = []
    
    for threshold in thresholds:
        # Filtrar apostas acima do threshold
        filtered = backtest_data[backtest_data['edge'] >= threshold]
        
        if len(filtered) > 50:
            roi = calculate_roi(filtered)
            n_bets = len(filtered)
            
            results.append({
                'threshold': threshold,
                'roi': roi,
                'n_bets': n_bets
            })
    
    # Selecionar threshold com melhor ROI
    best = max(results, key=lambda x: x['roi'])
    
    return best['threshold']
```

---

## 4. OTIMIZAÇÃO DE FRAÇÃO KELLY

```python
def optimize_kelly_fraction(backtest_data, fractions):
    """
    Otimiza fração de Kelly baseada em Sharpe ratio.
    
    Args:
        backtest_data: Dados de backtest
        fractions: Lista de frações a testar
    
    Returns:
        Fração ótima
    """
    results = []
    
    for fraction in fractions:
        # Simular com fração de Kelly
        simulated = simulate_with_kelly_fraction(backtest_data, fraction)
        
        sharpe = calculate_sharpe(simulated['roi_series'])
        max_drawdown = calculate_max_drawdown(simulated['pnl_series'])
        
        results.append({
            'fraction': fraction,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown
        })
    
    # Selecionar fração com melhor Sharpe, respeitando drawdown < 20%
    valid = [r for r in results if r['max_drawdown'] < 0.20]
    best = max(valid, key=lambda x: x['sharpe'])
    
    return best['fraction']
```

---

## 5. OTIMIZAÇÃO PERIÓDICA

```python
def periodic_threshold_optimization():
    """Executa otimização de thresholds semanalmente."""
    # Obter dados dos últimos 3 meses
    backtest_data = get_backtest_data(months=3)
    
    # Otimizar edge threshold
    edge_thresholds = [0.02, 0.03, 0.04, 0.05, 0.06]
    optimal_edge = optimize_edge_threshold(backtest_data, edge_thresholds)
    
    # Otimizar Kelly fraction
    kelly_fractions = [0.25, 0.5, 0.75]
    optimal_kelly = optimize_kelly_fraction(backtest_data, kelly_fractions)
    
    # Atualizar configuração
    update_config({
        'edge_threshold': optimal_edge,
        'kelly_fraction': optimal_kelly
    })
    
    logger.info(f"Thresholds otimizados: edge={optimal_edge:.2%}, kelly={optimal_kelly:.2f}")
```

---

## 6. CRITÉRIOS

- **Otimizar semanalmente**
- **Mínimo 50 apostas** por threshold
- **Drawdown < 20%** obrigatório

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[STAKE_CALCULATOR]]
