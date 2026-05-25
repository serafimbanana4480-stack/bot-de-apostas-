# 🛡️ Gestão de Risco

**Componente:** Risk Management  
**Status:** 🚧 Em desenvolvimento (80%)  
**Responsável:** Quant Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Proteger o bankroll através de gestão de risco rigorosa, dimensionamento de stakes baseado em Kelly Criterion, e circuit breakers automáticos para prevenir drawdowns catastróficos.

---

## 🏗️ Arquitetura

### Componentes de Risco

| Componente | Status | Prioridade |
|------------|--------|------------|
| **Kelly Criterion** | ✅ Implementado | Alta |
| **Circuit Breakers** | 🚧 Em desenvolvimento | Alta |
| **Bankroll Management** | ✅ Implementado | Alta |
| **Exposure Limits** | 🚧 Em desenvolvimento | Média |
| **Drawdown Monitoring** | 🚧 Em desenvolvimento | Alta |

---

## 🔧 Componentes Técnicos

### 1. Kelly Criterion

**Arquivo:** `src/risk/kelly.py`

**Descrição:** Dimensionamento matemático ótimo de stakes

**Fórmula:**
```
f* = (bp - q) / b

Onde:
f* = fração do bankroll a apostar
b = odds decimais - 1
p = probabilidade de vitória (do modelo)
q = probabilidade de derrota (1 - p)
```

**Implementação:**
```python
def calculate_kelly_fraction(probability, odds):
    """
    Calcula a fração de Kelly
    
    Args:
        probability: Probabilidade de vitória (0-1)
        odds: Odds decimais
    
    Returns:
        Fração do bankroll a apostar (0-1)
    """
    b = odds - 1  # Net odds
    p = probability
    q = 1 - p
    
    kelly_fraction = (b * p - q) / b
    
    # Kelly negativo = valor esperado negativo
    if kelly_fraction < 0:
        return 0
    
    return kelly_fraction
```

**Kelly Fractional:**
```python
def calculate_fractional_kelly(probability, odds, kelly_fraction=0.25):
    """
    Kelly fractional para reduzir volatilidade
    
    Args:
        probability: Probabilidade de vitória
        odds: Odds decimais
        kelly_fraction: Multiplicador de Kelly (padrão: 0.25)
    
    Returns:
        Fração do bankroll a apostar
    """
    full_kelly = calculate_kelly_fraction(probability, odds)
    return full_kelly * kelly_fraction
```

**Configuração:**
- **Kelly Fractional:** 0.25 (conservador)
- **Stake Máximo:** 2% do bankroll
- **Stake Mínimo:** 0.1% do bankroll

### 2. Circuit Breakers

**Arquivo:** `src/risk/circuit_breakers.py`

**Descrição:** Proteção automática contra drawdowns

**Tipos de Circuit Breakers:**

#### Daily Loss Limit
```python
class DailyLossCircuitBreaker:
    def __init__(self, max_daily_loss_pct=5):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.daily_pnl = 0
        self.bankroll_start = 0
    
    def check(self, current_pnl):
        """
        Verifica se o limite de perda diária foi atingido
        """
        loss_pct = (self.daily_pnl / self.bankroll_start) * 100
        
        if loss_pct <= -self.max_daily_loss_pct:
            return False  # Stop betting
        
        return True  # Continue betting
```

#### Drawdown Limit
```python
class DrawdownCircuitBreaker:
    def __init__(self, max_drawdown_pct=20):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_bankroll = 0
        self.current_bankroll = 0
    
    def check(self):
        """
        Verifica se o drawdown máximo foi atingido
        """
        drawdown_pct = ((self.peak_bankroll - self.current_bankroll) / 
                       self.peak_bankroll) * 100
        
        if drawdown_pct >= self.max_drawdown_pct:
            return False  # Stop betting
        
        return True  # Continue betting
```

#### Streak Limit
```python
class StreakCircuitBreaker:
    def __init__(self, max_loss_streak=5):
        self.max_loss_streak = max_loss_streak
        self.current_loss_streak = 0
    
    def check(self, bet_result):
        """
        Verifica se o streak de derrotas foi atingido
        """
        if bet_result == 'loss':
            self.current_loss_streak += 1
        else:
            self.current_loss_streak = 0
        
        if self.current_loss_streak >= self.max_loss_streak:
            return False  # Stop betting
        
        return True  # Continue betting
```

#### Volatility Limit
```python
class VolatilityCircuitBreaker:
    def __init__(self, max_volatility_threshold=2.0):
        self.max_volatility_threshold = max_volatility_threshold
        self.pnl_history = []
    
    def check(self, current_pnl):
        """
        Verifica se a volatilidade está muito alta
        """
        self.pnl_history.append(current_pnl)
        
        if len(self.pnl_history) < 20:
            return True
        
        volatility = np.std(self.pnl_history[-20:])
        
        if volatility > self.max_volatility_threshold:
            return False  # Stop betting
        
        return True  # Continue betting
```

### 3. Bankroll Management

**Arquivo:** `src/risk/bankroll.py`

**Descrição:** Gestão completa do bankroll

**Implementação:**
```python
class BankrollManager:
    def __init__(self, initial_bankroll):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll
        self.bet_history = []
    
    def calculate_stake(self, probability, odds):
        """
        Calcula o stake baseado em Kelly e limites
        """
        # Calculate Kelly
        kelly_frac = calculate_fractional_kelly(probability, odds, 0.25)
        
        # Calculate stake amount
        stake = self.current_bankroll * kelly_frac
        
        # Apply limits
        max_stake = self.current_bankroll * 0.02  # 2% max
        min_stake = self.current_bankroll * 0.001  # 0.1% min
        
        stake = max(min_stake, min(stake, max_stake))
        
        return stake
    
    def update_bankroll(self, stake, odds, result):
        """
        Atualiza o bankroll após uma aposta
        """
        if result == 'win':
            profit = stake * (odds - 1)
            self.current_bankroll += profit
        elif result == 'loss':
            self.current_bankroll -= stake
        elif result == 'push':
            pass  # No change
        
        # Update peak
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
        
        # Record bet
        self.bet_history.append({
            'stake': stake,
            'odds': odds,
            'result': result,
            'bankroll_after': self.current_bankroll
        })
    
    def get_metrics(self):
        """
        Calcula métricas do bankroll
        """
        total_bets = len(self.bet_history)
        wins = sum(1 for bet in self.bet_history if bet['result'] == 'win')
        losses = sum(1 for bet in self.bet_history if bet['result'] == 'loss')
        
        win_rate = wins / total_bets if total_bets > 0 else 0
        roi = ((self.current_bankroll - self.initial_bankroll) / 
               self.initial_bankroll) * 100
        
        drawdown = ((self.peak_bankroll - self.current_bankroll) / 
                    self.peak_bankroll) * 100
        
        return {
            'total_bets': total_bets,
            'win_rate': win_rate,
            'roi': roi,
            'drawdown': drawdown,
            'current_bankroll': self.current_bankroll,
            'peak_bankroll': self.peak_bankroll
        }
```

### 4. Exposure Limits

**Arquivo:** `src/risk/exposure.py`

**Descrição:** Limites de exposição por categoria

**Tipos de Exposure:**

#### Exposure por Jogo
```python
class PerGameExposureLimit:
    def __init__(self, max_exposure_pct=5):
        self.max_exposure_pct = max_exposure_pct
        self.current_exposure = 0
    
    def check(self, stake):
        """
        Verifica se a exposição por jogo é aceitável
        """
        exposure_pct = (self.current_exposure / self.current_bankroll) * 100
        
        if exposure_pct + (stake / self.current_bankroll) * 100 > self.max_exposure_pct:
            return False  # Reject bet
        
        return True  # Accept bet
```

#### Exposure por Dia
```python
class PerDayExposureLimit:
    def __init__(self, max_exposure_pct=10):
        self.max_exposure_pct = max_exposure_pct
        self.daily_exposure = 0
    
    def check(self, stake):
        """
        Verifica se a exposição diária é aceitável
        """
        exposure_pct = (self.daily_exposure / self.current_bankroll) * 100
        
        if exposure_pct + (stake / self.current_bankroll) * 100 > self.max_exposure_pct:
            return False  # Reject bet
        
        return True  # Accept bet
```

#### Exposure por Equipa
```python
class PerTeamExposureLimit:
    def __init__(self, max_exposure_pct=3):
        self.max_exposure_pct = max_exposure_pct
        self.team_exposure = {}
    
    def check(self, team_id, stake):
        """
        Verifica se a exposição por equipa é aceitável
        """
        current_exposure = self.team_exposure.get(team_id, 0)
        exposure_pct = (current_exposure / self.current_bankroll) * 100
        
        if exposure_pct + (stake / self.current_bankroll) * 100 > self.max_exposure_pct:
            return False  # Reject bet
        
        return True  # Accept bet
```

---

## 🔄 Pipeline de Risco

### Fluxo de Decisão

```python
def evaluate_bet(risk_manager, probability, odds, game_info):
    """
    Avalia se uma aposta deve ser feita
    """
    # 1. Check Kelly Criterion
    kelly_frac = calculate_kelly_fraction(probability, odds)
    if kelly_frac <= 0:
        return {'approved': False, 'reason': 'No edge'}
    
    # 2. Calculate stake
    stake = risk_manager.calculate_stake(probability, odds)
    
    # 3. Check circuit breakers
    if not risk_manager.daily_loss_breaker.check():
        return {'approved': False, 'reason': 'Daily loss limit reached'}
    
    if not risk_manager.drawdown_breaker.check():
        return {'approved': False, 'reason': 'Drawdown limit reached'}
    
    if not risk_manager.streak_breaker.check('pending'):
        return {'approved': False, 'reason': 'Loss streak limit reached'}
    
    # 4. Check exposure limits
    if not risk_manager.game_exposure.check(stake):
        return {'approved': False, 'reason': 'Per-game exposure limit reached'}
    
    if not risk_manager.day_exposure.check(stake):
        return {'approved': False, 'reason': 'Daily exposure limit reached'}
    
    if not risk_manager.team_exposure.check(game_info['home_team'], stake):
        return {'approved': False, 'reason': 'Team exposure limit reached'}
    
    # 5. Approve bet
    return {
        'approved': True,
        'stake': stake,
        'kelly_fraction': kelly_frac
    }
```

---

## 📊 Monitorização

### Métricas de Risco

**Bankroll Metrics:**
- Bankroll atual
- Bankroll peak
- Drawdown atual
- Drawdown máximo

**Performance Metrics:**
- ROI
- Win rate
- Sharpe Ratio
- Sortino Ratio

**Risk Metrics:**
- Volatilidade
- VaR (Value at Risk)
- CVaR (Conditional VaR)
- Maximum drawdown

### Alertas

**Telegram Alerts:**
- Drawdown > 15%
- Daily loss > 4%
- Loss streak > 4
- Volatility > 2.0
- Bankroll < 80% do inicial

---

## 🚀 Configuração

### Parâmetros de Risco

```python
RISK_CONFIG = {
    # Kelly Criterion
    'kelly_fraction': 0.25,  # 25% de Kelly
    'max_stake_pct': 0.02,  # 2% do bankroll
    'min_stake_pct': 0.001,  # 0.1% do bankroll
    
    # Circuit Breakers
    'max_daily_loss_pct': 5,  # 5% do bankroll
    'max_drawdown_pct': 20,  # 20% do bankroll
    'max_loss_streak': 5,  # 5 derrotas consecutivas
    'max_volatility': 2.0,  # 2x desvio-padrão
    
    # Exposure Limits
    'max_game_exposure_pct': 5,  # 5% do bankroll
    'max_day_exposure_pct': 10,  # 10% do bankroll
    'max_team_exposure_pct': 3,  # 3% do bankroll
}
```

---

## 📝 Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Implementar todos os circuit breakers
- [ ] Adicionar exposure limits
- [ ] Criar dashboard de risco
- [ ] Adicionar alertas automáticos

### Médio Prazo (1-2 meses)
- [ ] Implementar VaR e CVaR
- [ ] Adicionar simulação Monte Carlo
- [ ] Criar stress testing
- [ ] Implementar adaptive risk

### Longo Prazo (3-6 meses)
- [ ] Multi-bankroll management
- [ ] Portfolio optimization
- [ ] Risk parity
- [ ] Dynamic risk adjustment

---

## 🔗 Links Relacionados

- [[Motor de Edge]] - Cálculo de oportunidades
- [[Sistema de Apostas]] - Execução de apostas
- [[Backtesting]] - Validação de estratégias
- [[Índice Mestre]] - Documentação completa

---

**Última atualização:** 2026-05-19  
**Responsável:** Quant Engineer  
**Status:** 🚧 Em desenvolvimento