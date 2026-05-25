# Métricas Paper Trading

**ID:** PAPER-005 | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Métricas que validam a prontidão do sistema para operar com dinheiro real. Paper trading deve demonstrar que o sistema funciona operacionalmente antes de arriscar capital.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Validar métricas operacionais antes de dinheiro real |
| **Métricas** | CLV, ROI, Sharpe, Fill Rate, Latência |
| **Thresholds** | CLV > 1%, ROI > 0%, Fill Rate > 80% |
| **Custo** | 0€ (monitorização) |

---

## 2. MÉTRICAS CRÍTICAS

### 2.1 CLV (Closed Line Value)

**Definição:** Diferença entre probabilidade do modelo e probabilidade implícita das odds ao fecho do mercado.

**Threshold:** CLV médio > 1%

```python
clv_mean = paper_results['clv'].mean()
if clv_mean > 0.01:
    status = "PASS"
else:
    status = "FAIL - CLV muito baixo"
```

**Significado:** CLV positivo indica que o modelo tem edge real sobre o mercado.

### 2.2 ROI (Return on Investment)

**Definição:** Lucro líquido / Stake total

**Threshold:** ROI médio > 0%

```python
roi_mean = paper_results['roi'].mean()
if roi_mean > 0:
    status = "PASS"
else:
    status = "FAIL - ROI negativo"
```

**Significado:** ROI positivo indica que o sistema é lucrativo em paper trading.

### 2.3 Sharpe Ratio

**Definição:** ROI médio / desvio padrão de ROI

**Threshold:** Sharpe > 0.5

```python
sharpe = calculate_sharpe(paper_results['roi'])
if sharpe > 0.5:
    status = "PASS"
else:
    status = "FAIL - Sharpe muito baixo"
```

**Significado:** Sharpe > 0.5 indica que o lucro é consistente, não aleatório.

### 2.4 Fill Rate

**Definição:** % de sinais que seriam executados (odd disponível)

**Threshold:** Fill Rate > 80%

```python
fill_rate = signals_executed / signals_total
if fill_rate > 0.8:
    status = "PASS"
else:
    status = "FAIL - Fill rate muito baixo"
```

**Significado:** Fill rate alto indica que os sinais são executáveis na prática.

### 2.5 Latência

**Definição:** Tempo médio entre sinal e odd obtida

**Threshold:** Latência < 30s

```python
latency_mean = paper_results['latency'].mean()
if latency_mean < 30:
    status = "PASS"
else:
    status = "FAIL - Latência muito alta"
```

**Significado:** Latência baixa indica que o sistema é operacionalmente viável.

---

## 3. MÉTRICAS ADICIONAIS

### 3.1 Brier Score

**Definição:** Erro quadrático médio das probabilidades

**Threshold:** Brier < 0.25

```python
brier = calculate_brier(paper_results['prob'], paper_results['outcome'])
if brier < 0.25:
    status = "PASS"
else:
    status = "FAIL - Brier muito alto"
```

### 3.2 Calibração (ECE)

**Definição:** Expected Calibration Error

**Threshold:** ECE < 0.05

```python
ece = calculate_ece(paper_results['prob'], paper_results['outcome'])
if ece < 0.05:
    status = "PASS"
else:
    status = "FAIL - Calibração ruim"
```

### 3.3 Drawdown Máximo

**Definição:** Perda máxima em relação ao pico

**Threshold:** Drawdown < 20%

```python
max_drawdown = calculate_max_drawdown(paper_results['pnl'])
if max_drawdown < 0.2:
    status = "PASS"
else:
    status = "FAIL - Drawdown muito alto"
```

---

## 4. CRITÉRIOS DE PASSAGEM PARA MICRO BANCA

### 4.1 Checklist

- [ ] CLV médio > 1%
- [ ] ROI médio > 0%
- [ ] Sharpe > 0.5
- [ ] Fill Rate > 80%
- [ ] Latência < 30s
- [ ] Brier Score < 0.25
- [ ] ECE < 0.05
- [ ] Drawdown < 20%
- [ ] Pelo menos 100 sinais
- [ ] Pelo menos 30 dias de dados

### 4.2 Score de Prontidão

```python
def calculate_readiness_score(paper_results: dict) -> int:
    """Calcula score de prontidão (0-100)"""
    score = 0
    
    # CLV (20 pontos)
    if paper_results['clv_mean'] > 0.02:
        score += 20
    elif paper_results['clv_mean'] > 0.01:
        score += 15
    
    # ROI (20 pontos)
    if paper_results['roi_mean'] > 0.03:
        score += 20
    elif paper_results['roi_mean'] > 0:
        score += 15
    
    # Sharpe (15 pontos)
    if paper_results['sharpe'] > 1.0:
        score += 15
    elif paper_results['sharpe'] > 0.5:
        score += 10
    
    # Fill Rate (15 pontos)
    if paper_results['fill_rate'] > 0.9:
        score += 15
    elif paper_results['fill_rate'] > 0.8:
        score += 10
    
    # Latência (15 pontos)
    if paper_results['latency_mean'] < 10:
        score += 15
    elif paper_results['latency_mean'] < 30:
        score += 10
    
    # Calibração (15 pontos)
    if paper_results['ece'] < 0.03:
        score += 15
    elif paper_results['ece'] < 0.05:
        score += 10
    
    return score

# Thresholds
if score >= 80:
    status = "PRONTO PARA MICRO BANCA"
elif score >= 60:
    status = "QUASE PRONTO - REVISAR"
else:
    status = "NÃO PRONTO - CONTINUAR PAPER"
```

---

## 5. RELATÓRIO DIÁRIO

### 5.1 Template

```markdown
# Relatório Paper Trading - [Data]

## Métricas Operacionais

| Métrica | Valor | Threshold | Status |
|---------|-------|-----------|--------|
| CLV Médio | X% | > 1% | [✅/❌] |
| ROI Médio | X% | > 0% | [✅/❌] |
| Sharpe | X | > 0.5 | [✅/❌] |
| Fill Rate | X% | > 80% | [✅/❌] |
| Latência | Xs | < 30s | [✅/❌] |
| Brier Score | X | < 0.25 | [✅/❌] |
| ECE | X | < 0.05 | [✅/❌] |
| Drawdown | X% | < 20% | [✅/❌] |

## Score de Prontidão

**Score:** X/100

**Status:** [PRONTO/QUASE PRONTO/NÃO PRONTO]

## Observações

[Observações e anomalias]

## Ações Recomendadas

- [ ] [Ação 1]
- [ ] [Ação 2]

## Próxima Revisão

[Data da próxima revisão]
```

---

## 6. LINKS CRUZADOS

- [[21_Paper_Trading/INDEX]] ← Secção mãe
- [[DIVERGENCIA_BACKTEST]] → Divergência backtest vs paper
- [[LATENCIA_PAPER]] → Latência em paper trading
- [[36_KPIs/INDEX]] → KPIs do sistema

---

**Custo de implementação:** 0€ (monitorização)  
**Tempo estimado de implementação:** 3-5 dias  
**Prioridade:** ALTA (fundamental para validar antes de dinheiro real)
