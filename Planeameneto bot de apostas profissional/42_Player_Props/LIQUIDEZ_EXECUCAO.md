# LIQUIDEZ_EXECUCAO — Liquidez e Execução em Player Props

**ID:** `PP-005` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar as características de liquidez e execução específicas de player props, incluindo volume típico, slippage esperado, limites de tamanho, e estratégias para otimizar execução em mercados ilíquidos.

---

## 2. CARACTERÍSTICAS DE LIQUIDEZ

### 2.1 Comparação de Liquidez

| Mercado | Volume Típico | Slippage Esperado | Depth | Limites |
|---------|---------------|-------------------|-------|---------|
| Moneyline | €10,000-50,000 | 0.5% | 5-10 níveis | €5,000+ |
| Spread | €5,000-20,000 | 0.7% | 3-7 níveis | €2,000-5,000 |
| Totals | €3,000-10,000 | 0.8% | 3-5 níveis | €1,000-3,000 |
| Player Props (Star) | €500-2,000 | 1.0-1.5% | 2-4 níveis | €200-500 |
| Player Props (Role Player) | €100-500 | 1.5-2.5% | 1-2 níveis | €50-200 |
| Player Props (PRA) | €200-800 | 1.2-2.0% | 2-3 níveis | €100-300 |

### 2.2 Fatores que Afetam Liquidez

```python
liquidity_factors = {
    # Popularidade do jogador
    "player_popularity": {
        "star": "Alta liquidez (€1,000-2,000)",
        "starter": "Média liquidez (€300-800)",
        "role_player": "Baixa liquidez (€100-300)",
    },
    
    # Tipo de estatística
    "stat_type": {
        "PTS": "Mais líquido",
        "REB": "Liquidez média",
        "AST": "Menos líquido",
        "PRA": "Liquidez variável",
    },
    
    # Momento do jogo
    "timing": {
        "pre_game_24h": "Liquidez crescente",
        "pre_game_1h": "Liquidez máxima",
        "in_game": "Liquidez cai drasticamente",
        "post_game": "Sem liquidez",
    },
    
    # Importância do jogo
    "game_importance": {
        "playoff": "Liquidez aumentada",
        "rivalry": "Liquidez aumentada",
        "national_tv": "Liquidez aumentada",
        "regular_season": "Liquidez normal",
    },
}
```

---

## 3. SLIPPAGE EM PLAYER PROPS

### 3.1 Slippage por Categoria

```python
slippage_by_category = {
    # Por tipo de jogador
    "star": {
        "pts": 0.008,      # 0.8%
        "reb": 0.010,      # 1.0%
        "ast": 0.012,      # 1.2%
        "pra": 0.010,      # 1.0%
    },
    
    # Por tipo de jogador
    "starter": {
        "pts": 0.012,      # 1.2%
        "reb": 0.015,      # 1.5%
        "ast": 0.018,      # 1.8%
        "pra": 0.015,      # 1.5%
    },
    
    # Por tipo de jogador
    "role_player": {
        "pts": 0.018,      # 1.8%
        "reb": 0.022,      # 2.2%
        "ast": 0.025,      # 2.5%
        "pra": 0.020,      # 2.0%
    },
}
```

### 3.2 Modelo de Slippage

```python
def calculate_slippage(
    stake,
    player_type,
    stat_type,
    market_depth,
    base_slippage=None
):
    """
    Calcula slippage esperado para uma aposta de player prop.
    
    Args:
        stake: valor da aposta
        player_type: star/starter/role_player
        stat_type: PTS/REB/AST/PRA
        market_depth: profundidade do mercado (volume disponível)
        base_slippage: slippage base (opcional, usa defaults se não fornecido)
    
    Returns:
        slippage_percent: slippage esperado em %
    """
    # Slippage base por categoria
    if base_slippage is None:
        base_slippage = slippage_by_category[player_type][stat_type.lower()]
    
    # Ajuste por tamanho (slippage aumenta com tamanho)
    size_multiplier = 1.0 + (stake / market_depth) * 0.5
    
    # Ajuste por profundidade (menos profundidade = mais slippage)
    depth_multiplier = 1.0 + (1000 / market_depth) * 0.3
    
    # Slippage final
    slippage_percent = base_slippage * size_multiplier * depth_multiplier
    
    # Limitar slippage máximo
    slippage_percent = min(slippage_percent, 0.05)  # Máximo 5%
    
    return slippage_percent

# Exemplo
slippage = calculate_slippage(
    stake=200,
    player_type="starter",
    stat_type="PTS",
    market_depth=800
)
# Resultado: ~1.5-2.0%
```

### 3.3 Sensibilidade ao Tamanho

```python
def size_sensitivity_analysis(player_type, stat_type, base_depth):
    """
    Analisa como slippage muda com diferentes tamanhos de aposta.
    """
    stakes = [50, 100, 200, 500, 1000]
    slippages = []
    
    for stake in stakes:
        slip = calculate_slippage(
            stake=stake,
            player_type=player_type,
            stat_type=stat_type,
            market_depth=base_depth
        )
        slippages.append(slip)
    
    return pd.DataFrame({
        'stake': stakes,
        'slippage_percent': slippages
    })

# Exemplo para starter PTS com depth 800
sensitivity = size_sensitivity_analysis("starter", "PTS", 800)
# stake=50 -> 1.2%
# stake=100 -> 1.3%
# stake=200 -> 1.5%
# stake=500 -> 2.1%
# stake=1000 -> 3.3%
```

---

## 4. ESTRATÉGIAS DE EXECUÇÃO

### 4.1 Timing de Execução

```python
execution_timing = {
    # Estratégias de timing
    "early_bird": {
        "timing": "24-48h antes do jogo",
        "advantage": "Liquidez crescente, odds podem ter edge",
        "disadvantage": "Injury risk ainda alto",
        "slippage": "0.8-1.2%",
    },
    
    "optimal_window": {
        "timing": "1-4h antes do jogo",
        "advantage": "Liquidez boa, injury reports mais claros",
        "disadvantage": "Edge pode ter diminuído",
        "slippage": "1.0-1.5%",
    },
    
    "last_minute": {
        "timing": "<1h antes do jogo",
        "advantage": "Injury risk resolvido, liquidez máxima",
        "disadvantage": "Edge mínimo, slippage pode aumentar",
        "slippage": "1.2-2.0%",
    },
}
```

### 4.2 Sizing de Apostas

```python
def calculate_optimal_stake(
    edge,
    bankroll,
    player_type,
    stat_type,
    market_depth,
    max_stake_percent=0.02
):
    """
    Calcula stake ótimo considerando edge, liquidez e risco.
    
    Args:
        edge: edge esperado (ex: 0.03 para 3%)
        bankroll: banca total
        player_type: star/starter/role_player
        stat_type: PTS/REB/AST/PRA
        market_depth: profundidade do mercado
        max_stake_percent: máximo % da banca por aposta
    
    Returns:
        optimal_stake: stake recomendado
    """
    # Kelly fraction (conservador)
    kelly_fraction = edge / 2  # Half-Kelly
    
    # Stake baseado em Kelly
    kelly_stake = bankroll * kelly_fraction
    
    # Limitar por liquidez (não exceder 20% do depth)
    liquidity_limit = market_depth * 0.20
    
    # Limitar por tamanho máximo da aposta
    max_stake = bankroll * max_stake_percent
    
    # Stake ótimo é o mínimo dos três
    optimal_stake = min(kelly_stake, liquidity_limit, max_stake)
    
    # Arredondar para valores típicos (múltiplos de 10 ou 50)
    optimal_stake = round(optimal_stake / 10) * 10
    
    return max(optimal_stake, 10)  # Mínimo €10

# Exemplo
stake = calculate_optimal_stake(
    edge=0.04,
    bankroll=10000,
    player_type="starter",
    stat_type="PTS",
    market_depth=800
)
# Resultado: ~€100-200
```

### 4.3 Execução em Várias Parcelas

Para apostas grandes, dividir em várias parcelas para reduzir slippage.

```python
def split_bet_execution(
    total_stake,
    market_depth,
    max_per_trade=200,
    min_time_between_trades=300  # 5 minutos
):
    """
    Divide aposta em várias parcelas para reduzir slippage.
    
    Args:
        total_stake: stake total desejado
        market_depth: profundidade do mercado
        max_per_trade: máximo por trade
        min_time_between_trades: tempo mínimo entre trades (segundos)
    
    Returns:
        execution_plan: lista de (stake, timing)
    """
    # Se stake é pequeno, executar tudo de uma vez
    if total_stake <= max_per_trade:
        return [(total_stake, 0)]
    
    # Calcular número de parcelas
    n_trades = min(
        int(total_stake / max_per_trade) + 1,
        int(market_depth / max_per_trade)
    )
    
    # Calcular stake por parcela
    stake_per_trade = total_stake / n_trades
    
    # Criar plano de execução
    execution_plan = []
    for i in range(n_trades):
        execution_plan.append((
            round(stake_per_trade),
            i * min_time_between_trades
        ))
    
    return execution_plan

# Exemplo
plan = split_bet_execution(
    total_stake=500,
    market_depth=800,
    max_per_trade=200
)
# [(200, 0), (200, 300), (100, 600)]
```

---

## 5. GESTÃO DE LIMITES

### 5.1 Limites de Bookmakers

Bookmakers limitam rapidamente apostadores em player props.

```python
bookmaker_limits = {
    # Limites típicos por tipo de jogador
    "star": {
        "initial_limit": 500,
        "after_restriction": 50,
        "time_to_restriction": "10-20 bets",
    },
    
    "starter": {
        "initial_limit": 200,
        "after_restriction": 25,
        "time_to_restriction": "5-10 bets",
    },
    
    "role_player": {
        "initial_limit": 100,
        "after_restriction": 10,
        "time_to_restriction": "3-5 bets",
    },
}
```

### 5.2 Estratégias para Evitar Restrições

```python
avoid_restriction_strategies = {
    # Diversificar bookmakers
    "use_multiple_books": {
        "description": "Usar 3-5 bookmakers diferentes",
        "benefit": "Atrasa restrições significativamente",
        "implementation": "Rotacionar apostas entre books",
    },
    
    # Misturar apostas
    "mix_bets": {
        "description": "Misturar value bets com apostas aleatórias",
        "benefit": "Dificulta detecção de padrões",
        "implementation": "20-30% de apostas aleatórias (small stakes)",
    },
    
    # Variar timing
    "vary_timing": {
        "description": "Não apostar sempre no mesmo timing",
        "benefit": "Menos óbvio",
        "implementation": "Misturar early, optimal, last-minute",
    },
    
    # Apostar em ambos os lados
    "bet_both_sides": {
        "description": "Ocasionalmente apostar no under",
        "benefit": "Parece mais natural",
        "implementation": "10% de apostas no under (quando edge pequeno)",
    },
}
```

### 5.3 Rotação de Contas

```python
class AccountRotation:
    """
    Gerencia rotação entre múltiplas contas para evitar restrições.
    """
    
    def __init__(self, accounts):
        self.accounts = accounts
        self.current_index = 0
        self.bet_count = {acc: 0 for acc in accounts}
        self.last_bet_time = {acc: None for acc in accounts}
    
    def select_account(self, min_cooldown=3600):
        """
        Seleciona a próxima conta disponível.
        
        Args:
            min_cooldown: tempo mínimo entre apostas na mesma conta (segundos)
        """
        now = time.time()
        
        # Encontrar contas disponíveis
        available = []
        for acc in self.accounts:
            if self.last_bet_time[acc] is None:
                available.append(acc)
            elif now - self.last_bet_time[acc] > min_cooldown:
                available.append(acc)
        
        if not available:
            # Nenhuma disponível, esperar
            return None
        
        # Selecionar conta com menos apostas
        selected = min(available, key=lambda x: self.bet_count[x])
        
        # Atualizar contadores
        self.bet_count[selected] += 1
        self.last_bet_time[selected] = now
        
        return selected
```

---

## 6. EXECUÇÃO EM BETFAIR

### 6.1 Liquidez Betfair para Player Props

Betfair tem liquidez limitada para player props NBA.

```python
betfair_liquidity = {
    # Volume típico por mercado
    "pts_star": {
        "volume_total": 2000,
        "volume_per_side": 1000,
        "best_3_levels": 600,
    },
    
    "pts_starter": {
        "volume_total": 800,
        "volume_per_side": 400,
        "best_3_levels": 250,
    },
    
    "pts_role_player": {
        "volume_total": 300,
        "volume_per_side": 150,
        "best_3_levels": 100,
    },
}
```

### 6.2 Estratégia Betfair

```python
def betfair_execution_strategy(
    selection_id,
    side,  # BACK or LAY
    price,
    stake,
    liquidity_profile
):
    """
    Estratégia de execução em Betfair para player props.
    
    Args:
        selection_id: ID da seleção Betfair
        side: BACK ou LAY
        price: preço desejado
        stake: stake desejado
        liquidity_profile: perfil de liquidez do mercado
    """
    # Verificar liquidez disponível
    available_liquidity = get_available_liquidity(selection_id, side, price)
    
    # Se liquidez suficiente, executar imediatamente
    if available_liquidity >= stake:
        return execute_bet(selection_id, side, price, stake)
    
    # Se não, usar ordem limite
    else:
        # Colocar ordem limite
        place_limit_order(selection_id, side, price, stake)
        
        # Monitorizar e ajustar se necessário
        return monitor_order(selection_id)
```

### 6.3 Comissão Betfair

```python
def calculate_betfair_pnl(
    stake,
    price,
    outcome,
    commission_rate=0.05
):
    """
    Calcula PnL considerando comissão Betfair.
    
    Args:
        stake: stake da aposta
        price: preço (odd decimal)
        outcome: True se ganhou, False se perdeu
        commission_rate: taxa de comissão (5% padrão)
    
    Returns:
        pnl: lucro ou prejuízo líquido
    """
    if outcome:
        profit = stake * (price - 1)
        commission = profit * commission_rate
        pnl = profit - commission
    else:
        pnl = -stake
    
    return pnl

# Exemplo
pnl_win = calculate_betfair_pnl(stake=100, price=2.00, outcome=True)
# Lucro bruto: 100, Comissão: 5, PnL: 95

pnl_loss = calculate_betfair_pnl(stake=100, price=2.00, outcome=False)
# PnL: -100
```

---

## 7. MONITORIZAÇÃO DE EXECUÇÃO

### 7.1 Métricas de Execução

```python
execution_metrics = {
    # Métricas de qualidade
    "avg_slippage": "Slippage médio real vs esperado",
    "fill_rate": "Taxa de execução bem-sucedida",
    "execution_time": "Tempo médio para executar aposta",
    
    # Métricas de liquidez
    "avg_market_depth": "Profundidade média do mercado",
    "liquidity_variance": "Variância de liquidez entre jogos",
    
    # Métricas de restrições
    "accounts_restricted": "Número de contas restritas",
    "time_to_restriction": "Tempo médio até restrição",
    "limit_reduction": "Redução média de limite",
}
```

### 7.2 Logging de Execução

```python
def log_execution(
    bet_id,
    player_id,
    stat_type,
    line,
    side,
    price_requested,
    price_executed,
    stake,
    slippage,
    execution_time,
    success
):
    """
    Regista detalhes de execução para análise posterior.
    """
    log_entry = {
        'bet_id': bet_id,
        'player_id': player_id,
        'stat_type': stat_type,
        'line': line,
        'side': side,
        'price_requested': price_requested,
        'price_executed': price_executed,
        'stake': stake,
        'slippage': slippage,
        'execution_time': execution_time,
        'success': success,
        'timestamp': datetime.now(),
    }
    
    # Guardar em base de dados
    save_execution_log(log_entry)
    
    return log_entry
```

---

## 8. BACKLOG

- [ ] Medir slippage real em paper trading
- [ ] Calibrar modelo de slippage com dados reais
- [ ] Implementar sistema de sizing dinâmico
- [ ] Implementar sistema de execução em parcelas
- [ ] Implementar rotação de contas
- [ ] Integrar com API Betfair
- [ ] Criar dashboard de métricas de execução
- [ ] Documentar limites por bookmaker
- [ ] Desenvolver estratégias para evitar restrições

---

## 9. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/DIFERENCAS_TEAM_VS_PLAYER]] → Diferenças de liquidez
- [[06_Backtesting/SLIPPAGE_COMISSOES]] → Slippage geral
- [[09_Execution_System/INDEX]] → Sistema de execução
- [[14_APIs/BETFAIR_API]] → API Betfair