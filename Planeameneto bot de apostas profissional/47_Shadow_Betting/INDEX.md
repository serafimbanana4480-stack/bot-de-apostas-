# 47_Shadow Betting — INDEX

**ID:** `SEC-47` | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Simular apostas em múltiplas casas sem execução real para medir o **True CLV** e validar que o edge existe independentemente da casa escolhida. O shadow betting é o teste de stress do sistema antes de dinheiro real.

---

## 2. PORQUE SHADOW MULTI-CASA

A odd de fecho da Pinnacle é considerada a referência, mas:
- Pinnacle não aceita apostadores de todos os países
- Betfair Exchange tem liquidez variável
- Outras casas podem ter odds mais lentas (e portanto mais fáceis de "pegar")

Medir o edge em 3+ casas dá uma estimativa robusta do True CLV, não do "CLV teórico da Pinnacle".

---

## 3. PROTOCOLO SHADOW

```
1. Sinal aprovado pelo motor de value
2. Sistema regista odd disponível em:
   ├── Pinnacle (proxy via fontes)
   ├── Betfair Exchange (API se disponível)
   ├── Casa tradicional X (scraping limitado ou API)
   └── Casa tradicional Y (opcional)

3. Após o jogo, sistema recolhe:
   ├── Odd de fecho em cada casa
   ├── Resultado do jogo
   └── Calcula CLV_expost para cada casa

4. Relatório diário:
   ├── True CLV = média ponderada dos CLVs por casa
   ├── Dispersão de CLV (max - min) por casa
   └── Casa com melhor CLV consistente
```

---

## 4. MÉTRICAS DE SHADOW

| Métrica | Target | Interpretação |
|---------|--------|---------------|
| True CLV médio | > 1.5% | Edge real existe |
| Dispersão de CLV | < 2% | Edge é robusto entre casas |
| Fill rate simulado | > 80% | Apostas seriam executáveis |
| Slippage shadow vs backtest | < 1% | Backtest não é otimista |

---

## 5. IMPLEMENTAÇÃO DETALHADA

### 5.1 Arquitetura do Sistema Shadow Multi-Casa

```
┌─────────────────────────────────────────────────────────────────┐
│ SISTEMA SHADOW MULTI-CASA                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Signal       │                                               │
│  │ Generator    │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Shadow Multi-Casa Engine                                  │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Betfair  │  │Pinnacle  │  │Smarkets  │  │Casa X    │ │   │
│  │  │ Capture  │  │Capture   │  │Capture   │  │Capture   │ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │   │
│  │       │             │             │             │        │   │
│  │       └─────────────┴─────────────┴─────────────┘        │   │
│  │                      ↓                                   │   │
│  │              ┌───────────────┐                           │   │
│  │              │ Aggregator    │                           │   │
│  │              └───────┬───────┘                           │   │
│  │                      ↓                                   │   │
│  │              ┌───────────────┐                           │   │
│  │              │ CLV Calculator│                           │   │
│  │              └───────┬───────┘                           │   │
│  └──────────────────────┼───────────────────────────────────┘   │
│                         ↓                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Database (Shadow Bets)                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Configuração de Casas para Shadow

```python
SHADOW_HOUSES_CONFIG = {
    'betfair': {
        'enabled': True,
        'api_client': BetfairAPI,
        'priority': 1,  # Primária
        'commission': 0.05,
        'weight': 0.5,  # 50% do True CLV
    },
    'pinnacle': {
        'enabled': True,
        'api_client': PinnacleAPI,
        'priority': 2,  # Referência
        'commission': 0.02,
        'weight': 0.3,  # 30% do True CLV
    },
    'smarkets': {
        'enabled': True,
        'api_client': SmarketsAPI,
        'priority': 3,
        'commission': 0.02,
        'weight': 0.2,  # 20% do True CLV
    }
}
```

### 5.3 Motor Shadow Multi-Casa

```python
class ShadowMultiHouseEngine:
    def __init__(self, config):
        self.houses = self._init_houses(config)
        self.db = Database(config['database'])

    def process_signal(self, signal):
        """Processa sinal em shadow mode multi-casa"""
        shadow_bets = []

        for house_name, house_config in self.houses.items():
            if not house_config['enabled']:
                continue

            # Capturar odd na casa
            odd_data = self._capture_odd(house_name, signal)

            if odd_data:
                # Registrar shadow bet
                shadow_bet = {
                    'signal_id': signal.id,
                    'house': house_name,
                    'market_id': signal.market_id,
                    'selection_id': signal.selection_id,
                    'signal_odds': signal.odds,
                    'shadow_odds': odd_data['value'],
                    'liquidity': odd_data['liquidity'],
                    'timestamp': datetime.now(),
                    'weight': house_config['weight']
                }

                shadow_bets.append(shadow_bet)

        # Armazenar
        for bet in shadow_bets:
            self.db.insert_shadow_bet(bet)

        return shadow_bets

    def _capture_odd(self, house_name, signal):
        """Captura odd em casa específica"""
        try:
            api_client = self.houses[house_name]['api_client']
            odd_data = api_client.get_odds(
                market_id=signal.market_id,
                selection_id=signal.selection_id
            )
            return odd_data
        except Exception as e:
            log_error(f"Failed to capture odd from {house_name}: {e}")
            return None

    def calculate_true_clv(self, signal_id):
        """Calcula True CLV ponderado"""
        shadow_bets = self.db.get_shadow_bets(signal_id)

        if not shadow_bets:
            return None

        # Aguardar odd de fecho
        closing_odds = self._get_closing_odds(shadow_bets[0])

        # Calcular CLV por casa
        clv_values = []
        weights = []

        for bet in shadow_bets:
            clv = (bet['shadow_odds'] / closing_odds) - 1
            clv_values.append(clv)
            weights.append(bet['weight'])

        # CLV ponderado
        true_clv = sum(c * w for c, w in zip(clv_values, weights)) / sum(weights)

        return {
            'true_clv': true_clv,
            'clv_by_house': dict(zip([b['house'] for b in shadow_bets], clv_values)),
            'weights': weights
        }
```

### 5.4 Análise de Dispersão de CLV

```python
class CLVDispersionAnalyzer:
    def __init__(self, db):
        self.db = db

    def analyze_dispersion(self, signal_id):
        """Analisa dispersão de CLV entre casas"""
        shadow_bets = self.db.get_shadow_bets(signal_id)
        closing_odds = self._get_closing_odds(shadow_bets[0])

        clv_by_house = {}
        for bet in shadow_bets:
            clv = (bet['shadow_odds'] / closing_odds) - 1
            clv_by_house[bet['house']] = clv

        # Métricas de dispersão
        clv_values = list(clv_by_house.values())
        dispersion = {
            'max': max(clv_values),
            'min': min(clv_values),
            'range': max(clv_values) - min(clv_values),
            'stddev': statistics.stdev(clv_values) if len(clv_values) > 1 else 0,
            'cv': statistics.stdev(clv_values) / statistics.mean(clv_values) if clv_values else 0
        }

        # Interpretação
        if dispersion['range'] < 0.01:  # < 1%
            interpretation = 'VERY_CONSISTENT'
        elif dispersion['range'] < 0.02:  # < 2%
            interpretation = 'CONSISTENT'
        elif dispersion['range'] < 0.04:  # < 4%
            interpretation = 'MODERATE'
        else:
            interpretation = 'HIGH_DISPERSION'

        return {
            'clv_by_house': clv_by_house,
            'dispersion': dispersion,
            'interpretation': interpretation
        }
```

### 5.5 Seleção de Casa Ótima

```python
class HouseSelector:
    def __init__(self, db):
        self.db = db

    def select_best_house(self, signal_id, historical_performance=True):
        """Seleciona melhor casa baseado em critérios"""
        shadow_bets = self.db.get_shadow_bets(signal_id)

        if not shadow_bets:
            return None

        scores = {}

        for bet in shadow_bets:
            house = bet['house']
            score = 0

            # Critério 1: Liquidez (30%)
            if bet['liquidity'] >= 10000:
                score += 30
            elif bet['liquidity'] >= 5000:
                score += 20
            elif bet['liquidity'] >= 1000:
                score += 10

            # Critério 2: CLV histórico (40%)
            if historical_performance:
                historical_clv = self._get_historical_clv(house)
                score += min(historical_clv * 100, 40)

            # Critério 3: Comissão (20%)
            commission = self._get_commission(house)
            if commission <= 0.02:
                score += 20
            elif commission <= 0.05:
                score += 10

            # Critério 4: Slippage histórico (10%)
            historical_slippage = self._get_historical_slippage(house)
            score += max(10 - historical_slippage * 100, 0)

            scores[house] = score

        # Casa com maior score
        best_house = max(scores, key=scores.get)

        return {
            'best_house': best_house,
            'scores': scores,
            'recommendation': f"Use {best_house} for execution"
        }

    def _get_historical_clv(self, house):
        """Obtém CLV histórico médio da casa"""
        # Implementar query à BD
        return 0.02  # exemplo

    def _get_commission(self, house):
        """Obtém comissão da casa"""
        commissions = {
            'betfair': 0.05,
            'pinnacle': 0.02,
            'smarkets': 0.02
        }
        return commissions.get(house, 0.05)

    def _get_historical_slippage(self, house):
        """Obtém slippage histórico médio da casa"""
        # Implementar query à BD
        return 0.01  # exemplo
```

---

## 6. ESTRATÉGIA DE VALIDAÇÃO

### 6.1 Fase 3: Validação Inicial

**Objetivo:** Validar que edge existe independentemente da casa.

**Protocolo:**
1. Executar shadow mode por 30 dias
2. Calcular True CLV ponderado
3. Analisar dispersão de CLV
4. Identificar casa mais consistente

**Critérios de Sucesso:**
- True CLV médio > 1.5%
- Dispersão de CLV < 3%
- Pelo menos 2 casas com CLV > 1%

**Decisão:**
```
SE True CLV > 1.5% E Dispersão < 3%:
    → APROVADO para micro banca
    → Selecionar casa primária baseado em análise
SENÃO:
    → INVESTIGAR
    → Possível edge específico de casa
```

### 6.2 Fase 6+: Validação Contínua

**Objetivo:** Monitorizar consistência de CLV entre casas.

**Protocolo:**
1. Executar shadow mode continuamente (amostra de 10% dos sinais)
2. Comparar CLV real com CLV shadow
3. Detectar deterioração de edge
4. Ajustar seleção de casa se necessário

**Alertas:**
- Se CLV shadow cai < 1%: Investigar modelo
- Se dispersão aumenta > 5%: Investigar casas
- Se CLV real < CLV shadow - 2%: Investigar execução

---

## 7. INTEGRAÇÃO COM EXECUÇÃO REAL

### 7.1 Seleção Dinâmica de Casa

```python
class DynamicHouseSelector:
    def __init__(self, shadow_engine, house_selector):
        self.shadow_engine = shadow_engine
        self.house_selector = house_selector

    def select_house_for_execution(self, signal):
        """Seleciona casa para execução real baseado em shadow data"""
        # 1. Executar shadow capture
        shadow_bets = self.shadow_engine.process_signal(signal)

        # 2. Selecionar melhor casa
        selection = self.house_selector.select_best_house(signal.id)

        # 3. Validar seleção
        if selection['best_house'] and selection['scores'][selection['best_house']] > 50:
            return selection['best_house']
        else:
            # Fallback para casa padrão
            return 'betfair'
```

### 7.2 Comparação CLV Shadow vs Real

```python
class CLVComparator:
    def __init__(self, db):
        self.db = db

    def compare_shadow_vs_real(self, signal_id):
        """Compara CLV shadow com CLV real após execução"""
        # Obter CLV shadow
        shadow_clv = self.db.get_shadow_clv(signal_id)

        # Obter CLV real
        real_clv = self.db.get_real_clv(signal_id)

        # Comparar
        difference = real_clv - shadow_clv

        return {
            'shadow_clv': shadow_clv,
            'real_clv': real_clv,
            'difference': difference,
            'difference_pct': (difference / shadow_clv) * 100 if shadow_clv else 0,
            'within_tolerance': abs(difference) < 0.01  # 1% tolerância
        }
```

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[03_Quant_Research/INDEX]] → Cálculo de CLV
- [[21_Paper_Trading/INDEX]] → Paper trading (simulação sem multi-casa)
- [[22_Real_Money_Operations/INDEX]] → Próxima fase após shadow
- [[45_Bookmaker_Analysis/BOOKMAKER_COMPARISON]] → Comparação de casas
