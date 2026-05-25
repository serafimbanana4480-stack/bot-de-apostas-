# BOOTSTRAP_BLOCK_RESAMPLING — Intervalos de Confiança

**ID:** `QR-004` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Calcular intervalos de confiança para métricas como ROI e CLV usando block bootstrap, que preserva a estrutura temporal dos dados.

---

## 2. PROBLEMA DO BOOTSTRAP SIMPLES

Bootstrap simples (amostragem aleatória com reposição) quebra a estrutura temporal - pode gerar sequências impossíveis no tempo.

**Solução:** Block bootstrap - amostra blocos consecutivos para preservar autocorrelação.

---

## 3. IMPLEMENTAÇÃO

```python
import numpy as np

def block_bootstrap(returns, block_size=10, n_bootstrap=1000):
    """
    Block bootstrap para séries temporais.
    
    Args:
        returns: Array de retornos (ROI por aposta)
        block_size: Tamanho do bloco (ex: 10 apostas)
        n_bootstrap: Número de amostras bootstrap
    
    Returns:
        Array de médias bootstrap (ROI simulado)
    """
    n = len(returns)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        # Selecionar blocos aleatórios
        n_blocks = n // block_size
        block_starts = np.random.randint(0, n - block_size, n_blocks)
        
        # Construir série bootstrap
        bootstrap_series = np.concatenate([
            returns[start:start+block_size]
            for start in block_starts
        ])
        
        # Calcular média
        bootstrap_means.append(np.mean(bootstrap_series))
    
    return np.array(bootstrap_means)
```

---

## 4. SELEÇÃO DE BLOCK SIZE

O block size ideal deve capturar a autocorrelação dos dados:

```python
def optimal_block_size(returns, max_block=50):
    """
    Encontra block size ótimo baseado em autocorrelação.
    """
    from statsmodels.tsa.stattools import acf
    
    autocorr = acf(returns, nlags=max_block)
    
    # Encontrar onde autocorrelação cai abaixo de 0.1
    for lag, ac in enumerate(autocorr):
        if ac < 0.1:
            return lag + 1
    
    return max_block  # Default se não cair
```

---

## 5. CÁLCULO DE INTERVALO DE CONFIANÇA

```python
def confidence_interval(bootstrap_means, alpha=0.05):
    """
    Calcula IC de (1-alpha)%.
    """
    lower = np.percentile(bootstrap_means, (alpha/2) * 100)
    upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
    return lower, upper

# Exemplo
bootstrap_roi = block_bootstrap(returns, block_size=10, n_bootstrap=10000)
ci_lower, ci_upper = confidence_interval(bootstrap_roi)

print(f"ROI: {np.mean(returns):.2%}")
print(f"IC 95%: [{ci_lower:.2%}, {ci_upper:.2%}]")
```

---

## 6. APLICAÇÃO A CLV

```python
def bootstrap_clv(clv_series, block_size=10, n_bootstrap=10000):
    """Bootstrap para CLV médio."""
    return block_bootstrap(clv_series, block_size, n_bootstrap)

# Teste de significância
clv_bootstrap = bootstrap_clv(clv_series)
ci_lower, ci_upper = confidence_interval(clv_bootstrap)

if ci_lower > 0:
    print("CLV significativamente positivo (p < 0.05)")
else:
    print("CLV não significativo")
```

---

## 7. CRITÉRIOS

- Block size ≥ 5 para preservar autocorrelação diária
- IC 95% não deve incluir 0 para métricas de edge
- N bootstrap ≥ 1000 para estabilidade

---

## 8. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[STATISTICAL_SIGNIFICANCE]] → Testes de hipótese
