# Reconciliação Diária

**ID:** REAL-003 | **Fase:** #phase/4-6 | **Owner:** Operations Lead + Risk Manager | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Processo diário de verificação de que a execução real de apostas corresponde ao plano de risco e sinais gerados pelo sistema.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Garantir que execução = plano de risco |
| **Frequência** | Diária (após último jogo do dia) |
| **Responsável** | Operations Lead |
| **Custo** | 0€ (processo operacional) |

---

## 2. FLUXO DE RECONCILIAÇÃO

```
┌─────────────────────────────────────────────────────────────┐
│ 1. OBTER DADOS DO DIA                                      │
│    - Sinais gerados pela BD                                 │
│    - Apostas executadas (Betfair API)                       │
│    - Resultados dos jogos                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. COMPARAR SINAIS VS APOSTAS                               │
│    - Quantos sinais foram gerados?                           │
│    - Quantas apostas foram executadas?                       │
│    - Quais sinais não foram executados? Porquê?              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. VERIFICAR STAKES                                          │
│    - Stake executado = stake recomendado?                    │
│    - Se não, porquê? (limites, liquidez, erro)              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CALCULAR PnL                                              │
│    - PnL real (apostas executadas)                           │
│    - PnL esperado (sinais não executados)                    │
│    - Diferença e causas                                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. VERIFICAR LIMITES DE RISCO                                │
│    - Exposição diária dentro de limites?                      │
│    - Stake por aposta dentro de limites?                      │
│    - Circuit breakers não foram violados?                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. GERAR RELATÓRIO                                           │
│    - Resumo do dia                                           │
│    - Métricas principais                                     │
│    - Anomalias identificadas                                 │
│    - Ações recomendadas                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CHECKLIST DE RECONCILIAÇÃO

### 3.1 Antes de Começar

- [ ] Todos os jogos do dia terminaram
- [ ] Resultados estão atualizados na BD
- [ ] Apostas foram importadas da Betfair API
- [ ] Sinais foram gerados para todos os jogos

### 3.2 Durante Reconciliação

- [ ] Contar sinais gerados vs apostas executadas
- [ ] Verificar que cada aposta corresponde a um sinal
- [ ] Verificar stakes executados vs recomendados
- [ ] Calcular PnL real vs esperado
- [ ] Verificar limites de exposição
- [ ] Identificar anomalias

### 3.3 Após Reconciliação

- [ ] Gerar relatório diário
- [ ] Enviar relatório para canal de operações
- [ ] Documentar anomalias
- [ ] Planejar ações corretivas se necessário

---

## 4. MÉTRICAS DE RECONCILIAÇÃO

### 4.1 Fill Rate

```python
fill_rate = apostas_executadas / sinais_gerados

# Thresholds
if fill_rate >= 0.9:
    status = "EXCELLENT"
elif fill_rate >= 0.8:
    status = "ACEITÁVEL"
else:
    status = "CRÍTICO - INVESTIGAR"
```

### 4.2 Stake Accuracy

```python
stake_accuracy = 1 - abs(stake_executado - stake_recomendado) / stake_recomendado

# Thresholds
if stake_accuracy >= 0.95:
    status = "EXCELLENT"
elif stake_accuracy >= 0.9:
    status = "ACEITÁVEL"
else:
    status = "CRÍTICO - INVESTIGAR"
```

### 4.3 PnL Divergence

```python
pnl_divergence = abs(pnl_real - pnl_esperado)

# Thresholds
if pnl_divergence < 10:
    status = "EXCELLENT"
elif pnl_divergence < 50:
    status = "ACEITÁVEL"
else:
    status = "CRÍTICO - INVESTIGAR"
```

---

## 5. ANOMALIAS COMUNS

### 5.1 Sinais Não Executados

**Causas:**
- Odd caiu abaixo do threshold
- Liquidez insuficiente
- Mercado fechado
- Erro de execução
- Operador não executou (se manual)

**Ação:**
- Investigar causa raiz
- Se recorrente, ajustar thresholds
- Se erro de sistema, corrigir

### 5.2 Stake Executado ≠ Stake Recomendado

**Causas:**
- Limites de exposição
- Liquidez insuficiente
- Erro de cálculo
- Operador alterou (se manual)

**Ação:**
- Verificar se foi intencional
- Se erro, corrigir
- Se operador, reforçar treinamento

### 5.3 PnL Divergence

**Causas:**
- Slippage não simulado
- Odds diferentes do esperado
- Comissões não contabilizadas
- Erro de cálculo

**Ação:**
- Investigar causa raiz
- Atualizar modelo se necessário
- Corrigir erros de cálculo

---

## 6. RELATÓRIO DIÁRIO

### 6.1 Template

```markdown
# Relatório de Reconciliação - [Data]

## Resumo do Dia

- **Data:** [Data]
- **Sinais Gerados:** X
- **Apostas Executadas:** Y
- **Fill Rate:** Z%
- **PnL Real:** €X
- **PnL Esperado:** €Y
- **Divergência:** €Z

## Detalhes por Aposta

| ID | Jogo | Mercado | Seleção | Odd Sinal | Odd Exec | Stake Rec | Stake Exec | Resultado | PnL |
|----|------|---------|---------|-----------|----------|-----------|------------|-----------|------|-----|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Anomalias

- [Anomalia 1]
- [Anomalia 2]

## Ações Recomendadas

- [ ] [Ação 1]
- [ ] [Ação 2]

## Assinatura

[Operations Lead]
```

---

## 7. FERRAMENTAS

```python
# vbq/operations/reconciliation.py
import pandas as pd
from datetime import datetime

def daily_reconciliation(date: str, db):
    """Executa reconciliação diária"""
    
    # Obter dados
    signals = db.get_signals(date)
    bets = db.get_bets(date)
    results = db.get_results(date)
    
    # Comparar
    reconciliation = compare_signals_vs_bets(signals, bets)
    
    # Calcular métricas
    fill_rate = len(bets) / len(signals)
    stake_accuracy = calculate_stake_accuracy(bets, signals)
    pnl_divergence = calculate_pnl_divergence(bets, signals, results)
    
    # Gerar relatório
    report = generate_report(reconciliation, fill_rate, stake_accuracy, pnl_divergence)
    
    return report
```

---

## 8. LINKS CRUZADOS

- [[22_Real_Money_Operations/INDEX]] ← Secção mãe
- [[TRACKING_APOSTAS]] → Tracking de apostas
- [[DIVERGENCIA_PNL]] → Divergência PnL real vs esperado
- [[08_Risk_Management/INDEX]] → Gestão de risco

---

**Custo de implementação:** 0€ (processo operacional)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para operação com dinheiro real)
