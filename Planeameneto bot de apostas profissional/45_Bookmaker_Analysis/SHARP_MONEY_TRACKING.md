# SHARP_MONEY_TRACKING — Rastreamento de Sharp Money e Line Movement

**ID:** `BA-002` | **Fase:** #phase/3-6 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Rastrear movimentos de odds e identificar "sharp money" (apostadores profissionais) para validar edge e antecipar movimentos de mercado. Sharp money frequentemente move linhas antes do mercado geral.

**Princípio:** Seguir sharp money = seguir informação privilegiada = melhor CLV.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 Sharp Money vs Public Money

**Sharp Money:**
- Apostadores profissionais/institucionais
- Stakes grandes (milhares a milhões)
- Informação privilegiada ou modelo superior
- Movem linhas antes do público
- Focam em value, não em favoritos

**Public Money:**
- Apostadores recreacionais
- Stakes pequenos (dezenas a centenas)
- Seguem intuição/emoção
- Movem linhas após sharp money
- Focam em favoritos populares

**Exemplo:**
```
Lakers vs Celtics
Odd inicial: Lakers 2.10, Celtics 1.80

09:00 - Sharp money entra no Celtics (stake €50k)
        → Celtics cai para 1.75

10:00 - Public money entra no Lakers (stake €5k)
        → Lakers sobe para 2.15

Interpretação: Sharp money viu value no Celtics
Ação: Seguir sharp money → apostar Celtics
```

### 2.2 Line Movement

**Tipos de Movimento:**

| Tipo | Padrão | Interpretação |
|------|--------|---------------|
| Steam Move | Movimento rápido e forte em uma direção | Sharp money entrando |
| Reverse Line Movement | Odd move oposto ao public betting % | Sharp action |
| Drift | Movimento lento e consistente | Informação gradual |
| Spike | Movimento repentino mas breve | News ou injury |
| Oscillation | Movimento para frente e trás | Mercado indeciso |

**Tempo de Movimento:**

| Período | Característica | Importância |
|---------|---------------|-------------|
| Opening → 1h | Sharp money | Alta |
| 1h → Game start | Public money | Média |
| In-game | Live betting | Baixa (para pré-jogo) |

---

## 3. INDICADORES DE SHARP MONEY

### 3.1 Contrarian Indicator

**Conceito:** Apostar contra o público quando há divergência significativa.

```
SE Public Betting % > 70% E Odd move oposto:
    → Sharp money no lado oposto
    → APOSTAR contra o público
```

**Exemplo:**
```
Warriors vs Heat
Public betting: 75% Warriors
Odd movement: Warriors 1.90 → 1.95 (subiu)

Interpretação: Público no Warriors, mas sharp no Heat
Ação: Apostar Heat
```

### 3.2 Steam Moves

**Conceito:** Identificar movimentos rápidos de odds.

```
SE Odd move > 3% em < 5 minutos:
    → Steam move detectado
    → Identificar direção
    → Seguir movimento
```

**Implementação:**
```python
def detect_steam_move(odds_history, threshold=0.03, window=300):
    """
    Detecta steam moves no histórico de odds
    """
    for i in range(len(odds_history) - 1):
        current = odds_history[i]
        next_odds = odds_history[i + 1]

        # Verificar tempo entre medidas
        time_diff = (next_odds.timestamp - current.timestamp).total_seconds()

        if time_diff <= window:
            # Calcular movimento percentual
            movement = abs(next_odds.value - current.value) / current.value

            if movement >= threshold:
                return {
                    'detected': True,
                    'direction': 'up' if next_odds.value > current.value else 'down',
                    'magnitude': movement,
                    'time_window': time_diff
                }

    return {'detected': False}
```

### 3.3 Reverse Line Movement (RLM)

**Conceito:** Odd move oposto ao percentual de apostas do público.

```
SE Public Betting % > 60% E Odd move no lado oposto:
    → RLM detectado
    → Sharp action no lado oposto
    → APOSTAR no lado do odd move
```

**Exemplo:**
```
Bulls vs Knicks
Public betting: 80% Bulls
Odd movement: Bulls 1.85 → 1.90 (subiu), Knicks 2.00 → 1.95 (caiu)

Interpretação: RLM - sharp no Knicks
Ação: Apostar Knicks
```

### 3.4 Closing Line Value (CLV) como Sharp Indicator

**Conceito:** Se consistentemente capturar CLV positivo, está seguindo sharp money.

```
SE CLV médio > 2%:
    → Capturando sharp money
    → Continuar estratégia

SE CLV médio < 0%:
    → No lado errado (public money)
    → Revisar estratégia
```

---

## 4. SISTEMA DE RASTREAMENTO

### 4.1 Coleta de Dados

**Fontes de Dados:**

| Fonte | Dados | Latência | Custo |
|-------|-------|----------|-------|
| Pinnacle API | Odds, volume | Baixa | Pago |
| Betfair API | Odds, volume | Baixa | Pago |
| OddsPortal | Odds históricas | Alta | Gratuito |
| Sports Insights | Public betting % | Média | Pago |
| DonBest | Line movement | Média | Pago |

**Implementação de Coleta:**
```python
class SharpMoneyTracker:
    def __init__(self, config):
        self.pinnacle_api = PinnacleAPI(config['pinnacle'])
        self.betfair_api = BetfairAPI(config['betfair'])
        self.db = Database(config['database'])

    def collect_odds(self, market_id):
        """Coleta odds de múltiplas fontes"""
        odds = {}

        # Pinnacle
        odds['pinnacle'] = self.pinnacle_api.get_odds(market_id)

        # Betfair
        odds['betfair'] = self.betfair_api.get_odds(market_id)

        # Timestamp
        odds['timestamp'] = datetime.now()

        # Armazenar
        self.db.insert_odds_snapshot(market_id, odds)

        return odds

    def collect_public_betting(self, game_id):
        """Coleta percentual de apostas do público"""
        # Fonte: Sports Insights ou similar
        public_betting = self._get_public_betting(game_id)

        self.db.insert_public_betting(game_id, public_betting)

        return public_betting
```

### 4.2 Análise de Line Movement

```python
class LineMovementAnalyzer:
    def __init__(self, db):
        self.db = db

    def analyze_movement(self, market_id, window_hours=24):
        """Analisa movimento de linha nas últimas X horas"""
        # Obter histórico de odds
        odds_history = self.db.get_odds_history(
            market_id,
            since=datetime.now() - timedelta(hours=window_hours)
        )

        # Calcular movimento
        movements = []
        for i in range(len(odds_history) - 1):
            current = odds_history[i]
            next_odds = odds_history[i + 1]

            movement = {
                'from': current.value,
                'to': next_odds.value,
                'change': next_odds.value - current.value,
                'change_pct': (next_odds.value - current.value) / current.value,
                'time': next_odds.timestamp - current.timestamp
            }

            movements.append(movement)

        # Classificar movimento
        total_change = movements[-1]['to'] - movements[0]['from']
        total_change_pct = total_change / movements[0]['from']

        return {
            'total_change': total_change,
            'total_change_pct': total_change_pct,
            'direction': 'up' if total_change > 0 else 'down',
            'movements': movements,
            'classification': self._classify_movement(movements)
        }

    def _classify_movement(self, movements):
        """Classifica tipo de movimento"""
        # Detectar steam move
        for m in movements:
            if abs(m['change_pct']) > 0.03 and m['time'].total_seconds() < 300:
                return 'STEAM_MOVE'

        # Detectar drift
        if len(movements) > 10:
            direction = 'up' if movements[-1]['to'] > movements[0]['from'] else 'down'
            consistent = all(
                (m['change'] > 0 if direction == 'up' else m['change'] < 0)
                for m in movements
            )
            if consistent:
                return 'DRIFT'

        return 'NORMAL'
```

### 4.3 Detecção de Sharp Action

```python
class SharpActionDetector:
    def __init__(self, db):
        self.db = db

    def detect_sharp_action(self, game_id):
        """Detecta sharp action no jogo"""
        # Obter dados
        public_betting = self.db.get_public_betting(game_id)
        line_movement = self._analyze_line_movement(game_id)

        # Indicadores
        indicators = []

        # 1. Contrarian indicator
        if public_betting['pct_favorite'] > 0.70:
            if line_movement['direction'] == 'up':
                indicators.append({
                    'type': 'CONTRARIAN',
                    'signal': 'STRONG',
                    'side': 'underdog'
                })

        # 2. Reverse line movement
        if public_betting['pct_favorite'] > 0.60:
            if line_movement['direction'] == 'up':
                indicators.append({
                    'type': 'RLM',
                    'signal': 'MODERATE',
                    'side': 'underdog'
                })

        # 3. Steam move
        if line_movement['classification'] == 'STEAM_MOVE':
            indicators.append({
                'type': 'STEAM_MOVE',
                'signal': 'STRONG',
                'side': line_movement['direction']
            })

        # 4. Drift
        if line_movement['classification'] == 'DRIFT':
            indicators.append({
                'type': 'DRIFT',
                'signal': 'MODERATE',
                'side': line_movement['direction']
            })

        return {
            'detected': len(indicators) > 0,
            'indicators': indicators,
            'overall_signal': self._calculate_overall_signal(indicators)
        }

    def _calculate_overall_signal(self, indicators):
        """Calcula sinal combinado"""
        if not indicators:
            return 'NEUTRAL'

        strength = sum(
            2 if i['signal'] == 'STRONG' else 1
            for i in indicators
        )

        if strength >= 4:
            return 'STRONG'
        elif strength >= 2:
            return 'MODERATE'
        else:
            return 'WEAK'
```

---

## 5. INTEGRAÇÃO COM ESTRATÉGIA

### 5.1 Filtro de Sharp Money

**Integrar sharp money como filtro adicional:**

```python
def enhanced_signal_generation(model_signal, sharp_indicator):
    """
    Gera sinal final combinando modelo e sharp money
    """
    if sharp_indicator['overall_signal'] == 'NEUTRAL':
        return model_signal

    # Se sharp money forte, aumentar confiança
    if sharp_indicator['overall_signal'] == 'STRONG':
        model_signal.confidence *= 1.2
        model_signal.stake *= 1.1

    # Se sharp money moderado, manter confiança
    if sharp_indicator['overall_signal'] == 'MODERATE':
        model_signal.confidence *= 1.1

    # Se sharp money fraco, manter confiança
    if sharp_indicator['overall_signal'] == 'WEAK':
        model_signal.confidence *= 1.05

    return model_signal
```

### 5.2 Estratégia de Follow-the-Sharp

**Estratégia pura baseada em sharp money:**

```python
def follow_sharp_strategy(game_id):
    """
    Estratégia simples: seguir sharp money
    """
    sharp_action = detect_sharp_action(game_id)

    if not sharp_action['detected']:
        return None  # Sem sinal

    # Identificar lado com mais indicadores
    side_votes = {}
    for indicator in sharp_action['indicators']:
        side = indicator['side']
        side_votes[side] = side_votes.get(side, 0) + 1

    # Lado com mais votos
    best_side = max(side_votes, key=side_votes.get)

    # Gerar sinal
    return {
        'game_id': game_id,
        'side': best_side,
        'confidence': sharp_action['overall_signal'],
        'reason': 'SHARP_MONEY_FOLLOW'
    }
```

---

## 6. MÉTRICAS DE VALIDAÇÃO

### 6.1 Métricas de Sharp Money

| Métrica | Como Calcular | Target |
|---------|---------------|--------|
| Sharp hit rate | Apostas seguindo sharp que ganham | > 52% |
| Sharp CLV | CLV médio seguindo sharp | > 2% |
| Sharp vs Model | Comparação ROI sharp vs modelo | Similar |
| Public fade hit rate | Apostas contra público que ganham | > 53% |

### 6.2 Backtest de Sharp Money

```python
def backtest_sharp_strategy(start_date, end_date):
    """Backtest de estratégia baseada em sharp money"""
    results = []

    for game in get_games_in_period(start_date, end_date):
        # Detectar sharp action no momento do jogo
        sharp_action = detect_sharp_action_at_time(
            game.id,
            game.start_time - timedelta(hours=2)
        )

        if sharp_action['detected']:
            # Simular aposta seguindo sharp
            bet = follow_sharp_strategy(game.id)

            if bet:
                # Calcular resultado
                result = calculate_bet_result(bet, game)
                results.append(result)

    # Calcular métricas
    roi = sum(r['pnl'] for r in results) / sum(r['stake'] for r in results)
    hit_rate = sum(1 for r in results if r['outcome'] == 'WIN') / len(results)
    avg_clv = sum(r['clv'] for r in results) / len(results)

    return {
        'roi': roi,
        'hit_rate': hit_rate,
        'avg_clv': avg_clv,
        'n_bets': len(results)
    }
```

---

## 7. RISCOS E LIMITAÇÕES

### 7.1 Riscos

**False Positives:**
- Sharp money pode estar errado
- Public money pode estar certo
- Overfitting a padrões de sharp money

**Latência de Dados:**
- Sharp money move rápido
- Dados podem ter delay
- Pode perder janela de oportunidade

**Custo de Dados:**
- Fontes de sharp money são pagas
- Pode não ser rentável para banca pequena

### 7.2 Limitações

- Sharp money não é infalível (~52-55% hit rate)
- Funciona melhor em certos mercados (NBA, NFL)
- Requer dados em tempo real (custoso)
- Dificil de distinguir sharp vs whale recreational

---

## 8. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Seção mãe
- [[45_Bookmaker_Analysis/BOOKMAKER_COMPARISON]] → Comparação de casas
- [[03_Quant_Research/INDEX]] → Pesquisa quantitativa
- [[07_Value_Detection/INDEX]] → Detecção de value