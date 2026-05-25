# 08_Risk_Management — INDEX

**ID:** `SEC-08` | **Fase:** #phase/2-6 | **Owner:** Risk Manager + Chief Quant | **Status:** #status/active

---

## 1. OBJETIVO

Garantir a **sobrevivência da banca** acima de tudo. O sistema pode ter o melhor edge do mundo e mesmo assim falhar se a gestão de risco for negligenciada. O objetivo não é maximizar lucro, mas maximizar o crescimento seguro do capital.

**Regra de ouro:** Se não sobrevivermos aos drawdowns, nunca chegaremos ao longo prazo.

---

## 2. NOTAS FUNDAMENTAIS

- [[KELLY_FRACIONADO]] — Teoria e implementação do Kelly Criterion fracionado
- [[KELLY_CRITERIO_AUTOMATICO]] — Kelly Criterion automático com ajuste dinâmico de drawdown e volatilidade
- [[DRAWDOWN_CONTROL]] — Limites de drawdown, redução de stakes, recovery
- [[EXPOSURE_LIMITS]] — Limites por aposta, por jogo, por dia, por mercado
- [[CIRCUIT_BREAKERS]] — Condições de paragem automática
- [[VOLATILITY_REGIMES]] — Ajuste de sizing em regimes de alta/baixa volatilidade
- [[BANKROLL_SURVIVAL]] — Teoria de ruína e simulações de Monte Carlo
- [[STOP_SYSTEMS]] — Regras de pausa após sequências de perdas
- [[RECONCILIACAO]] — Verificação de que execução = plano de risco

---

## 3. FRAMEWORK DE GESTÃO DE RISCO

```
1. SIZING DA APOSTA (Kelly Fracionado)
   ├── f = K * (prob * odd - 1) / (odd - 1)
   ├── K = 0.5 (meio Kelly)
   └── Stake = f * bankroll_atual

2. LIMITES ABSOLUTOS (Hard Caps)
   ├── Max stake por aposta: 2% do bankroll
   ├── Max exposição por jogo: 4% do bankroll (soma de todos os mercados)
   ├── Max exposição diária: 12% do bankroll
   └── Max exposição por mercado: 6% do bankroll (Moneyline vs Spread)

3. CIRCUIT BREAKERS (Paragem Automática)
   ├── Drawdown > 15% desde máximo → reduzir stakes 50%
   ├── 5 perdas consecutivas → pausa 1 hora + notificação
   ├── CLV médio 3 dias < 0% → pausa de novas apostas
   ├── Feed de odds falha > 5 min → sem apostas até recuperar
   └── Erro em execução > 3 vezes num dia → paragem manual obrigatória

4. REGIMES DE VOLATILIDADE
   ├── Regime normal: sizing standard
   ├── Regime alto vol ( playoffs, mercados novos): sizing 50%
   └── Regime baixo vol (época regular estável): sizing standard

5. MONITORIZAÇÃO CONTÍNUA
   ├── Drawdown atual vs máximo permitido
   ├── Exposição diária vs limite
   ├── Número de apostas em aberto
   └── Variância esperada vs realizada
```

---

## 4. KELLY FRACIONADO — IMPLEMENTAÇÃO COMPLETA

### 4.1 Fórmula Base
```python
def kelly_fraction(prob: float, odd: float, K: float = 0.5) -> float:
    """
    K: fator de conservadorismo (0.5 = meio Kelly)
    """
    if prob * odd <= 1.0:
        return 0.0  # Sem edge, não apostar
    
    f_kelly = (prob * odd - 1.0) / (odd - 1.0)
    return K * f_kelly
```

### 4.2 Com Limites Absolutos
```python
def calculate_stake(prob: float, odd: float, bankroll: float,
                    K: float = 0.5, max_pct: float = 0.02) -> float:
    f = kelly_fraction(prob, odd, K)
    stake = f * bankroll
    
    # Hard cap
    max_stake = bankroll * max_pct
    return min(stake, max_stake)
```

### 4.3 Com Ajuste de Drawdown
```python
def calculate_stake_with_drawdown(prob: float, odd: float, bankroll: float,
                                  bankroll_peak: float,
                                  K: float = 0.5, max_pct: float = 0.02) -> float:
    drawdown = (bankroll_peak - bankroll) / bankroll_peak
    
    # Redutor de drawdown
    if drawdown > 0.15:
        K = K * 0.5  # Reduzir Kelly para um quarto
    elif drawdown > 0.10:
        K = K * 0.75
    
    f = kelly_fraction(prob, odd, K)
    stake = f * bankroll
    max_stake = bankroll * max_pct
    return min(stake, max_stake)
```

---

## 5. CIRCUIT BREAKERS — ESPECIFICAÇÃO

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| **Alpha** | Drawdown > 15% | Reduzir stakes 50% | Drawdown < 10% por 48h |
| **Beta** | 5 perdas consecutivas | Pausa 1h + alerta ops | Revisão manual obrigatória |
| **Gamma** | CLV 3d < 0% | Pausa novas apostas | CLV 3d > 1% por 24h |
| **Delta** | Feed falha > 5 min | Sem novas apostas | Feed OK por 10 min |
| **Epsilon** | Erro execução > 3x/dia | Paragem total | Fix + teste shadow |
| **Zeta** | Exposição diária > 12% | Rejeitar novos sinais | Nova sessão (dia seguinte) |

**Regra:** Todos os circuit breakers são **automáticos**. Nenhum operador humano pode sobrepor sem registo em audit log.

---

## 6. SIMULAÇÃO DE SOBREVIVÊNCIA

### 6.1 Risk of Ruin Analítico
```
R = ((1 - edge) / (1 + edge)) ^ bankroll_units

Para edge = 3%, stake média = 2%, banca = 1000€:
R ≈ 0.0001 (1 em 10,000)
```

### 6.2 Monte Carlo
```python
def monte_carlo_survival(n_sims: int = 10000, n_bets: int = 1000,
                         edge: float = 0.03, stake_pct: float = 0.02,
                         ruin_threshold: float = 0.50) -> float:
    """Retorna probabilidade de não atingir ruin_threshold da banca inicial."""
    survivors = 0
    for _ in range(n_sims):
        bankroll = 1.0
        for _ in range(n_bets):
            if random.random() < (1/2.0 + edge):  # Simplificado
                bankroll += bankroll * stake_pct * (2.0 - 1)
            else:
                bankroll -= bankroll * stake_pct
            if bankroll < ruin_threshold:
                break
        if bankroll >= ruin_threshold:
            survivors += 1
    return survivors / n_sims
```

**Target:** Probabilidade de sobrevivência após 1000 apostas > 99%.

---

## 7. IMPLEMENTAÇÃO COMPLETA

### 7.1 Script Robusto de Gestão de Risco
```python
"""
Sistema completo de gestão de risco para value betting
Inclui Kelly Criterion, circuit breakers, Monte Carlo, e limites de exposição
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CircuitBreakerStatus(Enum):
    """Status do circuit breaker"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    RECOVERING = "recovering"
    DISABLED = "disabled"

@dataclass
class RiskConfig:
    """Configuração de risco"""
    kelly_fraction: float = 0.5
    max_stake_pct: float = 0.02
    max_exposure_per_game: float = 0.04
    max_exposure_daily: float = 0.12
    max_exposure_per_market: float = 0.06
    drawdown_limit: float = 0.15
    consecutive_losses_limit: int = 5
    clv_lookback_days: int = 3
    clv_threshold: float = 0.0
    monte_carlo_sims: int = 10000
    ruin_threshold: float = 0.5

@dataclass
class Position:
    """Posição de aposta"""
    signal_id: str
    game_id: str
    market: str
    selection: str
    stake: float
    odd: float
    prob: float
    edge: float
    timestamp: datetime
    status: str = "open"

class KellyCriterion:
    """Calculadora de Kelly Criterion"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        logger.info("📐 KellyCriterion inicializado")
    
    def calculate_kelly_fraction(self, prob: float, odd: float) -> float:
        """
        Calcula fração Kelly ótima
        """
        if prob * odd <= 1.0:
            return 0.0  # Sem edge, não apostar
        
        # Fórmula Kelly: f* = (p*b - q) / b
        # onde p = probabilidade de vitória, q = probabilidade de derrota, b = odd - 1
        b = odd - 1.0
        q = 1.0 - prob
        
        f_kelly = (prob * b - q) / b
        
        # Aplicar fração de conservadorismo
        f = f_kelly * self.config.kelly_fraction
        
        return max(0.0, f)
    
    def calculate_stake(self, prob: float, odd: float, bankroll: float,
                     drawdown: float = 0.0) -> float:
        """
        Calcula stake com ajustes de risco
        """
        # Ajustar Kelly baseado em drawdown
        kelly_frac = self.config.kelly_fraction
        
        if drawdown > self.config.drawdown_limit:
            kelly_frac *= 0.25  # Reduzir para 25% em drawdown severo
            logger.warning(f"⚠️  Drawdown severo detectado: {drawdown:.2%}. Kelly reduzido para {kelly_frac:.2%}")
        elif drawdown > 0.10:
            kelly_frac *= 0.5  # Reduzir para 50% em drawdown moderado
            logger.info(f"ℹ️  Drawdown moderado: {drawdown:.2%}. Kelly reduzido para {kelly_frac:.2%}")
        
        # Calcular fração Kelly
        f = self.calculate_kelly_fraction(prob, odd)
        f_adjusted = f * kelly_frac / self.config.kelly_fraction
        
        # Calcular stake
        stake = f_adjusted * bankroll
        
        # Aplicar hard cap
        max_stake = bankroll * self.config.max_stake_pct
        stake = min(stake, max_stake)
        
        logger.info(f"📊 Stake calculado: €{stake:.2f} (Kelly: {f:.4f}, Drawdown: {drawdown:.2%})")
        
        return stake

class CircuitBreaker:
    """Sistema de circuit breakers automáticos"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.status = CircuitBreakerStatus.ACTIVE
        self.triggers = []
        self.last_trigger_time = None
        self.consecutive_losses = 0
        self.last_clv_check = None
        
        logger.info("🔒 CircuitBreaker inicializado")
    
    def check_drawdown(self, bankroll: float, peak_bankroll: float) -> bool:
        """Verifica se drawdown excede limite"""
        if peak_bankroll <= 0:
            return False
        
        drawdown = (peak_bankroll - bankroll) / peak_bankroll
        
        if drawdown > self.config.drawdown_limit:
            logger.warning(f"🚨 CIRCUIT BREAKER: Drawdown {drawdown:.2%} > limite {self.config.drawdown_limit:.2%}")
            self.trigger("drawdown", f"Drawdown {drawdown:.2%}")
            return True
        
        return False
    
    def check_consecutive_losses(self, outcome: str) -> bool:
        """Verifica sequência de perdas consecutivas"""
        if outcome == "loss":
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        if self.consecutive_losses >= self.config.consecutive_losses_limit:
            logger.warning(f"🚨 CIRCUIT BREAKER: {self.consecutive_losses} perdas consecutivas")
            self.trigger("consecutive_losses", f"{self.consecutive_losses} perdas consecutivas")
            return True
        
        return False
    
    def check_clv(self, recent_clv: float) -> bool:
        """Verifica CLV recente"""
        if recent_clv < self.config.clv_threshold:
            logger.warning(f"🚨 CIRCUIT BREAKER: CLV recente {recent_clv:.4f} < threshold {self.config.clv_threshold}")
            self.trigger("clv", f"CLV {recent_clv:.4f}")
            return True
        
        return False
    
    def check_exposure(self, daily_exposure: float) -> bool:
        """Verifica exposição diária"""
        if daily_exposure > self.config.max_exposure_daily:
            logger.warning(f"🚨 CIRCUIT BREAKER: Exposição diária {daily_exposure:.2%} > limite {self.config.max_exposure_daily:.2%}")
            self.trigger("exposure", f"Exposição {daily_exposure:.2%}")
            return True
        
        return False
    
    def trigger(self, trigger_type: str, description: str):
        """Ativa circuit breaker"""
        self.status = CircuitBreakerStatus.TRIGGERED
        self.last_trigger_time = datetime.now()
        
        trigger_info = {
            'type': trigger_type,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'status': 'triggered'
        }
        
        self.triggers.append(trigger_info)
        
        logger.error(f"🔒 Circuit breaker ATIVADO: {trigger_type} - {description}")
    
    def can_trade(self) -> bool:
        """Verifica se pode fazer novas apostas"""
        if self.status == CircuitBreakerStatus.ACTIVE:
            return True
        
        if self.status == CircuitBreakerStatus.TRIGGERED:
            # Verificar se já passou tempo suficiente para recovery
            if self.last_trigger_time:
                elapsed = (datetime.now() - self.last_trigger_time).total_seconds()
                if elapsed > 3600:  # 1 hora
                    self.status = CircuitBreakerStatus.RECOVERING
                    logger.info("🔄 Circuit breaker em recovery")
                else:
                    return False
        
        if self.status == CircuitBreakerStatus.RECOVERING:
            # Verificar condições de recovery
            if self._check_recovery_conditions():
                self.status = CircuitBreakerStatus.ACTIVE
                logger.info("✅ Circuit breaker resetado")
                return True
            else:
                return False
        
        return False
    
    def _check_recovery_conditions(self) -> bool:
        """Verifica condições para recovery"""
        # Simplificado - em produção, verificar métricas reais
        return True
    
    def get_status(self) -> Dict:
        """Retorna status do circuit breaker"""
        return {
            'status': self.status.value,
            'can_trade': self.can_trade(),
            'triggers': self.triggers,
            'consecutive_losses': self.consecutive_losses
        }

class MonteCarloSimulator:
    """Simulador de Monte Carlo para análise de sobrevivência"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        logger.info("🎲 MonteCarloSimulator inicializado")
    
    def simulate(self, n_sims: int = None, n_bets: int = 1000,
                edge: float = 0.03, win_prob: float = 0.5,
                stake_pct: float = None, bankroll: float = 1000.0) -> Dict:
        """
        Executa simulação de Monte Carlo
        """
        if n_sims is None:
            n_sims = self.config.monte_carlo_sims
        
        if stake_pct is None:
            stake_pct = self.config.max_stake_pct
        
        logger.info(f"🎲 Executando Monte Carlo: {n_sims} simulações, {n_bets} apostas")
        
        final_bankrolls = []
        max_drawdowns = []
        survivors = 0
        
        for sim in range(n_sims):
            current_bankroll = bankroll
            peak_bankroll = bankroll
            sim_max_dd = 0.0
            
            for bet in range(n_bets):
                # Simular resultado da aposta
                if np.random.random() < (win_prob + edge):
                    # Vitória
                    profit = current_bankroll * stake_pct
                    current_bankroll += profit
                else:
                    # Derrota
                    loss = current_bankroll * stake_pct
                    current_bankroll -= loss
                
                # Atualizar peak e drawdown
                if current_bankroll > peak_bankroll:
                    peak_bankroll = current_bankroll
                
                drawdown = (peak_bankroll - current_bankroll) / peak_bankroll
                sim_max_dd = max(sim_max_dd, drawdown)
                
                # Verificar ruína
                if current_bankroll < bankroll * self.config.ruin_threshold:
                    break
            
            final_bankrolls.append(current_bankroll)
            max_drawdowns.append(sim_max_dd)
            
            if current_bankroll >= bankroll * self.config.ruin_threshold:
                survivors += 1
        
        # Calcular estatísticas
        survival_rate = survivors / n_sims
        avg_final_bankroll = np.mean(final_bankrolls)
        median_final_bankroll = np.median(final_bankrolls)
        avg_max_drawdown = np.mean(max_drawdowns)
        
        logger.info(f"✅ Monte Carlo completo:")
        logger.info(f"   Taxa de sobrevivência: {survival_rate:.2%}")
        logger.info(f"   Banca final média: €{avg_final_bankroll:.2f}")
        logger.info(f"   Drawdown médio: {avg_max_drawdown:.2%}")
        
        return {
            'survival_rate': survival_rate,
            'avg_final_bankroll': avg_final_bankroll,
            'median_final_bankroll': median_final_bankroll,
            'avg_max_drawdown': avg_max_drawdown,
            'final_bankrolls': final_bankrolls,
            'max_drawdowns': max_drawdowns,
            'n_sims': n_sims,
            'n_bets': n_bets
        }

class RiskManager:
    """Gestor de risco principal"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.kelly = KellyCriterion(config)
        self.circuit_breaker = CircuitBreaker(config)
        self.monte_carlo = MonteCarloSimulator(config)
        
        # Estado atual
        self.bankroll = 1000.0
        self.peak_bankroll = 1000.0
        self.daily_exposure = 0.0
        self.positions = []
        self.bet_history = []
        
        logger.info("🛡️  RiskManager inicializado")
    
    def calculate_stake(self, prob: float, odd: float, game_id: str,
                       market: str) -> float:
        """
        Calcula stake com todas as verificações de risco
        """
        logger.info(f"📊 Calculando stake para {game_id} - {market}")
        
        # Verificar circuit breaker
        if not self.circuit_breaker.can_trade():
            logger.warning("❌ Trading bloqueado por circuit breaker")
            return 0.0
        
        # Verificar exposição diária
        if self.daily_exposure >= self.config.max_exposure_daily:
            logger.warning(f"❌ Exposição diária {self.daily_exposure:.2%} >= limite {self.config.max_exposure_daily:.2%}")
            return 0.0
        
        # Verificar exposição por jogo
        game_exposure = sum(p.stake for p in self.positions if p.game_id == game_id)
        max_game_stake = self.bankroll * self.config.max_exposure_per_game - game_exposure
        
        if max_game_stake <= 0:
            logger.warning(f"❌ Exposição por jogo {game_id} excedida")
            return 0.0
        
        # Verificar exposição por mercado
        market_exposure = sum(p.stake for p in self.positions if p.market == market)
        max_market_stake = self.bankroll * self.config.max_exposure_per_market - market_exposure
        
        if max_market_stake <= 0:
            logger.warning(f"❌ Exposição por mercado {market} excedida")
            return 0.0
        
        # Calcular drawdown atual
        drawdown = (self.peak_bankroll - self.bankroll) / self.peak_bankroll if self.peak_bankroll > 0 else 0.0
        
        # Calcular stake via Kelly
        stake = self.kelly.calculate_stake(prob, odd, self.bankroll, drawdown)
        
        # Aplicar limites de exposição
        stake = min(stake, max_game_stake, max_market_stake)
        stake = min(stake, self.bankroll * self.config.max_stake_pct)
        
        logger.info(f"✅ Stake aprovado: €{stake:.2f}")
        
        return stake
    
    def add_position(self, position: Position):
        """Adiciona nova posição"""
        self.positions.append(position)
        self.daily_exposure += position.stake / self.bankroll
        
        logger.info(f"📈 Posição adicionada: {position.signal_id} - €{position.stake:.2f}")
    
    def close_position(self, signal_id: str, outcome: str, pnl: float):
        """Fecha posição e atualiza métricas"""
        # Encontrar posição
        position = next((p for p in self.positions if p.signal_id == signal_id), None)
        
        if position:
            position.status = "closed"
            
            # Atualizar bankroll
            self.bankroll += pnl
            
            # Atualizar peak
            if self.bankroll > self.peak_bankroll:
                self.peak_bankroll = self.bankroll
            
            # Verificar circuit breaker
            self.circuit_breaker.check_drawdown(self.bankroll, self.peak_bankroll)
            self.circuit_breaker.check_consecutive_losses(outcome)
            
            # Registrar no histórico
            self.bet_history.append({
                'signal_id': signal_id,
                'outcome': outcome,
                'pnl': pnl,
                'bankroll': self.bankroll,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"📊 Posição fechada: {signal_id} - PnL: €{pnl:.2f} - Banca: €{self.bankroll:.2f}")
    
    def get_status(self) -> Dict:
        """Retorna status completo do sistema de risco"""
        return {
            'bankroll': self.bankroll,
            'peak_bankroll': self.peak_bankroll,
            'drawdown': (self.peak_bankroll - self.bankroll) / self.peak_bankroll if self.peak_bankroll > 0 else 0.0,
            'daily_exposure': self.daily_exposure,
            'n_open_positions': len([p for p in self.positions if p.status == "open"]),
            'circuit_breaker': self.circuit_breaker.get_status(),
            'total_bets': len(self.bet_history),
            'total_pnl': sum(b['pnl'] for b in self.bet_history)
        }
    
    def run_monte_carlo(self, n_sims: int = 10000, n_bets: int = 1000) -> Dict:
        """Executa simulação de Monte Carlo"""
        return self.monte_carlo.simulate(n_sims, n_bets)

# Uso
if __name__ == "__main__":
    # Configuração
    config = RiskConfig()
    
    # Criar risk manager
    risk_manager = RiskManager(config)
    
    # Exemplo de uso
    prob = 0.58
    odd = 1.85
    game_id = "0022300001"
    market = "moneyline"
    
    # Calcular stake
    stake = risk_manager.calculate_stake(prob, odd, game_id, market)
    
    if stake > 0:
        # Criar posição
        position = Position(
            signal_id="SIG-001",
            game_id=game_id,
            market=market,
            selection="Celtics",
            stake=stake,
            odd=odd,
            prob=prob,
            edge=prob * odd - 1,
            timestamp=datetime.now()
        )
        
        risk_manager.add_position(position)
        
        # Simular resultado
        outcome = "win"
        pnl = stake * (odd - 1)
        risk_manager.close_position("SIG-001", outcome, pnl)
    
    # Verificar status
    status = risk_manager.get_status()
    print(f"Status: {status}")
    
    # Monte Carlo
    mc_result = risk_manager.run_monte_carlo(n_sims=1000, n_bets=500)
    print(f"Taxa de sobrevivência: {mc_result['survival_rate']:.2%}")
```

---

## 8. BACKLOG TÉCNICO
x] Documentar Kelly Criterion automático
- [
- [ ] Implementar cálculo de Kelly com limites absolutos
- [ ] Criar módulo de circuit breakers automáticos
- [ ] Implementar simulação de Monte Carlo para bankroll
- [ ] Criar dashboard de drawdown e exposição em tempo real
- [ ] Implementar ajuste dinâmico de K baseado em volatilidade recente
- [ ] Criar sistema de alertas para aproximação a limites
- [ ] Documentar SOP de intervenção manual em circuit breaker

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[07_Value_Detection/INDEX]] → Motor de edge que gera sinais
- [[09_Execution_System/INDEX]] → Onde o risco encontra a realidade
- [[22_Real_Money_Operations/INDEX]] → Operações com dinheiro real
- [[37_CLV_Analytics/INDEX]] → Métricas que validam o edge real
- [[28_Failure_Scenarios/INDEX]] → Cenários de falha do sistema de risco
