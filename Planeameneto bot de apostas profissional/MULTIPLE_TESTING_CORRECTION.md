# MULTIPLE_TESTING_CORRECTION — Correção de Bonferroni

**ID:** `QR-010` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Corrigir p-values quando múltiplos testes são realizados para evitar falsos positivos (inflação do erro tipo I).

---

## 2. PROBLEMA

Ao realizar múltiplos testes (ex: testar 10 features), a probabilidade de pelo menos um falso positivo aumenta dramaticalmente.

---

## 3. CORREÇÃO DE BONFERRONI

```python
def bonferroni_correction(p_values, alpha=0.05):
    """
    Correção de Bonferroni para múltiplos testes.
    
    Args:
        p_values: Array de p-values
        alpha: Nível de significância original
    
    Returns:
        corrected_alpha, significant_tests
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests
    
    significant = [p < corrected_alpha for p in p_values]
    
    return corrected_alpha, significant
```

---

## 4. EXEMPLO

```python
# Testar 10 features
p_values = [0.01, 0.03, 0.08, 0.12, 0.02, 0.15, 0.04, 0.09, 0.01, 0.07]

# Sem correção: 6 significativos (p < 0.05)
# Com correção: alpha = 0.05/10 = 0.005, apenas 2 significativos

corrected_alpha, significant = bonferroni_correction(p_values)
print(f"Alpha corrigido: {corrected_alpha:.4f}")
print(f"Testes significativos: {sum(significant)}/10")
```

---

## 5. FDR (False Discovery Rate)

Alternativa menos conservadora:

```python
from statsmodels.stats.multitest import multipletests

def fdr_correction(p_values, alpha=0.05):
    """
    Correção Benjamini-Hochberg (FDR).
    """
    rejected, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return rejected, p_corrected
```

---

## 6. QUANDO USAR

- **Bonferroni:** Poucos testes (< 20), muito conservador
- **FDR:** Muitos testes (> 20), menos conservador
- **Sem correção:** Teste único ou pré-definido

---

## 7. CRITÉRIOS

- **Usar Bonferroni** para < 20 testes
- **Usar FDR** para > 20 testes
- **Documentar método** usado

---

## 8. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[STATISTICAL_SIGNIFICANCE]]
