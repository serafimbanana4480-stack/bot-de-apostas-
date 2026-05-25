# MMA/UFC INTEGRATION — Estratégia Detalhada

**ID:** `SEC-43-02` | **Status:** #status/pending | **Versão:** `2.0.0-MMA`

---

## 1. OBJETIVO

Expandir o sistema para incluir MMA/UFC com modelo Bayesiano e edge estimado de 5-8%.

---

## 2. MERCADOS PRIORITÁRIOS

### 2.1 Tipos de Mercados

| Mercado | Edge Estimado | Volume | Prioridade |
|---------|---------------|--------|------------|
| **Moneyline** | 5-8% | Alto | MÁXIMA |
| **Method of Victory** | 6-10% | Médio | ALTA |
| **Over/Under Rounds** | 4-6% | Médio | MÉDIA |
| **Fight Goes Distance** | 3-5% | Médio | MÉDIA |

### 2.2 Foco em Nichos de Alto Edge

**UFC Preliminares (Prelims):**
- Menos atenção dos analistas
- Edge potencial: 5-8%
- Volume: Médio

**UFC Heavyweights:**
- Alta variância (KO mais provável)
- Edge potencial: 6-9%
- Volume: Médio

---

## 3. DADOS E FONTES

### 3.1 Dados de Lutadores

```python
# Fontes de dados
mma_api_sources = [
    "UFC Stats API",      # Dados oficiais UFC
    "Sherdog",            # Histórico de lutas
    "Tapology",           # Rankings e stats
    "FightMetric",        # Dados avançados
]

# Dados necessários
required_data = {
    'fighter_stats': ['record', 'win_by_ko', 'win_by_submission', 'win_by_decision'],
    'physical': ['height', 'reach', 'weight', 'age'],
    'recent_performance': ['last_5_fights', 'last_10_fights', 'streak'],
    'style': ['striking_accuracy', 'grappling_accuracy', 'takedown_defense'],
    'card_position': ['prelim_vs_main', 'televised_flag'],
}
```

---

## 4. MODELO PREDITIVO BAYESIAN

### 4.1 Arquitetura

```
┌─────────────────────────────────────────┐
│         FEATURES (50-60)                 │
│  Stats │ Physical │ Style │ Card Position│
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      MODELO BAYESIAN HIERÁRQUICO        │
│  Prior: Distribuição de vitórias         │
│  Likelihood: Dados históricos            │
│  Posterior: Probabilidade de vitória     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    META-LABELING COM INCERTEZA          │
│  Features: std_dev_prob, effective_sample│
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         CÁLCULO DE EDGE                 │
│  edge = (P_posterior × odd) - 1         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      GESTÃO DE RISCO (Kelly)             │
│  Stake ajustado por incerteza            │
└─────────────────────────────────────────┘
```

### 4.2 Modelo Bayesiano

```python
import numpy as np
from scipy.stats import beta

class BayesianMMAFighter:
    """
    Modelo Bayesiano para força de lutador.
    """
    def __init__(self):
        self.prior_alpha = 1.0
        self.prior_beta = 1.0
        self.posterior_alpha = {}
        self.posterior_beta = {}
    
    def update_from_fight(self, fighter_id, won):
        """
        Atualiza posterior com resultado de luta.
        """
        if fighter_id not in self.posterior_alpha:
            self.posterior_alpha[fighter_id] = self.prior_alpha
            self.posterior_beta[fighter_id] = self.prior_beta
        
        # Atualizar posterior
        if won:
            self.posterior_alpha[fighter_id] += 1
        else:
            self.posterior_beta[fighter_id] += 1
    
    def get_fighter_strength(self, fighter_id):
        """
        Retorna força estimada do lutador (0-1).
        """
        if fighter_id not in self.posterior_alpha:
            return 0.5  # Prior uniforme
        
        alpha = self.posterior_alpha[fighter_id]
        beta = self.posterior_beta[fighter_id]
        
        # Média da distribuição Beta
        strength = alpha / (alpha + beta)
        
        return strength
    
    def get_fighter_uncertainty(self, fighter_id):
        """
        Retorna incerteza (desvio padrão da posterior).
        """
        if fighter_id not in self.posterior_alpha:
            return 0.5  # Alta incerteza para novos lutadores
        
        alpha = self.posterior_alpha[fighter_id]
        beta = self.posterior_beta[fighter_id]
        
        # Desvio padrão da distribuição Beta
        std_dev = np.sqrt((alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1)))
        
        return std_dev
    
    def get_effective_sample_size(self, fighter_id):
        """
        Retorna número efetivo de observações.
        """
        if fighter_id not in self.posterior_alpha:
            return 0
        
        alpha = self.posterior_alpha[fighter_id]
        beta = self.posterior_beta[fighter_id]
        
        # Alpha + beta - 2 = número de observações (ajustado pelo prior)
        effective_n = alpha + beta - 2
        
        return max(0, effective_n)
```

### 4.3 Modelo de Luta

```python
class BayesianMMAMatchup:
    """
    Modelo Bayesiano para matchup entre dois lutadores.
    """
    def __init__(self):
        self.fighter_model = BayesianMMAFighter()
    
    def predict_matchup(self, fighter_a, fighter_b):
        """
        Prevê probabilidade de vitória do fighter A.
        """
        # Obter forças de ambos lutadores
        strength_a = self.fighter_model.get_fighter_strength(fighter_a)
        strength_b = self.fighter_model.get_fighter_strength(fighter_b)
        
        # Calcular probabilidade usando logit
        logit = np.log(strength_a / (1 - strength_a)) - np.log(strength_b / (1 - strength_b))
        prob_a = 1 / (1 + np.exp(-logit))
        
        # Obter incerteza
        std_a = self.fighter_model.get_fighter_uncertainty(fighter_a)
        std_b = self.fighter_model.get_fighter_uncertainty(fighter_b)
        combined_uncertainty = np.sqrt(std_a**2 + std_b**2)
        
        # Obter sample sizes
        sample_a = self.fighter_model.get_effective_sample_size(fighter_a)
        sample_b = self.fighter_model.get_effective_sample_size(fighter_b)
        
        return {
            'prob_a': prob_a,
            'std_dev_prob': combined_uncertainty,
            'effective_sample_size': min(sample_a, sample_b)
        }
```

---

## 5. FEATURES PARA MMA

### 5.1 Features de Stats (20 features)

```python
# Record geral
win_rate = wins / total_fights
win_by_ko_rate = wins_by_ko / total_fights
win_by_sub_rate = wins_by_submission / total_fights
win_by_decision_rate = wins_by_decision / total_fights

# Performance recente
last_5_win_rate = wins_last_5 / 5
last_10_win_rate = wins_last_10 / 10
current_streak = current_win_streak  # Positivo para vitórias
momentum = last_5_win_rate - last_10_win_rate
```

### 5.2 Features Físicas (10 features)

```python
height_cm = fighter_height
reach_cm = fighter_reach
weight_kg = fighter_weight
age_years = fighter_age
height_reach_advantage = reach_cm - avg_reach_division
weight_cut_difficulty = weight_difficulty_score
```

### 5.3 Features de Estilo (15 features)

```python
striking_accuracy_pct = significant_strikes_landed / significant_strikes_attempted
grappling_accuracy_pct = takedowns_landed / takedowns_attempted
takedown_defense_pct = takedowns_defended / takedowns_attempted_against
strikes_absorbed_per_min = strikes_absorbed / fight_time
takedowns_attempted_per_15min = takedowns_attempted / (fight_time / 15)
```

### 5.4 Features de Card Position (5 features)

```python
prelim_flag = 1 if is_prelim else 0
televised_flag = 1 if will_be_televised else 0
card_position = position_on_card (1-13)
main_event_flag = 1 if is_main_event else 0
co_main_event_flag = 1 if is_co_main else 0
```

---

## 6. META-LABELING COM INCERTEZA

### 6.1 Features de Incerteza

```python
def extract_uncertainty_features(matchup_prediction):
    """
    Extrai features de incerteza para meta-labeling.
    """
    return {
        'std_dev_prob': matchup_prediction['std_dev_prob'],
        'effective_sample_size': matchup_prediction['effective_sample_size'],
        'uncertainty_ratio': matchup_prediction['std_dev_prob'] / matchup_prediction['prob_a'],
        'sample_size_threshold': 1 if matchup_prediction['effective_sample_size'] < 5 else 0
    }
```

### 6.2 Meta-Modelo com Incerteza

```python
from xgboost import XGBClassifier

meta_mma_config = {
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "auc"],
    "max_depth": 3,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 20,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "seed": 42,
    "n_estimators": 500,
}

# Features do meta-modelo:
# - edge calculado
# - confiança do modelo
# - std_dev_prob (incerteza)
# - effective_sample_size
# - regime (favorito vs underdog)
```

---

## 7. RETREINO PÓS-EVENTO

### 7.1 Retreino Após Cada Card

```python
class MMAPostEventRetrainer:
    """
    Retreina modelo após cada card UFC.
    """
    def __init__(self):
        self.bayesian_model = BayesianMMAMatchup()
        self.meta_model = XGBClassifier(**meta_mma_config)
    
    def retrain_after_card(self, card_id, results):
        """
        Retreina após card UFC.
        """
        # 1. Atualizar modelo Bayesiano com novos resultados
        for fight in results:
            winner_id = fight['winner']
            loser_id = fight['loser']
            
            self.bayesian_model.fighter_model.update_from_fight(winner_id, won=True)
            self.bayesian_model.fighter_model.update_from_fight(loser_id, won=False)
        
        # 2. Retreinar meta-modelo com novos dados
        new_features = extract_mma_features(results)
        new_outcomes = [1 if f['winner'] == f['fighter_a'] else 0 for f in results]
        
        # Warm start retreino
        self.meta_model.fit(
            new_features,
            new_outcomes,
            xgb_model=self.meta_model.get_booster() if hasattr(self.meta_model, 'get_booster') else None
        )
        
        # 3. Validar melhoria
        if validate_improvement(self.meta_model) > 0.01:
            promote_to_production(self.meta_model)
```

---

## 8. GESTÃO DE RISCO ESPECÍFICA PARA MMA

### 8.1 Stake Ajustado por Incerteza

```python
def calculate_mma_stake(edge, uncertainty, bankroll):
    """
    Calcula stake para MMA ajustado por incerteza.
    """
    base_stake = kelly_fraction(edge, bankroll)
    
    # Ajustar por incerteza (mais incerteza = menos stake)
    uncertainty_adjustment = 1 / (1 + uncertainty * 10)
    
    # Ajustar por sample size (menos dados = menos stake)
    sample_adjustment = min(1.0, effective_sample_size / 10)
    
    final_stake = base_stake * uncertainty_adjustment * sample_adjustment
    
    # Limitar a 1% da banca por aposta (mais conservativo)
    final_stake = min(final_stake, 0.01 * bankroll)
    
    return final_stake
```

### 8.2 Limites de Exposição

- Máximo 2 apostas por card (moneyline + method of victory)
- Máximo 1% da banca total em MMA por card
- Evitar apostas em lutadores com < 3 lutas (incerteza muito alta)
- Priorizar prelims e heavyweights (maior edge)

---

## 9. CRONOGRAMA DE IMPLEMENTAÇÃO

**Mês 7-8:** Coleta de dados históricos MMA
**Mês 9:** Feature engineering para MMA
**Mês 10:** Treino e validação de modelo Bayesiano
**Mês 11:** Shadow mode (sem apostas reais)
**Mês 12:** Produção com banca reduzida (3% da banca total)

---

## 10. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| Brier Score | < 0.15 |
| CLV médio | > 5% |
| ROI simulado | > 7% |
| Sharpe Ratio | > 0.6 |
| Effective sample size médio | > 5 |

---

## 11. NOTAS DETALHADAS

### 11.1 Weight Classes e Impacto

**Características por Weight Class:**

| Weight Class | KO Rate | Submission Rate | Decision Rate | Volatilidade | Edge Potencial |
|--------------|---------|----------------|--------------|--------------|----------------|
| **Flyweight** | 35% | 25% | 40% | Média | 5-6% |
| **Bantamweight** | 40% | 30% | 30% | Média-Alta | 5-7% |
| **Featherweight** | 45% | 25% | 30% | Alta | 6-8% |
| **Lightweight** | 40% | 35% | 25% | Alta | 6-8% |
| **Welterweight** | 50% | 20% | 30% | Alta | 7-9% |
| **Middleweight** | 55% | 15% | 30% | Muito Alta | 7-10% |
| **Light Heavyweight** | 60% | 15% | 25% | Muito Alta | 8-11% |
| **Heavyweight** | 70% | 10% | 20% | Extrema | 9-12% |

**Notas:**
- Heavyweights têm maior KO rate = maior volatilidade = maior edge potencial
- Classes mais leves têm mais decisions = menor volatilidade = menor edge
- Flyweight/Bantamweight: menos liquidez, edge menor mas mais consistente
- Heavyweight: menos dados (menos lutadores), maior incerteza

**Features de Weight Class:**
```python
weight_class_ko_rate = historical_ko_rate[weight_class]
weight_class_sub_rate = historical_sub_rate[weight_class]
weight_class_decision_rate = historical_decision_rate[weight_class]
weight_class_volatility = historical_volatility[weight_class]
```

### 11.2 Stylistic Matchups

**Princípio Fundamental:** Estilo faz lutas. Lutadores com estilos incompatíveis têm resultados mais imprevisíveis.

**Matchups Favoráveis:**
- Striker vs Wrestler: 50/50 (depende de takedown defense)
- BJJ Specialist vs Striker com má defesa: Advantage BJJ
- Counter-striker vs Aggressive striker: Advantage counter-striker

**Matchups Desfavoráveis (Alta Incerteza):**
- BJJ Specialist vs Wrestler (muito técnico)
- Striker vs Striker (pode ir para qualquer lado)
- Two well-rounded fighters (difícil prever)

**Features de Stylistic Matchup:**
```python
# Differential de skills
striking_diff = fighter_a_striking - fighter_b_striking
grappling_diff = fighter_a_grappling - fighter_b_grappling
takedown_diff = fighter_a_takedown - fighter_b_takedown

# Style compatibility
style_compatibility_score = calculate_style_matchup(fighter_a, fighter_b)

# Historical performance vs similar style
vs_striker_record = fighter_a_record_vs_strikers
vs_wrestler_record = fighter_a_record_vs_wrestlers
vs_bjj_record = fighter_a_record_vs_bjj
```

**Nota:** Stylistic matchup é a feature mais importante em MMA. Deve ter peso alto no modelo.

### 11.3 Fighter Camps e Coaching

**Impacto do Camp:**
- Lutadores de camps de elite (American Top Team, Jackson-Wink, AKA) têm melhor preparação
- Mudança de camp pode indicar problemas ou melhorias
- Quality of coaching afeta gameplan e adaptação

**Camps de Elite (Exemplos):**
- American Top Team (Florida) - Striking + Wrestling balance
- Jackson-Wink MMA (Albuquerque) - Game planning superior
- AKA (San Jose) - Wrestling base
- Tristar (Montreal) - BJJ focus
- Tiger Muay Thai (Thailand) - Muay Thai specialization

**Features de Camp:**
```python
camp_rating = historical_camp_performance[camp_name]
camp_coach_quality = assess_coach_quality(camp_name)
camp_mate_count = number_of_elite_fighters_in_camp
recent_camp_change = days_since_camp_change
camp_change_impact = assess_camp_change_impact(fighter_id)
```

### 11.4 Ring Rust e Layoff

**Ring Rust:**
- Lutadores fora 12+ meses: performance degradada -10% a -20%
- Lutadores fora 6-12 meses: performance degradada -5% a -10%
- Lutadores fora 3-6 meses: performance degradada -2% a -5%

**Fatores que Agravam Ring Rust:**
- Idade avançada (>35 anos)
- Lesões anteriores
- Mudança de weight class
- Retirada temporária

**Features de Ring Rust:**
```python
days_since_last_fight = current_date - last_fight_date
ring_rust_score = calculate_ring_rust(days_since_last_fight, age)
layoff_reason = reason_for_layoff  # injury, personal, contract
age_adjustment = age > 35 ? 1.2 : 1.0
```

**Nota:** Ring rust é um fator crítico, especialmente para lutadores >35 anos.

### 11.5 Fight Camps e Mudanças

**Mudança de Fight Camp:**
- Indica problemas com camp anterior
- Pode ser positivo (melhor treinamento) ou negativo (instabilidade)
- Primeira luta após mudança: maior incerteza

**Indicadores de Problemas:**
- Perdas consecutivas
- Mudanças frequentes de camp
- Problemas de peso (weight cuts)
- Lesões recorrentes

**Features de Camp Change:**
```python
camp_change_recent = days_since_camp_change < 90
camp_change_count = number_of_camp_changes_last_2_years
camp_change_performance = record_after_camp_change
camp_stability_score = 1 / (1 + camp_change_count)
```

### 11.6 Weight Cut Difficulty

**Impacto do Weight Cut:**
- Weight cuts difíceis: -5% a -10% performance
- Weight cuts extremos: -10% a -20% performance
- Histórico de problemas de peso: indicador de risco

**Sinais de Weight Cut Problemático:**
- Histórico de não fazer peso
- Luta em weight class inferior ao natural
- Perda de peso extrema em pouco tempo
- Desidratação visível no weigh-in

**Features de Weight Cut:**
```python
weight_cut_difficulty = assess_weight_cut_difficulty(fighter_id)
weight_mismatch = natural_weight - fight_weight_class
missed_weight_history = count_missed_weight(fighter_id)
weight_cut_time = days_to_cut_weight
```

### 11.7 Southpaw vs Orthodox

**Advantage Southpaw:**
- Lutadores southpaws têm advantage vs orthodox (rareza)
- Orthodox vs Southpaw: +5% edge para southpaw
- Southpaw vs Southpaw: mais imprevisível

**Features de Stance:**
```python
fighter_a_stance = 'southpaw' or 'orthodox'
fighter_b_stance = 'southpaw' or 'orthodox'
stance_advantage = 1 if fighter_a_stance != fighter_b_stance else 0
vs_southpaw_record = fighter_a_record_vs_southpaws
```

### 11.8 Reach e Height Advantage

**Reach Advantage:**
- Reach advantage > 3 inches: +5% a +10% edge
- Reach advantage < -3 inches: -5% a -10% edge
- Height advantage correlaciona mas é menos importante que reach

**Nota:** Reach advantage é mais importante para strikers que para grapplers.

**Features Físicas:**
```python
reach_advantage_inches = fighter_a_reach - fighter_b_reach
height_advantage_inches = fighter_a_height - fighter_b_height
reach_weighted_by_style = reach_advantage * striking_importance
```

### 11.9 Age e Declínio

**Age Curve em MMA:**
- 20-25: Improving, mas inexperiente
- 25-30: Prime, melhor performance
- 30-35: Leve declínio, ainda competitivo
- 35-40: Declínio significativo
- 40+: Declínio severo

**Declínio Acelerado por:**
- Lutas KO/TKO (brain trauma)
- Lutas longas (war damage)
- Weight cuts extremos
- Estilo agressivo

**Features de Age:**
```python
age_years = fighter_age
age_prime = 25 <= age <= 30
age_decline = age > 30 ? (age - 30) * 0.02 : 0
fight_age = current_date - debut_date
total_fights = career_fight_count
```

### 11.10 Fight IQ e Game Planning

**Fight IQ:**
- Capacidade de adaptar durante a luta
- Game planning pré-luta
- Leitura de oponente

**Indicadores de Alto Fight IQ:**
- Lutadores com muitos decisions (adaptam bem)
- Lutadores que vencem estilos variados
- Lutadores com vitórias por métodos diferentes

**Features de Fight IQ:**
```python
decision_win_rate = wins_by_decision / total_wins
method_diversity = number_of_different_win_methods
adaptation_score = assess_in_fight_adaptation(fighter_id)
comeback_wins = count_comeback_victories(fighter_id)
```

### 11.11 Card Position e Pressure

**Card Position Impact:**
- Main Event: Maior pressão, mais tempo para preparação
- Co-Main Event: Pressão moderada
- Prelims: Menos pressão, menos tempo para preparação
- Early Prelims: Menos atenção, maior edge potencial

**Features de Card Position:**
```python
main_event_flag = 1 if is_main_event else 0
co_main_event_flag = 1 if is_co_main else 0
prelim_flag = 1 if is_prelim else 0
early_prelim_flag = 1 if is_early_prelim else 0
card_pressure_score = calculate_card_pressure(card_position)
```

### 11.12 Backtesting Específico para MMA

**Purged CV com Embargo:**
- Purge: Remover dados de 30 dias antes e 30 dias após cada luta
- Embargo: Não usar dados de lutas futuras no treino
- MMA tem menos dados que NBA → embargo mais longo

**Validação Out-of-Sample:**
- Treinar em cards UFC 2019-2022
- Validar em cards UFC 2023-2024
- Testar em cards UFC 2024-2025 (não usados em treino)

**Métricas de Validação:**
```python
# Calcular CLV por tipo de aposta
clv_moneyline = calculate_clv(moneyline_bets)
clv_mov = calculate_clv(method_of_victory_bets)
clv_over_under = calculate_clv(over_under_bets)

# Calcular ROI por weight class
roi_heavyweight = calculate_roi(heavyweight_bets)
roi_lightweight = calculate_roi(lightweight_bets)
roi_flyweight = calculate_roi(flyweight_bets)

# Calcular ROI por card position
roi_main_event = calculate_roi(main_event_bets)
roi_prelims = calculate_roi(prelim_bets)

# Identificar nichos com melhor edge
best_niche = argmax([roi_heavyweight, roi_prelims, roi_mov])
```

### 11.13 Notas de Produção

**Execução em MMA:**
- Liquidez em MMA é menor que NBA/Football
- Odds podem ser mais voláteis (menor eficiência de mercado)
- Prelims têm menos liquidez mas maior edge

**Recomendações:**
- Usar limit orders com timeout de 60 segundos (liquidez menor)
- Monitorizar liquidez antes de cada aposta
- Priorizar prelims e heavyweights (maior edge)
- Evitar apostas em lutadores com < 3 lutas (incerteza muito alta)
- Reduzir stakes se liquidez < 30% do esperado

**Timing de Apostas:**
- 24-48 horas antes: odds iniciais, liquidez baixa
- 6-12 horas antes: odds estabilizadas, liquidez boa
- 1-2 horas antes: weigh-ins confirmados, ajuste por weight cuts
- 30 minutos antes: liquidez máxima, odds mais eficientes

**Nota:** MMA cards são menos frequentes que jogos de NBA/Football → menos oportunidades mas maior edge por aposta.

---

## 12. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/FOOTBALL_INTEGRATION]] → Football
- [[43_Multi_Sport_Expansion/UNIFIED_DECISION_ENGINE]] → Motor unificado
- [[05_Machine_Learning/ENSEMBLE_STACKING]] → Ensemble NBA
- [[08_Risk_Management/EXIT_CRITERIA_SPORT]] → Exit criteria
