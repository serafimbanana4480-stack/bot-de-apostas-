# USAGE_ROLE_CHANGES — Usage e Role Changes

**ID:** `PP-010` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar a análise e gestão de usage rate e role changes em player props, incluindo deteção de mudanças de role, projeção de usage, e ajustes de previsão baseados em alterações de lineup e situação de equipa.

---

## 2. USAGE RATE

### 2.1 Definição e Importância

```python
usage_rate_definition = {
    # Definição
    "definition": "Taxa de uso = % de posses que terminam em ação do jogador (arremesso, turnover, ou assistência que leva a arremesso)",
    
    # Cálculo
    "calculation": "Usage = (FGA + 0.44*FTA + TOV) / (Team FGA + 0.44*Team FTA + Team TOV)",
    
    # Importância para player props
    "importance": {
        "pontos": "Alta correlação (usage ↑ → pontos ↑)",
        "ressaltos": "Correlação moderada (usage ↑ → minutos ↑ → ressaltos ↑)",
        "assistências": "Correlação alta (usage ↑ → toques ↑ → assistências ↑)",
    },
    
    # Range típico
    "typical_range": {
        "star": "25-35%",
        "starter": "15-25%",
        "role_player": "10-20%",
    },
}
```

### 2.2 Cálculo de Usage Rate

```python
def calculate_usage_rate(
    fga,  # Field goals attempts
    fta,  # Free throws attempts
    tov,  # Turnovers
    team_fga,
    team_fta,
    team_tov
):
    """
    Calcula usage rate de um jogador.
    
    Args:
        fga: tentativas de campo
        fta: tentativas de livres
        tov: turnovers
        team_fga: tentativas de campo da equipa
        team_fta: tentativas de livres da equipa
        team_tov: turnovers da equipa
    
    Returns:
        usage_rate: taxa de uso (0-1)
    """
    numerator = fga + 0.44 * fta + tov
    denominator = team_fga + 0.44 * team_fta + team_tov
    
    usage_rate = numerator / denominator if denominator > 0 else 0
    
    return usage_rate

# Exemplo
usage = calculate_usage_rate(
    fga=20, fta=5, tov=3,
    team_fga=90, team_fta=20, team_tov=15
)
# numerator = 20 + 0.44*5 + 3 = 25.2
# denominator = 90 + 0.44*20 + 15 = 113.8
# usage = 25.2/113.8 = 0.221 (22.1%)
```

### 2.3 Features de Usage

```python
usage_features = {
    # Usage atual
    "usage_rate_last1": float,      # Usage no jogo anterior
    "usage_rate_last3": float,      # Média últimos 3 jogos
    "usage_rate_last5": float,      # Média últimos 5 jogos
    "usage_rate_last10": float,     # Média últimos 10 jogos
    "usage_rate_season": float,     # Média da época
    
    # Volatilidade de usage
    "usage_std_last5": float,       # Desvio padrão últimos 5
    "usage_cv_last5": float,        # Coeficiente de variação
    
    # Tendência de usage
    "usage_trend_5": float,         # Tendência últimos 5 jogos
    "usage_trend_10": float,        # Tendência últimos 10 jogos
    
    # Usage vs matchup
    "usage_vs_weak_def": float,     # Usage contra defesas fracas
    "usage_vs_strong_def": float,   # Usage contra defesas fortes
    
    # Usage com/sem companheiros
    "usage_with_star_active": float,  # Usage quando estrela presente
    "usage_with_star_injured": float, # Usage quando estrela ausente
}
```

---

## 3. DETEÇÃO DE ROLE CHANGES

### 3.1 Tipos de Role Changes

```python
role_change_types = {
    # Promoção
    "promoted_to_starter": {
        "trigger": "Titular lesionado, trade, ou decisão do técnico",
        "usage_change": "+15-25%",
        "minutes_change": "+8-12 minutos",
        "production_change": "+20-30%",
        "stabilization_time": "5-10 jogos",
    },
    
    "increased_usage": {
        "trigger": "Companheiro lesionado (mas mantém role de suplente)",
        "usage_change": "+10-20%",
        "minutes_change": "+3-5 minutos",
        "production_change": "+15-25%",
        "stabilization_time": "3-5 jogos",
    },
    
    # Diminuição
    "demoted_to_bench": {
        "trigger": "Novo titular, trade, ou decisão do técnico",
        "usage_change": "-20-30%",
        "minutes_change": "-10-15 minutos",
        "production_change": "-25-40%",
        "stabilization_time": "5-10 jogos",
    },
    
    "decreased_usage": {
        "trigger": "Novo companheiro estrela, ou decisão do técnico",
        "usage_change": "-10-20%",
        "minutes_change": "-3-5 minutos",
        "production_change": "-15-25%",
        "stabilization_time": "3-5 jogos",
    },
    
    # Mudança de posição
    "position_change": {
        "trigger": "Necessidade da equipa",
        "usage_change": "Variável",
        "production_change": "Variável (depende da posição)",
        "stabilization_time": "5-10 jogos",
    },
}
```

### 3.2 Detetor de Role Changes

```python
class RoleChangeDetector:
    """
    Deteta mudanças de role baseado em dados recentes.
    """
    
    def __init__(self, usage_threshold=0.10, minutes_threshold=5, window=5):
        self.usage_threshold = usage_threshold  # 10% de mudança de usage
        self.minutes_threshold = minutes_threshold  # 5 minutos de mudança
        self.window = window  # Janela de jogos para análise
    
    def detect_role_change(self, player_data, current_date):
        """
        Deteta se houve mudança de role recente.
        
        Args:
            player_data: DataFrame com dados históricos do jogador
            current_date: data atual
        
        Returns:
            change_type: tipo de mudança (ou None)
            change_info: detalhes da mudança
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
            return None, {"reason": "Dados insuficientes"}
        
        # Comparar métricas
        recent_usage = recent_data['usage_rate'].mean()
        baseline_usage = baseline_data['usage_rate'].mean()
        usage_change = recent_usage - baseline_usage
        
        recent_minutes = recent_data['minutes'].mean()
        baseline_minutes = baseline_data['minutes'].mean()
        minutes_change = recent_minutes - baseline_minutes
        
        recent_starter_rate = recent_data['is_starter'].mean()
        baseline_starter_rate = baseline_data['is_starter'].mean()
        starter_change = recent_starter_rate - baseline_starter_rate
        
        # Classificar mudança
        change_type, change_info = self._classify_change(
            usage_change, minutes_change, starter_change,
            recent_usage, baseline_usage
        )
        
        return change_type, change_info
    
    def _classify_change(self, usage_change, minutes_change, starter_change, recent_usage, baseline_usage):
        """
        Classifica o tipo de mudança de role.
        """
        # Promoção a titular
        if starter_change > 0.5 and usage_change > 0.15 and minutes_change > 5:
            return "promoted_to_starter", {
                'usage_change': usage_change,
                'minutes_change': minutes_change,
                'starter_change': starter_change,
                'recent_usage': recent_usage,
                'baseline_usage': baseline_usage,
            }
        
        # Aumento de usage (mas mantém suplente)
        elif usage_change > 0.10 and starter_change < 0.3:
            return "increased_usage", {
                'usage_change': usage_change,
                'minutes_change': minutes_change,
                'recent_usage': recent_usage,
                'baseline_usage': baseline_usage,
            }
        
        # Demissão para banco
        elif starter_change < -0.5 and usage_change < -0.15 and minutes_change < -5:
            return "demoted_to_bench", {
                'usage_change': usage_change,
                'minutes_change': minutes_change,
                'starter_change': starter_change,
                'recent_usage': recent_usage,
                'baseline_usage': baseline_usage,
            }
        
        # Diminuição de usage
        elif usage_change < -0.10 and starter_change > -0.3:
            return "decreased_usage", {
                'usage_change': usage_change,
                'minutes_change': minutes_change,
                'recent_usage': recent_usage,
                'baseline_usage': baseline_usage,
            }
        
        # Mudança menor
        elif abs(usage_change) > 0.05:
            return "minor_change", {
                'usage_change': usage_change,
                'minutes_change': minutes_change,
                'recent_usage': recent_usage,
                'baseline_usage': baseline_usage,
            }
        
        # Sem mudança significativa
        else:
            return None, {"reason": "Sem mudança significativa"}
```

---

## 4. PROJEÇÃO DE USAGE

### 4.1 Projeção Base

```python
def project_usage_base(player_id, game_date, historical_data, window=10):
    """
    Projeta usage base baseado em histórico recente.
    
    Args:
        player_id: ID do jogador
        game_date: data do jogo
        historical_data: dados históricos
        window: janela de jogos
    
    Returns:
        usage_projected: usage projetado
        confidence: confiança na projeção (0-1)
    """
    # Dados históricos
    player_history = historical_data[
        (historical_data['player_id'] == player_id) &
        (historical_data['game_date'] < game_date)
    ].tail(window)
    
    if len(player_history) < 3:
        return 0.2, 0.3  # Default baixo com baixa confiança
    
    # Média recente
    usage_recent = player_history['usage_rate'].mean()
    
    # Tendência
    usage_trend = calculate_trend(player_history['usage_rate'])
    
    # Projeção base
    usage_projected = usage_recent + usage_trend
    
    # Limitar a range razoável
    usage_projected = max(0.10, min(0.40, usage_projected))
    
    # Calcular confiança
    std = player_history['usage_rate'].std()
    confidence = max(0, 1 - (std / 0.1))  # Menos volatilidade = mais confiança
    
    return usage_projected, confidence
```

### 4.2 Ajuste por Contexto

```python
def adjust_usage_by_context(
    base_usage,
    opponent_def_rating,
    is_home_game,
    is_back_to_back,
    teammate_injured,
    teammate_usage
):
    """
    Ajusta projeção de usage baseado em contexto.
    
    Args:
        base_usage: usage base projetado
        opponent_def_rating: rating defensivo do adversário (0-1)
        is_home_game: se é jogo em casa
        is_back_to_back: se é jogo consecutivo
        teammate_injured: se companheiro está lesionado
        teammate_usage: usage do companheiro lesionado
    
    Returns:
        usage_adjusted: usage ajustado
    """
    usage_adjusted = base_usage
    
    # Ajuste por matchup (defesa fraca = mais usage)
    if opponent_def_rating > 0.6:  # Defesa fraca
        usage_adjusted *= 1.05
    elif opponent_def_rating < 0.4:  # Defesa forte
        usage_adjusted *= 0.95
    
    # Ajuste por casa
    if is_home_game:
        usage_adjusted *= 1.02
    
    # Ajuste por back-to-back (veteranos jogam menos)
    if is_back_to_back:
        usage_adjusted *= 0.95
    
    # Ajuste por companheiro lesionado
    if teammate_injured and teammate_usage > 0.20:
        # Distribuir usage do companheiro
        usage_increase = teammate_usage * 0.3  # 30% vai para este jogador
        usage_adjusted += usage_increase
    
    # Limitar
    usage_adjusted = max(0.10, min(0.45, usage_adjusted))
    
    return usage_adjusted
```

### 4.3 Projeção Completa

```python
def project_usage_complete(
    player_id,
    game_date,
    historical_data,
    opponent_id,
    is_home_game,
    is_back_to_back,
    injured_teammates
):
    """
    Projeção completa de usage considerando todos os fatores.
    """
    # Projeção base
    base_usage, base_confidence = project_usage_base(player_id, game_date, historical_data)
    
    # Rating defensivo do adversário
    opponent_def_rating = calculate_team_defensive_rating(opponent_id, 'PTS', historical_data)
    
    # Ajuste por companheiros lesionados
    teammate_injured = len(injured_teammates) > 0
    teammate_usage = 0
    if injured_teammates:
        teammate_usage = sum([get_player_usage(tm) for tm in injured_teammates])
    
    # Ajuste por contexto
    usage_adjusted = adjust_usage_by_context(
        base_usage,
        opponent_def_rating,
        is_home_game,
        is_back_to_back,
        teammate_injured,
        teammate_usage
    )
    
    return usage_adjusted, base_confidence
```

---

## 5. AJUSTE DE PREVISÃO POR USAGE

### 5.1 Relação Usage ↔ Produção

```python
usage_production_relationship = {
    # Pontos
    "pts": {
        "correlation": 0.85,  # Alta correlação
        "formula": "PTS = Usage * Team_PTS * (Player_Minutes / Team_Minutes)",
        "sensitivity": "1% de uso ≈ 0.8-1.2 pontos",
    },
    
    # Ressaltos
    "reb": {
        "correlation": 0.60,  # Correlação moderada
        "formula": "REB = Usage * Team_REB * (Player_Minutes / Team_Minutes) * Position_Factor",
        "sensitivity": "1% de uso ≈ 0.3-0.5 ressaltos",
    },
    
    # Assistências
    "ast": {
        "correlation": 0.75,  # Alta correlação
        "formula": "AST = Usage * Team_AST * (Player_Minutes / Team_Minutes) * Playmaker_Factor",
        "sensitivity": "1% de uso ≈ 0.4-0.6 assistências",
    },
}
```

### 5.2 Ajuste por Mudança de Usage

```python
def adjust_prediction_by_usage_change(
    base_prediction,
    current_usage,
    projected_usage,
    stat_type
):
    """
    Ajusta previsão baseado em mudança de usage.
    
    Args:
        base_prediction: previsão base do modelo
        current_usage: usage atual
        projected_usage: usage projetado
        stat_type: PTS/REB/AST
    
    Returns:
        adjusted_prediction: previsão ajustada
    """
    # Calcular fator de mudança
    usage_change_factor = projected_usage / current_usage
    
    # Sensibilidade por estatística
    sensitivity = {
        'PTS': 0.9,   # 1% mudança de uso = 0.9% mudança de pontos
        'REB': 0.5,   # 1% mudança de uso = 0.5% mudança de ressaltos
        'AST': 0.7,   # 1% mudança de uso = 0.7% mudança de assistências
    }
    
    sens = sensitivity.get(stat_type, 0.7)
    
    # Calcular ajuste
    # Se usage aumenta 10%, produção aumenta 10% * sensibilidade
    production_change = (usage_change_factor - 1.0) * sens
    adjustment_factor = 1.0 + production_change
    
    # Limitar ajuste (evitar overfitting)
    adjustment_factor = max(0.7, min(1.3, adjustment_factor))
    
    adjusted_prediction = base_prediction * adjustment_factor
    
    return adjusted_prediction

# Exemplo
base_pred = 25.0
current_usage = 0.20
projected_usage = 0.25  # Aumento de 25%

adjusted = adjust_prediction_by_usage_change(base_pred, current_usage, projected_usage, 'PTS')
# change_factor = 0.25/0.20 = 1.25
# production_change = (1.25 - 1.0) * 0.9 = 0.225
# adjustment_factor = 1.0 + 0.225 = 1.225
# adjusted = 25.0 * 1.225 = 30.6
```

### 5.3 Ajuste por Role Change

```python
def adjust_prediction_by_role_change(
    base_prediction,
    role_change_type,
    days_since_change,
    stat_type
):
    """
    Ajusta previsão baseado em tipo de role change.
    
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

## 6. MONITORIZAÇÃO DE ROLE

### 6.1 Sistema de Monitorização

```python
class RoleMonitor:
    """
    Monitoriza role de jogadores ao longo do tempo.
    """
    
    def __init__(self):
        self.role_history = {}  # player_id -> list of (date, role)
        self.detector = RoleChangeDetector()
    
    def update(self, player_id, game_date, player_data):
        """
    Atualiza monitorização com novo jogo.
    """
        # Detectar mudança de role
        change_type, change_info = self.detector.detect_role_change(
            player_data, game_date
        )
        
        # Guardar histórico
        if player_id not in self.role_history:
            self.role_history[player_id] = []
        
        current_role = self._classify_current_role(player_data.tail(1))
        self.role_history[player_id].append((game_date, current_role))
        
        return change_type, change_info
    
    def _classify_current_role(self, latest_data):
        """
    Classifica role atual baseado em dados mais recentes.
    """
        usage = latest_data['usage_rate'].iloc[0]
        minutes = latest_data['minutes'].iloc[0]
        is_starter = latest_data['is_starter'].iloc[0]
        
        if is_starter and usage >= 0.25 and minutes >= 32:
            return 'star'
        elif is_starter and usage >= 0.15 and minutes >= 25:
            return 'starter'
        else:
            return 'role_player'
    
    def get_current_role(self, player_id):
        """
    Obtém role atual de um jogador.
    """
        if player_id not in self.role_history or len(self.role_history[player_id]) == 0:
            return 'unknown'
        
        return self.role_history[player_id][-1][1]
    
    def get_role_trend(self, player_id, window=5):
        """
    Obtém tendência de role (melhorando/piorando/estável).
    """
        if player_id not in self.role_history:
            return 'unknown'
        
        recent_roles = [role for _, role in self.role_history[player_id][-window:]]
        
        if 'star' in recent_roles and 'role_player' not in recent_roles:
            return 'stable_star'
        elif recent_roles.count('star') > recent_roles.count('role_player'):
            return 'improving'
        elif recent_roles.count('role_player') > recent_roles.count('star'):
            return 'declining'
        else:
            return 'stable'
```

---

## 7. INTEGRAÇÃO NO PIPELINE

### 7.1 Pipeline de Uso e Role

```python
def usage_role_pipeline(
    player_id,
    game_date,
    base_prediction,
    historical_data,
    game_context,
    injured_teammates
):
    """
    Pipeline completo de análise de usage e role.
    """
    # 1. Projetar usage
    usage_projected, usage_confidence = project_usage_complete(
        player_id, game_date, historical_data,
        game_context['opponent_id'],
        game_context['is_home'],
        game_context['is_back_to_back'],
        injured_teammates
    )
    
    # 2. Detectar role change
    role_change, role_info = RoleChangeDetector().detect_role_change(
        historical_data, game_date
    )
    
    # 3. Obter usage atual
    current_usage = historical_data[
        historical_data['player_id'] == player_id
    ].tail(1)['usage_rate'].iloc[0]
    
    # 4. Ajustar previsão por usage
    adjusted_prediction = adjust_prediction_by_usage_change(
        base_prediction,
        current_usage,
        usage_projected,
        'PTS'  # ou REB/AST
    )
    
    # 5. Ajustar por role change se aplicável
    if role_change is not None:
        days_since_change = (game_date - role_info.get('change_date', game_date)).days
        adjusted_prediction = adjust_prediction_by_role_change(
            adjusted_prediction,
            role_change,
            days_since_change,
            'PTS'
        )
    
    return {
        'usage_projected': usage_projected,
        'usage_confidence': usage_confidence,
        'role_change': role_change,
        'role_info': role_info,
        'prediction_adjusted': adjusted_prediction,
    }
```

---

## 8. BACKLOG

- [ ] Implementar cálculo de usage rate
- [ ] Implementar detetor de role changes
- [ ] Implementar projeção de usage base
- [ ] Implementar ajuste de usage por contexto
- [ ] Implementar ajuste de previsão por usage
- [ ] Implementar ajuste por role change
- [ ] Implementar monitorização de role
- [ ] Calibrar sensibilidade de usage por estatística
- [ ] Validar se ajustes de usage melhoram previsões

---

## 9. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/FEATURES_JOGADOR]] → Features de usage
- [[42_Player_Props/RISCOS_ESPECIFICOS]] → Riscos de role changes
- [[42_Player_Props/MODELACAO_PLAYER_PROPS]] → Modelagem