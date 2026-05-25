# MOTOR_EDGE — Calculo e Filtros

**ID:** `VD-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Calcular o edge matematico de cada aposta e aplicar filtros de qualidade antes de emitir sinal.

---

## 2. FORMULA DE EDGE

```python
def calculate_edge(prob_calibrated, odd_market):
    """
    Edge = Prob * Odd - 1
    
    Exemplo: prob=0.55, odd=2.00
    Edge = 0.55 * 2.00 - 1 = 0.10 (10%)
    """
    return prob_calibrated * odd_market - 1.0
```

---

## 3. FLUXO COMPLETO

```python
class ValueEngine:
    def __init__(self, primary_model, meta_model, calibrators, config):
        self.primary_model = primary_model
        self.meta_model = meta_model
        self.calibrators = calibrators
        self.config = config
    
    def process_game(self, features, odd_market, market, volume):
        # 1. Probabilidade primaria
        prob_raw = self.primary_model.predict_proba(features)[0, 1]
        
        # 2. Calibracao por regime
        regime = self.get_regime(prob_raw)
        prob_cal = self.calibrators[regime].predict(prob_raw)
        
        # 3. Edge
        edge = calculate_edge(prob_cal, odd_market)
        
        # 4. Filtros basicos
        if edge <= self.config['edge_min']:
            return None  # Sem edge suficiente
        if prob_cal < self.config['prob_min'] or prob_cal > self.config['prob_max']:
            return None  # Extremo demais
        if volume < self.config['min_volume']:
            return None  # Sem liquidez
        
        # 5. Meta-labeling
        meta_features = self.build_meta_features(prob_cal, edge, features)
        prob_meta = self.meta_model.predict_proba(meta_features)[0, 1]
        
        if prob_meta < self.config['prob_meta_min']:
            return None  # Meta-modelo rejeita
        
        # 6. Sinal aprovado
        return Signal(
            prob=prob_cal,
            edge=edge,
            prob_meta=prob_meta,
            odd=odd_market,
            market=market
        )
```

---

## 4. THRESHOLDS

| Parametro | Valor Inicial | Range Otimizacao |
|-----------|---------------|------------------|
| edge_min | 0.04 | [0.02, 0.08] |
| prob_min | 0.15 | [0.10, 0.30] |
| prob_max | 0.85 | [0.70, 0.90] |
| prob_meta_min | 0.60 | [0.50, 0.70] |
| min_volume | 500 EUR | [100, 2000] |

---

## 5. FILTROS DETALHADOS

### 5.1 Filtro de Probabilidade

```python
def filter_probability(prob_cal: float, config: dict) -> bool:
    """
    Rejeita probabilidades extremas.
    
    Razão: Modelos tendem a ser menos calibrados nas caudas.
    Uma probabilidade de 0.90 pode na realidade ser 0.82 (overconfident).
    """
    return config['prob_min'] <= prob_cal <= config['prob_max']
```

**Explicação:** Probabilidades muito baixas (< 15%) ou muito altas (> 85%) são onde modelos de ML tendem a ser menos calibrados. O ECE (Expected Calibration Error) é tipicamente maior nas caudas. Limitar a [15%, 85%] foca no "sweet spot" do modelo.

### 5.2 Filtro de Liquidez

```python
def filter_liquidity(volume: float, stake: float, min_multiplier: float = 1.5) -> bool:
    """
    Liquidez deve ser suficiente para absorver a aposta.
    
    Razão: Apostar em mercados com pouca liquidez causa slippage
    e pode afetar a odd para outros apostadores.
    """
    return volume >= stake * min_multiplier
```

**Explicação:** Se apostamos 50€ num mercado com apenas 100€ de liquidez, movemos o mercado. O nosso próprio dinheiro altera a odd, reduzindo o edge. Target: liquidez >= 1.5x a stake.

### 5.3 Filtro de Edge Mínimo

```python
def filter_edge(edge: float, edge_min: float = 0.04) -> bool:
    """
    Edge deve ser suficiente para cobrir custos de transação e variância.
    
    Razão: Um edge de 1% não cobre:
    - Variância estatística (ruído de curto prazo)
    - Custo de oportunidade (tempo gasto)
    - Risco de modelo degradado
    """
    return edge >= edge_min
```

**Explicação:** Edge de 4% é o mínimo para ser lucrativo a longo prazo. Com 1000 apostas, edge 4% tem expectativa de 40 unidades de lucro. Edge 2% tem expectativa de apenas 20 unidades — demasiado sensível à variação.

### 5.4 Filtro de Meta-Labeling

```python
def build_meta_features(prob_cal: float, edge: float, features: pd.Series) -> pd.DataFrame:
    """
    Features para o meta-modelo decidir se o sinal é "tradeable".
    
    O meta-modelo aprende a identificar quais apostas com edge positivo
    realmente ganham vs. quais perdem, baseado em características
    que o modelo primário não usa diretamente.
    """
    return pd.DataFrame({
        'prob_cal': [prob_cal],
        'edge': [edge],
        'prob_confidence': [abs(prob_cal - 0.5)],  # Quanto mais distante de 0.5, mais confiante
        'regime': [get_regime(prob_cal)],
        'day_of_week': [features['game_date'].dayofweek],
        'is_back_to_back': [features['is_back_to_back']],
        'rest_diff': [features['rest_days_home'] - features['rest_days_away']],
        'market_volatility': [features['market_volatility_7d']],
    })
```

**Explicação:** O meta-modelo é treinado para prever não "quem ganha" mas "esta aposta vai ganhar DADO que o modelo primário tem edge positivo". É um filtro de segunda ordem que reduz falsos positivos.

---

## 6. EXPIRAÇÃO DE SINAIS

### 6.1 Regras de Expiry

| Condição | Tempo de Expiração | Razão |
|----------|-------------------|-------|
| Odd movimentou > 2% | Imediata | Edge desapareceu |
| Jogo começa em < 1h | 5 minutos | Mercado fecha em breve |
| Jogo começa em > 1h | 15 minutos | Odds ainda podem movimentar |
| Feed offline > 5 min | Imediata | Não sabemos odd atual |

### 6.2 Implementação

```python
class SignalExpiryManager:
    """Gerencia expiração de sinais baseado em condições de mercado."""
    
    def __init__(self):
        self.active_signals = {}  # signal_id -> Signal
        self.redis = redis_client
    
    def create_signal(self, signal: Signal) -> str:
        """Cria sinal com TTL baseado no tempo até ao jogo."""
        signal_id = f"SIG-{uuid4().hex[:8]}"
        
        # Calcular TTL
        hours_until_game = (signal.game_date - datetime.now()).total_seconds() / 3600
        if hours_until_game < 1:
            ttl = 300  # 5 minutos
        else:
            ttl = 900  # 15 minutos
        
        # Armazenar no Redis com TTL
        self.redis.setex(f"signal:{signal_id}", ttl, signal.to_json())
        
        logger.info(f"Sinal {signal_id} criado, expira em {ttl}s")
        return signal_id
    
    def check_signal_valid(self, signal_id: str, current_odd: float) -> bool:
        """Verifica se sinal ainda é válido dadas condições atuais."""
        signal_json = self.redis.get(f"signal:{signal_id}")
        if not signal_json:
            return False  # Expirou
        
        signal = Signal.from_json(signal_json)
        
        # Verificar se odd movimentou demais
        slippage = abs(current_odd - signal.odd) / signal.odd
        if slippage > 0.02:
            logger.warning(f"Sinal {signal_id} expirado: slippage {slippage:.2%}")
            return False
        
        return True
```

---

## 7. OTIMIZAÇÃO DE THRESHOLDS

### 7.1 Walk-Forward Optimization

```python
class ThresholdOptimizer:
    """Otimiza thresholds usando walk-forward cross-validation."""
    
    def optimize(self, predictions: pd.DataFrame, actuals: pd.Series, 
                 cv: PurgedWalkForwardCV) -> dict:
        """
        Otimiza edge_min para maximizar Sharpe Ratio.
        
        Args:
            predictions: DataFrame com 'prob_cal', 'odd_market', 'edge'
            actuals: Series com resultados (1=win, 0=loss)
            cv: Walk-forward CV splitter
        
        Returns:
            Dict com thresholds otimizados por regime
        """
        best_sharpe = -np.inf
        best_threshold = 0.04
        
        for edge_min in np.arange(0.02, 0.10, 0.005):
            sharpe_scores = []
            
            for train_idx, val_idx in cv.split(predictions):
                # Filtrar apostas com edge >= edge_min
                mask = predictions.iloc[val_idx]['edge'] >= edge_min
                
                if mask.sum() < 20:  # Poucas apostas para confiança
                    continue
                
                # Calcular ROI e Sharpe neste fold
                returns = predictions.iloc[val_idx][mask]['pnl'] / predictions.iloc[val_idx][mask]['stake']
                sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0
                sharpe_scores.append(sharpe)
            
            avg_sharpe = np.mean(sharpe_scores)
            if avg_sharpe > best_sharpe:
                best_sharpe = avg_sharpe
                best_threshold = edge_min
        
        return {
            'edge_min': best_threshold,
            'sharpe': best_sharpe,
            'n_folds': len(sharpe_scores)
        }
```

---

## 8. BACKLOG

- [x] Documentar fórmula de edge
- [x] Documentar fluxo completo com ValueEngine
- [x] Documentar thresholds iniciais e ranges de otimização
- [x] Documentar filtros detalhados (prob, liquidez, edge, meta-labeling)
- [x] Implementar sistema de expiry de sinais
- [x] Documentar otimização de thresholds com walk-forward
- [ ] Implementar motor edge em tempo real
- [ ] Testar thresholds otimizados em paper trading

---

## 9. LINKS CRUZADOS

- [[07_Value_Detection/INDEX]] ← Secção mãe
- [[05_Machine_Learning/CALIBRACAO_ISOTONICA]] → Calibração de probabilidades
- [[08_Risk_Management/KELLY_FRACIONADO]] → Kelly e sizing
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
