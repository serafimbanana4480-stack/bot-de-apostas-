# Volatility Regimes

**ID:** RM-006 | **Fase:** Fase 2+ | **Owner:** Principal Quant Engineer

---

## 1. OBJETIVO

Identificar e adaptar a diferentes regimes de volatilidade nos mercados de apostas para otimizar estratégias de sizing e filtros de qualidade.

---

## 2. CONCEITO

Regimes de volatilidade são períodos onde a variância dos resultados e dos movimentos de odds difere significativamente da média histórica. Adaptar a estes regimes é crítico para:

- Ajustar tamanhos de aposta (Kelly adaptativo)
- Modificar filtros de qualidade (thresholds dinâmicos)
- Calibrar expectativas de risco
- Otimizar timing de entrada

---

## 3. DETECÇÃO DE REGIMES

### 3.1 Métricas de Volatilidade

| Métrica | Fórmula | Janela |
|---------|---------|--------|
| Volatilidade de Odds | std(odds_changes) / mean(odds) | 7 dias |
| Volatilidade de Resultados | std(returns) | 30 apostas |
| Volatilidade de Spread | std(spread_changes) | 7 dias |
| Volume Anômalo | volume / mean(volume) | 24h |

### 3.2 Classificação de Regimes

```python
def classify_volatility_regime(volatility_metrics):
    """
    Classifica o regime de volatilidade atual
    """
    odds_vol = volatility_metrics['odds_volatility']
    results_vol = volatility_metrics['results_volatility']
    
    if odds_vol < 0.02 and results_vol < 0.15:
        return 'LOW_VOLATILITY'
    elif odds_vol < 0.04 and results_vol < 0.25:
        return 'NORMAL_VOLATILITY'
    elif odds_vol < 0.07 and results_vol < 0.40:
        return 'HIGH_VOLATILITY'
    else:
        return 'EXTREME_VOLATILITY'
```

### 3.3 Detecção de Mudança de Regime

```python
def detect_regime_change(current_regime, historical_regimes):
    """
    Detecta mudança significativa de regime usando Changepoint Detection
    """
    # Método 1: CUSUM (Cumulative Sum)
    cusum_score = calculate_cusum(historical_regimes)
    
    # Método 2: Bayesian Changepoint Detection
    bcp_prob = calculate_bcp_probability(historical_regimes)
    
    # Método 3: Rolling Z-score
    z_score = calculate_rolling_zscore(historical_regimes)
    
    if cusum_score > threshold or bcp_prob > 0.8 or abs(z_score) > 3:
        return True, current_regime
    else:
        return False, current_regime
```

---

## 4. ESTRATÉGIAS POR REGIME

### 4.1 Regime Baixa Volatilidade

**Características:**
- Movimentos de odds pequenos e previsíveis
- Volume estável
- Spread entre casas consistente

**Ajustes:**
- **Kelly Fraction:** 1.0x (normal)
- **Threshold de Edge:** 2.0% (padrão)
- **Liquidez Mínima:** €2,000
- **Confiança Mínima:** 0.60

**Estratégia:**
- Apostar agressivamente em edge validado
- Focar em mercados com liquidez alta
- Minimizar filtros de qualidade

### 4.2 Regime Normal Volatilidade

**Características:**
- Movimentos de odds dentro da média histórica
- Volume normal
- Spread consistente

**Ajustes:**
- **Kelly Fraction:** 1.0x (normal)
- **Threshold de Edge:** 2.5% (padrão)
- **Liquidez Mínima:** €5,000
- **Confiança Mínima:** 0.65

**Estratégia:**
- Operação padrão
- Filtros de qualidade normais
- Sizing baseado em Kelly

### 4.3 Regime Alta Volatilidade

**Características:**
- Movimentos de odds grandes e rápidos
- Volume aumentado ou diminuído
- Spread entre casas variável

**Ajustes:**
- **Kelly Fraction:** 0.75x (reduzido)
- **Threshold de Edge:** 3.5% (mais conservador)
- **Liquidez Mínima:** €10,000
- **Confiança Mínima:** 0.75

**Estratégia:**
- Reduzir tamanho de apostas
- Aumentar filtros de qualidade
- Focar em apostas de alta confiança
- Evitar mercados com baixa liquidez

### 4.4 Regime Volatilidade Extrema

**Características:**
- Movimentos de odds muito grandes
- Volume anômalo
- Spread entre casas muito variável
- Possível regime change

**Ajustes:**
- **Kelly Fraction:** 0.5x (muito reduzido)
- **Threshold de Edge:** 5.0% (muito conservador)
- **Liquidez Mínima:** €20,000
- **Confiança Mínima:** 0.85

**Estratégia:**
- Parar apostas automáticas
- Modo manual apenas
- Investigar causa da volatilidade
- Considerar pausa operacional

---

## 5. IMPLEMENTAÇÃO

### 5.1 Sistema de Detecção em Tempo Real

```python
class VolatilityRegimeDetector:
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.historical_metrics = []
        self.current_regime = 'NORMAL_VOLATILITY'
    
    def update(self, new_metrics):
        """Atualiza métricas e detecta regime"""
        self.historical_metrics.append(new_metrics)
        
        # Manter janela fixa
        if len(self.historical_metrics) > self.window_size:
            self.historical_metrics.pop(0)
        
        # Calcular volatilidade atual
        volatility_metrics = self.calculate_volatility()
        
        # Classificar regime
        new_regime = classify_volatility_regime(volatility_metrics)
        
        # Detectar mudança
        changed, regime = detect_regime_change(
            new_regime, 
            self.historical_metrics
        )
        
        if changed:
            self.current_regime = regime
            self.alert_regime_change(regime)
        
        return self.current_regime
    
    def alert_regime_change(self, new_regime):
        """Alerta mudança de regime"""
        send_alert(
            severity='HIGH',
            message=f"Volatility regime changed to {new_regime}",
            channel='telegram'
        )
```

### 5.2 Integração com Motor de Edge

```python
class AdaptiveEdgeEngine:
    def __init__(self, regime_detector):
        self.regime_detector = regime_detector
        self.regime_configs = {
            'LOW_VOLATILITY': {
                'kelly_multiplier': 1.0,
                'edge_threshold': 0.02,
                'min_liquidity': 2000,
                'min_confidence': 0.60
            },
            'NORMAL_VOLATILITY': {
                'kelly_multiplier': 1.0,
                'edge_threshold': 0.025,
                'min_liquidity': 5000,
                'min_confidence': 0.65
            },
            'HIGH_VOLATILITY': {
                'kelly_multiplier': 0.75,
                'edge_threshold': 0.035,
                'min_liquidity': 10000,
                'min_confidence': 0.75
            },
            'EXTREME_VOLATILITY': {
                'kelly_multiplier': 0.5,
                'edge_threshold': 0.05,
                'min_liquidity': 20000,
                'min_confidence': 0.85
            }
        }
    
    def calculate_adaptive_stake(self, base_kelly, prediction):
        """Calcula stake adaptativo baseado no regime"""
        current_regime = self.regime_detector.current_regime
        config = self.regime_configs[current_regime]
        
        # Ajustar Kelly
        adjusted_kelly = base_kelly * config['kelly_multiplier']
        
        # Ajustar por confiança
        confidence_factor = prediction['confidence'] / config['min_confidence']
        adjusted_kelly *= min(confidence_factor, 1.0)
        
        return adjusted_kelly
    
    def validate_prediction(self, prediction):
        """Valida predição baseado no regime"""
        current_regime = self.regime_detector.current_regime
        config = self.regime_configs[current_regime]
        
        checks = {
            'edge': prediction['edge'] >= config['edge_threshold'],
            'liquidity': prediction['liquidity'] >= config['min_liquidity'],
            'confidence': prediction['confidence'] >= config['min_confidence']
        }
        
        return all(checks.values()), checks
```

---

## 6. BACKTESTING POR REGIME

### 6.1 Estratégia

- Separar dados históricos por regime
- Backtestar estratégias específicas para cada regime
- Validar que ajustes de regime melhoram performance

### 6.2 Métricas

| Regime | Sharpe Ratio | Max Drawdown | Win Rate |
|--------|--------------|--------------|----------|
| Low Volatility | > 1.5 | < 10% | > 55% |
| Normal Volatility | > 1.2 | < 15% | > 53% |
| High Volatility | > 0.8 | < 20% | > 50% |
| Extreme Volatility | > 0.5 | < 25% | > 48% |

---

## 7. MONITORAMENTO

### 7.1 Dashboard de Regimes

**Métricas:**
- Regime atual
- Histórico de regimes (últimos 30 dias)
- Volatilidade de odds em tempo real
- Volatilidade de resultados (rolling)
- Número de dias em cada regime (último mês)

### 7.2 Alertas

| Condição | Severidade | Ação |
|----------|------------|------|
| Mudança para High Volatility | HIGH | Ajustar configurações |
| Mudança para Extreme Volatility | CRITICAL | Considerar pausa |
| > 5 dias em Extreme Volatility | CRITICAL | Investigar causa |

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar detector de regimes de volatilidade
- [ ] Criar sistema de backtesting por regime
- [ ] Integrar com motor de edge
- [ ] Configurar alertas de mudança de regime
- [ ] Criar dashboard de regimes
- [ ] Documentar performance histórica por regime

---

## 9. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Índice principal
- [[08_Risk_Management/KELLY_FRACIONADO]] → Cálculo de Kelly
- [[48_Data_Drift/INDEX]] → Detecção de data drift
- [[05_Machine_Learning/MONITORIZACAO_DRIFT]] → Monitorização de drift
