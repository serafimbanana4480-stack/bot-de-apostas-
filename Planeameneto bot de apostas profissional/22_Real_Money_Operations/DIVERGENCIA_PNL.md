# Divergência PnL Real vs Esperado

**ID:** REAL-004 | **Fase:** #phase/4-6 | **Owner:** Operations Lead + Risk Manager | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise sistemática de diferenças entre PnL real (execução) e PnL esperado (sinais). Divergências indicam problemas operacionais, slippage não simulado, ou erros de execução.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar causas de divergência PnL real vs esperado |
| **Métricas** | Divergência absoluta, divergência relativa, por causa |
| **Thresholds** | Divergência < 10€ ou < 5% |
| **Custo** | 0€ (análise) |

---

## 2. CAUSAS DE DIVERGÊNCIA

### 2.1 Slippage Não Simulado

**Sintoma:** PnL real < PnL esperado consistentemente

**Causas:**
- Backtest não simula slippage real
- Odds mudam entre sinal e execução
- Liquidez insuficiente para stake completo

**Exemplo:**
```
Sinal: Odd 1.90, Stake 10€, PnL esperado: +9€
Execução: Odd 1.85, Stake 10€, PnL real: +8.50€
Divergência: -0.50€ (-5.6%)
```

**Mitigação:**
- Adicionar slippage simulado ao backtest
- Usar odds conservadoras
- Limitar stake por liquidez

### 2.2 Sinais Não Executados

**Sintoma:** PnL esperado inclui sinais não executados

**Causas:**
- Odd caiu abaixo do threshold
- Liquidez insuficiente
- Mercado fechado
- Erro de execução

**Exemplo:**
```
Sinais gerados: 10
Apostas executadas: 8
PnL esperado (10 sinais): +50€
PnL real (8 apostas): +40€
Divergência: -10€ (-20%)
```

**Mitigação:**
- Ajustar thresholds
- Melhorar liquidez
- Corrigir erros de execução

### 2.3 Comissões Não Contabilizadas

**Sintoma:** PnL real menor que esperado, mas não há slippage óbvio

**Causas:**
- Comissões da Betfair não incluídas no backtest
- Taxas de depósito/levantamento não consideradas

**Exemplo:**
```
PnL bruto: +100€
Comissões (5%): -5€
PnL líquido: +95€
Divergência: -5€
```

**Mitigação:**
- Incluir comissões no backtest
- Usar odds líquidas

### 2.4 Erros de Execução

**Sintoma:** Apostas executadas incorretamente

**Causas:**
- Seleção errada (equipa/market)
- Stake errado
- Ordem rejeitada parcialmente

**Exemplo:**
```
Sinal: Celtics Moneyline, Stake 10€
Execução: Lakers Moneyline, Stake 10€ (erro)
Divergência: Variável (depende do resultado)
```

**Mitigação:**
- Validação antes de execução
- Verificação pós-execução
- Treinamento de operadores

---

## 3. MÉTRICAS DE DIVERGÊNCIA

### 3.1 Divergência Absoluta

```python
divergencia_absoluta = abs(pnl_real - pnl_esperado)

# Thresholds
if divergencia_absoluta < 10:
    status = "EXCELLENT"
elif divergencia_absoluta < 50:
    status = "ACEITÁVEL"
else:
    status = "CRÍTICO - INVESTIGAR"
```

### 3.2 Divergência Relativa

```python
divergencia_relativa = abs(pnl_real - pnl_esperado) / abs(pnl_esperado)

# Thresholds
if divergencia_relativa < 0.05:
    status = "EXCELLENT"
elif divergencia_relativa < 0.10:
    status = "ACEITÁVEL"
else:
    status = "CRÍTICO - INVESTIGAR"
```

### 3.3 Divergência por Causa

```python
divergencia_por_causa = {
    'slippage': 0,
    'sinais_nao_executados': 0,
    'comissoes': 0,
    'erros_execucao': 0
}

# Calcular divergência por causa
for bet in bets:
    if bet['slippage'] > 0:
        divergencia_por_causa['slippage'] += bet['slippage']
    if bet['nao_executado']:
        divergencia_por_causa['sinais_nao_executados'] += bet['pnl_esperado']
    # etc.
```

---

## 4. DIAGNÓSTICO

### 4.1 Checklist

- [ ] Verificar se slippage está sendo simulado no backtest
- [ ] Comparar fill rate com esperado
- [ ] Verificar se comissões estão incluídas
- [ ] Analisar erros de execução
- [ ] Verificar se há apostas incorretas
- [ ] Comparar odds obtidas vs odds sinalizadas

### 4.2 Ferramentas de Diagnóstico

```python
# vbq/analysis/pnl_divergence.py
import pandas as pd

def analyze_pnl_divergence(bets: pd.DataFrame, signals: pd.DataFrame):
    """Analisa divergência de PnL"""
    
    # PnL real
    pnl_real = bets['pnl'].sum()
    
    # PnL esperado (sinais executados)
    pnl_esperado_executado = signals[signals['executado']]['pnl_esperado'].sum()
    
    # PnL esperado (todos os sinais)
    pnl_esperado_total = signals['pnl_esperado'].sum()
    
    # Divergências
    div_executado = abs(pnl_real - pnl_esperado_executado)
    div_total = abs(pnl_real - pnl_esperado_total)
    
    # Causas
    slippage = bets['slippage'].sum()
    sinais_nao_executado = signals[~signals['executado']]['pnl_esperado'].sum()
    
    return {
        'pnl_real': pnl_real,
        'pnl_esperado_executado': pnl_esperado_executado,
        'pnl_esperado_total': pnl_esperado_total,
        'divergencia_executado': div_executado,
        'divergencia_total': div_total,
        'slippage': slippage,
        'sinais_nao_executado': sinais_nao_executado
    }
```

---

## 5. AÇÕES CORRETIVAS

### 5.1 Slippage

- Adicionar slippage simulado ao backtest
- Usar odds conservadoras
- Limitar stake por liquidez
- Melhorar timing de execução

### 5.2 Sinais Não Executados

- Ajustar thresholds de edge
- Melhorar liquidez
- Corrigir erros de execução
- Aumentar latência de execução

### 5.3 Comissões

- Incluir comissões no backtest
- Usar odds líquidas
- Contabilizar todas as taxas

### 5.4 Erros de Execução

- Validação antes de execução
- Verificação pós-execução
- Treinamento de operadores
- Automação quando possível

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard de Divergência

```
┌─────────────────────────────────────────────────────────────┐
│ DIVERGÊNCIA PNL - [DATA]                                   │
├─────────────────────────────────────────────────────────────┤
│ Divergência Total: €15.20 (target: < €10) ⚠️               │
│ Divergência Relativa: 8.5% (target: < 5%) ⚠️               │
├─────────────────────────────────────────────────────────────┤
│ Por Causa:                                                   │
│ Slippage: €8.50 (56%)                                       │
│ Sinais não executados: €5.20 (34%)                           │
│ Comissões: €1.50 (10%)                                      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se divergência > threshold
if divergence_absoluta > 50:
    send_alert("Divergência PNL crítica", divergence)

# Alerta se causa específica > threshold
if slippage > 20:
    send_alert("Slippage crítico", slippage)
```

---

## 7. LINKS CRUZADOS

- [[22_Real_Money_Operations/INDEX]] ← Secção mãe
- [[RECONCILIACAO_DIARIA]] → Reconciliação diária
- [[DIVERGENCIA_BACKTEST]] → Divergência backtest vs paper
- [[09_Execution_System/SLIPPAGE_TRACKING]] → Tracking de slippage

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para entender performance real)
