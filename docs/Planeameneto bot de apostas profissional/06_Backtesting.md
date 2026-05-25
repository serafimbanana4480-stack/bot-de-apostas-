# 06_BACKTESTING — Validação Temporal Rigorosa de Modelos

**ID:** `BT-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Validar o modelo preditivo através de simulação histórica rigorosa, evitando todas as armadilhas que transformam backtests em fantasias. Um backtest que não passa no audit de rigor estatístico NUNCA pode ser usado para justificar dinheiro real.

---

## 2. PRINCÍPIOS FUNDAMENTAIS

### 2.1 Sem Leakage Temporal

**Regra de ouro:** Nenhuma informação de um jogo pode ser usada para prever o próprio jogo.

**Exemplos de leakage:**
- Usar estatísticas DO jogo para prever o resultado DO jogo
- Usar odds de fecho para prever resultado (look-ahead bias)
- Usar "four factors" calculados com dados DO jogo
- Usar dados de lesões que só ficaram disponíveis DEPOIS do jogo começar

### 2.2 Sem Overfitting

**Problema:** Modelo que se ajusta demasiado aos dados de treino e falha em generalizar.

**Sinais:**
- Performance treino >> performance validação/teste
- Feature importance instável entre folds
- Hiperparâmetros muito específicos

**Solução:** Purged walk-forward CV com validação hold-out

### 2.3 Custos Realistas

**Custos a incluir:**
- Comissão da exchange (Betfair: ~5%)
- Slippage (diferença entre odd sinal e odd executada): 0.5%
- Latência (tempo entre sinal e execução)
- Fill rate (nem todos os sinais são executáveis)

---

## 3. ARQUITETURA DE BACKTEST

```
┌─────────────────────────────────────────────────────────────┐
│                     DADOS HISTÓRICOS                       │
│              5 Épocas NBA (2019-2024)                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  PURGED WALK-FORWARD CV                    │
│  ├─ Treino: 36 meses rolling (ex: 2019-2022)           │
│  ├─ Validação: 1 mês (ex: Janeiro 2023)                   │
│  ├─ Embargo: 2 dias (excluir eventos próximos)        │
│  └─ Teste: 1 mês final (ex: Fevereiro 2024)             │
│                                                              │
│  Iterar: 12 folds (um por mês de validação)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              SIMULAÇÃO DE APOSTAS                          │
│  ├─ Edge > 4%                                             │
│  ├─ Prob ∈ [0.15, 0.85]                                  │
│  ├─ Stake: Kelly fracionado (K=0.5)                      │
│  ├─ Slippage: 0.5%                                         │
│  ├─ Comissão: 5%                                          │
│  └─ Limites: max 2% por aposta, 12% por dia              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MÉTRICAS DE SAÍDA                       │
│  ├─ CLV médio > 2%                                        │
│  ├─ ROI > 5% após custos                                   │
│  ├─ Sharpe Ratio > 0.5                                    │
│  ├─ Max drawdown < 20%                                   │
│  └─ Monte Carlo: 10.000 simulações                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. PURGED WALK-FORWARD CV

### 4.1 Por Que Purged?

Standard cross-validation aleatória é inadequada para dados temporais porque:
- Mistura dados do passado e futuro (leakage)
- Não respeita a ordem cronológica dos eventos
- Subestima overfitting temporal

### 4.2 Embargo

**Definição:** Período de exclusão entre treino e validação.

**Razão:** Eventos próximos no tempo podem ter informações implícitas em comum (ex: mesma equipa jogando em dias consecutivos).

**Implementação:**
- Mínimo: 2 dias
- Ideal: 3-5 dias para NBA (jogos frequentes)
- Verificar: Nenhum evento da validação está dentro do período de embargo do treino

### 4.3 Iteração Mensal

```
Fold 1: Treino Jan-Dez 2022 → Validar Nov 2022 (embargo 2-3 dias)
Fold 2: Treino Fev-Nov 2022 → Validar Dez 2022 (embargo 2-3 dias)
...
Fold 12: Treino Nov 2022-Ago 2023 → Validar Set 2023 (embargo 2-3 dias)
```

**Hold-out final:** Último mês (ex: Fevereiro 2024) NUNCA usado em treino ou validação.

---

## 5. MÉTRICAS DE DECISÃO

### 5.1 Métricas Principais

| Métrica | Fórmula | Target | Interpretação |
|---------|---------|--------|-------------|
| **CLV médio** | (odd_fecho / odd_usada) - 1 | > 2.0% | Edge sobre sharp money |
| **ROI simulado** | (Σ PnL / Σ stakes) × 100 | > 5.0% | Lucro após custos |
| **Sharpe Ratio** | ROI_médio / σ(ROI) | > 0.5 | Retorno ajustado ao risco |
| **Max Drawdown** | (peak - trough) / peak | < 20% | Perda máxima aceitável |
| **Brier Score** | (1/n) Σ (P_prev - P_real)² | < mercado | Calibração vs odds implícitas |
| **ECE** | Σ (n_i/N) × |P_prev - P_real| | < 0.05 | Erro de calibração |

### 5.2 Critérios de Passagem

O modelo passa o backtest se E SÓ SE:

1. ✅ CLV médio > 2.0% (IC 95% inferior > 0.5%)
2. ✅ ROI simulado > 5% após custos
3. ✅ Sharpe Ratio > 0.5
4. ✅ Max drawdown < 20% da banca
5. ✅ Randomization test: métricas do modelo > percentil 95 das métricas aleatórias
6. ✅ Feature importance top 5 estáveis em ≥ 8 dos 12 folds
7. ✅ Nenhuma feature com correlação > 0.95 com target (sinal de leakage)

---

## 6. SIMULAÇÃO DE MONTE CARLO

### 6.1 Objetivo

Estimar a distribuição de possíveis resultados futuros, não apenas o resultado médio.

### 6.2 Processo

```
Para i em 1 a 10.000 simulações:
    Para cada aposta no backtest:
        resultado = Bernoulli(P_modelo)  # 1 = ganha, 0 = perde
        PnL = resultado × (odd - 1) × stake
        bankroll += PnL
    Guardar bankroll_final_i
```

### 6.3 Análise de Resultados

- **Probabilidade de ruína:** % de simulações com bankroll < 50% do inicial
- **Drawdown médio:** Média de drawdown máximo por simulação
- **Drawdown p95:** 95º percentil de drawdown (pior cenário em 95% dos casos)
- **Probabilidade de objetivo:** % de simulações que atingem ROI target

### 6.4 Uso para Sizing

Se simulações mostram:
- Probabilidade de ruína > 5% com Kelly fracionado → Reduzir para 0.25 Kelly
- Probabilidade de drawdown > 30% → Reduzir stakes máximos

---

## 7. RANDOMIZATION TEST

### 7.1 Objetivo

Verificar se o modelo tem skill real ou se os resultados são devidos ao acaso.

### 7.2 Processo

```
1. Guardar métricas reais do modelo:
   - CLV médio: 2.5%
   - ROI: 6%
   - Sharpe: 0.6

2. Para i em 1 a 1000:
   - Permutar aleatoriamente os targets (vitória/derrota)
   - Treinar modelo com dados permutados
   - Calcular métricas no mesmo backtest

3. Comparar:
   - Se modelo real > percentil 95 dos modelos aleatórios → Skill real
   - Se modelo real ≈ mediana dos aleatórios → Sem skill
```

### 7.3 White's Reality Check

Teste estatístico mais formal que verifica se a performance do modelo é significativamente melhor que um benchmark (ex: apostar aleatoriamente).

---

## 8. AUDIT DE RIGOR

### 8.1 Checklist de Validação

- [ ] Purged CV implementado com embargo ≥ 2 dias
- [ ] Hold-out final separado e não usado em otimização
- [ ] Todas as features verificadas quanto a leakage temporal
- [ ] Slippage e comissão incluídos
- [ ] Randomization test passa
- [ ] Monte Carlo realizado e analisado
- [ ] Feature importance estável across folds
- [ ] Calibração validada (Brier, ECE, reliability diagrams)
- [ ] Nenhuma feature com correlação > 0.95 com target
- [ ] Código de backtest disponível para auditoria

### 8.2 Documentação

Todo backtest deve incluir:
- Dados usados (épocas, número de jogos)
- Configuração do CV (janelas, embargo, folds)
- Hiperparâmetros do modelo
- Métricas completas com intervalos de confiança
- Código ou pseudocódigo reproduzível
- Análise de sensibilidade (o que acontece se X mudar)

---

## 9. BACKTEST VS. REALIDADE

### 9.1 Por Que Backtest ≠ Realidade

1. **Slippage real pode ser maior:** 0.5% é estimativa
2. **Fill rate pode ser menor:** Nem todos os sinais são executáveis
3. **Mercado pode adaptar:** Se edge se tornar conhecido, odds mudam
4. **Modelo pode degradar:** Drift não capturado no backtest

### 9.2 Mitigação

- **Shadow mode:** Simular em produção antes de dinheiro real
- **Micro banca:** Começar com 500-1000€ para validar
- **Monitorização contínua:** Comparar backtest vs real em tempo real
- **Conservadorismo:** Usar thresholds mais conservadores em produção

---

## 10. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Modelos a validar
- [[07_Value_Detection/INDEX]] → Motor de edge validado no backtest
- [[22_Real_Money_Operations/INDEX]] → Validação com dinheiro real
- [[21_Paper_Trading/INDEX]] → Shadow mode antes de real