# RELIABILITY DIAGRAMS — Visualização de Calibração

**ID:** `BT-005` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Visualizar graficamente a qualidade da calibração do modelo. Reliability diagrams mostram como as probabilidades previstas se comparam às frequências observadas, permitindo identificar overconfidence, underconfidence, e regiões problemáticas.

---

## 2. CONCEITO

### 2.1 O Que É Um Reliability Diagram?

Gráfico que compara:
- **Eixo X:** Probabilidade prevista pelo modelo (binned)
- **Eixo Y:** Frequência observada real

**Linha diagonal (y = x):** Calibração perfeita
- Se P_prevista = 0.7, então P_real deve ser ≈ 0.7

### 2.2 Interpretação

| Posição vs. Diagonal | Interpretação | Impacto no Edge |
|---------------------|--------------|-----------------|
| **Abaixo** | Overconfiante (P_prevista > P_real) | Edge inflacionado, perdas reais |
| **Acima** | Subconfiante (P_prevista < P_real) | Edge subestimado, oportunidades perdidas |
| **Na diagonal** | Bem calibrado | Edge preciso |

---

## 3. IMPLEMENTAÇÃO

### 3.1 Código Base

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve

def plot_reliability_diagram(y_true: np.array, y_pred: np.array, 
                             n_bins: int = 10, title: str = "Reliability Diagram"):
    """
    Plota reliability diagram com curva de calibração e histograma
    
    Args:
        y_true: Array de outcomes reais (0 ou 1)
        y_pred: Array de probabilidades previstas
        n_bins: Número de bins para agrupar
        title: Título do gráfico
    """
    # Calcular curva de calibração
    prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=n_bins)
    
    # Criar figura com 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    # --- Subplot 1: Reliability Diagram ---
    ax1.plot([0, 1], [0, 1], "k:", label="Perfeitamente Calibrado")
    ax1.plot(prob_pred, prob_true, "s-", label="Modelo", 
             linewidth=2, markersize=8)
    
    # Adicionar área de confiança (opcional)
    ax1.fill_between(prob_pred, prob_true - 0.05, prob_true + 0.05, 
                     alpha=0.2, label="±5% tolerância")
    
    ax1.set_xlabel("Probabilidade Prevista Média")
    ax1.set_ylabel("Frequência Observada")
    ax1.set_title(title)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 1])
    ax1.set_ylim([0, 1])
    
    # --- Subplot 2: Histograma de previsões ---
    ax2.hist(y_pred, bins=n_bins, range=(0, 1), alpha=0.7, edgecolor='black')
    ax2.set_xlabel("Probabilidade Prevista")
    ax2.set_ylabel("Número de Previsões")
    ax2.set_title("Distribuição de Probabilidades Previstas")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 1])
    
    plt.tight_layout()
    plt.show()
    
    # Retornar métricas
    return {
        "prob_true": prob_true,
        "prob_pred": prob_pred,
        "n_bins": n_bins
    }
```

### 3.2 Uso

```python
# Exemplo com dados de validação
y_val_true = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 0])  # Outcomes reais
y_val_pred = np.array([0.7, 0.3, 0.8, 0.6, 0.4, 0.9, 0.2, 0.35, 0.75, 0.25])  # Previsões

# Plotar
metrics = plot_reliability_diagram(y_val_true, y_val_pred, n_bins=5, 
                                   title="Validação - Modelo XGBoost")
```

---

## 4. RELIABILITY DIAGRAM POR REGIME

### 4.1 Por Que Separar?

Diferentes regimes podem ter calibração diferente:
- Favoritos podem ser overconfiantes
- Underdogs podem ser subconfiantes
- Equilibrados geralmente mais precisos

### 4.2 Implementação Multi-Regime

```python
def plot_reliability_by_regime(y_true: np.array, y_pred: np.array):
    """Plota reliability diagram separado por regime"""
    
    # Definir regimes
    def get_regime(p):
        if p >= 0.65:
            return "Favorito"
        elif p <= 0.35:
            return "Underdog"
        else:
            return "Equilibrado"
    
    regimes = [get_regime(p) for p in y_pred]
    unique_regimes = ["Favorito", "Equilibrado", "Underdog"]
    
    # Criar subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for idx, regime in enumerate(unique_regimes):
        mask = np.array([r == regime for r in regimes])
        
        if mask.sum() > 50:  # Mínimo de amostras
            prob_true, prob_pred = calibration_curve(
                y_true[mask], y_pred[mask], n_bins=5
            )
            
            ax = axes[idx]
            ax.plot([0, 1], [0, 1], "k:", label="Perfeito")
            ax.plot(prob_pred, prob_true, "s-", label=regime, 
                    linewidth=2, markersize=8)
            ax.set_xlabel("Probabilidade Prevista")
            ax.set_ylabel("Frequência Observada")
            ax.set_title(f"Regime: {regime} (n={mask.sum()})")
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1])
        else:
            axes[idx].text(0.5, 0.5, f"Insuficiente dados\n(n={mask.sum()})", 
                          ha='center', va='center')
            axes[idx].set_title(f"Regime: {regime}")
    
    plt.tight_layout()
    plt.show()
```

---

## 5. ANÁLISE E DIAGNÓSTICO

### 5.1 Padrões Comuns

| Padrão | Diagnóstico | Solução |
|--------|-------------|---------|
| **Curva abaixo da diagonal** | Overconfiança generalizada | Calibração isotónica |
| **Curva acima da diagonal** | Subconfiança generalizada | Calibração isotónica |
| **Formato S invertido** | Overconfiança em extremos | Calibração por regime |
| **Ruído aleatório** | Modelo não tem skill | Revisar features/engineering |
| **Poucos dados em bins extremos** | Amostra insuficiente | Coletar mais dados |

### 5.2 Exemplos Visuais

#### Exemplo 1: Bem Calibrado
```
Frequência Observada
1.0 |                    *
    |                 *
0.8 |              *
    |           *
0.6 |        *
    |     *
0.4 |  *
    |*
0.2 +----------------------------
    0   0.2  0.4  0.6  0.8  1.0
          Probabilidade Prevista
```

#### Exemplo 2: Overconfiante
```
Frequência Observada
1.0 |                 *
    |              *
0.8 |           *
    |        *  (abaixo da diagonal)
0.6 |     *
    |  *
0.4 |*
    |  
0.2 +----------------------------
    0   0.2  0.4  0.6  0.8  1.0
          Probabilidade Prevista
```

---

## 6. MÉTRICAS DERIVADAS

### 6.1 Maximum Calibration Error (MCE)

```python
def calculate_mce(y_true: np.array, y_pred: np.array, n_bins: int = 10) -> float:
    """Erro máximo de calibração"""
    prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=n_bins)
    mce = np.max(np.abs(prob_true - prob_pred))
    return mce
```

**Target:** MCE < 0.15

### 6.2 Expected Calibration Error (ECE)

```python
def calculate_ece(y_true: np.array, y_pred: np.array, n_bins: int = 10) -> float:
    """Erro esperado de calibração (ponderado por n)"""
    prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=n_bins)
    
    # Calcular número de amostras por bin
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_counts = np.histogram(y_pred, bins=bin_edges)[0]
    
    # ECE ponderado
    ece = 0.0
    total_samples = len(y_pred)
    
    for i in range(n_bins):
        if bin_counts[i] > 0:
            ece += (bin_counts[i] / total_samples) * abs(prob_true[i] - prob_pred[i])
    
    return ece
```

**Target:** ECE < 0.05

---

## 7. INTEGRAÇÃO COM BACKTEST

### 7.1 Reliability Diagram no Relatório de Backtest

```python
def generate_backtest_report(model, X_test, y_test):
    """Gera relatório completo incluindo reliability diagram"""
    
    # Previsões
    y_pred = model.predict_proba(X_test)[:, 1]
    
    # Calibração
    y_pred_calibrated = calibrate_predictions(y_pred, y_test)
    
    # Plotar
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Antes da calibração
    prob_true, prob_pred = calibration_curve(y_test, y_pred, n_bins=10)
    axes[0].plot([0, 1], [0, 1], "k:", label="Perfeito")
    axes[0].plot(prob_pred, prob_true, "s-", label="Não Calibrado")
    axes[0].set_title("Antes da Calibração")
    axes[0].legend()
    
    # Depois da calibração
    prob_true_c, prob_pred_c = calibration_curve(y_test, y_pred_calibrated, n_bins=10)
    axes[1].plot([0, 1], [0, 1], "k:", label="Perfeito")
    axes[1].plot(prob_pred_c, prob_true_c, "s-", label="Calibrado")
    axes[1].set_title("Depois da Calibração")
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig("backtest_calibration.png")
    
    # Métricas
    ece_before = calculate_ece(y_test, y_pred)
    ece_after = calculate_ece(y_test, y_pred_calibrated)
    
    return {
        "ece_before": ece_before,
        "ece_after": ece_after,
        "improvement": ece_before - ece_after
    }
```

---

## 8. MELHORES PRÁTICAS

1. **Número de bins:** 10 é padrão, mas pode ajustar (5-15)
2. **Amostra mínima:** Mínimo 50 amostras por bin para confiabilidade
3. **Separar por regime:** Sempre plotar por regime (favorito/underdog)
4. **Comparar com baseline:** Comparar com probabilidades implícitas do mercado
5. **Monitorizar continuamente:** Gerar diagramas semanalmente em produção

---

## 9. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secção mãe
- [[05_Machine_Learning/CALIBRACAO_ISOTONICA]] → Implementação de calibração
- [[03_Quant_Research/INDEX]] → Fundamentos de calibração