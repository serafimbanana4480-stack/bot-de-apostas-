# Divergência Backtest vs Paper

**ID:** PAPER-003 | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise sistemática de diferenças entre resultados de backtest e paper trading. Divergências indicam problemas operacionais, model leakage, ou overfitting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar causas de divergência entre backtest e paper |
| **Métricas** | CLV, ROI, Sharpe, Brier Score |
| **Thresholds** | Diferença CLV < 1%, ROI < 2% |
| **Custo** | 0€ (análise) |

---

## 2. CAUSAS DE DIVERGÊNCIA

### 2.1 Look-Ahead Leakage

**Sintoma:** Paper CLV muito menor que backtest CLV

**Causas:**
- Features usam dados futuros no backtest
- Odds do backtest não refletem disponibilidade real
- Modelo treinado com informação não disponível em tempo real

**Mitigação:**
- Verificar timestamp de cada feature
- Validar embargo period
- Revisar pipeline de features

### 2.2 Slippage Não Simulado

**Sintoma:** Paper ROI menor que backtest ROI

**Causas:**
- Backtest não simula slippage real
- Odds mudam entre sinal e execução
- Liquidez insuficiente para stake completo

**Mitigação:**
- Adicionar slippage simulado ao backtest
- Usar odds conservadoras no backtest
- Limitar stake por liquidez

### 2.3 Overfitting

**Sintoma:** Paper performance cai drasticamente após alguns dias

**Causas:**
- Modelo memoriza padrões específicos do treino
- Não generaliza para dados fora de amostra
- Hiperparâmetros otimizados para treino

**Mitigação:**
- Purged CV com embargo
- Regularização mais forte
- Reduzir complexidade do modelo

### 2.4 Regime Change

**Sintoma:** Performance cai abruptamente sem causa óbvia

**Causas:**
- Mercado mudou (ex: regras da liga)
- Estratégia de apostas das casas mudou
- Modelo detetou padrões que deixaram de existir

**Mitigação:**
- Detetar regime change automaticamente
- Retreinar modelo com dados recentes
- Monitorizar drift de features

---

## 3. MÉTRICAS DE DIVERGÊNCIA

### 3.1 CLV Divergence

```python
clv_divergence = abs(clv_paper - clv_backtest)

# Thresholds
if clv_divergence < 0.5%:
    status = "EXCELLENT"
elif clv_divergence < 1.0%:
    status = "ACCEPTABLE"
elif clv_divergence < 2.0%:
    status = "CONCERNING"
else:
    status = "CRITICAL - INVESTIGATE"
```

### 3.2 ROI Divergence

```python
roi_divergence = abs(roi_paper - roi_backtest)

# Thresholds
if roi_divergence < 1.0%:
    status = "EXCELLENT"
elif roi_divergence < 2.0%:
    status = "ACCEPTABLE"
elif roi_divergence < 3.0%:
    status = "CONCERNING"
else:
    status = "CRITICAL - INVESTIGATE"
```

### 3.3 Sharpe Ratio Divergence

```python
sharpe_divergence = abs(sharpe_paper - sharpe_backtest)

# Thresholds
if sharpe_divergence < 0.1:
    status = "EXCELLENT"
elif sharpe_divergence < 0.2:
    status = "ACCEPTABLE"
elif sharpe_divergence < 0.3:
    status = "CONCERNING"
else:
    status = "CRITICAL - INVESTIGATE"
```

---

## 4. DIAGNÓSTICO DE DIVERGÊNCIA

### 4.1 Checklist de Diagnóstico

- [ ] Verificar timestamps das features (look-ahead?)
- [ ] Validar embargo period (2+ dias)
- [ ] Comparar odds backtest vs odds reais
- [ ] Calcular slippage médio no paper
- [ ] Verificar se liquidez é suficiente
- [ ] Analisar performance por regime/tempo
- [ ] Revisar complexidade do modelo
- [ ] Verificar se há data leakage

### 4.2 Ferramentas de Diagnóstico

```python
# vbq/tools/divergence_analysis.py
import pandas as pd
import numpy as np

def analyze_divergence(backtest_results: pd.DataFrame, paper_results: pd.DataFrame):
    """Analisa divergência entre backtest e paper"""
    
    # CLV
    clv_backtest = backtest_results['clv'].mean()
    clv_paper = paper_results['clv'].mean()
    clv_divergence = abs(clv_backtest - clv_paper)
    
    # ROI
    roi_backtest = backtest_results['roi'].mean()
    roi_paper = paper_results['roi'].mean()
    roi_divergence = abs(roi_backtest - roi_paper)
    
    # Sharpe
    sharpe_backtest = calculate_sharpe(backtest_results['pnl'])
    sharpe_paper = calculate_sharpe(paper_results['pnl'])
    sharpe_divergence = abs(sharpe_backtest - sharpe_paper)
    
    return {
        'clv_divergence': clv_divergence,
        'roi_divergence': roi_divergence,
        'sharpe_divergence': sharpe_divergence,
        'status': determine_status(clv_divergence, roi_divergence, sharpe_divergence)
    }
```

---

## 5. AÇÕES CORRETIVAS

### 5.1 Look-Ahead Leakage

- Revisar pipeline de features
- Adicionar validação de timestamps
- Implementar embargo period estrito

### 5.2 Slippage

- Adicionar slippage simulado ao backtest
- Usar odds conservadoras
- Limitar stake por liquidez

### 5.3 Overfitting

- Aumentar regularização
- Reduzir complexidade do modelo
- Aumentar tamanho de treino

### 5.4 Regime Change

- Detetar regime change
- Retreinar modelo
- Monitorizar drift

---

## 6. RELATÓRIO DE DIVERGÊNCIA

### 6.1 Template

```markdown
# Relatório de Divergência - [Data]

## Métricas de Divergência

| Métrica | Backtest | Paper | Divergência | Status |
|---------|----------|-------|-------------|--------|
| CLV | X% | Y% | Z% | [STATUS] |
| ROI | X% | Y% | Z% | [STATUS] |
| Sharpe | X | Y | Z | [STATUS] |

## Análise

[Causa provável identificada]

## Ações Recomendadas

- [ ] [Ação 1]
- [ ] [Ação 2]
- [ ] [Ação 3]

## Próxima Revisão

[Data da próxima revisão]
```

---

## 7. LINKS CRUZADOS

- [[21_Paper_Trading/INDEX]] ← Secção mãe
- [[DIVERGENCIA_PNL]] → Divergência PnL real vs esperado
- [[06_Backtesting/INDEX]] → Backtesting rigoroso
- [[LEAKAGE_TEMPORAL]] → Temporal leakage detection

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para validar modelo antes de dinheiro real)
