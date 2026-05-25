# Bankroll Survival

**ID:** RM-007 | **Fase:** Fase 1+ | **Owner:** Risk Manager

---

## 1. OBJETIVO

Garantir sobrevivência da banca através de análise de risco de ruína e simulações Monte Carlo. O objetivo não é maximizar lucro, mas minimizar probabilidade de bancarrota.

---

## 2. RISCO DE RUÍNA

### 2.1 Fórmula de Ruína (Kelly Fraction)

Probabilidade de ruína para um dado Kelly fraction:

```
P(ruin) = ( (1 - f) / (1 + f) )^(bankroll / stake_unit)

Onde:
- f = Kelly fraction (0 a 1)
- bankroll = banca atual
- stake_unit = unidade base de aposta
```

### 2.2 Exemplos

| Kelly Fraction | Banca €1,000 | Banca €5,000 | Banca €10,000 |
|----------------|---------------|---------------|----------------|
| Full Kelly (1.0) | 13.5% | 0.02% | < 0.001% |
| Half Kelly (0.5) | 1.8% | < 0.001% | < 0.001% |
| Quarter Kelly (0.25) | 0.13% | < 0.001% | < 0.001% |
| Eighth Kelly (0.125) | 0.01% | < 0.001% | < 0.001% |

**Conclusão:** Half Kelly ou Quarter Kelly é recomendado para sobrevivência.

---

## 3. SIMULAÇÃO MONTE CARLO

### 3.1 Metodologia

```python
import numpy as np

def monte_carlo_simulation(
    bankroll,
    expected_edge,
    win_rate,
    kelly_fraction,
    num_bets=1000,
    num_simulations=10000
):
    """
    Simula trajetórias de banca usando Monte Carlo
    """
    results = []
    
    for _ in range(num_simulations):
        bankroll_path = [bankroll]
        current_bankroll = bankroll
        
        for _ in range(num_bets):
            # Determinar resultado (win/loss)
            outcome = np.random.binomial(1, win_rate)
            
            # Calcular stake (Kelly)
            stake = current_bankroll * kelly_fraction
            
            if outcome == 1:
                # Win
                profit = stake * expected_edge
                current_bankroll += profit
            else:
                # Loss
                current_bankroll -= stake
            
            # Checar ruína
            if current_bankroll <= 0:
                bankroll_path.append(0)
                break
            
            bankroll_path.append(current_bankroll)
        
        results.append(bankroll_path)
    
    return results
```

### 3.2 Métricas de Sobrevivência

```python
def calculate_survival_metrics(simulation_results):
    """
    Calcula métricas de sobrevivência das simulações
    """
    final_bankrolls = [path[-1] for path in simulation_results]
    
    metrics = {
        'ruin_probability': sum(1 for b in final_bankrolls if b <= 0) / len(final_bankrolls),
        'median_final_bankroll': np.median(final_bankrolls),
        'mean_final_bankroll': np.mean(final_bankrolls),
        'percentile_5': np.percentile(final_bankrolls, 5),
        'percentile_95': np.percentile(final_bankrolls, 95),
        'max_drawdown': calculate_max_drawdown(simulation_results),
        'expected_time_to_ruin': calculate_expected_time_to_ruin(simulation_results)
    }
    
    return metrics
```

### 3.3 Cenários de Simulação

#### Cenário 1: Edge 3%, Win Rate 53%

| Kelly Fraction | Prob. Ruína | Mediana Final | Média Final | Max Drawdown |
|----------------|-------------|---------------|-------------|--------------|
| 0.25 (Quarter) | 0.01% | €2,500 | €3,200 | 25% |
| 0.50 (Half) | 0.5% | €4,800 | €6,400 | 40% |
| 1.00 (Full) | 8% | €9,200 | €12,800 | 65% |

#### Cenário 2: Edge 2%, Win Rate 51%

| Kelly Fraction | Prob. Ruína | Mediana Final | Média Final | Max Drawdown |
|----------------|-------------|---------------|-------------|--------------|
| 0.25 (Quarter) | 0.5% | €1,800 | €2,400 | 30% |
| 0.50 (Half) | 4% | €3,200 | €4,800 | 50% |
| 1.00 (Full) | 25% | €5,500 | €9,600 | 80% |

**Recomendação:** Quarter Kelly para edge < 2.5%

---

## 4. RESERVA DE EMERGÊNCIA

### 4.1 Conceito

Manter uma reserva de emergência separada da banca operacional para garantir continuidade em caso de drawdown severo.

### 4.2 Tamanho da Reserva

**Fórmula:**
```
Reserva = 6 × Custos Operacionais Mensais + 20% da Banca Operacional
```

**Exemplo:**
- Custos operacionais: €500/mês
- Banca operacional: €5,000
- Reserva = 6 × 500 + 0.2 × 5,000 = €3,000 + €1,000 = €4,000

### 4.3 Regras de Uso

- **Uso permitido:** Apenas em drawdown > 30% da banca operacional
- **Reposição:** Repor reserva assim que banca operacional recupera para 90% do nível pré-drawdown
- **Investimento:** Reserva em conta separada, de baixo risco (depósito a prazo)

---

## 5. ESTRATÉGIAS DE SOBREVIVÊNCIA

### 5.1 Kelly Fracionado com Limites

```python
def calculate_fractional_kelly_with_limits(
    bankroll,
    edge,
    odds,
    min_stake=10,
    max_stake_percent=0.05
):
    """
    Calcula Kelly fracionado com limites absolutos
    """
    # Kelly ótimo
    kelly_optimal = edge / (odds - 1)
    
    # Kelly fracionado (quarter)
    kelly_fractional = kelly_optimal * 0.25
    
    # Calcular stake
    stake = bankroll * kelly_fractional
    
    # Aplicar limites
    stake = max(stake, min_stake)
    stake = min(stake, bankroll * max_stake_percent)
    
    return stake
```

### 5.2 Stop Loss Dinâmico

```python
def calculate_dynamic_stop_loss(bankroll, historical_drawdowns):
    """
    Calcula stop loss dinâmico baseado em drawdowns históricos
    """
    # Média de drawdowns históricos
    avg_drawdown = np.mean(historical_drawdowns)
    std_drawdown = np.std(historical_drawdowns)
    
    # Stop loss = média + 2 desvios padrão
    stop_loss = avg_drawdown + 2 * std_drawdown
    
    # Limitar a 30% máximo
    stop_loss = min(stop_loss, 0.30)
    
    return stop_loss
```

### 5.3 Escala Conservadora

**Regras:**
1. Começar com Quarter Kelly
2. Aumentar para Half Kelly após 100 apostas com ROI positivo
3. Aumentar para Full Kelly apenas após 500 apostas com ROI > 5%
4. Reduzir imediatamente se drawdown > 20%

---

## 6. ANÁLISE DE SOBREVIVÊNCIA POR FASE

### Fase 1: Paper Trading

- **Objetivo:** Validar edge sem risco
- **Banca:** Virtual (ilimitada)
- **Kelly:** Full (para teste)
- **Stop Loss:** N/A

### Fase 2: Micro Banca (€500-1,000)

- **Objetivo:** Validar execução real
- **Banca:** €500-1,000
- **Kelly:** Quarter (0.25)
- **Stop Loss:** 30%
- **Reserva:** €500

### Fase 3: Banca Pequena (€1,000-5,000)

- **Objetivo:** Escala controlada
- **Banca:** €1,000-5,000
- **Kelly:** Half (0.5)
- **Stop Loss:** 25%
- **Reserva:** €1,000

### Fase 4: Banca Média (€5,000-20,000)

- **Objetivo:** Operação estável
- **Banca:** €5,000-20,000
- **Kelly:** Half (0.5)
- **Stop Loss:** 20%
- **Reserva:** €3,000

### Fase 5: Banca Grande (>€20,000)

- **Objetivo:** Maximização controlada
- **Banca:** >€20,000
- **Kelly:** Three-Quarter (0.75)
- **Stop Loss:** 15%
- **Reserva:** €5,000

---

## 7. MONITORAMENTO

### 7.1 Métricas de Sobrevivência

| Métrica | Target | Frequência |
|---------|--------|------------|
| Probabilidade de Ruína (Monte Carlo) | < 1% | Mensal |
| Max Drawdown Real | < 20% | Contínuo |
| Reserve Ratio | > 100% | Mensal |
| Time to Recovery (após drawdown) | < 30 dias | Contínuo |

### 7.2 Dashboard

**Visualizações:**
- Trajetórias de banca (Monte Carlo vs real)
- Distribuição de resultados finais
- Probabilidade de ruína ao longo do tempo
- Drawdown real vs simulado

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar simulação Monte Carlo
- [ ] Criar dashboard de sobrevivência
- [ ] Configurar alertas de probabilidade de ruína
- [ ] Implementar stop loss dinâmico
- [ ] Automatizar cálculo de reserva
- [ ] Criar relatórios mensais de sobrevivência

---

## 9. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Índice principal
- [[08_Risk_Management/KELLY_FRACIONADO]] → Cálculo de Kelly
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
