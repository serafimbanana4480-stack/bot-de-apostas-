# ONLINE LEARNING — EWA e Kalman Filter

**ID:** `SEC-05-03` | **Status:** #status/pending | **Versão:** `2.0.0-ONLINE`

---

## 1. OBJETIVO

Implementar aprendizagem online usando Exponentially Weighted Averages (EWA) e Kalman Filter para atualizar team ratings em tempo real após cada jogo.

---

## 2. EXPONENTIALLY WEIGHTED AVERAGE (EWA)

### 2.1 Conceito

EWA dá mais peso a observações recentes, permitindo que o modelo adapte-se rapidamente a mudanças de forma.

```python
class EWATeamRating:
    """
    Team rating atualizado com EWA.
    """
    def __init__(self, alpha=0.1, initial_rating=0.0):
        """
        alpha: Fator de suavização (0-1). Valores menores = mais suavização.
        """
        self.alpha = alpha
        self.rating = initial_rating
        self.history = []
    
    def update(self, new_observation):
        """
        Atualiza rating com nova observação.
        """
        self.rating = self.alpha * new_observation + (1 - self.alpha) * self.rating
        self.history.append(self.rating)
        return self.rating
    
    def predict(self):
        """
        Retorna rating atual.
        """
        return self.rating
```

### 2.2 Aplicação a Team Ratings

```python
class TeamRatingEWA:
    """
    Sistema de ratings de equipas usando EWA.
    """
    def __init__(self, alpha_offensive=0.15, alpha_defensive=0.15):
        self.offensive_ratings = {}  # {team_id: EWATeamRating}
        self.defensive_ratings = {}  # {team_id: EWATeamRating}
        self.alpha_offensive = alpha_offensive
        self.alpha_defensive = alpha_defensive
    
    def get_or_create_rating(self, team_id, rating_type):
        """
        Cria rating se não existir.
        """
        ratings_dict = self.offensive_ratings if rating_type == 'offensive' else self.defensive_ratings
        
        if team_id not in ratings_dict:
            ratings_dict[team_id] = EWATeamRating(
                alpha=self.alpha_offensive if rating_type == 'offensive' else self.alpha_defensive,
                initial_rating=0.0
            )
        
        return ratings_dict[team_id]
    
    def update_after_game(self, team_id, points_scored, points_conceded):
        """
        Atualiza ratings ofensivo e defensivo após jogo.
        """
        # Calcular performance ofensiva (normalizada)
        offensive_perf = normalize_performance(points_scored)
        defensive_perf = normalize_performance(points_conceded)  # Invertido
        
        # Atualizar ratings
        off_rating = self.get_or_create_rating(team_id, 'offensive')
        def_rating = self.get_or_create_rating(team_id, 'defensive')
        
        off_rating.update(offensive_perf)
        def_rating.update(defensive_perf)
        
        return off_rating.rating, def_rating.rating
    
    def get_matchup_rating(self, team_a_id, team_b_id):
        """
        Retorna rating relativo para matchup.
        """
        off_a = self.get_or_create_rating(team_a_id, 'offensive').predict()
        def_b = self.get_or_create_rating(team_b_id, 'defensive').predict()
        
        # Rating ofensivo de A vs rating defensivo de B
        matchup_rating = off_a - def_b
        
        return matchup_rating
```

---

## 3. KALMAN FILTER

### 3.1 Conceito

Kalman Filter estima estado oculto (rating real) com incerteza, combinando previsão do modelo com observação.

```python
import numpy as np

class KalmanTeamRating:
    """
    Team rating atualizado com Kalman Filter.
    """
    def __init__(self, process_noise=0.1, measurement_noise=0.5, initial_uncertainty=1.0):
        """
        process_noise: Variância do processo de evolução do rating
        measurement_noise: Variância da observação (performance do jogo)
        initial_uncertainty: Incerteza inicial do rating
        """
        self.state = 0.0  # Rating estimado
        self.uncertainty = initial_uncertainty  # Covariância
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
    
    def predict(self):
        """
        Step de predição (antes de nova observação).
        """
        # Estado não muda sem nova observação
        # Incerteza aumenta com o tempo
        self.uncertainty += self.process_noise
        return self.state, self.uncertainty
    
    def update(self, observation):
        """
        Step de atualização com nova observação.
        """
        # Kalman Gain
        K = self.uncertainty / (self.uncertainty + self.measurement_noise)
        
        # Atualizar estado
        self.state = self.state + K * (observation - self.state)
        
        # Atualizar incerteza
        self.uncertainty = (1 - K) * self.uncertainty
        
        return self.state, self.uncertainty
```

### 3.2 Aplicação a Team Ratings

```python
class TeamRatingKalman:
    """
    Sistema de ratings de equipas usando Kalman Filter.
    """
    def __init__(self):
        self.offensive_ratings = {}  # {team_id: KalmanTeamRating}
        self.defensive_ratings = {}  # {team_id: KalmanTeamRating}
    
    def get_or_create_rating(self, team_id, rating_type):
        """
        Cria rating se não existir.
        """
        ratings_dict = self.offensive_ratings if rating_type == 'offensive' else self.defensive_ratings
        
        if team_id not in ratings_dict:
            ratings_dict[team_id] = KalmanTeamRating()
        
        return ratings_dict[team_id]
    
    def update_after_game(self, team_id, points_scored, points_conceded):
        """
        Atualiza ratings após jogo.
        """
        # Predição (incerteza aumenta)
        off_rating = self.get_or_create_rating(team_id, 'offensive')
        def_rating = self.get_or_create_rating(team_id, 'defensive')
        
        off_rating.predict()
        def_rating.predict()
        
        # Atualização com observação
        offensive_perf = normalize_performance(points_scored)
        defensive_perf = normalize_performance(points_conceded)
        
        off_rating.update(offensive_perf)
        def_rating.update(defensive_perf)
        
        return off_rating.state, off_rating.uncertainty
```

---

## 4. COMPARAÇÃO EWA vs KALMAN

| Aspecto | EWA | Kalman Filter |
|---------|-----|---------------|
| Complexidade | Baixa | Média |
| Incerteza | Não explícita | Explícita |
| Adaptabilidade | Fixa (alpha) | Dinâmica (Kalman Gain) |
| Robustez a ruído | Sensível a alpha | Mais robusto |
| Interpretação | Simples | Mais técnica |

**Recomendação:** Usar EWA para simplicidade inicial, migrar para Kalman se precisar de incerteza explícita.

---

## 5. INTEGRAÇÃO COM PIPELINE DE TREINO

```python
class OnlineLearningPipeline:
    """
    Pipeline de treino com online learning.
    """
    def __init__(self, use_kalman=False):
        self.rating_system = TeamRatingKalman() if use_kalman else TeamRatingEWA()
        self.feature_extractor = extract_expanded_features
    
    def train_initial_model(self, historical_data):
        """
        Treina modelo inicial com dados históricos.
        """
        # 1. Calcular ratings históricos com EWA/Kalman
        for game in historical_data:
            self.rating_system.update_after_game(
                game['team_a'], game['points_a'], game['points_conceded_a']
            )
            self.rating_system.update_after_game(
                game['team_b'], game['points_b'], game['points_conceded_b']
            )
        
        # 2. Extrair features com ratings atualizados
        features = []
        for game in historical_data:
            game_features = self.feature_extractor(game, self.rating_system)
            features.append(game_features)
        
        # 3. Treinar ensemble model
        X = pd.DataFrame(features)
        y = historical_data['outcome']
        
        ensemble = EnsembleStacking(xgb_config, lgb_config, cat_config, meta_config)
        ensemble.fit(X, y)
        
        return ensemble
    
    def update_with_new_game(self, new_game, ensemble_model):
        """
        Atualiza ratings e retreina modelo com novo jogo.
        """
        # 1. Atualizar ratings
        self.rating_system.update_after_game(
            new_game['team_a'], new_game['points_a'], new_game['points_conceded_a']
        )
        
        # 2. Retreino rápido (warm start)
        new_features = self.feature_extractor(new_game, self.rating_system)
        ensemble_model.partial_fit([new_features], [new_game['outcome']])
        
        return ensemble_model
```

---

## 6. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| Adaptabilidade a mudanças de forma | Rating ajusta em < 5 jogos |
| Estabilidade a ruído | Rating não oscila > 0.1 por jogo |
| CLV com online learning | > 2.5% (vs 2% baseline) |
| Tempo de atualização por jogo | < 50ms |
| Convergência | Rating converge em < 20 jogos |
