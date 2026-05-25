# VOLATILITY_REGIMES — Regimes de Volatilidade

**ID:** `QR-013` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Identificar regimes de volatilidade no mercado para ajustar estratégia de apostas.

---

## 2. REGIMES DE VOLATILIDADE

| Regime | Descrição | Características |
|--------|-----------|-----------------|
| Baixa | Mercado estável | Odds mudam pouco |
| Média | Mercado normal | Variação esperada |
| Alta | Mercado volátil | Odds mudam rapidamente |

---

## 3. DETECÇÃO DE REGIME

```python
def detect_volatility_regime(odds_series, window=10):
    """
    Detecta regime de volatilidade baseado em variação de odds.
    
    Args:
        odds_series: Série de odds
        window: Janela para calcular volatilidade
    
    Returns:
        Regime ('low', 'medium', 'high')
    """
    # Calcular variação percentual
    pct_change = odds_series.pct_change().abs()
    
    # Média móvel da volatilidade
    volatility = pct_change.rolling(window).mean()
    
    # Classificar regime
    if volatility < 0.01:
        return 'low'
    elif volatility < 0.03:
        return 'medium'
    else:
        return 'high'
```

---

## 4. AJUSTE DE ESTRATÉGIA

```python
def adjust_strategy_for_regime(regime):
    """
    Ajusta parâmetros baseado no regime.
    
    Returns:
        Config ajustada
    """
    config = default_config.copy()
    
    if regime == 'low':
        # Volatilidade baixa: stakes mais agressivas
        config['kelly_fraction'] = 0.6
        config['edge_threshold'] = 0.03
        
    elif regime == 'medium':
        # Volatilidade média: configuração padrão
        config['kelly_fraction'] = 0.5
        config['edge_threshold'] = 0.04
        
    elif regime == 'high':
        # Volatilidade alta: mais conservador
        config['kelly_fraction'] = 0.3
        config['edge_threshold'] = 0.05
    
    return config
```

---

## 5. MONITORIZAÇÃO

```python
def monitor_regime_changes():
    """Monitoriza mudanças de regime."""
    current_regime = detect_volatility_regime(current_odds)
    previous_regime = get_previous_regime()
    
    if current_regime != previous_regime:
        send_alert(f"⚠️ Mudança de regime: {previous_regime} → {current_regime}")
        
        # Ajustar estratégia
        new_config = adjust_strategy_for_regime(current_regime)
        update_config(new_config)
```

---

## 6. CRITÉRIOS

- **Detectar regime** a cada hora
- **Ajustar stakes** baseado no regime
- **Alertar** se regime muda

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[EDGE_DECAY_REGIME]]
