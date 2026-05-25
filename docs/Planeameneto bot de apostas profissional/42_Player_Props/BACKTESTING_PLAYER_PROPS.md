# BACKTESTING_PLAYER_PROPS — Backtesting para Player Props

**ID:** `PP-007` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir a abordagem de backtesting específica para player props, incluindo diferenças em relação ao backtesting de team props, slippage aumentado, purging agressivo, e métricas específicas para avaliar performance.

---

## 2. DIFERENÇAS VS TEAM PROPS

### 2.1 Comparação de Backtesting

| Aspecto | Team Props | Player Props |
|---------|------------|--------------|
| Slippage | 0.5-0.7% | 1.0-2.0% |
| Purging | 7 dias | 14 dias |
| Dados por jogo | 1 (equipa) | 10-15 (jogadores) |
| Esparsidade | Baixa | Alta (jogadores não jogam) |
| Lesões | Impacto mitigado | Impacto crítico |
| Blowout | Filtro simples | Filtro agressivo |
| Calibração | Por regime | Por linha + jogador |
| Período mínimo | 1 época | 2 épocas |

### 2.2 Implicações

```python
backtesting_differences = {
    # Slippage maior
    "slippage": {
        "team_props": 0.005,
        "player_props": 0.015,
        "impact": "ROI reduzido em ~1%",
    },
    
    # Purging mais agressivo
    "purging": {
        "team_props": 7,
        "player_props": 14,
        "impact": "Menos dados de treino, mais folds necessários",
    },
    
    # Esparsidade
    "sparsity": {
        "team_props": "0% missing",
        "player_props": "10-20% missing (lesões, DNP)",
        "impact": "Necessário lidar com missing data",
    },
    
    # Calibração
    "calibration": {
        "team_props": "Por regime (3 categorias)",
        "player_props": "Por linha (5-10 bins) + jogador (3 tipos)",
        "impact": "Mais complexo, mais calibradores",
    },
}
```

---

## 3. DADOS HISTÓRICOS

### 3.1 Requisitos de Dados

```python
data_requirements = {
    # Período mínimo
    "minimum_seasons": 2,
    "minimum_games": 1500,  # Jogos por mercado (PTS/REB/AST)
    
    # Dados necessários
    "box_scores": {
        "player_id": True,
        "game_id": True,
        "game_date": True,
        "team_id": True,
        "opponent_id": True,
        "minutes": True,
        "pts": True,
        "reb": True,
        "ast": True,
        "starter": True,
    },
    
    # Odds históricas
    "odds": {
        "line": True,
        "over_odds": True,
        "under_odds": True,
        "opening_odds": True,
        "closing_odds": True,
    },
    
    # Contexto
    "context": {
        "injury_status": True,
        "lineup": True,
        "spread_line": True,
        "total_line": True,
    },
}
```

### 3.2 Fontes de Dados

```python
data_sources = {
    # Box scores
    "box_scores": [
        "NBA API (official)",
        "Basketball Reference",
        "Stats NBA",
    ],
    
    # Odds
    "odds": [
        "Betfair Historical Data",
        "OddsPortal",
        "Action Network",
    ],
    
    # Contexto
    "context": [
        "NBA Official Injury Report",
        "ESPN Injury News",
        "Rotowire",
    ],
}
```

---

## 4. PREPARAÇÃO DE DADOS

### 4.1 Limpeza de Dados

```python
def clean_player_props_data(df):
    """
    Limpa dados de player props para backtesting.
    
    Args:
        df: DataFrame raw com dados históricos
    
    Returns:
        df_clean: DataFrame limpo
    """
    df_clean = df.copy()
    
    # Remover jogos onde jogador não jogou (DNP)
    df_clean = df_clean[df_clean['minutes'] > 0]
    
    # Remover outliers (minutos < 5 ou > 48)
    df_clean = df_clean[
        (df_clean['minutes'] >= 5) &
        (df_clean['minutes'] <= 48)
    ]
    
    # Remover jogos com dados incompletos
    df_clean = df_clean.dropna(subset=['pts', 'reb', 'ast', 'line'])
    
    # Remover linhas irrealistas (ex: PTS line < 5 ou > 50)
    df_clean = df_clean[
        (df_clean['line'] >= 5) &
        (df_clean['line'] <= 50)
    ]
    
    # Validar odds (entre 1.01 e 10.0)
    df_clean = df_clean[
        (df_clean['over_odds'] >= 1.01) &
        (df_clean['over_odds'] <= 10.0)
    ]
    
    return df_clean
```

### 4.2 Engenharia de Features para Backtesting

```python
def engineer_features_for_backtest(df, window=10):
    """
    Cria features para backtesting (usando apenas dados históricos).
    
    CRÍTICO: Usar apenas dados com data < game_date
    """
    features_list = []
    
    # Ordenar por data
    df = df.sort_values('game_date')
    
    # Para cada jogo
    for idx, row in df.iterrows():
        game_date = row['game_date']
        player_id = row['player_id']
        
        # Dados históricos antes deste jogo
        historical = df[
            (df['player_id'] == player_id) &
            (df['game_date'] < game_date)
        ].tail(window)
        
        if len(historical) < 3:
            continue  # Pular se dados insuficientes
        
        # Criar features
        features = {
            'game_id': row['game_id'],
            'player_id': player_id,
            'game_date': game_date,
            'line': row['line'],
            'over_odds': row['over_odds'],
            'under_odds': row['under_odds'],
            
            # Histórico
            'pts_last5': historical['pts'].tail(5).mean(),
            'pts_last10': historical['pts'].tail(10).mean(),
            'reb_last5': historical['reb'].tail(5).mean(),
            'reb_last10': historical['reb'].tail(10).mean(),
            'ast_last5': historical['ast'].tail(5).mean(),
            'ast_last10': historical['ast'].tail(10).mean(),
            
            # Minutos
            'minutes_last5': historical['minutes'].tail(5).mean(),
            'minutes_last10': historical['minutes'].tail(10).mean(),
            
            # Volatilidade
            'pts_std_last5': historical['pts'].tail(5).std(),
            
            # Target (valor real)
            'pts_actual': row['pts'],
            'reb_actual': row['reb'],
            'ast_actual': row['ast'],
        }
        
        features_list.append(features)
    
    return pd.DataFrame(features_list)
```

---

## 5. WALK-FORWARD CV

### 5.1 Configuração Específica

```python
def player_props_walk_forward_cv(df, n_splits=10, train_size=0.7, purge_days=14):
    """
    Walk-forward cross-validation específico para player props.
    
    Diferenças vs team props:
    - Mais splits (10 vs 5) para compensar dados esparsos
    - Purging mais agressivo (14 vs 7 dias)
    - Train size maior (70% vs 60%) para ter dados suficientes
    """
    splits = []
    
    # Ordenar por data
    df = df.sort_values('game_date')
    dates = df['game_date'].unique()
    
    n_dates = len(dates)
    
    for i in range(n_splits):
        # Definir índices
        train_end_idx = int(n_dates * train_size) + i * int((n_dates * (1 - train_size)) / n_splits)
        val_start_idx = train_end_idx + int(purge_days / 1)  # Assumir ~1 jogo por dia
        val_end_idx = val_start_idx + int((n_dates * (1 - train_size)) / n_splits)
        
        if val_end_idx >= n_dates:
            break
        
        # Datas
        train_dates = dates[:train_end_idx]
        val_dates = dates[val_start_idx:val_end_idx]
        
        # Filtrar dataframe
        train_df = df[df['game_date'].isin(train_dates)]
        val_df = df[df['game_date'].isin(val_dates)]
        
        splits.append((train_df, val_df))
    
    return splits
```

### 5.2 Validação com Purging Agressivo

```python
def aggressive_purging(train_df, val_df, purge_days=14):
    """
    Remove dados de treino que estão muito próximos de validação.
    
    Para player props, usar 14 dias (vs 7 dias para team props).
    """
    min_val_date = val_df['game_date'].min()
    purge_threshold = min_val_date - pd.Timedelta(days=purge_days)
    
    # Remover treino dentro de purge_days
    train_purged = train_df[train_df['game_date'] < purge_threshold]
    
    return train_purged, val_df
```

---

## 6. SIMULAÇÃO DE BETTING

### 6.1 Simulação com Slippage Aumentado

```python
def simulate_betting_player_props(
    predictions,
    lines,
    odds_over,
    odds_under,
    actual_values,
    slippage=0.015,
    commission=0.05,
    edge_threshold=0.02
):
    """
    Simula betting de player props com slippage aumentado.
    
    Args:
        predictions: previsões do modelo
        lines: linhas do mercado
        odds_over: odds para over
        odds_under: odds para under
        actual_values: valores reais
        slippage: slippage (1.5% padrão para player props)
        commission: comissão Betfair (5%)
        edge_threshold: edge mínimo para apostar (2%)
    
    Returns:
        results: DataFrame com resultados
    """
    results = []
    
    for i in range(len(predictions)):
        pred = predictions[i]
        line = lines[i]
        odd_over = odds_over[i]
        odd_under = odds_under[i]
        actual = actual_values[i]
        
        # Calcular probabilidade de over
        prob_over = calculate_over_probability(pred, line, std_dev=4.5)
        
        # Calcular edge para over
        market_prob_over = 1 / odd_over
        edge_over = prob_over - market_prob_over
        
        # Calcular edge para under
        market_prob_under = 1 / odd_under
        edge_under = (1 - prob_over) - market_prob_under
        
        # Decidir apostar
        bet_over = edge_over > edge_threshold
        bet_under = edge_under > edge_threshold
        
        # Simular resultado
        if bet_over:
            odd_executed = odd_over * (1 - slippage)
            outcome = actual > line
            
            pnl = simulate_bet_outcome(odd_executed, outcome, commission)
            
            results.append({
                'side': 'over',
                'edge': edge_over,
                'pnl': pnl,
                'won': outcome,
            })
        
        elif bet_under:
            odd_executed = odd_under * (1 - slippage)
            outcome = actual <= line
            
            pnl = simulate_bet_outcome(odd_executed, outcome, commission)
            
            results.append({
                'side': 'under',
                'edge': edge_under,
                'pnl': pnl,
                'won': outcome,
            })
    
    return pd.DataFrame(results)

def simulate_bet_outcome(odd_executed, outcome, commission=0.05):
    """
    Simula resultado de uma aposta.
    """
    if outcome:
        profit = odd_executed - 1
        net_profit = profit * (1 - commission)
        return net_profit
    else:
        return -1.0
```

### 6.2 Simulação com Filtros de Risco

```python
def simulate_betting_with_risk_filters(
    predictions,
    lines,
    odds_over,
    odds_under,
    actual_values,
    injury_statuses,
    minutes_projected,
    blowout_probs,
    slippage=0.015,
    commission=0.05,
    edge_threshold=0.02
):
    """
    Simula betting com filtros de risco (lesões, minutos, blowout).
    """
    results = []
    
    for i in range(len(predictions)):
        # Aplicar filtros de risco
        if injury_statuses[i] in ["doubtful", "out"]:
            continue  # Pular
        
        if minutes_projected[i] < 20:
            continue  # Pular
        
        if blowout_probs[i] > 0.30:
            continue  # Pular
        
        # Simular aposta
        pred = predictions[i]
        line = lines[i]
        odd_over = odds_over[i]
        odd_under = odds_under[i]
        actual = actual_values[i]
        
        prob_over = calculate_over_probability(pred, line, std_dev=4.5)
        market_prob_over = 1 / odd_over
        edge_over = prob_over - market_prob_over
        
        if edge_over > edge_threshold:
            odd_executed = odd_over * (1 - slippage)
            outcome = actual > line
            pnl = simulate_bet_outcome(odd_executed, outcome, commission)
            
            results.append({
                'side': 'over',
                'edge': edge_over,
                'pnl': pnl,
                'won': outcome,
            })
    
    return pd.DataFrame(results)
```

---

## 7. MÉTRICAS DE AVALIAÇÃO

### 7.1 Métricas de Performance

```python
def calculate_backtest_metrics(results):
    """
    Calcula métricas de backtesting.
    """
    if len(results) == 0:
        return {}
    
    total_bets = len(results)
    total_pnl = results['pnl'].sum()
    avg_stake = 1.0  # Assumir stake unitário
    
    # ROI
    roi = total_pnl / (total_bets * avg_stake)
    
    # Win rate
    win_rate = results['won'].mean()
    
    # Média de edge
    avg_edge = results['edge'].mean()
    
    # Sharpe ratio (simplificado)
    std_pnl = results['pnl'].std()
    sharpe = (roi / std_pnl) if std_pnl > 0 else 0
    
    # Maximum drawdown
    cumulative = results['pnl'].cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Calmar ratio
    calmar = roi / abs(max_drawdown) if max_drawdown != 0 else 0
    
    metrics = {
        'total_bets': total_bets,
        'total_pnl': total_pnl,
        'roi': roi,
        'win_rate': win_rate,
        'avg_edge': avg_edge,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'calmar': calmar,
    }
    
    return metrics
```

### 7.2 Métricas por Categoria

```python
def calculate_metrics_by_category(results, categories):
    """
    Calcula métricas por categoria (ex: por tipo de jogador).
    """
    metrics_by_category = {}
    
    for category in categories.unique():
        mask = categories == category
        category_results = results[mask]
        
        if len(category_results) > 0:
            metrics = calculate_backtest_metrics(category_results)
            metrics_by_category[category] = metrics
    
    return metrics_by_category

# Exemplo: métricas por tipo de jogador
metrics_by_player_type = calculate_metrics_by_category(
    results,
    player_types  # star/starter/role_player
)
```

### 7.3 Métricas de Calibração

```python
def calculate_calibration_metrics(y_true, probs, n_bins=10):
    """
    Calcula métricas de calibração.
    """
    from sklearn.calibration import calibration_curve
    
    # Curva de calibração
    prob_true, prob_pred = calibration_curve(y_true, probs, n_bins=n_bins)
    
    # Brier score
    from sklearn.metrics import brier_score_loss
    brier = brier_score_loss(y_true, probs)
    
    # Expected Calibration Error (ECE)
    ece = 0
    for i in range(n_bins):
        bin_size = len(probs[(probs >= prob_pred[i]) & (probs < prob_pred[i+1])])
        if bin_size > 0:
            ece += bin_size / len(probs) * abs(prob_true[i] - prob_pred[i])
    
    return {
        'brier': brier,
        'ece': ece,
        'prob_true': prob_true,
        'prob_pred': prob_pred,
    }
```

---

## 8. SENSITIVITY ANALYSIS

### 8.1 Sensibilidade ao Slippage

```python
def slippage_sensitivity_analysis(
    predictions,
    lines,
    odds_over,
    odds_under,
    actual_values,
    slippage_range=[0.005, 0.010, 0.015, 0.020, 0.025]
):
    """
    Analisa como ROI muda com diferentes níveis de slippage.
    """
    results = {}
    
    for slippage in slippage_range:
        sim_results = simulate_betting_player_props(
            predictions, lines, odds_over, odds_under, actual_values,
            slippage=slippage
        )
        
        metrics = calculate_backtest_metrics(sim_results)
        results[slippage] = metrics
    
    return pd.DataFrame(results).T
```

### 8.2 Sensibilidade ao Edge Threshold

```python
def edge_threshold_sensitivity_analysis(
    predictions,
    lines,
    odds_over,
    odds_under,
    actual_values,
    edge_thresholds=[0.01, 0.015, 0.02, 0.025, 0.03]
):
    """
    Analisa como ROI muda com diferentes thresholds de edge.
    """
    results = {}
    
    for threshold in edge_thresholds:
        sim_results = simulate_betting_player_props(
            predictions, lines, odds_over, odds_under, actual_values,
            edge_threshold=threshold
        )
        
        metrics = calculate_backtest_metrics(sim_results)
        results[threshold] = metrics
    
    return pd.DataFrame(results).T
```

---

## 9. VALIDAÇÃO DE OVERFITTING

### 9.1 Teste de Overfitting

```python
def overfitting_test(train_metrics, val_metrics):
    """
    Compara métricas de treino e validação para detectar overfitting.
    """
    # Diferença em ROI
    roi_diff = train_metrics['roi'] - val_metrics['roi']
    
    # Diferença em win rate
    win_rate_diff = train_metrics['win_rate'] - val_metrics['win_rate']
    
    # Overfitting se diferença for grande
    is_overfitting = (roi_diff > 0.05) or (win_rate_diff > 0.10)
    
    return {
        'is_overfitting': is_overfitting,
        'roi_diff': roi_diff,
        'win_rate_diff': win_rate_diff,
    }
```

### 9.2 Teste de Forward Performance

```python
def forward_performance_test(
    model,
    train_data,
    test_data,
    feature_cols,
    target_col
):
    """
    Testa performance em dados futuros (não usados em treino).
    """
    # Treinar em dados históricos
    X_train = train_data[feature_cols]
    y_train = train_data[target_col]
    
    model.fit(X_train, y_train)
    
    # Prever em dados futuros
    X_test = test_data[feature_cols]
    predictions = model.predict(X_test)
    
    # Calcular métricas
    actual = test_data[target_col]
    mae = mean_absolute_error(actual, predictions)
    rmse = np.sqrt(mean_squared_error(actual, predictions))
    
    return {
        'mae': mae,
        'rmse': rmse,
    }
```

---

## 10. RELATÓRIO DE BACKTEST

### 10.1 Estrutura do Relatório

```python
def generate_backtest_report(metrics, sensitivity_results, overfitting_results):
    """
    Gera relatório de backtesting.
    """
    report = {
        # Resumo
        'summary': {
            'total_bets': metrics['total_bets'],
            'roi': metrics['roi'],
            'win_rate': metrics['win_rate'],
            'sharpe': metrics['sharpe'],
            'max_drawdown': metrics['max_drawdown'],
        },
        
        # Sensibilidade
        'sensitivity': {
            'slippage': sensitivity_results['slippage'],
            'edge_threshold': sensitivity_results['edge_threshold'],
        },
        
        # Overfitting
        'overfitting': overfitting_results,
        
        # Conclusão
        'conclusion': generate_conclusion(metrics, overfitting_results),
    }
    
    return report

def generate_conclusion(metrics, overfitting_results):
    """
    Gera conclusão do backtest.
    """
    if overfitting_results['is_overfitting']:
        return "BACKTEST FALHOU: Overfitting detectado"
    
    if metrics['roi'] < 0.01:
        return "BACKTEST FALHOU: ROI insuficiente"
    
    if metrics['sharpe'] < 1.0:
        return "BACKTEST FALHOU: Sharpe ratio insuficiente"
    
    if metrics['max_drawdown'] < -0.20:
        return "BACKTEST FALHOU: Drawdown excessivo"
    
    return "BACKTEST APROVADO: Métricas dentro dos limites aceitáveis"
```

---

## 11. BACKLOG

- [ ] Coletar dados históricos de 2 épocas
- [ ] Implementar pipeline de limpeza de dados
- [ ] Implementar engenharia de features para backtesting
- [ ] Implementar walk-forward CV com purging agressivo
- [ ] Implementar simulação de betting com slippage aumentado
- [ ] Implementar filtros de risco na simulação
- [ ] Implementar cálculo de métricas
- [ ] Implementar sensitivity analysis
- [ ] Implementar testes de overfitting
- [ ] Gerar relatório de backtesting

---

## 12. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/MODELACAO_PLAYER_PROPS]] → Modelagem usada no backtest
- [[42_Player_Props/RISCOS_ESPECIFICOS]] → Filtros de risco
- [[06_Backtesting/INDEX]] → Backtesting geral
- [[06_Backtesting/WALK_FORWARD_IMPLEMENTACAO]] → Walk-forward CV
- [[06_Backtesting/SLIPPAGE_COMISSOES]] → Slippage