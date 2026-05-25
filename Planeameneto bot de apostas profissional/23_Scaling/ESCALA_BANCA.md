# ESCALA_BANCA — Estratégias de Aumento Gradual

**ID:** `SC-001` | **Fase:** #phase/8 | **Owner:** Risk Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Definir estratégias matemáticas e operacionais para aumentar a banca de forma sustentável, maximizando crescimento enquanto minimiza risco de ruína.

---

## 2. FUNDAMENTOS MATEMÁTICOS

### 2.1 Kelly Criterion (Versão Conservadora)

```
Stake = (Banca_Ativa * Kelly_Fraction * Edge) / Odds

Onde:
- Banca_Ativa: 80% da banca total (20% reserva)
- Kelly_Fraction: 0.25 (conservador, não 1.0)
- Edge: CLV esperado (média dos últimos 100 apostas)
- Odds: odds da aposta decimal
```

**Por que Kelly Fraction de 0.25?**
- Kelly completo (1.0) assume conhecimento perfeito de edge
- Em apostas esportivas, edge é estimado com incerteza
- 0.25 reduz volatilidade em ~75%
- Ainda captura ~94% do crescimento a longo prazo
- Mais psicologicamente suportável

### 2.2 Exemplo Prático

```
Banca total: 1.000€
Banca ativa: 800€ (80%)
Kelly fraction: 0.25
Edge médio: 3% (CLV)
Odds da aposta: 2.00

Stake = (800 * 0.25 * 0.03) / 2.00
Stake = 3€
```

### 2.3 Ajuste por Confiança

```
Stake_Ajustado = Stake * Confiança_Factor

Onde Confiança_Factor depende de:
- Número de apostas históricas (mais = maior confiança)
- Consistência de CLV (menos variância = maior confiança)
- Recência de dados (dados recentes = maior confiança)

Tabela de Confiança:
Apostas < 50:  0.5x
Apostas 50-100: 0.75x
Apostas 100-500: 1.0x
Apostas 500+: 1.25x
```

---

## 3. CRITÉRIOS DE AUMENTO

### 3.1 Critérios Primários (BLOCKERS)

TODOS devem ser satisfeitos para aumentar:

| Critério | Threshold | Período | Justificação |
|----------|-----------|---------|--------------|
| ROI real | > 3% | Últimos 30 dias | Edge validado |
| ROI real | > 5% | Últimos 90 dias | Consistência |
| CLV médio | > 2% | Últimos 100 apostas | Edge real existe |
| Max drawdown | < 15% | Últimos 90 dias | Risco controlado |
| Sharpe ratio | > 0.5 | Últimos 90 dias | Risk-adjusted return |
| Número de apostas | > 100 | Total | Significância estatística |
| Uptime sistema | > 95% | Últimos 30 dias | Operação confiável |

### 3.2 Critérios Secundários (WARNINGS)

Se qualquer um falhar, investigar antes de aumentar:

| Critério | Warning | Critical |
|----------|---------|----------|
| Fill rate | < 80% | < 70% |
| Slippage médio | > 2% | > 3% |
| Variância de ROI | > 5% | > 10% |
| Erros operacionais | > 1/dia | > 5/dia |
| Churn (se SaaS) | > 10% | > 20% |

### 3.3 Critérios de Redução (ROLLBACK)

Se qualquer um ocorrer, reduzir imediatamente:

| Critério | Ação |
|----------|------|
| ROI < 0% por 30 dias | Reduzir banca 25% |
| Drawdown > 20% | Reduzir banca 50% |
| Drawdown > 30% | Parar operação |
| CLV < 0% por 50 apostas | Parar e revisar modelo |
| 3 meses consecutivos negativos | Parar e revisar estratégia |

---

## 4. FASES DE BANCA

### 4.1 Tabela Detalhada de Fases

| Fase | Banca Total | Banca Ativa | Stake Unitário | Stake Max | Exposição Diária | Timeline | Critério Entrada |
|------|-------------|-------------|----------------|-----------|------------------|----------|------------------|
| Micro 1 | 500€ | 400€ | 10€ | 20€ | 120€ | Mês 4-5 | Início |
| Micro 2 | 750€ | 600€ | 15€ | 30€ | 180€ | Mês 5-6 | ROI > 3% (30d) |
| Small 1 | 1.000€ | 800€ | 20€ | 40€ | 240€ | Mês 6-7 | ROI > 5% (90d) |
| Small 2 | 1.500€ | 1.200€ | 30€ | 60€ | 360€ | Mês 7-8 | ROI > 5% (90d) |
| Medium 1 | 2.000€ | 1.600€ | 40€ | 80€ | 480€ | Mês 8-9 | Drawdown < 15% |
| Medium 2 | 3.000€ | 2.400€ | 60€ | 120€ | 720€ | Mês 9-10 | Sharpe > 0.5 |
| Medium 3 | 5.000€ | 4.000€ | 100€ | 200€ | 1.200€ | Mês 10-12 | 3 meses lucro |
| Large 1 | 7.500€ | 6.000€ | 150€ | 300€ | 1.800€ | Mês 12-15 | Sharpe > 0.8 |
| Large 2 | 10.000€ | 8.000€ | 200€ | 400€ | 2.400€ | Mês 15-18 | Track record 12m |
| Large 3 | 15.000€ | 12.000€ | 300€ | 600€ | 3.600€ | Mês 18-21 | ROI anual > 20% |
| XL 1 | 25.000€ | 20.000€ | 500€ | 1.000€ | 6.000€ | Mês 21-24 | Multi-casa válido |
| XL 2 | 50.000€ | 40.000€ | 1.000€ | 2.000€ | 12.000€ | Mês 24+ | Institucional |

### 4.2 Limites por Fase

**Micro Banca (500-1.000€):**
- Max por aposta: 2 unidades
- Exposição diária: 12 unidades
- Max apostas/dia: 6
- Mercados: NBA core apenas

**Small Banca (1.000-3.000€):**
- Max por aposta: 2 unidades
- Exposição diária: 12 unidades
- Max apostas/dia: 8
- Mercados: NBA + Totals

**Medium Banca (3.000-10.000€):**
- Max por aposta: 2 unidades
- Exposição diária: 12 unidades
- Max apostas/dia: 10
- Mercados: NBA + Props

**Large Banca (10.000€+):**
- Max por aposta: 2 unidades (ou limitado por liquidez)
- Exposição diária: 12 unidades
- Max apostas/dia: ilimitado (limitado por liquidez)
- Mercados: Multi-desporto

---

## 5. ESTRATÉGIAS DE AUMENTO

### 5.1 Estratégia 1: Aumento Linear (Conservadora)

```
Aumentar 50% da banca a cada critério satisfeito
Exemplo: 500€ → 750€ → 1.000€ → 1.500€ → 2.000€

Vantagens:
- Crescimento previsível
- Risco controlado
- Fácil de implementar

Desvantagens:
- Pode ser lento
- Deixa dinheiro na mesa se edge é alto
```

### 5.2 Estratégia 2: Aumento por Performance (Agressiva)

```
Aumentar baseado em ROI recente
Se ROI > 10%: aumentar 100%
Se ROI 5-10%: aumentar 50%
Se ROI 3-5%: aumentar 25%

Vantagens:
- Aproveita edge alto
- Crescimento mais rápido

Desvantagens:
- Mais volátil
- Risco de over-betting
```

### 5.3 Estratégia 3: Híbrida (Recomendada)

```
Base: aumento linear de 50%
Bônus: +25% extra se ROI > 7%
Penalidade: -25% se ROI < 3%

Exemplo:
ROI 5%: 500€ → 750€ (50%)
ROI 8%: 500€ → 937€ (75%)
ROI 2%: 500€ → 625€ (25%)

Vantagens:
- Balanceia crescimento e risco
- Recompensa performance excepcional
- Penaliza performance fraca

Desvantagens:
- Mais complexo
- Requer monitorização constante
```

### 5.4 Estratégia 4: Ajuste Dinâmico (Avançada)

```
Stake dinâmico baseado em confiança recente
Se últimos 30 dias ROI > 5%: usar Kelly 0.3
Se últimos 30 dias ROI 3-5%: usar Kelly 0.25
Se últimos 30 dias ROI < 3%: usar Kelly 0.2

Vantagens:
- Adapta a condições de mercado
- Maximiza crescimento em boas fases
- Protege em más fases

Desvantagens:
- Muito complexo
- Requer sistema automatizado
- Pode ser volátil
```

---

## 6. PROCESSO DE AUMENTO

### 6.1 Checklist antes de Aumentar

**Financeiro:**
- [ ] ROI > 3% últimos 30 dias
- [ ] ROI > 5% últimos 90 dias
- [ ] Drawdown < 15% últimos 90 dias
- [ ] CLV médio > 2% últimos 100 apostas
- [ ] Sharpe > 0.5 últimos 90 dias

**Operacional:**
- [ ] Número de apostas > 100 total
- [ ] Uptime sistema > 95% últimos 30 dias
- [ ] Sem erros críticos últimos 30 dias
- [ ] Fill rate > 80%
- [ ] Slippage médio < 2%

**Psicológico:**
- [ ] Operador confortável com risco atual
- [ ] Sem sinais de tilt
- [ ] Disciplina mantida 100%
- [ ] Pronto para aumentar responsabilidade

### 6.2 Processo de Aumento

```
DIA 1: Decisão
  • Verificar todos os critérios
  • Calcular novo valor de banca
  • Calcular novos stakes
  • Documentar decisão

DIA 2: Execução
  • Depositar diferença na Betfair
  • Atualizar configuração do sistema
  • Recalcular limites de exposição
  • Notificar operador

DIA 3-30: Monitorização Intensiva
  • Métricas diárias
  • Check semanal
  • Alerta automático se drawdown > 10%

DIA 31: Decisão de Manter ou Rollback
  • Se ROI > 0% e drawdown < 10%: manter
  • Se ROI < 0% ou drawdown > 10%: rollback 25%
  • Se drawdown > 20%: rollback 50%
```

### 6.3 Processo de Rollback

```
IMEDIATO (se drawdown > 20%):
  1. Parar novas apostas
  2. Reduzir banca 50%
  3. Recalcular stakes
  4. Investigar causa
  5. Retornar após 7 dias se causa resolvida

PLANEJADO (se ROI < 0% por 30 dias):
  1. Reduzir banca 25%
  2. Continuar operação
  3. Monitorizar por 30 dias
  4. Se ainda ROI < 0%: reduzir mais 25%
  5. Se ROI > 0%: retomar escala normal
```

---

## 7. GESTÃO DE RISCO EM ESCALA

### 7.1 Risco de Ruína

```
Risco de Ruína ≈ ((1 - Edge) / (1 + Edge)) ^ (Banca / Stake_Max)

Exemplo:
Edge = 3%
Banca = 1.000€
Stake_Max = 40€

Risco ≈ ((1 - 0.03) / (1 + 0.03)) ^ (1000 / 40)
Risco ≈ (0.97 / 1.03) ^ 25
Risco ≈ 0.942 ^ 25
Risco ≈ 22%

Com Kelly 0.25 (stake médio 10€):
Risco ≈ (0.97 / 1.03) ^ (1000 / 10)
Risco ≈ 0.942 ^ 100
Risco ≈ 0.002 (0.2%)
```

**Regra:** Manter risco de ruína < 1%

### 7.2 Diversificação

```
Não apostar tudo num mercado:
- Max 30% da banca em NBA Moneyline
- Max 30% da banca em NBA Spread
- Max 20% da banca em NBA Totals
- Max 20% da banca em Props

Não apostar tudo num dia:
- Max 12 unidades/dia (30% da banca ativa)
- Distribuir ao longo da semana
```

### 7.3 Correlação

```
Evitar apostas altamente correlacionadas:
- Não apostar no mesmo jogo em mercados correlacionados
- Ex: Lakers Moneyline + Lakers -5.5 (alta correlação)
- Ex: Lakers Moneyline + Celtics Moneyline (correlação negativa OK)

Calcular correlação de portfolio:
Se correlação > 0.7: reduzir exposição
Se correlação < 0.3: pode aumentar exposição
```

---

## 8. MÉTRICAS DE ESCALA

### 8.1 Métricas Chave

| Métrica | Cálculo | Target | Frequência |
|---------|---------|--------|------------|
| ROI | (PnL / Stake_Total) * 100 | > 3% | Diário |
| Sharpe | (ROI_Médio / Desvio_Padrão) | > 0.5 | Mensal |
| Max Drawdown | (Max_Peak - Min_Valley) / Max_Peak | < 15% | Contínuo |
| CLV Médio | Média((Odd_Obtida / Odd_Fecho) - 1) | > 2% | Diário |
| Stake_Efficiency | PnL / Banca_Ativa | > 0.03 | Mensal |
| Risk_of_Ruin | Fórmula acima | < 1% | Mensal |

### 8.2 Dashboard de Escala

```
┌─────────────────────────────────────────────────────────────────┐
│ BANCA: 1.000€ | ATIVA: 800€ | RESERVA: 200€                      │
├─────────────────────────────────────────────────────────────────┤
│ ROI (30d): 4.2% ✓ | Sharpe: 0.8 ✓ | Drawdown: 8% ✓             │
│ CLV: 2.5% ✓ | Fill Rate: 92% ✓ | Slippage: 1.2% ✓               │
├─────────────────────────────────────────────────────────────────┤
│ PRÓXIMO AUMENTO: 1.500€ (+50%)                                  │
│ CRITÉRIOS: 6/7 satisfeitos                                      │
│ FALTANDO: Sharpe > 0.5 por 90 dias (atual: 0.8 por 60 dias)     │
│ ESTIMADO: 15 dias                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. SIMULAÇÕES DE ESCALA

### 9.1 Simulação Conservadora (ROI 3%)

```
Banca inicial: 500€
ROI mensal: 3%
Aumento: 50% a cada 3 meses de ROI > 3%

Mês 0: 500€
Mês 3: 515€ (ROI 3%) → 773€ (aumento 50%)
Mês 6: 797€ → 1.196€
Mês 9: 1.232€ → 1.848€
Mês 12: 1.903€ → 2.855€
Mês 24: ~8.000€
```

### 9.2 Simulação Otimista (ROI 7%)

```
Banca inicial: 500€
ROI mensal: 7%
Aumento: 50% a cada 3 meses de ROI > 5%

Mês 0: 500€
Mês 3: 535€ (ROI 7%) → 803€ (aumento 50%)
Mês 6: 859€ → 1.289€
Mês 9: 1.379€ → 2.069€
Mês 12: 2.214€ → 3.321€
Mês 24: ~25.000€
```

### 9.3 Simulação Pessimista (ROI 1%)

```
Banca inicial: 500€
ROI mensal: 1%
Sem aumento (não satisfaz critérios)

Mês 0: 500€
Mês 12: 563€
Mês 24: 635€

Conclusão: Se ROI < 3%, não escalar. Revisar modelo.
```

---

## 10. REGRAS FINAIS

1. **Nunca aumentar mais que 50% de uma vez.**
2. **Sempre manter 20% de reserva não apostável.**
3. **Aumento deve ser baseado em ROI real, não backtest.**
4. **Se drawdown > 20%, reduzir banca 50% imediatamente.**
5. **Se ROI < 0% por 30 dias, reduzir banca 25%.**
6. **Nunca escalar mais de um eixo ao mesmo tempo.**
7. **Monitorizar intensivamente por 30 dias após cada aumento.**
8. **Documentar todas as decisões de escala.**

---

## 11. ESTRATÉGIAS AVANÇADAS

### 11.1 Escala com Volatilidade Ajustada

**Conceito:** Ajustar Kelly fraction baseado na volatilidade recente.

```python
def volatility_adjusted_kelly(base_kelly, recent_volatility, base_volatility=0.05):
    """
    Ajusta Kelly baseado na volatilidade
    Volatilidade alta = Kelly reduzido
    Volatilidade baixa = Kelly aumentado
    """
    vol_ratio = recent_volatility / base_volatility

    # Ajuste inverso da volatilidade
    if vol_ratio > 1.5:
        return base_kelly * 0.5  # Reduzir 50% se volatilidade muito alta
    elif vol_ratio > 1.2:
        return base_kelly * 0.75  # Reduzir 25% se volatilidade alta
    elif vol_ratio < 0.8:
        return base_kelly * 1.25  # Aumentar 25% se volatilidade baixa
    else:
        return base_kelly  # Manter se volatilidade normal
```

### 11.2 Escala com Regime Detection

**Conceito:** Identificar regimes de mercado e ajustar estratégia de escala.

| Regime | Características | Estratégia de Escala |
|--------|-----------------|---------------------|
| Bull (edge alto) | CLV > 3%, ROI > 5% | Acelerar escala (+25% extra) |
| Normal | CLV 1-3%, ROI 3-5% | Escala normal (+50%) |
| Bear (edge baixo) | CLV < 1%, ROI < 3% | Parar escala, reduzir 25% |
| Transition | Volatilidade alta, CLV instável | Manter escala, monitorizar |

**Implementação:**
```python
def regime_based_scaling(current_metrics, historical_metrics):
    """Determina estratégia de escala baseado em regime"""
    current_clv = current_metrics['avg_clv']
    current_roi = current_metrics['roi']
    current_volatility = current_metrics['volatility']

    # Classificar regime
    if current_clv > 0.03 and current_roi > 0.05:
        regime = 'BULL'
    elif current_clv > 0.01 and current_roi > 0.03:
        regime = 'NORMAL'
    elif current_clv < 0.01 or current_roi < 0.03:
        regime = 'BEAR'
    elif current_volatility > 0.08:
        regime = 'TRANSITION'
    else:
        regime = 'NORMAL'

    # Estratégia de escala
    strategies = {
        'BULL': {'action': 'ACCELERATE', 'bonus': 0.25},
        'NORMAL': {'action': 'NORMAL', 'bonus': 0.0},
        'BEAR': {'action': 'REDUCE', 'penalty': 0.25},
        'TRANSITION': {'action': 'HOLD', 'bonus': 0.0}
    }

    return {
        'regime': regime,
        'strategy': strategies[regime]
    }
```

### 11.3 Escala com Correlação de Portfolio

**Conceito:** Ajustar escala baseado na correlação entre apostas.

```python
def correlation_adjusted_scale(base_stake, correlation_matrix):
    """
    Ajusta stake baseado na correlação do portfolio
    Correlação alta = reduzir stake (menos diversificação)
    Correlação baixa = manter stake (boa diversificação)
    """
    # Calcular correlação média
    avg_correlation = np.mean(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])

    # Ajuste
    if avg_correlation > 0.7:
        return base_stake * 0.7  # Reduzir 30% se correlação muito alta
    elif avg_correlation > 0.5:
        return base_stake * 0.85  # Reduzir 15% se correlação alta
    elif avg_correlation < 0.3:
        return base_stake * 1.15  # Aumentar 15% se correlação baixa
    else:
        return base_stake  # Manter se correlação normal
```

### 11.4 Escala com Confiança de Modelo

**Conceito:** Ajustar escala baseado na confiança do modelo.

```python
def confidence_adjusted_scale(base_stake, model_confidence):
    """
    Ajusta stake baseado na confiança do modelo
    Confiança alta = aumentar stake
    Confiança baixa = reduzir stake
    """
    if model_confidence > 0.8:
        return base_stake * 1.2  # Aumentar 20%
    elif model_confidence > 0.6:
        return base_stake * 1.0  # Manter
    elif model_confidence > 0.4:
        return base_stake * 0.8  # Reduzir 20%
    else:
        return base_stake * 0.5  # Reduzir 50%
```

---

## 12. AUTOMAÇÃO DE ESCALA

### 12.1 Sistema de Escala Automático

```python
class AutoScalingSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config

    def check_scaling_opportunity(self):
        """Verifica se é possível escalar"""
        metrics = self._calculate_metrics()

        # Verificar critérios
        criteria_met = 0
        total_criteria = 7

        # Critério 1: ROI > 3% últimos 30 dias
        if metrics['roi_30d'] > 0.03:
            criteria_met += 1

        # Critério 2: ROI > 5% últimos 90 dias
        if metrics['roi_90d'] > 0.05:
            criteria_met += 1

        # Critério 3: CLV > 2%
        if metrics['avg_clv'] > 0.02:
            criteria_met += 1

        # Critério 4: Drawdown < 15%
        if metrics['max_drawdown'] < 0.15:
            criteria_met += 1

        # Critério 5: Sharpe > 0.5
        if metrics['sharpe'] > 0.5:
            criteria_met += 1

        # Critério 6: Número de apostas > 100
        if metrics['n_bets'] > 100:
            criteria_met += 1

        # Critério 7: Uptime > 95%
        if metrics['uptime'] > 0.95:
            criteria_met += 1

        # Decisão
        if criteria_met >= 6:  # 6 de 7 critérios
            return {
                'can_scale': True,
                'criteria_met': criteria_met,
                'total_criteria': total_criteria
            }
        else:
            return {
                'can_scale': False,
                'criteria_met': criteria_met,
                'total_criteria': total_criteria,
                'missing': total_criteria - criteria_met
            }

    def execute_scale(self, scale_factor):
        """Executa aumento de banca"""
        current_bankroll = self.db.get_current_bankroll()
        new_bankroll = current_bankroll * scale_factor

        # Atualizar configuração
        self.db.update_bankroll(new_bankroll)

        # Recalcular limites
        self._recalculate_limits(new_bankroll)

        # Registrar escala
        self._log_scale(current_bankroll, new_bankroll, scale_factor)

        return new_bankroll
```

### 12.2 Sistema de Rollback Automático

```python
class AutoRollbackSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.last_scale = None

    def check_rollback_necessity(self):
        """Verifica se rollback é necessário"""
        metrics = self._calculate_metrics_since_last_scale()

        # Critérios de rollback
        if metrics['roi'] < 0:
            return {'rollback': True, 'reason': 'Negative ROI', 'action': 'REDUCE_25'}
        elif metrics['drawdown'] > 0.20:
            return {'rollback': True, 'reason': 'High drawdown', 'action': 'REDUCE_50'}
        elif metrics['drawdown'] > 0.30:
            return {'rollback': True, 'reason': 'Critical drawdown', 'action': 'STOP'}
        elif metrics['clv'] < 0:
            return {'rollback': True, 'reason': 'Negative CLV', 'action': 'STOP'}
        else:
            return {'rollback': False}

    def execute_rollback(self, action):
        """Executa rollback"""
        current_bankroll = self.db.get_current_bankroll()

        if action == 'REDUCE_25':
            new_bankroll = current_bankroll * 0.75
        elif action == 'REDUCE_50':
            new_bankroll = current_bankroll * 0.5
        elif action == 'STOP':
            new_bankroll = current_bankroll * 0.5  # Reduzir e parar

        self.db.update_bankroll(new_bankroll)
        self._recalculate_limits(new_bankroll)
        self._log_rollback(current_bankroll, new_bankroll, action)

        return new_bankroll
```

---

## 13. LINKS CRUZADOS

- [[23_Scaling/INDEX]] ← Seção mãe
- [[08_Risk_Management/INDEX]] → Gestão de risco e Kelly
- [[22_Real_Money_Operations/INDEX]] → Operação com dinheiro real
