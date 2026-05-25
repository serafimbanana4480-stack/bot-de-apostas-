# MULTI-SPORT INTEGRATION — Motor de Decisão Unificado

**ID:** `SEC-43-03` | **Status:** #status/pending | **Versão:** `2.0.0-UNIFIED`

---

## 1. OBJETIVO

Criar motor de decisão unificado que agrega sinais de múltiplos desportos com gestão de risco global.

---

## 2. ARQUITETURA UNIFICADA

```
┌─────────────────────────────────────────────────────────────┐
│                  MODELOS POR DESPORTO                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   NBA    │  │ Football  │  │   MMA    │                 │
│  │ Ensemble │  │ Poisson+ML│  │ Bayesian │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
└───────┼──────────────┼──────────────┼───────────────────────┘
        │              │              │
        ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              MOTOR DE DECISÃO UNIFICADO                      │
│  1. Agregar sinais por desporto                             │
│  2. Aplicar filtros globais                                 │
│  3. Calcular stake por desporto                             │
│  4. Verificar limites de exposição global                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              GESTÃO DE RISCO GLOBAL                           │
│  - Limite por desporto                                      │
│  - Limite de exposição total                               │
│  - Circuit breaker global                                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              EXECUÇÃO UNIFICADA                               │
│  - Priorizar sinais por edge                                │
│  - Distribuir capital                                      │
│  - Executar via Betfair API                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. MOTOR DE DECISÃO UNIFICADO

### 3.1 Agregação de Sinais

```python
class UnifiedDecisionEngine:
    """
    Motor de decisão unificado para múltiplos desportos.
    """
    def __init__(self):
        self.sport_models = {
            'NBA': NBAEnsembleModel(),
            'Football': FootballHybridModel(),
            'MMA': MMABayesianModel()
        }
        self.signal_queue = []
    
    def generate_signals(self, market_data):
        """
        Gera sinais de todos os desportos disponíveis.
        """
        all_signals = []
        
        for sport, model in self.sport_models.items():
            sport_markets = market_data.get(sport, [])
            
            for market in sport_markets:
                signal = model.predict(market)
                if signal['edge'] > 0.04:  # Filtro de edge mínimo
                    signal['sport'] = sport
                    all_signals.append(signal)
        
        return all_signals
    
    def rank_signals(self, signals):
        """
        Ordena sinais por edge e confiança.
        """
        for signal in signals:
            # Score = edge × confiança × ajuste_volatilidade
            signal['score'] = (
                signal['edge'] * 
                signal['confidence'] * 
                self.get_volatility_adjustment(signal['sport'])
            )
        
        # Ordenar por score descendente
        ranked_signals = sorted(signals, key=lambda x: x['score'], reverse=True)
        
        return ranked_signals
    
    def get_volatility_adjustment(self, sport):
        """
        Retorna ajuste de volatilidade por desporto.
        """
        volatility_factors = {
            'NBA': 1.0,
            'Football': 0.9,
            'MMA': 0.7  # Mais volátil, reduzir peso
        }
        return volatility_factors.get(sport, 0.8)
```

### 3.2 Alocação de Capital por Desporto

```python
class GlobalCapitalAllocator:
    """
    Aloca capital entre desportos baseado em edge e volatilidade.
    """
    def __init__(self):
        self.sport_allocations = {
            'NBA': 0.50,      # 50% para NBA (edge mais estável)
            'Football': 0.30,  # 30% para Football
            'MMA': 0.20        # 20% para MMA (edge mais alto mas volátil)
        }
        self.sport_limits = {
            'NBA': 0.02,       # 2% da banca por aposta NBA
            'Football': 0.015,  # 1.5% da banca por aposta Football
            'MMA': 0.01        # 1% da banca por aposta MMA
        }
    
    def calculate_sport_stake(self, signal, bankroll):
        """
        Calcula stake para uma aposta considerando limites por desporto.
        """
        sport = signal['sport']
        edge = signal['edge']
        
        # Stake base usando Kelly fracionado
        base_stake = kelly_fraction(edge, bankroll)
        
        # Aplicar limite por desporto
        max_stake = self.sport_limits[sport] * bankroll
        sport_stake = min(base_stake, max_stake)
        
        # Ajustar por alocação de capital disponível
        available_capital = bankroll * self.sport_allocations[sport]
        used_capital = get_used_capital(sport)
        remaining_capital = available_capital - used_capital
        
        if sport_stake > remaining_capital:
            sport_stake = remaining_capital
        
        return sport_stake
    
    def get_used_capital(self, sport):
        """
        Retorna capital já alocado para um desporto.
        """
        # Consultar BD para somar stakes ativos
        return sum_active_stakes(sport)
```

---

## 4. GESTÃO DE RISCO GLOBAL

### 4.1 Limites por Desporto

```python
class GlobalRiskManager:
    """
    Gestão de risco global multi-desporto.
    """
    def __init__(self):
        self.sport_limits = {
            'NBA': {
                'max_daily_exposure': 0.03,      # 3% da banca por dia
                'max_active_bets': 5,            # Máximo 5 apostas simultâneas
                'max_drawdown': 0.10            # 10% drawdown antes de pausa
            },
            'Football': {
                'max_daily_exposure': 0.02,      # 2% da banca por dia
                'max_active_bets': 3,
                'max_drawdown': 0.12
            },
            'MMA': {
                'max_daily_exposure': 0.015,     # 1.5% da banca por dia
                'max_active_bets': 2,
                'max_drawdown': 0.15
            }
        }
        
        self.global_limits = {
            'max_total_exposure': 0.05,         # 5% da banca total por dia
            'max_active_bets': 10,              # Máximo 10 apostas simultâneas
            'max_global_drawdown': 0.15,        # 15% drawdown global antes de pausa
            'max_loss_streak': 10               # 10 perdas consecutivas
        }
    
    def check_sport_limits(self, signal, bankroll):
        """
        Verifica se aposta respeita limites do desporto.
        """
        sport = signal['sport']
        limits = self.sport_limits[sport]
        
        # Verificar exposição diária
        daily_exposure = get_daily_exposure(sport)
        if daily_exposure + signal['stake'] > limits['max_daily_exposure'] * bankroll:
            return False, "Excede exposição diária do desporto"
        
        # Verificar número de apostas ativas
        active_bets = count_active_bets(sport)
        if active_bets >= limits['max_active_bets']:
            return False, "Número máximo de apostas ativas atingido"
        
        # Verificar drawdown do desporto
        sport_drawdown = calculate_sport_drawdown(sport)
        if sport_drawdown > limits['max_drawdown']:
            return False, f"Drawdown do desporto excede {limits['max_drawdown']*100}%"
        
        return True, "OK"
    
    def check_global_limits(self, bankroll):
        """
        Verifica limites globais do sistema.
        """
        # Verificar exposição total
        total_exposure = get_total_exposure()
        if total_exposure > self.global_limits['max_total_exposure'] * bankroll:
            return False, "Excede exposição total global"
        
        # Verificar número total de apostas
        total_active_bets = count_total_active_bets()
        if total_active_bets >= self.global_limits['max_active_bets']:
            return False, "Número máximo de apostas globais atingido"
        
        # Verificar drawdown global
        global_drawdown = calculate_global_drawdown()
        if global_drawdown > self.global_limits['max_global_drawdown']:
            return False, f"Drawdown global excede {self.global_limits['max_global_drawdown']*100}%"
        
        # Verificar loss streak
        loss_streak = get_loss_streak()
        if loss_streak >= self.global_limits['max_loss_streak']:
            return False, f"Loss streak de {loss_streak} apostas"
        
        return True, "OK"
    
    def trigger_circuit_breaker(self, reason):
        """
        Ativa circuit breaker global.
        """
        # Pausar todas as estratégias não-garantidas
        pause_all_strategies()
        
        # Enviar alerta
        send_emergency_alert(f"CIRCUIT BREAKER: {reason}")
        
        # Registar evento
        log_circuit_breaker_event(reason)
```

---

## 5. PIPELINE UNIFICADO

```python
class UnifiedBettingPipeline:
    """
    Pipeline unificado de apostas multi-desporto.
    """
    def __init__(self):
        self.decision_engine = UnifiedDecisionEngine()
        self.capital_allocator = GlobalCapitalAllocator()
        self.risk_manager = GlobalRiskManager()
        self.executor = BetfairExecutor()
    
    def run_pipeline(self, market_data, bankroll):
        """
        Executa pipeline completo de decisão e execução.
        """
        # 1. Verificar limites globais
        global_ok, global_msg = self.risk_manager.check_global_limits(bankroll)
        if not global_ok:
            self.risk_manager.trigger_circuit_breaker(global_msg)
            return
        
        # 2. Gerar sinais de todos os desportos
        all_signals = self.decision_engine.generate_signals(market_data)
        
        # 3. Ordenar sinais por score
        ranked_signals = self.decision_engine.rank_signals(all_signals)
        
        # 4. Processar sinais em ordem
        for signal in ranked_signals:
            # 4.1 Calcular stake
            stake = self.capital_allocator.calculate_sport_stake(signal, bankroll)
            signal['stake'] = stake
            
            # 4.2 Verificar limites do desporto
            sport_ok, sport_msg = self.risk_manager.check_sport_limits(signal, bankroll)
            if not sport_ok:
                continue  # Pular este sinal
            
            # 4.3 Executar aposta
            try:
                order_result = self.executor.place_order(signal)
                
                # 4.4 Registar aposta
                register_bet(signal, order_result)
                
            except Exception as e:
                log_error(f"Erro ao executar aposta: {e}")
                continue
```

---

## 6. MONITORIZAÇÃO GLOBAL

### 6.1 Métricas por Desporto

```python
def get_sport_metrics(sport):
    """
    Obtém métricas agregadas por desporto.
    """
    return {
        'total_bets': count_total_bets(sport),
        'win_rate': calculate_win_rate(sport),
        'roi': calculate_roi(sport),
        'clv': calculate_clv(sport),
        'current_exposure': get_current_exposure(sport),
        'drawdown': calculate_sport_drawdown(sport),
        'sharpe_ratio': calculate_sharpe(sport)
    }
```

### 6.2 Dashboard Unificado

```python
def generate_unified_dashboard():
    """
    Gera dashboard unificado com métricas de todos os desportos.
    """
    dashboard = {
        'global': {
            'total_bankroll': get_total_bankroll(),
            'total_exposure': get_total_exposure(),
            'global_drawdown': calculate_global_drawdown(),
            'loss_streak': get_loss_streak()
        },
        'sports': {
            'NBA': get_sport_metrics('NBA'),
            'Football': get_sport_metrics('Football'),
            'MMA': get_sport_metrics('MMA')
        },
        'active_bets': list_active_bets(),
        'alerts': get_recent_alerts()
    }
    
    return dashboard
```

---

## 7. CRONOGRAMA DE IMPLEMENTAÇÃO

**Mês 9:** Desenvolvimento de motor de decisão unificado
**Mês 10:** Implementação de gestão de risco global
**Mês 11:** Teste de integração multi-desporto
**Mês 12:** Produção com 3 desportos operacionais

---

## 8. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| Latência de decisão | < 500ms |
| Taxa de execução | > 95% |
| ROI global | > 15% |
| Sharpe global | > 0.8 |
| Correlação entre desportos | < 0.3 (diversificação) |
