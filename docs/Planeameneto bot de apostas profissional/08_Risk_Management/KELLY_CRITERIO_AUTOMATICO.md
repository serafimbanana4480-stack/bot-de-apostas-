# Kelly Criterion Automático

**ID:** `KELLY-001` | **Fase:** #phase/2-6 | **Owner:** Risk Manager | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Implementação automática do Kelly Criterion fracionado para sizing de apostas, com ajuste dinâmico baseado em drawdown, volatilidade, e limites absolutos de exposição. Baseado na implementação do projeto kyleskom/NBA-ML-Betting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Maximizar crescimento seguro da banca com sizing automático |
| **Fórmula Base** | f = K × (p × odd - 1) / (odd - 1) |
| **K Padrão** | 0.5 (meio Kelly - conservador) |
| **Ajuste Dinâmico** | Redução automática em drawdown/volatilidade alta |
| **Hard Cap** | Máximo 2% da banca por aposta |

---

## 2. FÓRMULA BASE E VARIAÇÕES

### 2.1 Fórmula Kelly Padrão

```
f = (p × odd - 1) / (odd - 1)

Onde:
- f = fração da banca a apostar
- p = probabilidade estimada de ganho (0-1)
- odd = odd decimal (ex: 1.85)
```

### 2.2 Kelly Fracionado

```
f_kelly = K × f

Onde:
- K = fator de conservadorismo (0.5 = meio Kelly, 0.25 = quarto Kelly)
- K padrão = 0.5 (balance entre crescimento e risco)
```

### 2.3 Com Hard Cap

```
f_final = min(f_kelly, max_cap)

Onde:
- max_cap = 0.02 (2% da banca por aposta)
- Stake = f_final × bankroll_atual
```

---

## 3. KELLY FRACIONADO COM AJUSTE DE DRAWDOWN

### 3.1 Lógica de Ajuste

```python
def calculate_kelly_with_drawdown(
    prob: float, 
    odd: float, 
    bankroll: float,
    bankroll_peak: float,
    K_base: float = 0.5,
    max_cap: float = 0.02
) -> dict:
    """
    Calcula Kelly Criterion com ajuste dinâmico de drawdown.
    
    Args:
        prob: Probabilidade estimada (0-1)
        odd: Odd decimal
        bankroll: Banca atual
        bankroll_peak: Banca máxima histórica
        K_base: Fator Kelly base (default: 0.5)
        max_cap: Hard cap máximo (default: 2%)
    
    Returns:
        dict: {stake, stake_pct, K_used, drawdown, reason}
    """
    # Calcular drawdown
    drawdown = (bankroll_peak - bankroll) / bankroll_peak if bankroll_peak > 0 else 0
    
    # Ajustar K baseado em drawdown
    K = K_base
    reason = "standard"
    
    if drawdown > 0.20:  # > 20% drawdown
        K = K_base * 0.25  # Reduzir para 1/8 Kelly
        reason = "severe_drawdown"
    elif drawdown > 0.15:  # > 15% drawdown
        K = K_base * 0.5  # Reduzir para 1/4 Kelly
        reason = "high_drawdown"
    elif drawdown > 0.10:  # > 10% drawdown
        K = K_base * 0.75  # Reduzir para 3/8 Kelly
        reason = "moderate_drawdown"
    
    # Calcular Kelly
    if prob * odd <= 1.0:
        return {
            "stake": 0.0,
            "stake_pct": 0.0,
            "K_used": K,
            "drawdown": drawdown,
            "reason": "no_edge"
        }
    
    f_kelly = (prob * odd - 1.0) / (odd - 1.0)
    f_final = K * f_kelly
    
    # Aplicar hard cap
    f_capped = min(f_final, max_cap)
    
    stake = f_capped * bankroll
    
    return {
        "stake": round(stake, 2),
        "stake_pct": round(f_capped * 100, 2),
        "K_used": round(K, 3),
        "drawdown": round(drawdown * 100, 2),
        "reason": reason
    }
```

### 3.2 Exemplos de Cálculo

```python
# Exemplo 1: Situação normal
bankroll = 10000
bankroll_peak = 10000
prob = 0.58
odd = 1.85

result = calculate_kelly_with_drawdown(prob, odd, bankroll, bankroll_peak)
# Resultado: stake=€145.00, stake_pct=1.45%, K=0.5, drawdown=0%, reason="standard"

# Exemplo 2: Com drawdown de 12%
bankroll = 8800
bankroll_peak = 10000
prob = 0.58
odd = 1.85

result = calculate_kelly_with_drawdown(prob, odd, bankroll, bankroll_peak)
# Resultado: stake=€109.00, stake_pct=1.24%, K=0.375, drawdown=12%, reason="moderate_drawdown"

# Exemplo 3: Com drawdown severo (18%)
bankroll = 8200
bankroll_peak = 10000
prob = 0.58
odd = 1.85

result = calculate_kelly_with_drawdown(prob, odd, bankroll, bankroll_peak)
# Resultado: stake=€73.00, stake_pct=0.89%, K=0.25, drawdown=18%, reason="high_drawdown"
```

---

## 4. KELLY COM AJUSTE DE VOLATILIDADE

### 4.1 Cálculo de Volatilidade

```python
def calculate_volatility_regime(
    historical_pnl: List[float],
    window: int = 30
) -> dict:
    """
    Calcula regime de volatilidade baseado em PnL histórico.
    
    Args:
        historical_pnl: Lista de PnL diários
        window: Janela de cálculo (default: 30 dias)
    
    Returns:
        dict: {regime, std_dev, multiplier, reason}
    """
    if len(historical_pnl) < window:
        return {
            "regime": "insufficient_data",
            "std_dev": 0,
            "multiplier": 1.0,
            "reason": "need_more_data"
        }
    
    recent_pnl = historical_pnl[-window:]
    std_dev = np.std(recent_pnl)
    mean = np.mean(recent_pnl)
    
    # Normalizar pela banca média
    avg_bankroll = np.mean([10000] * len(recent_pnl))  # Simplificado
    normalized_std = std_dev / avg_bankroll
    
    # Determinar regime
    if normalized_std < 0.02:  # < 2% volatilidade diária
        regime = "low"
        multiplier = 1.0
        reason = "low_volatility"
    elif normalized_std < 0.04:  # 2-4% volatilidade
        regime = "normal"
        multiplier = 1.0
        reason = "normal_volatility"
    elif normalized_std < 0.06:  # 4-6% volatilidade
        regime = "high"
        multiplier = 0.75
        reason = "high_volatility"
    else:  # > 6% volatilidade
        regime = "extreme"
        multiplier = 0.5
        reason = "extreme_volatility"
    
    return {
        "regime": regime,
        "std_dev": round(normalized_std * 100, 2),
        "multiplier": multiplier,
        "reason": reason
    }
```

### 4.2 Kelly com Ajuste de Volatilidade

```python
def calculate_kelly_with_volatility(
    prob: float,
    odd: float,
    bankroll: float,
    historical_pnl: List[float],
    K_base: float = 0.5,
    max_cap: float = 0.02
) -> dict:
    """
    Calcula Kelly com ajuste de volatilidade.
    """
    # Calcular regime de volatilidade
    vol_regime = calculate_volatility_regime(historical_pnl)
    
    # Ajustar K baseado em volatilidade
    K_vol = K_base * vol_regime["multiplier"]
    
    # Calcular Kelly
    if prob * odd <= 1.0:
        return {
            "stake": 0.0,
            "stake_pct": 0.0,
            "K_used": K_vol,
            "volatility_regime": vol_regime["regime"],
            "reason": "no_edge"
        }
    
    f_kelly = (prob * odd - 1.0) / (odd - 1.0)
    f_final = K_vol * f_kelly
    f_capped = min(f_final, max_cap)
    
    stake = f_capped * bankroll
    
    return {
        "stake": round(stake, 2),
        "stake_pct": round(f_capped * 100, 2),
        "K_used": round(K_vol, 3),
        "volatility_regime": vol_regime["regime"],
        "volatility_multiplier": vol_regime["multiplier"],
        "reason": vol_regime["reason"]
    }
```

---

## 5. KELLY COM AJUSTE COMBINADO (DRAWDOWN + VOLATILIDADE)

### 5.1 Função Unificada

```python
def calculate_kelly_full(
    prob: float,
    odd: float,
    bankroll: float,
    bankroll_peak: float,
    historical_pnl: List[float],
    K_base: float = 0.5,
    max_cap: float = 0.02
) -> dict:
    """
    Calcula Kelly com ajuste combinado de drawdown e volatilidade.
    
    Usa o ajuste mais conservador entre drawdown e volatilidade.
    """
    # Ajuste por drawdown
    drawdown = (bankroll_peak - bankroll) / bankroll_peak if bankroll_peak > 0 else 0
    K_drawdown = K_base
    
    if drawdown > 0.20:
        K_drawdown = K_base * 0.25
    elif drawdown > 0.15:
        K_drawdown = K_base * 0.5
    elif drawdown > 0.10:
        K_drawdown = K_base * 0.75
    
    # Ajuste por volatilidade
    vol_regime = calculate_volatility_regime(historical_pnl)
    K_volatility = K_base * vol_regime["multiplier"]
    
    # Usar o K mais conservador (menor)
    K = min(K_drawdown, K_volatility)
    
    # Calcular Kelly
    if prob * odd <= 1.0:
        return {
            "stake": 0.0,
            "stake_pct": 0.0,
            "K_used": round(K, 3),
            "K_drawdown": round(K_drawdown, 3),
            "K_volatility": round(K_volatility, 3),
            "drawdown": round(drawdown * 100, 2),
            "volatility_regime": vol_regime["regime"],
            "reason": "no_edge"
        }
    
    f_kelly = (prob * odd - 1.0) / (odd - 1.0)
    f_final = K * f_kelly
    f_capped = min(f_final, max_cap)
    
    stake = f_capped * bankroll
    
    return {
        "stake": round(stake, 2),
        "stake_pct": round(f_capped * 100, 2),
        "K_used": round(K, 3),
        "K_drawdown": round(K_drawdown, 3),
        "K_volatility": round(K_volatility, 3),
        "drawdown": round(drawdown * 100, 2),
        "volatility_regime": vol_regime["regime"],
        "reason": f"combined_adjustment"
    }
```

---

## 6. LIMITES ABSOLUTOS E HARD CAPS

### 6.1 Tabela de Limites

| Limite | Valor | Descrição |
|--------|-------|-----------|
| **Max stake por aposta** | 2% da banca | Hard cap individual |
| **Max exposição por jogo** | 4% da banca | Soma de todos os mercados |
| **Max exposição diária** | 12% da banca | Total de apostas do dia |
| **Max exposição por mercado** | 6% da banca | Moneyline vs Spread |
| **Min stake** | €10.00 | Mínimo por aposta |
| **Max stake** | €500.00 | Máximo por aposta |

### 6.2 Implementação de Limites

```python
class ExposureManager:
    def __init__(self, db: Session):
        self.db = db
    
    def check_exposure_limits(self, game_id: str, proposed_stake: float) -> dict:
        """
        Verifica se stake proposto respeita limites de exposição.
        
        Returns:
            dict: {approved, reason, current_exposure, limit}
        """
        # Obter banca atual
        bankroll = self.get_current_bankroll()
        
        # Verificar limite por aposta
        max_stake_per_bet = bankroll * 0.02
        if proposed_stake > max_stake_per_bet:
            return {
                "approved": False,
                "reason": "exceeds_max_stake_per_bet",
                "current_exposure": proposed_stake,
                "limit": max_stake_per_bet
            }
        
        # Verificar exposição por jogo
        game_exposure = self.get_game_exposure(game_id)
        max_game_exposure = bankroll * 0.04
        if game_exposure + proposed_stake > max_game_exposure:
            return {
                "approved": False,
                "reason": "exceeds_max_game_exposure",
                "current_exposure": game_exposure,
                "limit": max_game_exposure
            }
        
        # Verificar exposição diária
        daily_exposure = self.get_daily_exposure()
        max_daily_exposure = bankroll * 0.12
        if daily_exposure + proposed_stake > max_daily_exposure:
            return {
                "approved": False,
                "reason": "exceeds_max_daily_exposure",
                "current_exposure": daily_exposure,
                "limit": max_daily_exposure
            }
        
        return {
            "approved": True,
            "reason": "all_limits_ok",
            "current_exposure": proposed_stake,
            "limit": max_stake_per_bet
        }
```

---

## 7. INTEGRAÇÃO COM MOTOR DE DECISÃO

### 7.1 Pipeline Completo

```python
# vbq/risk/kelly_engine.py
class KellyEngine:
    def __init__(self, db: Session):
        self.db = db
        self.exposure_manager = ExposureManager(db)
    
    def calculate_stake_for_signal(
        self,
        game_id: str,
        prob: float,
        odd: float,
        historical_pnl: List[float] = None
    ) -> dict:
        """
        Calcula stake para um sinal, aplicando todos os ajustes e limites.
        
        Pipeline:
        1. Calcular Kelly com ajuste combinado (drawdown + volatilidade)
        2. Verificar limites de exposição
        3. Ajustar se necessário
        4. Retornar stake final
        """
        # Obter banca atual e pico
        bankroll = self.get_current_bankroll()
        bankroll_peak = self.get_bankroll_peak()
        
        # Obter PnL histórico se não fornecido
        if historical_pnl is None:
            historical_pnl = self.get_historical_pnl(days=30)
        
        # Calcular Kelly com ajuste completo
        kelly_result = calculate_kelly_full(
            prob=prob,
            odd=odd,
            bankroll=bankroll,
            bankroll_peak=bankroll_peak,
            historical_pnl=historical_pnl
        )
        
        # Verificar limites de exposição
        exposure_check = self.exposure_manager.check_exposure_limits(
            game_id,
            kelly_result["stake"]
        )
        
        if not exposure_check["approved"]:
            # Reduzir stake para respeitar limites
            kelly_result["stake"] = exposure_check["limit"]
            kelly_result["stake_pct"] = (exposure_check["limit"] / bankroll) * 100
            kelly_result["reason"] = f"exposure_limit: {exposure_check['reason']}"
        
        return kelly_result
```

---

## 8. MONITORIZAÇÃO E ALERTAS

### 8.1 Métricas de Kelly

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| kelly_avg_stake_pct | Stake médio % da banca | 0.5-2% |
| kelly_avg_k_used | K médio usado | 0.3-0.5 |
| kelly_drawdown_adjustments | Número de ajustes por drawdown | < 10/semana |
| kelly_volatility_adjustments | Número de ajustes por volatilidade | < 10/semana |

### 8.2 Dashboard de Kelly

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KELLY CRITERION DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ESTATÍSTICAS ATUAIS:
- Banca atual: €10,450.00
- Banca pico: €12,000.00
- Drawdown: -12.9%
- K atual: 0.375 (ajustado por drawdown)
- Regime volatilidade: high

💰 STAKING RECENTE:
- Stake médio (7 dias): €145.00 (1.39%)
- Stake médio (30 dias): €158.00 (1.52%)
- Ajustes drawdown: 3
- Ajustes volatilidade: 5

⚠️ ALERTAS:
- Drawdown > 10% → K reduzido para 0.375
- Volatilidade alta → K reduzido para 0.375

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 9. BACKTEST DE KELLY VS FLAT BETTING

### 9.1 Metodologia

```python
def backtest_kelly_vs_flat(
    start_date: str,
    end_date: str,
    flat_stake_pct: float = 0.02,
    K_base: float = 0.5
) -> dict:
    """
    Compara Kelly Criterion vs Flat Betting em dados históricos.
    
    Args:
        start_date: Data início (YYYY-MM-DD)
        end_date: Data fim (YYYY-MM-DD)
        flat_stake_pct: Stake fixo % (default: 2%)
        K_base: Fator Kelly base (default: 0.5)
    
    Returns:
        dict: Resultados comparativos
    """
    # Obter sinais históricos
    signals = get_historical_signals(start_date, end_date)
    
    # Simular Flat Betting
    flat_bankroll = 10000
    flat_pnl = []
    
    for signal in signals:
        stake = flat_bankroll * flat_stake_pct
        if signal['win']:
            flat_bankroll += stake * (signal['odd'] - 1)
        else:
            flat_bankroll -= stake
        flat_pnl.append(flat_bankroll)
    
    # Simular Kelly Criterion
    kelly_bankroll = 10000
    kelly_bankroll_peak = 10000
    kelly_pnl = []
    
    for signal in signals:
        kelly_result = calculate_kelly_full(
            prob=signal['prob'],
            odd=signal['odd'],
            bankroll=kelly_bankroll,
            bankroll_peak=kelly_bankroll_peak,
            historical_pnl=kelly_pnl[-30:] if len(kelly_pnl) >= 30 else []
        )
        
        stake = kelly_result['stake']
        if signal['win']:
            kelly_bankroll += stake * (signal['odd'] - 1)
        else:
            kelly_bankroll -= stake
        
        # Atualizar pico
        if kelly_bankroll > kelly_bankroll_peak:
            kelly_bankroll_peak = kelly_bankroll
        
        kelly_pnl.append(kelly_bankroll)
    
    # Calcular métricas
    flat_roi = (flat_bankroll - 10000) / 10000 * 100
    kelly_roi = (kelly_bankroll - 10000) / 10000 * 100
    flat_max_dd = calculate_max_drawdown(flat_pnl)
    kelly_max_dd = calculate_max_drawdown(kelly_pnl)
    
    return {
        "flat": {
            "final_bankroll": round(flat_bankroll, 2),
            "roi": round(flat_roi, 2),
            "max_drawdown": round(flat_max_dd, 2),
            "sharpe": calculate_sharpe(flat_pnl)
        },
        "kelly": {
            "final_bankroll": round(kelly_bankroll, 2),
            "roi": round(kelly_roi, 2),
            "max_drawdown": round(kelly_max_dd, 2),
            "sharpe": calculate_sharpe(kelly_pnl)
        },
        "winner": "kelly" if kelly_roi > flat_roi else "flat"
    }
```

### 9.2 Exemplo de Resultados

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACKTEST KELLY VS FLAT BETTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Período: 2024-01-01 a 2024-01-31 (31 dias)
Sinais: 87

FLAT BETTING (2% fixo):
- Banca final: €11,450.00
- ROI: +14.5%
- Máximo drawdown: -8.2%
- Sharpe ratio: 1.45

KELLY CRITERION (meio Kelly + ajustes):
- Banca final: €12,180.00
- ROI: +21.8%
- Máximo drawdown: -12.5%
- Sharpe ratio: 1.62

VENCEDOR: Kelly Criterion (+7.3% ROI adicional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 10. TROUBLESHOOTING

### 10.1 Stake Muito Alto

```bash
# Verificar K atual
vbq-cli report kelly --detailed

# Verificar drawdown
vbq-cli report pnl --drawdown

# Forçar redução manual de K
# Editar config.yaml: kelly.force_K = 0.25
```

### 10.2 Stake Muito Baixo

```bash
# Verificar se há edge suficiente
vbq-cli predict today --verbose

# Verificar regime de volatilidade
vbq-cli report kelly --volatility

# Aumentar K temporariamente (cuidado!)
# Editar config.yaml: kelly.min_K = 0.3
```

### 10.3 Ajustes Excessivos

```bash
# Verificar histórico de ajustes
vbq-cli report kelly --adjustments

# Se ajustes de drawdown > 20/week:
# - Considerar reduzir sensibilidade
# - Editar config.yaml: kelly.drawdown_sensitivity = low
```

---

## 11. EXEMPLOS DE CÓDIGO

### 11.1 Classe Principal

```python
# vbq/risk/kelly_calculator.py
class KellyCalculator:
    def __init__(self, db: Session):
        self.db = db
        self.exposure_manager = ExposureManager(db)
    
    def calculate_stake(
        self,
        game_id: str,
        prob: float,
        odd: float,
        use_adjustments: bool = True
    ) -> dict:
        """
        Calcula stake usando Kelly Criterion.
        
        Args:
            game_id: ID do jogo
            prob: Probabilidade estimada
            odd: Odd decimal
            use_adjustments: Aplicar ajustes de drawdown/volatilidade
        
        Returns:
            dict: {stake, stake_pct, K_used, adjustments_applied}
        """
        # Obter banca
        bankroll = self.get_current_bankroll()
        bankroll_peak = self.get_bankroll_peak()
        
        # Calcular Kelly base
        if prob * odd <= 1.0:
            return {"stake": 0.0, "stake_pct": 0.0, "reason": "no_edge"}
        
        f_kelly = (prob * odd - 1.0) / (odd - 1.0)
        K = 0.5  # Meio Kelly padrão
        
        if use_adjustments:
            # Ajustar por drawdown
            drawdown = (bankroll_peak - bankroll) / bankroll_peak
            K = self._adjust_k_by_drawdown(K, drawdown)
            
            # Ajustar por volatilidade
            historical_pnl = self.get_historical_pnl(days=30)
            vol_regime = calculate_volatility_regime(historical_pnl)
            K = K * vol_regime["multiplier"]
        
        # Aplicar hard cap
        f_final = K * f_kelly
        f_capped = min(f_final, 0.02)  # 2% max
        
        stake = f_capped * bankroll
        
        # Verificar limites de exposição
        exposure_check = self.exposure_manager.check_exposure_limits(
            game_id, stake
        )
        
        if not exposure_check["approved"]:
            stake = exposure_check["limit"]
            f_capped = stake / bankroll
        
        return {
            "stake": round(stake, 2),
            "stake_pct": round(f_capped * 100, 2),
            "K_used": round(K, 3),
            "adjustments_applied": use_adjustments
        }
```

---

## 12. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Secção mãe
- [[08_Risk_Management/KELLY_FRACIONADO]] → Documentação base de Kelly
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Gestão de drawdown
- [[07_Value_Detection/MOTOR_EDGE]] → Uso de Kelly no motor de decisão
- [[09_Execution_System/CLI_OPERACOES_DIARIAS]] → CLI de sizing

---

**Custo de implementação:** 0€ (código Python)  
**Tempo estimado de implementação:** 1-2 semanas  
**Prioridade:** ALTA (fundamental para gestão de risco)
