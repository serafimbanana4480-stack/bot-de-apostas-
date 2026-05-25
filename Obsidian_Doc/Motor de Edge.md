# 🎯 Motor de Edge

**Componente:** Value Detection  
**Status:** 🚧 Em desenvolvimento (75%)  
**Responsável:** Quant Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Identificar oportunidades de value betting através do cálculo de Closed Line Value (CLV) e comparação de odds entre múltiplas casas, garantindo edge estatístico antes de executar apostas.

---

## 🏗️ Arquitetura

### Componentes do Motor

| Componente | Status | Prioridade |
|------------|--------|------------|
| **CLV Calculator** | ✅ Implementado | Alta |
| **Odds Normalization** | 🚧 Em desenvolvimento | Alta |
| **Multi-Bookmaker Comparison** | 🚧 Em desenvolvimento | Alta |
| **Edge Thresholds** | ✅ Implementado | Alta |
| **Signal Generation** | 🚧 Em desenvolvimento | Alta |

---

## 🔧 Componentes Técnicos

### 1. CLV Calculator

**Arquivo:** `src/engine/edge.py`

**Descrição:** Calcula o valor esperado baseado no movimento de odds

**Fórmula CLV:**
```
CLV = (Odds_Abertura / Odds_Fechamento) - 1

Onde:
CLV > 0 indica que a aposta foi feita com odds melhores que o fechamento
CLV < 0 indica que a aposta foi feita com odds piores que o fechamento
```

**Implementação:**
```python
def calculate_clv(opening_odds, closing_odds):
    """
    Calcula o Closed Line Value
    
    Args:
        opening_odds: Odds no momento da aposta
        closing_odds: Odds no fechamento do mercado
    
    Returns:
        CLV como percentagem
    """
    clv = (opening_odds / closing_odds) - 1
    return clv * 100  # Convert to percentage
```

**CLV Proxy:**
```python
def calculate_clv_proxy(current_odds, market_consensus):
    """
    Calcula CLV proxy usando consenso de mercado
    quando odds de fechamento não disponíveis
    """
    clv_proxy = (current_odds / market_consensus) - 1
    return clv_proxy * 100
```

### 2. Odds Normalization

**Arquivo:** `07_Value_Detection/ODDS_NORMALIZACAO.md`

**Descrição:** Normaliza odds de diferentes formatos

**Formatos Suportados:**
- Decimal (europeu)
- Americano (moneyline)
- Fracionário (britânico)

**Implementação:**
```python
def normalize_odds(odds, from_format='decimal', to_format='decimal'):
    """
    Normaliza odds entre diferentes formatos
    """
    if from_format == to_format:
        return odds
    
    # Convert to decimal first
    if from_format == 'american':
        if odds > 0:
            decimal = (odds / 100) + 1
        else:
            decimal = (100 / abs(odds)) + 1
    elif from_format == 'fractional':
        decimal = odds + 1
    else:  # decimal
        decimal = odds
    
    # Convert to target format
    if to_format == 'decimal':
        return decimal
    elif to_format == 'american':
        if decimal >= 2.0:
            american = (decimal - 1) * 100
        else:
            american = -100 / (decimal - 1)
        return american
    elif to_format == 'fractional':
        return decimal - 1
```

### 3. Multi-Bookmaker Comparison

**Arquivo:** `04_Data_Engineering/MULTI_SOURCE_AGGREGATION.md`

**Descrição:** Compara odds entre múltiplas casas

**Implementação:**
```python
def compare_odds_across_bookmakers(game_id, market_type):
    """
    Compara odds de múltiplas casas para um jogo
    """
    odds_data = fetch_all_odds(game_id, market_type)
    
    comparison = []
    for bookmaker, odds in odds_data.items():
        comparison.append({
            'bookmaker': bookmaker,
            'home_odds': odds['home'],
            'away_odds': odds['away'],
            'implied_prob_home': 1 / odds['home'],
            'implied_prob_away': 1 / odds['away']
        })
    
    # Find best odds
    best_home = max(comparison, key=lambda x: x['home_odds'])
    best_away = max(comparison, key=lambda x: x['away_odds'])
    
    return {
        'comparison': comparison,
        'best_home_odds': best_home,
        'best_away_odds': best_away
    }
```

### 4. Edge Calculation

**Arquivo:** `src/engine/edge.py`

**Descrição:** Calcula o edge esperado de uma aposta

**Fórmula:**
```
Edge = (Probabilidade_Modelo * Odds) - 1

Onde:
Edge > 0 indica valor esperado positivo
Edge < 0 indica valor esperado negativo
```

**Implementação:**
```python
def calculate_edge(model_probability, bookmaker_odds):
    """
    Calcula o edge esperado
    
    Args:
        model_probability: Probabilidade do modelo (0-1)
        bookmaker_odds: Odds da casa (decimal)
    
    Returns:
        Edge como percentagem
    """
    edge = (model_probability * bookmaker_odds) - 1
    return edge * 100  # Convert to percentage
```

**Edge Ajustado:**
```python
def calculate_adjusted_edge(model_probability, bookmaker_odds, clv=0):
    """
    Calcula edge ajustado por CLV
    """
    base_edge = calculate_edge(model_probability, bookmaker_odds)
    adjusted_edge = base_edge + clv
    return adjusted_edge
```

### 5. Signal Generation

**Arquivo:** `07_Value_Detection/SINAI_GENERATION.md`

**Descrição:** Gera sinais de aposta baseados em edge

**Thresholds:**
```python
EDGE_THRESHOLDS = {
    'minimum': 2.0,  # 2% edge mínimo
    'moderate': 4.0,  # 4% edge moderado
    'high': 6.0,  # 6% edge alto
    'very_high': 10.0  # 10% edge muito alto
}
```

**Implementação:**
```python
def generate_signal(game_info, model_prediction, odds):
    """
    Gera sinal de aposta
    """
    # Calculate edge
    edge = calculate_edge(model_prediction['probability'], odds)
    
    # Check thresholds
    if edge < EDGE_THRESHOLDS['minimum']:
        return None  # No signal
    
    # Determine signal strength
    if edge >= EDGE_THRESHOLDS['very_high']:
        strength = 'very_high'
    elif edge >= EDGE_THRESHOLDS['high']:
        strength = 'high'
    elif edge >= EDGE_THRESHOLDS['moderate']:
        strength = 'moderate'
    else:
        strength = 'minimum'
    
    # Generate signal
    signal = {
        'game_id': game_info['game_id'],
        'team': model_prediction['predicted_winner'],
        'probability': model_prediction['probability'],
        'odds': odds,
        'edge': edge,
        'strength': strength,
        'timestamp': datetime.now()
    }
    
    return signal
```

---

## 🔄 Pipeline de Edge

### Fluxo de Detecção

```python
def detect_value_opportunities(games, model, odds_sources):
    """
    Detecta oportunidades de value
    """
    opportunities = []
    
    for game in games:
        # Get model prediction
        prediction = model.predict(game['features'])
        
        # Get odds from all sources
        all_odds = {}
        for source in odds_sources:
            odds = fetch_odds(game['game_id'], source)
            all_odds[source] = odds
        
        # Compare odds
        comparison = compare_odds_across_bookmakers(game['game_id'], 'moneyline')
        
        # Calculate edge for each bookmaker
        for bookmaker, odds in all_odds.items():
            edge = calculate_edge(prediction['probability'], odds)
            
            # Check if edge meets threshold
            if edge >= EDGE_THRESHOLDS['minimum']:
                opportunity = {
                    'game_id': game['game_id'],
                    'bookmaker': bookmaker,
                    'team': prediction['predicted_winner'],
                    'probability': prediction['probability'],
                    'odds': odds,
                    'edge': edge,
                    'best_odds': comparison['best_home_odds'] if prediction['predicted_winner'] == 'home' else comparison['best_away_odds']
                }
                opportunities.append(opportunity)
    
    # Sort by edge
    opportunities.sort(key=lambda x: x['edge'], reverse=True)
    
    return opportunities
```

---

## 📊 Filtros de Qualidade

### False Positive Filter

**Arquivo:** `07_Value_Detection/FALSE_POSITIVE_FILTER.md`

**Filtros:**
```python
QUALITY_FILTERS = {
    'min_odds': 1.10,  # Odds mínimas
    'max_odds': 10.00,  # Odds máximas
    'min_probability': 0.20,  # Probabilidade mínima
    'max_probability': 0.80,  # Probabilidade máxima
    'min_clv': 1.0,  # CLV mínimo
    'max_market_movement': 0.10,  # Movimento máximo de mercado
    'min_liquidity': 1000,  # Liquidez mínima
    'max_time_to_game': 48  # Horas máximas até ao jogo
}
```

**Implementação:**
```python
def apply_quality_filters(opportunity):
    """
    Aplica filtros de qualidade
    """
    # Check odds range
    if not (QUALITY_FILTERS['min_odds'] <= opportunity['odds'] <= QUALITY_FILTERS['max_odds']):
        return False
    
    # Check probability range
    if not (QUALITY_FILTERS['min_probability'] <= opportunity['probability'] <= QUALITY_FILTERS['max_probability']):
        return False
    
    # Check CLV
    if opportunity.get('clv', 0) < QUALITY_FILTERS['min_clv']:
        return False
    
    # Check market movement
    if opportunity.get('market_movement', 0) > QUALITY_FILTERS['max_market_movement']:
        return False
    
    # Check liquidity
    if opportunity.get('liquidity', 0) < QUALITY_FILTERS['min_liquidity']:
        return False
    
    # Check time to game
    time_to_game = (opportunity['game_time'] - datetime.now()).total_seconds() / 3600
    if time_to_game > QUALITY_FILTERS['max_time_to_game']:
        return False
    
    return True
```

---

## 📈 Monitorização

### Métricas de Edge

**Edge Metrics:**
- Edge médio por sinal
- Distribuição de edge
- CLV médio
- Taxa de conversão (sinais → apostas)

**Performance Metrics:**
- ROI por nível de edge
- Win rate por nível de edge
- CLV realizado vs esperado

### Alertas

**Telegram Alerts:**
- Edge muito alto (> 10%)
- Oportunidade rara detectada
- Discrepância de odds significativa
- CLV anormal

---

## 🚀 Configuração

### Parâmetros do Motor

```python
EDGE_CONFIG = {
    # Thresholds
    'min_edge': 2.0,  # 2% edge mínimo
    'moderate_edge': 4.0,  # 4% edge moderado
    'high_edge': 6.0,  # 6% edge alto
    'very_high_edge': 10.0,  # 10% edge muito alto
    
    # Quality filters
    'min_odds': 1.10,
    'max_odds': 10.00,
    'min_probability': 0.20,
    'max_probability': 0.80,
    'min_clv': 1.0,
    'min_liquidity': 1000,
    
    # Timing
    'max_time_to_game': 48,  # horas
    'check_frequency': 300,  # segundos (5 minutos)
}
```

---

## 📝 Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Implementar odds normalization completo
- [ ] Adicionar multi-bookmaker comparison
- [ ] Refinar filtros de qualidade
- [ ] Adicionar backtesting de edge

### Médio Prazo (1-2 meses)
- [ ] Implementar signal generation avançado
- [ ] Adicionar CLV prediction
- [ ] Criar edge dashboard
- [ ] Implementar adaptive thresholds

### Longo Prazo (3-6 meses)
- [ ] Real-time edge detection
- [ ] Multi-market edge
- [ ] Machine learning para edge prediction
- [ ] Edge marketplace

---

## 🔗 Links Relacionados

- [[Gestão de Risco]] - Avaliação de apostas
- [[Machine Learning]] - Previsões do modelo
- [[Sistema de Apostas]] - Execução de sinais
- [[Índice Mestre]] - Documentação completa

---

**Última atualização:** 2026-05-19  
**Responsável:** Quant Engineer  
**Status:** 🚧 Em desenvolvimento