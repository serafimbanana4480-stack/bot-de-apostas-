# CALIBRACAO_PROBABILIDADES — Calibração para Player Props

**ID:** `PP-008` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar a estratégia de calibração específica para player props, incluindo calibração por regime de linha, por tipo de jogador, e por situação de jogo, dado que player props têm linhas muito variáveis e distribuições diferentes de team props.

---

## 2. DESAFIOS DE CALIBRAÇÃO EM PLAYER PROPS

### 2.1 Diferenças vs Team Props

| Aspecto | Team Props | Player Props |
|---------|------------|--------------|
| Linhas | Fixas (ML: 1.90-2.10, Spread: 1.90-1.95) | Variáveis (PTS: 10.5-40.5) |
| Distribuição | Binária (win/loss) | Contínua convertida em binária |
| Regimes | 3 (favorito/equilibrado/underdog) | 10+ (por linha) |
| Volatilidade | Baixa | Alta |
| Calibradores | 1 por regime | 1 por linha × 1 por jogador |
| Complexidade | Média | Alta |

### 2.2 Implicações

```python
calibration_challenges = {
    # Variabilidade de linhas
    "line_variability": {
        "description": "Linhas variam de 10.5 a 40.5 para PTS",
        "impact": "Calibrador único não funciona para todas as linhas",
        "solution": "Calibração por bins de linha",
    },
    
    # Distribuição assimétrica
    "asymmetric_distribution": {
        "description": "Distribuição não é normal (skewed)",
        "impact": "Assumir normalidade introduz bias",
        "solution": "Usar calibração não-paramétrica (isotónica)",
    },
    
    # Diferentes tipos de jogadores
    "player_types": {
        "description": "Estrelas, titulares, role players têm padrões diferentes",
        "impact": "Calibrador único introduz bias para alguns tipos",
        "solution": "Calibração por tipo de jogador",
    },
    
    # Situação de jogo
    "game_situation": {
        "description": "Blowouts, jogos próximos afetam distribuição",
        "impact": "Calibração não considera contexto",
        "solution": "Calibração por situação de jogo",
    },
}
```

---

## 3. CALIBRAÇÃO POR REGIME DE LINHA

### 3.1 Definição de Bins de Linha

```python
def create_line_bins(lines, n_bins=10):
    """
    Cria bins de linha para calibração.
    
    Args:
        lines: array de linhas históricas
        n_bins: número de bins
    
    Returns:
        bins: limites dos bins
        bin_labels: labels dos bins
    """
    # Usar percentis para criar bins
    percentiles = np.linspace(0, 100, n_bins + 1)
    bins = np.percentile(lines, percentiles)
    
    # Criar labels
    bin_labels = []
    for i in range(n_bins):
        label = f"line_{bins[i]:.1f}_{bins[i+1]:.1f}"
        bin_labels.append(label)
    
    return bins, bin_labels

# Exemplo para PTS
lines_pts = np.array([10.5, 15.5, 20.5, 25.5, 30.5, 35.5, 40.5])
bins, labels = create_line_bins(lines_pts, n_bins=5)
# bins: [10.5, 15.5, 20.5, 25.5, 30.5, 40.5]
# labels: ['line_10.5_15.5', 'line_15.5_20.5', ...]
```

### 3.2 Calibração por Bin

```python
from sklearn.calibration import IsotonicRegression

def calibrate_by_line_bins(y_true, y_pred, lines, n_bins=10, min_samples=50):
    """
    Calibra probabilidades por bins de linha.
    
    Args:
        y_true: valores reais
        y_pred: valores previstos pelo modelo
        lines: linhas do mercado
        n_bins: número de bins
        min_samples: mínimo de amostras por bin para calibrar
    
    Returns:
        calibrators: dicionário de calibradores por bin
    """
    # Criar bins
    bins, bin_labels = create_line_bins(lines, n_bins)
    
    calibrators = {}
    
    for i in range(n_bins):
        # Definir bin
        line_min = bins[i]
        line_max = bins[i + 1]
        label = bin_labels[i]
        
        # Filtrar dados deste bin
        mask = (lines >= line_min) & (lines < line_max)
        
        if mask.sum() >= min_samples:
            # Calibrar
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[label] = cal
        else:
            # Se amostras insuficientes, usar calibrador global
            calibrators[label] = None
    
    # Criar calibrador global (fallback)
    global_cal = IsotonicRegression(out_of_bounds='clip')
    global_cal.fit(y_pred, y_true)
    calibrators['global'] = global_cal
    
    return calibrators, bins

def apply_calibration_by_line(y_pred, lines, calibrators, bins):
    """
    Aplica calibração por bin de linha.
    
    Args:
        y_pred: previsões do modelo
        lines: linhas do mercado
        calibrators: dicionário de calibradores
        bins: limites dos bins
    
    Returns:
        y_cal: previsões calibradas
    """
    y_cal = np.zeros_like(y_pred)
    
    n_bins = len(bins) - 1
    
    for i in range(n_bins):
        # Definir bin
        line_min = bins[i]
        line_max = bins[i + 1]
        label = f"line_{line_min:.1f}_{line_max:.1f}"
        
        # Filtrar dados deste bin
        mask = (lines >= line_min) & (lines < line_max)
        
        if label in calibrators and calibrators[label] is not None:
            # Aplicar calibrador específico
            y_cal[mask] = calibrators[label].predict(y_pred[mask])
        else:
            # Usar calibrador global
            y_cal[mask] = calibrators['global'].predict(y_pred[mask])
    
    return y_cal
```

### 3.3 Exemplo de Uso

```python
# Dados de exemplo
y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 0])  # 1 = over, 0 = under
y_pred = np.array([0.6, 0.4, 0.7, 0.65, 0.35, 0.55, 0.45, 0.3, 0.8, 0.25])
lines = np.array([20.5, 15.5, 25.5, 22.5, 18.5, 30.5, 12.5, 16.5, 35.5, 14.5])

# Calibrar
calibrators, bins = calibrate_by_line_bins(y_true, y_pred, lines, n_bins=5)

# Aplicar calibração
y_cal = apply_calibration_by_line(y_pred, lines, calibrators, bins)

# Comparar
print(f"Brier score antes: {brier_score_loss(y_true, y_pred):.4f}")
print(f"Brier score depois: {brier_score_loss(y_true, y_cal):.4f}")
```

---

## 4. CALIBRAÇÃO POR TIPO DE JOGADOR

### 4.1 Classificação de Jogadores

```python
def classify_player_type(historical_data):
    """
    Classifica jogador em star/starter/role_player baseado em histórico.
    
    Args:
        historical_data: DataFrame com dados históricos do jogador
    
    Returns:
        player_type: 'star', 'starter', ou 'role_player'
    """
    # Métricas de classificação
    avg_minutes = historical_data['minutes'].mean()
    avg_usage = historical_data['usage_rate'].mean()
    is_starter_rate = historical_data['is_starter'].mean()
    
    # Classificação
    if avg_minutes >= 32 and avg_usage >= 0.25 and is_starter_rate >= 0.9:
        return 'star'
    elif avg_minutes >= 25 and avg_usage >= 0.15 and is_starter_rate >= 0.7:
        return 'starter'
    else:
        return 'role_player'
```

### 4.2 Calibração por Tipo

```python
def calibrate_by_player_type(y_true, y_pred, player_types, min_samples=50):
    """
    Calibra probabilidades por tipo de jogador.
    
    Args:
        y_true: valores reais
        y_pred: previsões do modelo
        player_types: array com tipos de jogadores
        min_samples: mínimo de amostras por tipo
    
    Returns:
        calibrators: dicionário de calibradores por tipo
    """
    calibrators = {}
    
    for player_type in ['star', 'starter', 'role_player']:
        # Filtrar dados deste tipo
        mask = player_types == player_type
        
        if mask.sum() >= min_samples:
            # Calibrar
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[player_type] = cal
    
    # Calibrador global (fallback)
    global_cal = IsotonicRegression(out_of_bounds='clip')
    global_cal.fit(y_pred, y_true)
    calibrators['global'] = global_cal
    
    return calibrators

def apply_calibration_by_player_type(y_pred, player_types, calibrators):
    """
    Aplica calibração por tipo de jogador.
    """
    y_cal = np.zeros_like(y_pred)
    
    for player_type in ['star', 'starter', 'role_player']:
        # Filtrar dados deste tipo
        mask = player_types == player_type
        
        if player_type in calibrators:
            # Aplicar calibrador específico
            y_cal[mask] = calibrators[player_type].predict(y_pred[mask])
        else:
            # Usar calibrador global
            y_cal[mask] = calibrators['global'].predict(y_pred[mask])
    
    return y_cal
```

---

## 5. CALIBRAÇÃO POR SITUAÇÃO DE JOGO

### 5.1 Classificação de Situação

```python
def classify_game_situation(spread_line, final_score_diff):
    """
    Classifica situação do jogo (apenas para calibração histórica).
    
    Args:
        spread_line: linha de spread
        final_score_diff: diferença final de pontos
    
    Returns:
        situation: 'blowout', 'close', ou 'normal'
    """
    abs_diff = abs(final_score_diff)
    
    if abs_diff >= 15:
        return 'blowout'
    elif abs_diff <= 5:
        return 'close'
    else:
        return 'normal'
```

### 5.2 Calibração por Situação

```python
def calibrate_by_game_situation(y_true, y_pred, situations, min_samples=30):
    """
    Calibra probabilidades por situação de jogo.
    
    NOTA: Esta calibração só pode ser feita em dados históricos
    (não pode ser usada em tempo real porque não conhecemos a situação).
    
    É útil para entender como o modelo performa em diferentes situações.
    """
    calibrators = {}
    
    for situation in ['blowout', 'close', 'normal']:
        # Filtrar dados desta situação
        mask = situations == situation
        
        if mask.sum() >= min_samples:
            # Calibrar
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[situation] = cal
    
    return calibrators
```

---

## 6. CALIBRAÇÃO HIERÁRQUICA

### 6.1 Abordagem em Dois Níveis

```python
class HierarchicalCalibrator:
    """
    Calibrador hierárquico: primeiro por linha, depois por tipo de jogador.
    """
    
    def __init__(self):
        self.line_calibrators = {}
        self.player_type_calibrators = {}
        self.global_calibrator = None
    
    def fit(self, y_true, y_pred, lines, player_types, n_line_bins=10):
        """
    Treina calibradores hierárquicos.
    """
        # Calibrador global
        self.global_calibrator = IsotonicRegression(out_of_bounds='clip')
        self.global_calibrator.fit(y_pred, y_true)
        
        # Calibradores por linha
        line_bins, _ = create_line_bins(lines, n_line_bins)
        for i in range(n_line_bins):
            line_min = line_bins[i]
            line_max = line_bins[i + 1]
            label = f"line_{line_min:.1f}_{line_max:.1f}"
            
            mask = (lines >= line_min) & (lines < line_max)
            if mask.sum() >= 50:
                cal = IsotonicRegression(out_of_bounds='clip')
                cal.fit(y_pred[mask], y_true[mask])
                self.line_calibrators[label] = cal
        
        # Calibradores por tipo de jogador (dentro de cada bin de linha)
        for player_type in ['star', 'starter', 'role_player']:
            for i in range(n_line_bins):
                line_min = line_bins[i]
                line_max = line_bins[i + 1]
                label = f"{player_type}_line_{line_min:.1f}_{line_max:.1f}"
                
                mask = (player_types == player_type) & (lines >= line_min) & (lines < line_max)
                if mask.sum() >= 30:
                    cal = IsotonicRegression(out_of_bounds='clip')
                    cal.fit(y_pred[mask], y_true[mask])
                    self.player_type_calibrators[label] = cal
    
    def predict(self, y_pred, lines, player_types):
        """
    Aplica calibração hierárquica.
    """
        y_cal = np.zeros_like(y_pred)
        
        for i in range(len(y_pred)):
            pred = y_pred[i]
            line = lines[i]
            player_type = player_types[i]
            
            # Tentar calibrador específico (tipo + linha)
            line_bin = self._get_line_bin(line)
            specific_label = f"{player_type}_{line_bin}"
            
            if specific_label in self.player_type_calibrators:
                y_cal[i] = self.player_type_calibrators[specific_label].predict([pred])[0]
            # Tentar calibrador por linha
            elif line_bin in self.line_calibrators:
                y_cal[i] = self.line_calibrators[line_bin].predict([pred])[0]
            # Usar calibrador global
            else:
                y_cal[i] = self.global_calibrator.predict([pred])[0]
        
        return y_cal
    
    def _get_line_bin(self, line, line_bins=None):
        """
    Determina o bin de linha para um valor específico.
    """
        if line_bins is None:
            # Usar bins padrão
            line_bins = np.array([10.5, 15.5, 20.5, 25.5, 30.5, 35.5, 40.5])
        
        for i in range(len(line_bins) - 1):
            if line_bins[i] <= line < line_bins[i + 1]:
                return f"line_{line_bins[i]:.1f}_{line_bins[i+1]:.1f}"
        
        return "line_35.5_40.5"  # Fallback para último bin
```

---

## 7. CALIBRAÇÃO POR TEMPO

### 7.1 Calibração Temporal

```python
def calibrate_by_time(y_true, y_pred, dates, n_periods=6):
    """
    Calibra por período temporal (ex: por mês).
    
    Útil para detectar drift temporal.
    """
    calibrators = {}
    
    # Dividir em períodos
    min_date = dates.min()
    max_date = dates.max()
    period_length = (max_date - min_date) / n_periods
    
    for i in range(n_periods):
        period_start = min_date + i * period_length
        period_end = period_start + period_length
        
        mask = (dates >= period_start) & (dates < period_end)
        
        if mask.sum() >= 30:
            cal = IsotonicRegression(out_of_bounds='clip')
            cal.fit(y_pred[mask], y_true[mask])
            calibrators[f"period_{i}"] = cal
    
    return calibrators
```

### 7.2 Detecção de Drift Temporal

```python
def detect_temporal_drift(calibrators_by_time):
    """
    Detecta se houve drift temporal comparando calibradores.
    """
    # Comparar primeiro e último período
    first_cal = calibrators_by_time['period_0']
    last_cal = calibrators_by_time[f'period_{len(calibrators_by_time)-1}']
    
    # Testar com probabilidades de exemplo
    test_probs = np.linspace(0.1, 0.9, 9)
    
    first_calibrated = first_cal.predict(test_probs)
    last_calibrated = last_cal.predict(test_probs)
    
    # Calcular diferença média
    avg_diff = np.abs(first_calibrated - last_calibrated).mean()
    
    drift_detected = avg_diff > 0.05  # 5% de diferença média
    
    return {
        'drift_detected': drift_detected,
        'avg_difference': avg_diff,
        'first_calibrated': first_calibrated,
        'last_calibrated': last_calibrated,
    }
```

---

## 8. AVALIAÇÃO DE CALIBRAÇÃO

### 8.1 Reliability Diagram

```python
def plot_reliability_diagram(y_true, y_pred, n_bins=10):
    """
    Plota reliability diagram para avaliar calibração.
    """
    from sklearn.calibration import calibration_curve
    import matplotlib.pyplot as plt
    
    prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=n_bins)
    
    plt.figure(figsize=(10, 6))
    plt.plot([0, 1], [0, 1], 'k--', label='Perfeitamente calibrado')
    plt.plot(prob_pred, prob_true, 'o-', label='Modelo')
    plt.xlabel('Probabilidade prevista')
    plt.ylabel('Probabilidade real')
    plt.title('Reliability Diagram')
    plt.legend()
    plt.grid(True)
    plt.show()
```

### 8.2 Brier Score

```python
from sklearn.metrics import brier_score_loss

def calculate_brier_score(y_true, y_pred):
    """
    Calcula Brier score (quanto menor, melhor).
    
    Brier score médio para classificação binária aleatória: 0.25
    Brier score perfeito: 0.0
    """
    return brier_score_loss(y_true, y_pred)
```

### 8.3 Expected Calibration Error (ECE)

```python
def calculate_ece(y_true, y_pred, n_bins=10):
    """
    Calcula Expected Calibration Error.
    
    ECE médio para modelo não calibrado: 0.05-0.10
    ECE bom: <0.02
    ECE excelente: <0.01
    """
    from sklearn.calibration import calibration_curve
    
    prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=n_bins)
    
    ece = 0
    for i in range(n_bins):
        bin_size = len(y_pred[(y_pred >= prob_pred[i]) & (y_pred < prob_pred[i+1])])
        if bin_size > 0:
            ece += bin_size / len(y_pred) * abs(prob_true[i] - prob_pred[i])
    
    return ece
```

---

## 9. MONITORIZAÇÃO DE CALIBRAÇÃO

### 9.1 Monitorização Contínua

```python
class CalibrationMonitor:
    """
    Monitoriza calibração ao longo do tempo.
    """
    
    def __init__(self, window=100):
        self.window = window
        self.history = []
    
    def update(self, y_true, y_pred, timestamp):
        """
    Atualiza monitorização com novos dados.
    """
        # Calcular métricas
        brier = brier_score_loss(y_true, y_pred)
        ece = calculate_ece(y_true, y_pred)
        
        # Guardar histórico
        self.history.append({
            'timestamp': timestamp,
            'brier': brier,
            'ece': ece,
            'n_samples': len(y_true),
        })
    
    def check_drift(self, threshold_brier=0.05, threshold_ece=0.03):
        """
    Verifica se houve drift na calibração.
    """
        if len(self.history) < 2:
            return False, "Dados insuficientes"
        
        current = self.history[-1]
        baseline = self.history[0]
        
        brier_increase = current['brier'] - baseline['brier']
        ece_increase = current['ece'] - baseline['ece']
        
        if brier_increase > threshold_brier or ece_increase > threshold_ece:
            return True, f"Drift detectado: Brier +{brier_increase:.3f}, ECE +{ece_increase:.3f}"
        
        return False, "Sem drift detectado"
```

---

## 10. BACKLOG

- [ ] Implementar calibração por bins de linha
- [ ] Implementar calibração por tipo de jogador
- [ ] Implementar calibração hierárquica
- [ ] Implementar monitorização de calibração
- [ ] Implementar detecção de drift temporal
- [ ] Calibrar número ótimo de bins
- [ ] Calibrar thresholds de drift
- [ ] Documentar performance de calibração por mercado (PTS/REB/AST)
- [ ] Criar sistema de recalibração automática

---

## 11. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/MODELACAO_PLAYER_PROPS]] → Modelagem que precisa de calibração
- [[05_Machine_Learning/CALIBRACAO_ISOTONICA]] → Calibração isotónica geral
- [[05_Machine_Learning/MONITORIZACAO_DRIFT]] → Monitorização de drift