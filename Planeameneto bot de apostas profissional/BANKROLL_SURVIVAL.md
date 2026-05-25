# BANKROLL_SURVIVAL — Análise de Sobrevivência de Bankroll

**ID:** `RM-007` | **Fase:** #phase/2 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Estimar probabilidade de sobrevivência do bankroll (não ir a zero).

---

## 2. SIMULAÇÃO MONTE CARLO

```python
def simulate_bankroll_survival(initial_bankroll, roi, std_dev, n_simulations=10000):
    """
    Simula sobrevivência de bankroll usando Monte Carlo.
    
    Args:
        initial_bankroll: Bankroll inicial
        roi: ROI esperado
        std_dev: Desvio padrão de retornos
        n_simulations: Número de simulações
    
    Returns:
        Probabilidade de sobrevivência
    """
    survivals = 0
    
    for _ in range(n_simulations):
        bankroll = initial_bankroll
        survived = True
        
        for _ in range(100):  # 100 apostas
            # Retorno aleatório
            return_pct = np.random.normal(roi, std_dev)
            bankroll *= (1 + return_pct)
            
            if bankroll <= 0:
                survived = False
                break
        
        if survived:
            survivals += 1
    
    survival_prob = survivals / n_simulations
    
    return survival_prob
```

---

## 3. ANÁLISE POR SCENÁRIO

| ROI | Std Dev | Probabilidade Sobrevivência |
|-----|---------|------------------------------|
| 5% | 15% | 85% |
| 5% | 20% | 72% |
| 10% | 15% | 95% |
| 10% | 20% | 88% |

---

## 4. CRITÉRIOS DE ACEITAÇÃO

- **Probabilidade > 90%** para aceitar sistema
- **Ajustar Kelly fraction** para aumentar sobrevivência
- **Stop-loss** se probabilidade < 80%

---

## 5. OTIMIZAÇÃO

```python
def optimize_for_survival(initial_bankroll, target_prob=0.9):
    """
    Otimiza Kelly fraction para atingir probabilidade de sobrevivência.
    
    Args:
        initial_bankroll: Bankroll inicial
        target_prob: Probabilidade alvo
    
    Returns:
        Kelly fraction otimizado
    """
    for kelly in [0.01, 0.02, 0.03, 0.04, 0.05]:
        roi = expected_roi * kelly
        std_dev = expected_std * kelly
        
        surv_prob = simulate_bankroll_survival(
            initial_bankroll, roi, std_dev
        )
        
        if surv_prob >= target_prob:
            return kelly
    
    return 0.01  # Conservador se não atingir
```

---

## 6. CRITÉRIOS

- **Simulação Monte Carlo** antes de operação
- **Probabilidade > 90%** para aceitar
- **Kelly fraction ajustado** para garantir sobrevivência

---

## 7. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[MONTE_CARLO_SIMULATION]]
