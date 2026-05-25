# Sistema de Decisão de Apostas

**ID:** DECISAO-001 | **Fase:** #phase/2-6 | **Owner:** Chief Quant | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Framework de decisão multi-camadas para identificar quais apostas são realmente importantes, combinando edge do modelo, qualidade de odds, histórico de CLV, limites de exposição, e ranking de oportunidades. Baseado nos projetos kyleskom/NBA-ML-Betting, NBA-Betting/NBA_Betting, e georgedouzas/sports-betting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar e priorizar as melhores oportunidades de aposta |
| **Camadas de Decisão** | 4 camadas (Edge → Qualidade Odds → CLV Histórico → Exposição) |
| **Thresholds Dinâmicos** | Ajustados por mercado, volatilidade, e regime |
| **Ranking** | Sistema de pontuação para oportunidades |
| **Custo** | 0€ (código Python) |

---

## 2. FRAMEWORK DE DECISÃO (PIPELINE)

### 2.1 Arquitetura do Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 1: EDGE DO MODELO                  │
│  (Probabilidade × Odd - 1)                                   │
│  Threshold: 4% base, ajustado por volatilidade             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 2: QUALIDADE DE ODDS               │
│  (Best price, liquidez, estabilidade)                       │
│  Threshold: Odds de Tier 1+ (Fanduel/DraftKings)           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 3: CLV HISTÓRICO                   │
│  (CLV médio 30 dias, consistência)                           │
│  Threshold: CLV > 0% (no mínimo)                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 4: EXPOSIÇÃO E LIMITES             │
│  (Exposição diária, por jogo, por mercado)                  │
│  Threshold: Respeitar todos os limites                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    RANKING DE OPORTUNIDADES                  │
│  (Pontuação 0-100, top N selecionados)                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    DECISÃO FINAL                             │
│  (Aprovado/Rejeitado + Stake via Kelly)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CAMADA 1: EDGE DO MODELO

### 3.1 Cálculo de Edge

```python
# vbq/decision/edge_calculator.py
class EdgeCalculator:
    """Calcula edge do modelo."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_edge(self, probability: float, odds: float) -> dict:
        """
        Calcula edge do modelo.
        
        Edge = (probabilidade × odd) - 1
        
        Args:
            probability: Probabilidade estimada pelo modelo (0-1)
            odds: Odd decimal
        
        Returns:
            dict: {edge, edge_pct, has_edge, threshold_met}
        """
        edge = (probability * odds) - 1.0
        edge_pct = edge * 100
        
        # Threshold dinâmico baseado em volatilidade
        threshold = self._get_dynamic_threshold()
        
        has_edge = edge > 0
        threshold_met = edge_pct >= threshold
        
        return {
            'edge': edge,
            'edge_pct': edge_pct,
            'has_edge': has_edge,
            'threshold_met': threshold_met,
            'threshold': threshold
        }
    
    def _get_dynamic_threshold(self) -> float:
        """
        Retorna threshold dinâmico baseado em volatilidade recente.
        
        - Regime normal: 4%
        - Regime alta vol: 5%
        - Regime baixa vol: 3%
        """
        vol_regime = self._get_volatility_regime()
        
        if vol_regime == 'high':
            return 5.0
        elif vol_regime == 'low':
            return 3.0
        else:
            return 4.0  # Normal
    
    def _get_volatility_regime(self) -> str:
        """Determina regime de volatilidade."""
        # Obter PnL dos últimos 30 dias
        pnl_history = self.get_historical_pnl(days=30)
        std_dev = np.std(pnl_history)
        
        # Normalizar pela banca
        normalized_std = std_dev / 10000  # Assumindo banca 10k
        
        if normalized_std > 0.04:
            return 'high'
        elif normalized_std < 0.02:
            return 'low'
        else:
            return 'normal'
```

### 3.2 Filtros de Edge

```python
def apply_edge_filters(opportunities: List[dict]) -> List[dict]:
    """
    Aplica filtros baseados em edge.
    
    Filtros:
    1. Edge > 0 (obrigatório)
    2. Edge >= threshold dinâmico
    3. Edge não excessivo (> 15% pode indicar erro)
    """
    filtered = []
    
    for opp in opportunities:
        edge_calc = opp['edge_calculation']
        
        # Filtro 1: Edge > 0
        if not edge_calc['has_edge']:
            opp['rejection_reason'] = 'no_edge'
            continue
        
        # Filtro 2: Edge >= threshold
        if not edge_calc['threshold_met']:
            opp['rejection_reason'] = f"edge_below_threshold ({edge_calc['edge_pct']:.1f}% < {edge_calc['threshold']}%)"
            continue
        
        # Filtro 3: Edge não excessivo
        if edge_calc['edge_pct'] > 15.0:
            opp['rejection_reason'] = f"edge_excessive ({edge_calc['edge_pct']:.1f}% > 15%)"
            continue
        
        filtered.append(opp)
    
    return filtered
```

---

## 4. CAMADA 2: QUALIDADE DE ODDS

### 4.1 Avaliação de Qualidade de Odds

```python
# vbq/decision/odds_quality.py
class OddsQualityEvaluator:
    """Avalia qualidade de odds."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_odds_quality(self, game_id: str, market: str, odds: float) -> dict:
        """
        Avalia qualidade de odds para uma oportunidade.
        
        Critérios:
        1. Fonte de odds (Tier 1 > Tier 2 > Tier 3)
        2. Best price vs outras casas
        3. Liquidez (volume estimado)
        4. Estabilidade (não mudou muito nos últimos 10 min)
        """
        # Obter odds de todas as casas
        all_odds = self._get_all_odds(game_id, market)
        
        # 1. Fonte de odds
        source_quality = self._evaluate_source_quality(all_odds)
        
        # 2. Best price
        best_price = self._find_best_price(all_odds)
        is_best_price = odds >= best_price * 0.98  # Dentro de 2%
        
        # 3. Liquidez
        liquidity_score = self._estimate_liquidity(game_id, market)
        
        # 4. Estabilidade
        stability_score = self._evaluate_stability(game_id, market)
        
        # Score agregado (0-100)
        quality_score = (
            source_quality * 0.4 +
            (is_best_price * 100) * 0.3 +
            liquidity_score * 0.2 +
            stability_score * 0.1
        )
        
        return {
            'quality_score': quality_score,
            'source_quality': source_quality,
            'is_best_price': is_best_price,
            'liquidity_score': liquidity_score,
            'stability_score': stability_score,
            'meets_threshold': quality_score >= 70
        }
    
    def _evaluate_source_quality(self, all_odds: List[dict]) -> float:
        """
        Avalia qualidade da fonte de odds.
        
        Tier 1 (Fanduel, DraftKings): 100 pontos
        Tier 2 (BetMGM, PointsBet, Caesars): 80 pontos
        Tier 3 (Wynn, BetRivers): 60 pontos
        Tier 4 (Betfair): 90 pontos (melhor preço mas com comissão)
        """
        source_scores = {
            'fanduel': 100,
            'draftkings': 100,
            'betmgm': 80,
            'pointsbet': 80,
            'caesars': 80,
            'wynn': 60,
            'betrivers': 60,
            'betfair': 90
        }
        
        # Retornar score da melhor fonte
        best_source = max(all_odds, key=lambda x: source_scores.get(x['source'], 50))
        return source_scores.get(best_source['source'], 50)
    
    def _find_best_price(self, all_odds: List[dict]) -> float:
        """Encontra a melhor odd."""
        return max([o['odds'] for o in all_odds])
    
    def _estimate_liquidity(self, game_id: str, market: str) -> float:
        """
        Estima liquidez (0-100).
        
        Simplificado: baseado em popularidade do jogo e mercado.
        """
        # Obter popularidade do jogo (baseado em equipas)
        popularity = self._get_game_popularity(game_id)
        
        # Ajustar por mercado
        market_liquidity = {
            'moneyline': 1.0,
            'spread': 0.9,
            'total': 0.8
        }
        
        return min(popularity * market_liquidity.get(market, 0.8) * 100, 100)
    
    def _evaluate_stability(self, game_id: str, market: str) -> float:
        """
        Avalia estabilidade das odds (0-100).
        
        Compara odds atuais com odds de 10 min atrás.
        """
        # Obter odds de 10 min atrás
        historical_odds = self._get_historical_odds(game_id, market, minutes_ago=10)
        
        if not historical_odds:
            return 50  # Sem dados
        
        current_odds = self._get_current_odds(game_id, market)
        
        # Calcular variação percentual
        variation = abs(current_odds - historical_odds) / historical_odds * 100
        
        # Menor variação = mais estável
        if variation < 1.0:
            return 100
        elif variation < 2.0:
            return 80
        elif variation < 5.0:
            return 60
        else:
            return 40
```

---

## 5. CAMADA 3: CLV HISTÓRICO

### 5.1 Avaliação de CLV Histórico

```python
# vbq/decision/clv_evaluator.py
class CLVEvaluator:
    """Avalia CLV histórico para filtrar oportunidades."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_clv_history(self, game_id: str, market: str) -> dict:
        """
        Avalia CLV histórico para um jogo/mercado.
        
        Critérios:
        1. CLV médio 30 dias > 0%
        2. CLV consistente (não muito volátil)
        3. CLV recente (últimos 7 dias) também positivo
        """
        # Obter CLV histórico
        clv_history = self._get_clv_history(game_id, market, days=30)
        
        if not clv_history:
            return {
                'clv_avg': 0,
                'clv_std': 0,
                'clv_recent_avg': 0,
                'meets_threshold': False,
                'rejection_reason': 'no_clv_history'
            }
        
        # 1. CLV médio 30 dias
        clv_avg = np.mean(clv_history)
        
        # 2. Consistência (desvio padrão)
        clv_std = np.std(clv_history)
        consistency_score = max(0, 100 - clv_std * 10)  # Menor std = melhor
        
        # 3. CLV recente (7 dias)
        clv_recent = clv_history[-7:] if len(clv_history) >= 7 else clv_history
        clv_recent_avg = np.mean(clv_recent)
        
        # Threshold: CLV médio > 0%
        meets_threshold = clv_avg > 0
        
        return {
            'clv_avg': clv_avg,
            'clv_std': clv_std,
            'clv_recent_avg': clv_recent_avg,
            'consistency_score': consistency_score,
            'meets_threshold': meets_threshold,
            'rejection_reason': f"clv_negative ({clv_avg:.2f}%)" if not meets_threshold else None
        }
```

---

## 6. CAMADA 4: EXPOSIÇÃO E LIMITES

### 6.1 Verificação de Exposição

```python
# vbq/decision/exposure_checker.py
class ExposureChecker:
    """Verifica limites de exposição."""
    
    def __init__(self, db: Session):
        self.db = db
        self.bankroll = self._get_current_bankroll()
    
    def check_exposure_limits(self, game_id: str, proposed_stake: float) -> dict:
        """
        Verifica se stake proposto respeita limites de exposição.
        
        Limites:
        - Max stake por aposta: 2% da banca
        - Max exposição por jogo: 4% da banca
        - Max exposição diária: 12% da banca
        - Max exposição por mercado: 6% da banca
        """
        # 1. Max stake por aposta
        max_stake_per_bet = self.bankroll * 0.02
        if proposed_stake > max_stake_per_bet:
            return {
                'approved': False,
                'rejection_reason': f"exceeds_max_stake_per_bet ({proposed_stake:.2f} > {max_stake_per_bet:.2f})"
            }
        
        # 2. Max exposição por jogo
        game_exposure = self._get_game_exposure(game_id)
        max_game_exposure = self.bankroll * 0.04
        if game_exposure + proposed_stake > max_game_exposure:
            return {
                'approved': False,
                'rejection_reason': f"exceeds_max_game_exposure ({game_exposure + proposed_stake:.2f} > {max_game_exposure:.2f})"
            }
        
        # 3. Max exposição diária
        daily_exposure = self._get_daily_exposure()
        max_daily_exposure = self.bankroll * 0.12
        if daily_exposure + proposed_stake > max_daily_exposure:
            return {
                'approved': False,
                'rejection_reason': f"exceeds_max_daily_exposure ({daily_exposure + proposed_stake:.2f} > {max_daily_exposure:.2f})"
            }
        
        # 4. Max exposição por mercado
        market_exposure = self._get_market_exposure()
        max_market_exposure = self.bankroll * 0.06
        if market_exposure + proposed_stake > max_market_exposure:
            return {
                'approved': False,
                'rejection_reason': f"exceeds_max_market_exposure ({market_exposure + proposed_stake:.2f} > {max_market_exposure:.2f})"
            }
        
        return {
            'approved': True,
            'rejection_reason': None
        }
```

---

## 7. RANKING DE OPORTUNIDADES

### 7.1 Sistema de Pontuação

```python
# vbq/decision/opportunity_ranker.py
class OpportunityRanker:
    """Ranking de oportunidades."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def rank_opportunities(self, opportunities: List[dict]) -> List[dict]:
        """
        Rankea oportunidades por pontuação 0-100.
        
        Pontuação:
        - Edge: 30 pontos (0.5% = 10 pts, 10% = 30 pts)
        - Qualidade odds: 25 pontos (0-100 score)
        - CLV histórico: 20 pontos (0-100 score)
        - Consistência: 15 pontos (0-100 score)
        - Liquidez: 10 pontos (0-100 score)
        """
        for opp in opportunities:
            # Edge score
            edge_pct = opp['edge_calculation']['edge_pct']
            edge_score = min(30, max(0, edge_pct * 3))  # 0.5% = 1.5 pts, 10% = 30 pts
            
            # Qualidade odds score
            odds_quality = opp['odds_quality']['quality_score']
            odds_score = odds_quality * 0.25  # 0-100 → 0-25 pts
            
            # CLV score
            clv_score = opp.get('clv_evaluation', {}).get('consistency_score', 50) * 0.2  # 0-100 → 0-20 pts
            
            # Consistência score
            consistency_score = opp.get('clv_evaluation', {}).get('consistency_score', 50) * 0.15  # 0-100 → 0-15 pts
            
            # Liquidez score
            liquidity_score = opp['odds_quality']['liquidity_score'] * 0.1  # 0-100 → 0-10 pts
            
            # Pontuação total
            total_score = edge_score + odds_score + clv_score + consistency_score + liquidity_score
            
            opp['ranking'] = {
                'total_score': total_score,
                'edge_score': edge_score,
                'odds_score': odds_score,
                'clv_score': clv_score,
                'consistency_score': consistency_score,
                'liquidity_score': liquidity_score
            }
        
        # Ordenar por pontuação
        ranked = sorted(opportunities, key=lambda x: x['ranking']['total_score'], reverse=True)
        
        return ranked
```

---

## 8. DECISÃO FINAL

### 8.1 Pipeline de Decisão Completo

```python
# vbq/decision/decision_engine.py
class DecisionEngine:
    """Motor de decisão de apostas."""
    
    def __init__(self, db: Session):
        self.db = db
        self.edge_calculator = EdgeCalculator(db)
        self.odds_quality_evaluator = OddsQualityEvaluator(db)
        self.clv_evaluator = CLVEvaluator(db)
        self.exposure_checker = ExposureChecker(db)
        self.opportunity_ranker = OpportunityRanker(db)
        self.kelly_engine = KellyEngine(db)
    
    def evaluate_opportunities(self, games: List[dict]) -> List[dict]:
        """
        Avalia oportunidades de aposta através do pipeline completo.
        
        Pipeline:
        1. Calcular edge (Camada 1)
        2. Filtrar por edge
        3. Avaliar qualidade de odds (Camada 2)
        4. Filtrar por qualidade
        5. Avaliar CLV histórico (Camada 3)
        6. Filtrar por CLV
        7. Calcular stake via Kelly
        8. Verificar exposição (Camada 4)
        9. Filtrar por exposição
        10. Rankear oportunidades
        11. Selecionar top N
        """
        opportunities = []
        
        for game in games:
            opp = {
                'game_id': game['game_id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'market': game['market'],
                'selection': game['selection'],
                'probability': game['probability'],
                'odds': game['odds']
            }
            
            # Camada 1: Edge
            opp['edge_calculation'] = self.edge_calculator.calculate_edge(
                opp['probability'], opp['odds']
            )
            
            # Filtro 1: Edge
            if not opp['edge_calculation']['threshold_met']:
                opp['rejection_reason'] = opp['edge_calculation'].get('rejection_reason', 'edge_below_threshold')
                opp['approved'] = False
                opportunities.append(opp)
                continue
            
            # Camada 2: Qualidade de odds
            opp['odds_quality'] = self.odds_quality_evaluator.evaluate_odds_quality(
                opp['game_id'], opp['market'], opp['odds']
            )
            
            # Filtro 2: Qualidade de odds
            if not opp['odds_quality']['meets_threshold']:
                opp['rejection_reason'] = f"odds_quality_low ({opp['odds_quality']['quality_score']:.1f} < 70)"
                opp['approved'] = False
                opportunities.append(opp)
                continue
            
            # Camada 3: CLV histórico
            opp['clv_evaluation'] = self.clv_evaluator.evaluate_clv_history(
                opp['game_id'], opp['market']
            )
            
            # Filtro 3: CLV
            if not opp['clv_evaluation']['meets_threshold']:
                opp['rejection_reason'] = opp['clv_evaluation']['rejection_reason']
                opp['approved'] = False
                opportunities.append(opp)
                continue
            
            # Calcular stake via Kelly
            kelly_result = self.kelly_engine.calculate_stake_for_signal(
                opp['game_id'],
                opp['probability'],
                opp['odds']
            )
            opp['stake'] = kelly_result['stake']
            opp['stake_pct'] = kelly_result['stake_pct']
            
            # Camada 4: Exposição
            exposure_check = self.exposure_checker.check_exposure_limits(
                opp['game_id'], opp['stake']
            )
            
            # Filtro 4: Exposição
            if not exposure_check['approved']:
                opp['rejection_reason'] = exposure_check['rejection_reason']
                opp['approved'] = False
                opportunities.append(opp)
                continue
            
            # Passou todos os filtros
            opp['approved'] = True
            opportunities.append(opp)
        
        # Rankear oportunidades
        ranked = self.opportunity_ranker.rank_opportunities(opportunities)
        
        # Selecionar top N (configurável, default 10)
        max_signals = self._get_max_signals_per_day()
        approved = [o for o in ranked if o['approved']]
        selected = approved[:max_signals]
        
        # Marcar não selecionados como rejeitados
        for opp in approved[max_signals:]:
            opp['approved'] = False
            opp['rejection_reason'] = 'not_in_top_ranking'
        
        return ranked
```

---

## 9. SISTEMA DE PRIORIZAÇÃO

### 9.1 Seleção de Top N

```python
def select_top_opportunities(opportunities: List[dict], max_signals: int = 10) -> List[dict]:
    """
    Seleciona as top N oportunidades.
    
    Estratégia:
    1. Rankear por pontuação
    2. Selecionar top N
    3. Garantir diversificação (máximo 2 apostas por jogo)
    """
    # Ordenar por ranking
    ranked = sorted(opportunities, key=lambda x: x['ranking']['total_score'], reverse=True)
    
    selected = []
    games_selected = {}  # game_id → count
    
    for opp in ranked:
        if len(selected) >= max_signals:
            break
        
        # Verificar diversificação (máximo 2 por jogo)
        game_count = games_selected.get(opp['game_id'], 0)
        if game_count >= 2:
            continue
        
        selected.append(opp)
        games_selected[opp['game_id']] = game_count + 1
    
    return selected
```

---

## 10. MONITORIZAÇÃO

### 10.1 Métricas de Decisão

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| decision_approval_rate | Taxa de aprovação de oportunidades | 10-30% |
| decision_avg_score | Score médio de oportunidades aprovadas | > 70 |
| decision_rejection_distribution | Distribuição de razões de rejeição | - |

---

## 11. EXEMPLOS DE CÓDIGO

### 11.1 CLI Integration

```bash
# Comando CLI para avaliação de oportunidades
vbq-cli decision evaluate --date 2024-01-15

# Ver detalhes de uma oportunidade
vbq-cli decision details --game-id game-123

# Ver ranking de oportunidades
vbq-cli decision ranking --date 2024-01-15
```

---

## 12. TROUBLESHOOTING

### 12.1 Taxa de Aprovação Muito Baixa

```bash
# Verificar thresholds
vbq-cli decision thresholds --show

# Ajustar thresholds temporariamente
# Editar config.yaml: decision.edge_threshold = 3.0
```

### 12.2 Taxa de Aprovação Muito Alta

```bash
# Verificar se CLV está a ser ignorado
vbq-cli decision clv-status

# Aumentar rigor de filtros
# Editar config.yaml: decision.odds_quality_threshold = 80
```

---

## 13. LINKS CRUZADOS

- [[07_Value_Detection/INDEX]] ← Secção mãe
- [[07_Value_Detection/MOTOR_EDGE]] → Motor de edge base
- [[08_Risk_Management/KELLY_CRITERIO_AUTOMATICO]] → Sizing via Kelly
- [[37_CLV_Analytics/ANALISE_CLV_COMPLETO]] → CLV tracking
- [[14_APIs/INTEGRACAO_ODDS_CASAS]] → Qualidade de odds

---

**Custo de implementação:** 0€ (código Python)  
**Tempo estimado de implementação:** 1-2 semanas  
**Prioridade:** ALTA (fundamental para seleção de apostas)
