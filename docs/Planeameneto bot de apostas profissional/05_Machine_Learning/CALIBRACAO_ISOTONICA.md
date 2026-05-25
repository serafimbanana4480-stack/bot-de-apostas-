# CALIBRAÇÃO ISOTÓNICA — Ajuste de Probabilidades por Regime

**ID:** `ML-006` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Calibrar as probabilidades brutas do modelo XGBoost para refletirem verdadeiras frequências de ocorrência. Modelos de ML tendem a ser overconfidentes (previsões extremas demais), o que reduz o edge real.

---

## 2. POR QUE CALIBRAR?

### 2.1 Problema de Overconfidence

```python
# Exemplo típico de modelo não calibrado
Probabilidade prevista: 0.80
Frequência real: 0.65
Erro: -0.15 (modelo superconfiante)

Probabilidade prevista: 0.20
Frequência real: 0.35
Erro: +0.15 (modelo subconfiante)
```

**Impacto no edge:**
- Se P_prevista = 0.80 mas P_real = 0.65, edge é inflacionado
- Apostas baseadas em probabilidades erradas têm EV negativo

### 2.2 Benefícios da Calibração

- ✅ Edge calculado é mais preciso
- ✅ Stake sizing (Kelly) é mais correto
- ✅ Meta-modelo recebe inputs mais confiáveis
- ✅ Interpretabilidade melhora

---

## 3. CALIBRAÇÃO POR REGIME

### 3.1 Por Que Dividir em Regimes?

Diferentes regiões do espaço de probabilidade têm diferentes padrões de erro:
- **Favoritos (P ≥ 0.65):** Modelo tende a superestimar
- **Equilibrados (0.35 < P < 0.65):** Modelo geralmente mais preciso
- **Underdogs (P ≤ 0.35):** Modelo tende a subestimar

### 3.2 Definição dos Regimes

```python
def get_regime(probabilidade: float) -> str:
    if probabilidade >= 0.65:
        return "favorito"
    elif probabilidade <= 0.35:
        return "underdog"
    else:
        return "equilibrado"
```

---

## 4. IMPLEMENTAÇÃO

### 4.1 Calibrador Isotónico por Regime

```python
from sklearn.isotonic import IsotonicRegression
import pickle

class RegimeCalibrator:
    def __init__(self):
        self.calibrators = {
            "favorito": IsotonicRegression(out_of_bounds='clip'),
            "equilibrado": IsotonicRegression(out_of_bounds='clip'),
            "underdog": IsotonicRegression(out_of_bounds='clip')
        }
    
    def fit(self, y_pred: np.array, y_true: np.array):
        """Treinar calibradores por regime"""
        for regime in self.calibrators.keys():
            # Filtrar dados do regime
            mask = np.array([get_regime(p) == regime for p in y_pred])
            if mask.sum() > 50:  # Mínimo de amostras
                self.calibrators[regime].fit(y_pred[mask], y_true[mask])
    
    def calibrate(self, probabilidade: float) -> float:
        """Calibrar uma probabilidade"""
        regime = get_regime(probabilidade)
        return self.calibrators[regime].predict([probabilidade])[0]
    
    def save(self, path: str):
        """Guardar calibradores"""
        with open(path, 'wb') as f:
            pickle.dump(self.calibrators, f)
    
    def load(self, path: str):
        """Carregar calibradores"""
        with open(path, 'rb') as f:
            self.calibrators = pickle.load(f)
```

### 4.2 Treino do Calibrador

```python
# Usar dados de validação (NUNCA de teste)
X_val, y_val = load_validation_data()

# Obter previsões do modelo
y_pred_raw = model.predict(X_val)

# Treinar calibrador
calibrator = RegimeCalibrator()
calibrator.fit(y_pred_raw, y_val)

# Guardar
calibrator.save("/models/calibrator.pkl")
```

### 4.3 Aplicação em Produção

```python
# Carregar calibrador
calibrator = RegimeCalibrator()
calibrator.load("/models/calibrator.pkl")

# Pipeline completo
def predict_with_calibration(features: dict) -> float:
    # 1. Previsão bruta do modelo
    prob_raw = model.predict_proba(features)[1]
    
    # 2. Calibração por regime
    prob_calibrated = calibrator.calibrate(prob_raw)
    
    # 3. Clipping para [0.01, 0.99] (evitar extremos)
    prob_final = np.clip(prob_calibrated, 0.01, 0.99)
    
    return prob_final
```

---

## 5. VALIDAÇÃO DA CALIBRAÇÃO

### 5.1 Reliability Diagram

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_reliability_diagram(y_pred: np.array, y_true: np.array, n_bins: int = 10):
    """Visualizar calibração"""
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    calibrated_freq = []
    empirical_freq = []
    
    for i in range(n_bins):
        mask = (y_pred >= bins[i]) & (y_pred < bins[i+1])
        if mask.sum() > 0:
            calibrated_freq.append(y_pred[mask].mean())
            empirical_freq.append(y_true[mask].mean())
    
    plt.figure(figsize=(8, 8))
    plt.plot([0, 1], [0, 1], 'k--', label='Perfeito')
    plt.plot(calibrated_freq, empirical_freq, 'ro-', label='Modelo')
    plt.xlabel('Probabilidade Calibrada')
    plt.ylabel('Frequência Observada')
    plt.legend()
    plt.title('Reliability Diagram')
    plt.show()
```

**Interpretação:**
- Pontos na linha diagonal = perfeitamente calibrado
- Pontos acima da linha = subconfiante (previsão < realidade)
- Pontos abaixo da linha = superconfiante (previsão > realidade)

### 5.2 ECE (Expected Calibration Error)

```python
def calculate_ece(y_pred: np.array, y_true: np.array, n_bins: int = 10) -> float:
    """Calcular ECE"""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_pred)
    
    for i in range(n_bins):
        mask = (y_pred >= bins[i]) & (y_pred < bins[i+1])
        n = mask.sum()
        if n > 0:
            avg_pred = y_pred[mask].mean()
            avg_true = y_true[mask].mean()
            ece += (n / total_samples) * abs(avg_pred - avg_true)
    
    return ece
```

**Target:** ECE < 0.05

---

## 6. MELHORES PRÁTICAS

### 6.1 Quando Recalibrar

- **Semanal:** Se PSI > 0.1 em features principais
- **Mensal:** Como parte de retreino regular do modelo
- **Quando performance degrada:** ROI cai > 20% vs. baseline

### 6.2 Amostras Mínimas

- Mínimo 50 amostras por regime para calibração estável
- Ideal > 200 amostras por regime

### 6.3 Out-of-Bounds Handling

```python
# Se probabilidade fora do range de treino, usar valor mais próximo
IsotonicRegression(out_of_bounds='clip')
```

---

## 7. ALTERNATIVAS

### 7.1 Platt Scaling

```python
from sklearn.calibration import CalibratedClassifierCV

# Logistic regression sobre as previsões
calibrated = CalibratedClassifierCV(model, method='sigmoid', cv='prefit')
calibrated.fit(X_val, y_val)
```

**Vantagem:** Mais simples
**Desvantagem:** Assume forma paramétrica (logística), menos flexível

### 7.2 Beta Calibration

```python
from betacal import BetaCalibration

calibrator = BetaCalibration()
calibrator.fit(y_pred_raw, y_true)
```

**Vantagem:** Trabalha bem com probabilidades extremas
**Desvantagem:** Menos maduro que isotonic

---

## 8. MONITORIZAÇÃO

### 8.1 Métricas de Calibração em Produção

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| ECE rolling 50 | Calcular nas últimas 50 apostas | < 0.10 | Diária |
| Bias por regime | (P_prev - P_real) médio | |0.05| | Semanal |
| CLV por regime | Edge médio por regime | > 2% | Semanal |

### 8.2 Alertas

- ECE > 0.15 → Alerta HIGH (recalibrar)
- Bias regime > 0.10 → Alerta MEDIUM (investigar)
- CLV regime cai < 0% → Alerta CRITICAL (pausar apostas nesse regime)

---

## 9. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secção mãe
- [[46_Meta_Labeling/INDEX]] → Meta-modelo que usa probabilidades calibradas
- [[06_Backtesting/INDEX]] → Validação de calibração no backtest