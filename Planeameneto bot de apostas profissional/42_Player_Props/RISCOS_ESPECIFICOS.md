# RISCOS_ESPECIFICOS — Riscos Específicos de Player Props

**ID:** `PP-006` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar os riscos específicos de player props que não existem (ou são muito menos significativos) em team props, incluindo lesões, mudanças de minutos, role changes, e estratégias de mitigação.

---

## 2. CATEGORIAS DE RISCO

### 2.1 Matriz de Risco

| Risco | Probabilidade | Impacto | Severidade | Mitigação |
|-------|---------------|---------|------------|-----------|
| Lesão do jogador | Média (5-10%) | CRÍTICO | ALTA | Monitor injury reports |
| Mudança de minutos | Alta (20-30%) | ALTO | ALTA | Projetar minutos, filtros |
| Role change | Média (10-15%) | ALTO | ALTA | Monitor lineup changes |
| Blowout | Média (15-20%) | ALTO | MÉDIA | Filtros de spread |
| Load management | Média (10-15%) | ALTO | MÉDIA | Back-to-back tracking |
| Início tardio | Baixa (5%) | MÉDIO | BAIXA | Monitor warmup reports |
| matchup defensivo | Alta (100%) | MÉDIO | MÉDIA | Incluir no modelo |
| Erro de line setting | Baixa (5%) | MÉDIO | BAIXA | Calibração |

---

## 3. LESÕES

### 3.1 Impacto de Lesões

Lesões são o risco mais crítico em player props porque:

- **Anulação total:** Se o jogador não jogar, a aposta é anulada (push)
- **Impacto imediato:** Lesão durante o jogo reduz minutos imediatamente
- **Recuperação variável:** Retorno pode ser em role reduzido
- **Dificuldade de previsão:** Lesões podem ocorrer até minutos antes do jogo

```python
injury_impact = {
    # Tipos de lesão e impacto típico
    "questionable": {
        "probability_play": 0.70,
        "minutes_reduction_if_plays": 0.20,  # 20% menos minutos
        "production_reduction": 0.25,  # 25% menos produção
    },
    
    "doubtful": {
        "probability_play": 0.30,
        "minutes_reduction_if_plays": 0.40,
        "production_reduction": 0.50,
    },
    
    "out": {
        "probability_play": 0.00,
        "minutes_reduction_if_plays": 1.00,
        "production_reduction": 1.00,
    },
    
    "day_to_day": {
        "probability_play": 0.85,
        "minutes_reduction_if_plays": 0.10,
        "production_reduction": 0.15,
    },
}
```

### 3.2 Sistema de Monitorização de Lesões

```python
class InjuryMonitor:
    """
    Monitoriza status de lesões em tempo real.
    """
    
    def __init__(self):
        self.injury_sources = [
            "NBA Official Injury Report",
            "ESPN Injury News",
            "Rotowire",
            "Twitter beat writers",
        ]
    
    def get_injury_status(self, player_id, game_date):
        """
        Obtém status de lesão de múltiplas fontes.
        """
        statuses = []
        
        for source in self.injury_sources:
            status = self._fetch_from_source(player_id, game_date, source)
            if status:
                statuses.append(status)
        
        # Agregar status (usar o mais conservador)
        if not statuses:
            return "healthy"
        
        # Prioridade: out > doubtful > questionable > day_to_day > healthy
        priority = {
            "out": 5,
            "doubtful": 4,
            "questionable": 3,
            "day_to_day": 2,
            "healthy": 1,
        }
        
        final_status = max(statuses, key=lambda x: priority.get(x, 0))
        
        return final_status
    
    def should_bet(self, player_id, game_date, min_confidence="healthy"):
        """
        Decide se deve apostar baseado em status de lesão.
        """
        status = self.get_injury_status(player_id, game_date)
        
        priority = {
            "out": 5,
            "doubtful": 4,
            "questionable": 3,
            "day_to_day": 2,
            "healthy": 1,
        }
        
        if priority.get(status, 0) >= priority.get(min_confidence, 0):
            return False
        
        return True
```

### 3.3 Ajuste de Previsão por Lesão

```python
def adjust_prediction_for_injury(
    base_prediction,
    injury_status,
    stat_type
):
    """
    Ajusta previsão base baseado em status de lesão.
    
    Args:
        base_prediction: previsão base do modelo
        injury_status: status de lesão
        stat_type: PTS/REB/AST
    
    Returns:
        adjusted_prediction: previsão ajustada
    """
    # Fatores de ajuste por status
    adjustment_factors = {
        "healthy": 1.00,
        "day_to_day": 0.85,
        "questionable": 0.75,
        "doubtful": 0.50,
        "out": 0.00,
    }
    
    factor = adjustment_factors.get(injury_status, 1.00)
    
    adjusted_prediction = base_prediction * factor
    
    return adjusted_prediction

# Exemplo
base_pts = 25.0
adjusted_pts = adjust_prediction_for_injury(base_pts, "questionable", "PTS")
# Resultado: 18.75
```

---

## 4. MUDANÇAS DE MINUTOS

### 4.1 Fatores que Afetam Minutos

```python
minutes_factors = {
    # Fatores que aumentam minutos
    "teammate_injured": {
        "impact": "+5-10 minutos",
        "probability": "Alta quando companheiro estrela lesionado",
    },
    
    "matchup_favorable": {
        "impact": "+2-5 minutos",
        "probability": "Média",
    },
    
    "close_game": {
        "impact": "+0-2 minutos",
        "probability": "Alta",
    },
    
    # Fatores que reduzem minutos
    "back_to_back": {
        "impact": "-3-5 minutos",
        "probability": "Média para veteranos",
    },
    
    "blowout": {
        "impact": "-5-15 minutos",
        "probability": "Média (15-20% dos jogos)",
    },
    
    "foul_trouble": {
        "impact": "-5-10 minutos",
        "probability": "Baixa (5-10% dos jogos)",
    },
    
    "poor_performance": {
        "impact": "-3-8 minutos",
        "probability": "Média",
    },
}
```

### 4.2 Sistema de Projeção de Minutos

```python
def project_minutes(
    player_id,
    game_date,
    historical_minutes,
    injury_status,
    is_back_to_back,
    opponent_strength,
    blowout_risk
):
    """
    Projeta minutos para um jogo específico.
    
    Args:
        player_id: ID do jogador
        game_date: data do jogo
        historical_minutes: minutos históricos (últimos 10 jogos)
        injury_status: status de lesão
        is_back_to_back: se é jogo consecutivo
        opponent_strength: força do adversário
        blowout_risk: risco de blowout
    
    Returns:
        minutes_projected: minutos projetados
        confidence: confiança na projeção (0-1)
    """
    # Base: média dos últimos 10 jogos
    base_minutes = historical_minutes.mean()
    
    # Ajuste por lesão
    injury_adjustment = {
        "healthy": 1.00,
        "day_to_day": 0.90,
        "questionable": 0.75,
        "doubtful": 0.50,
        "out": 0.00,
    }
    injury_factor = injury_adjustment.get(injury_status, 1.00)
    
    # Ajuste por back-to-back
    b2b_factor = 0.90 if is_back_to_back else 1.00
    
    # Ajuste por matchup (mais minutos contra equipas fracas)
    matchup_factor = 1.05 if opponent_strength < 0.4 else 1.00
    
    # Ajuste por risco de blowout
    blowout_factor = 1.0 - (blowout_risk * 0.3)  # Até -30% se blowout certo
    
    # Calcular projeção
    minutes_projected = base_minutes * injury_factor * b2b_factor * matchup_factor * blowout_factor
    
    # Calcular confiança
    confidence = 0.8  # Base
    
    if injury_status in ["questionable", "doubtful"]:
        confidence -= 0.3
    if is_back_to_back:
        confidence -= 0.1
    if blowout_risk > 0.3:
        confidence -= 0.2
    
    confidence = max(confidence, 0.0)
    
    return minutes_projected, confidence

# Exemplo
minutes_proj, conf = project_minutes(
    player_id="lebron_james",
    game_date="2024-01-15",
    historical_minutes=pd.Series([32, 35, 30, 33, 31, 34, 32, 35, 30, 33]),
    injury_status="healthy",
    is_back_to_back=False,
    opponent_strength=0.3,
    blowout_risk=0.2
)
# Resultado: ~33 minutos, confiança 0.7
```

### 4.3 Filtros de Minutos

```python
def should_bet_based_on_minutes(
    minutes_projected,
    confidence,
    min_minutes=20,
    min_confidence=0.6
):
    """
    Decide se deve apostar baseado em projeção de minutos.
    """
    if minutes_projected < min_minutes:
        return False, f"Minutos projetados ({minutes_projected:.1f}) abaixo do mínimo ({min_minutes})"
    
    if confidence < min_confidence:
        return False, f"Confiança ({confidence:.2f}) abaixo do mínimo ({min_confidence})"
    
    return True, "Minutos adequados"
```

---

## 5. ROLE CHANGES

### 5.1 Tipos de Role Changes

```python
role_change_types = {
    # Aumento de role
    "promoted_to_starter": {
        "trigger": "titular lesionado ou trade",
        "impact_usage": "+15-25%",
        "impact_minutes": "+8-12 minutos",
        "time_to_stabilize": "5-10 jogos",
    },
    
    "increased_usage": {
        "trigger": "companheiro lesionado",
        "impact_usage": "+10-20%",
        "impact_minutes": "+3-5 minutos",
        "time_to_stabilize": "3-5 jogos",
    },
    
    # Diminuição de role
    "demoted_to_bench": {
        "trigger": "novo titular, trade",
        "impact_usage": "-20-30%",
        "impact_minutes": "-10-15 minutos",
        "time_to_stabilize": "5-10 jogos",
    },
    
    "decreased_usage": {
        "trigger": "novo companheiro estrela",
        "impact_usage": "-10-20%",
        "impact_minutes": "-3-5 minutos",
        "time_to_stabilize": "3-5 jogos",
    },
}
```

### 5.2 Detecção de Role Changes

```python
class RoleChangeDetector:
    """
    Detecta mudanças de role baseado em dados recentes.
    """
    
    def __init__(self, window=5, threshold_usage=0.10, threshold_minutes=5):
        self.window = window
        self.threshold_usage = threshold_usage
        self.threshold_minutes = threshold_minutes
    
    def detect_role_change(self, player_data, current_date):
        """
        Detecta se houve mudança de role recente.
        """
        # Dados recentes
        recent_data = player_data[
            player_data['game_date'] >= current_date - pd.Timedelta(days=self.window * 2)
        ].tail(self.window)
        
        # Dados anteriores (baseline)
        baseline_data = player_data[
            player_data['game_date'] < current_date - pd.Timedelta(days=self.window * 2)
        ].tail(20)
        
        if len(recent_data) < 3 or len(baseline_data) < 10:
            return None, "Dados insuficientes"
        
        # Comparar métricas
        recent_usage = recent_data['usage_rate'].mean()
        baseline_usage = baseline_data['usage_rate'].mean()
        usage_change = recent_usage - baseline_usage
        
        recent_minutes = recent_data['minutes'].mean()
        baseline_minutes = baseline_data['minutes'].mean()
        minutes_change = recent_minutes - baseline_minutes
        
        # Detectar mudança significativa
        if abs(usage_change) > self.threshold_usage or abs(minutes_change) > self.threshold_minutes:
            change_type = self._classify_change(usage_change, minutes_change)
            return change_type, {
                'usage_change': usage_change,
                'minutes_change': minutes_change,
                'recent_usage': recent_usage,
                'baseline_usage': baseline_usage,
            }
        
        return None, "Sem mudança significativa"
    
    def _classify_change(self, usage_change, minutes_change):
        """
        Classifica o tipo de mudança de role.
        """
        if usage_change > 0.15 and minutes_change > 5:
            return "promoted_to_starter"
        elif usage_change > 0.10:
            return "increased_usage"
        elif usage_change < -0.15 and minutes_change < -5:
            return "demoted_to_bench"
        elif usage_change < -0.10:
            return "decreased_usage"
        else:
            return "minor_change"
```

### 5.3 Ajuste por Role Change

```python
def adjust_for_role_change(
    base_prediction,
    role_change_type,
    days_since_change,
    stat_type
):
    """
    Ajusta previsão baseado em mudança de role.
    
    Args:
        base_prediction: previsão base
        role_change_type: tipo de mudança
        days_since_change: dias desde a mudança
        stat_type: PTS/REB/AST
    
    Returns:
        adjusted_prediction: previsão ajustada
    """
    # Fatores de ajuste por tipo
    adjustment_factors = {
        "promoted_to_starter": 1.25,
        "increased_usage": 1.15,
        "demoted_to_bench": 0.70,
        "decreased_usage": 0.85,
        "minor_change": 1.00,
    }
    
    # Fator de estabilização (mudanças levam tempo a estabilizar)
    stabilization_days = 7
    stabilization_factor = min(days_since_change / stabilization_days, 1.0)
    
    # Ajuste parcial se não estabilizado
    base_factor = adjustment_factors.get(role_change_type, 1.00)
    adjusted_factor = 1.0 + (base_factor - 1.0) * stabilization_factor
    
    adjusted_prediction = base_prediction * adjusted_factor
    
    return adjusted_prediction
```

---

## 6. BLOWOUTS

### 6.1 Impacto de Blowouts

Blowouts (vitórias por >15 pontos) reduzem minutos de titulares porque:

- Coach tira titulares no 4º quart
- Garbage time reduz intensidade
- Jogadores não precisam produzir

```python
blowout_impact = {
    # Impacto por margem de vitória
    "15-20 points": {
        "minutes_reduction": "-3-5 minutos",
        "production_reduction": "-10-15%",
    },
    
    "20-25 points": {
        "minutes_reduction": "-5-8 minutos",
        "production_reduction": "-15-25%",
    },
    
    "25+ points": {
        "minutes_reduction": "-8-15 minutos",
        "production_reduction": "-25-40%",
    },
}
```

### 6.2 Previsão de Blowout

```python
def predict_blowout_probability(
    spread_line,
    team_talent,
    opponent_talent,
    rest_advantage,
    home_court_advantage
):
    """
    Preve probabilidade de blowout.
    
    Args:
        spread_line: linha de spread
        team_talent: talento da equipa (0-1)
        opponent_talent: talento do adversário (0-1)
        rest_advantage: vantagem de descanso (True/False)
        home_court_advantage: vantagem de casa (True/False)
    
    Returns:
        blowout_prob: probabilidade de blowout (0-1)
    """
    # Base: spread grande aumenta probabilidade
    base_prob = max(0, (abs(spread_line) - 5) / 20)  # 0 se spread <5, aumenta linearmente
    
    # Ajuste por diferença de talento
    talent_gap = abs(team_talent - opponent_talent)
    talent_adjustment = talent_gap * 0.3
    
    # Ajuste por descanso
    rest_adjustment = 0.1 if rest_advantage else 0.0
    
    # Ajuste por casa
    home_adjustment = 0.05 if home_court_advantage else -0.05
    
    # Probabilidade final
    blowout_prob = base_prob + talent_adjustment + rest_adjustment + home_adjustment
    
    # Limitar entre 0 e 0.5 (máximo 50%)
    blowout_prob = max(0, min(blowout_prob, 0.5))
    
    return blowout_prob

# Exemplo
prob = predict_blowout_probability(
    spread_line=12.5,
    team_talent=0.8,
    opponent_talent=0.4,
    rest_advantage=True,
    home_court_advantage=True
)
# Resultado: ~0.35 (35% de probabilidade de blowout)
```

### 6.3 Filtros de Blowout

```python
def should_bet_based_on_blowout_risk(
    blowout_prob,
    max_blowout_prob=0.30
):
    """
    Decide se deve apostar baseado em risco de blowout.
    """
    if blowout_prob > max_blowout_prob:
        return False, f"Risco de blowout ({blowout_prob:.2f}) acima do máximo ({max_blowout_prob})"
    
    return True, "Risco de blowout aceitável"
```

---

## 7. LOAD MANAGEMENT

### 7.1 Padrões de Load Management

```python
load_management_patterns = {
    # Jogadores veteranos
    "veteran_stars": {
        "age_threshold": 32,
        "back_to_back_sit_out_rate": 0.30,
        "minutes_reduction_b2b": 0.15,
    },
    
    # Jogadores com histórico de lesões
    "injury_prone": {
        "rest_days_preferred": 2,
        "back_to_back_sit_out_rate": 0.50,
        "minutes_reduction_b2b": 0.20,
    },
    
    # Jogadores jovens
    "young_players": {
        "age_threshold": 22,
        "back_to_back_sit_out_rate": 0.05,
        "minutes_reduction_b2b": 0.05,
    },
}
```

### 7.2 Detecção de Load Management

```python
class LoadManagementDetector:
    """
    Detecta padrões de load management.
    """
    
    def __init__(self):
        self.load_management_history = {}
    
    def detect_load_management_risk(self, player_id, player_age, injury_history):
        """
    Detecta risco de load management para um jogador.
    """
        risk_score = 0.0
        
        # Fator idade
        if player_age >= 32:
            risk_score += 0.3
        elif player_age >= 30:
            risk_score += 0.2
        
        # Fator histórico de lesões
        if injury_history['major_injuries_last_2_years'] >= 2:
            risk_score += 0.3
        elif injury_history['major_injuries_last_2_years'] >= 1:
            risk_score += 0.15
        
        # Fator histórico de load management
        if player_id in self.load_management_history:
            lm_rate = self.load_management_history[player_id]['sit_out_rate']
            risk_score += lm_rate * 0.5
        
        return min(risk_score, 1.0)
    
    def is_back_to_back(self, game_date, previous_game_date):
        """
        Verifica se é jogo consecutivo.
        """
        if previous_game_date is None:
            return False
        
        days_diff = (game_date - previous_game_date).days
        return days_diff == 1
```

### 7.3 Ajuste por Load Management

```python
def adjust_for_load_management(
    base_prediction,
    is_back_to_back,
    load_management_risk,
    player_age
):
    """
    Ajusta previsão baseado em risco de load management.
    """
    if not is_back_to_back:
        return base_prediction
    
    # Fator de ajuste baseado em risco
    if load_management_risk > 0.5:
        adjustment_factor = 0.70  # Redução de 30%
    elif load_management_risk > 0.3:
        adjustment_factor = 0.85  # Redução de 15%
    elif load_management_risk > 0.1:
        adjustment_factor = 0.95  # Redução de 5%
    else:
        adjustment_factor = 1.00  # Sem ajuste
    
    adjusted_prediction = base_prediction * adjustment_factor
    
    return adjusted_prediction
```

---

## 8. ESTRATÉGIA INTEGRADA DE GESTÃO DE RISCO

### 8.1 Pipeline de Decisão de Betting

```python
class PlayerPropsRiskManager:
    """
    Gestor de risco integrado para player props.
    """
    
    def __init__(self):
        self.injury_monitor = InjuryMonitor()
        self.role_change_detector = RoleChangeDetector()
        self.load_management_detector = LoadManagementDetector()
    
    def should_place_bet(
        self,
        player_id,
        game_date,
        base_prediction,
        line,
        edge,
        player_data,
        game_context
    ):
        """
        Decisão integrada de se apostar ou não.
        """
        # 1. Verificar lesão
        injury_status = self.injury_monitor.get_injury_status(player_id, game_date)
        if injury_status in ["doubtful", "out"]:
            return False, f"Jogador {injury_status}"
        
        # 2. Projetar minutos
        minutes_proj, minutes_conf = self.project_minutes(player_id, game_date, player_data)
        if minutes_proj < 20 or minutes_conf < 0.6:
            return False, f"Minutos inadequados: {minutes_proj:.1f} (conf: {minutes_conf:.2f})"
        
        # 3. Verificar mudança de role
        role_change, role_info = self.role_change_detector.detect_role_change(
            player_data, game_date
        )
        if role_change in ["demoted_to_bench", "decreased_usage"]:
            return False, f"Role change negativo: {role_change}"
        
        # 4. Verificar risco de blowout
        blowout_prob = self.predict_blowout_probability(game_context)
        if blowout_prob > 0.30:
            return False, f"Risco de blowout alto: {blowout_prob:.2f}"
        
        # 5. Verificar load management
        is_b2b = self.load_management_detector.is_back_to_back(
            game_date, player_data.iloc[-1]['game_date']
        )
        lm_risk = self.load_management_detector.detect_load_management_risk(
            player_id, player_data['age'].iloc[-1], player_data['injury_history']
        )
        if is_b2b and lm_risk > 0.5:
            return False, f"Load management risk alto em back-to-back: {lm_risk:.2f}"
        
        # 6. Ajustar previsão por fatores de risco
        adjusted_prediction = base_prediction
        adjusted_prediction = self.adjust_for_injury(adjusted_prediction, injury_status)
        adjusted_prediction = self.adjust_for_role_change(adjusted_prediction, role_change)
        adjusted_prediction = self.adjust_for_load_management(
            adjusted_prediction, is_b2b, lm_risk
        )
        
        # 7. Recalcular edge com previsão ajustada
        adjusted_edge = self.calculate_edge(adjusted_prediction, line)
        
        # 8. Verificar se edge ainda é suficiente
        if adjusted_edge < 0.02:  # Mínimo 2%
            return False, f"Edge ajustado ({adjusted_edge:.2%}) abaixo do mínimo"
        
        return True, f"Aposta aprovada (edge ajustado: {adjusted_edge:.2%})"
```

---

## 9. BACKLOG

- [ ] Implementar sistema de monitorização de lesões
- [ ] Implementar sistema de projeção de minutos
- [ ] Implementar detetor de role changes
- [ ] Implementar detetor de load management
- [ ] Implementar previsão de blowout
- [ ] Integrar todos os filtros no pipeline de decisão
- [ ] Calibrar thresholds com dados históricos
- [ ] Documentar casos de edge
- [ ] Criar alertas em tempo real para mudanças de risco

---

## 10. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/DIFERENCAS_TEAM_VS_PLAYER]] → Diferenças de risco
- [[42_Player_Props/FEATURES_JOGADOR]] → Features de risco
- [[08_Risk_Management/INDEX]] → Gestão de risco geral