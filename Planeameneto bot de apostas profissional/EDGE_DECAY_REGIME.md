# EDGE_DECAY_REGIME — Degradação de Edge ao Longo do Tempo

**ID:** `QR-005` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar como o edge estimado se degrada ao longo do tempo e como detectar mudanças de regime que indicam necessidade de re-treino.

---

## 2. CONCEITO

Edge não é estático - degrada à medida que:
- O mercado se adapta
- O modelo envelhece
- Mudanças no jogo ocorrem (regras, estratégias)

---

## 3. PADRÕES DE DECAY

### 3.1 Half-Life Decay

Edge segue decaimento exponencial com half-life:

```python
def edge_decay(initial_edge, days_elapsed, half_life_days=30):
    """
    Calcula edge após decaimento.
    
    Args:
        initial_edge: Edge inicial (ex: 0.05 = 5%)
        days_elapsed: Dias desde o treino
        half_life_days: Dias para edge cair para metade
    
    Returns:
        Edge após decaimento
    """
    decay_factor = 0.5 ** (days_elapsed / half_life_days)
    return initial_edge * decay_factor
```

### 3.2 Linear Decay

Para mudanças estruturais mais rápidas:

```python
def linear_decay(initial_edge, days_elapsed, decay_rate=0.001):
    """Decay linear."""
    return max(0, initial_edge - decay_rate * days_elapsed)
```

---

## 4. DETECÇÃO DE REGIME CHANGE

### 4.1 CUSUM Test

```python
def cusum_test(roi_series, threshold=2.0):
    """
    Detecta mudanças de regime usando CUSUM.
    
    Returns:
        Boolean se regime change detectado
    """
    mean_roi = np.mean(roi_series)
    std_roi = np.std(roi_series)
    
    cusum = np.cumsum(roi_series - mean_roi)
    normalized_cusum = cusum / (std_roi * np.sqrt(len(roi_series)))
    
    return np.any(np.abs(normalized_cusum) > threshold)
```

### 4.2 Rolling Window Comparison

```python
def detect_regime_change(clv_series, window=50, threshold=0.5):
    """
    Compara CLV médio de janelas consecutivas.
    """
    recent_mean = np.mean(clv_series[-window:])
    previous_mean = np.mean(clv_series[-2*window:-window])
    
    return abs(recent_mean - previous_mean) > threshold
```

---

## 5. RESPOSTA A REGIME CHANGE

### 5.1 Níveis de Alerta

| Alerta | Condição | Ação |
|--------|----------|------|
| Green | CLV estável ± 0.5% | Nenhuma |
| Yellow | CLV caiu 0.5-1.0% | Monitorizar, considerar re-treino |
| Red | CLV caiu > 1.0% ou regime change | Re-treino imediato |

### 5.2 Retraining Triggered

```python
def should_retrain(metrics):
    """Decide se re-treino é necessário."""
    conditions = [
        metrics['clv_recent'] < metrics['clv_baseline'] - 0.01,
        metrics['roi_recent'] < 0,
        detect_regime_change(metrics['clv_history'])
    ]
    
    return any(conditions)
```

---

## 6. PESO EM DADOS RECENTES

Se edge está degradando, dar mais peso a dados recentes:

```python
def weighted_loss(probs, outcomes, weights):
    """Loss function com pesos temporais."""
    return -np.mean(weights * (outcomes * np.log(probs) + (1-outcomes) * np.log(1-probs)))

# Pesos exponenciais (dados recentes têm mais peso)
n_samples = len(probs)
weights = np.exp(np.linspace(0, 2, n_samples))  # Ex: 0 a 2
weights = weights / weights.sum()  # Normalizar
```

---

## 7. MONITORIZAÇÃO

- Plotar CLV rolling (50, 100, 200 apostas)
- Alertar se slope de decay > threshold
- Registar regime changes em log

---

## 8. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[RETRAINING_STRATEGY]] → Quando re-treinar
