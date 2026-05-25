---
ID: FT-003
tags: #status/active #financial #bankroll #management #deposits #withdrawals
---

# Gestão de Banca

## Objetivo
Estabelecer políticas e processos rigorosos para gestão da banca de apostas (bankroll), incluindo regras de aporte (deposits), levantamentos (withdrawals), alocação de capital, e gestão de risco. O sistema deve garantir sustentabilidade a longo prazo, proteger contra ruína (risk of ruin), e otimizar o crescimento do capital.

## O que faz
- Define regras de stake sizing baseadas em Kelly fracionado e gestão de risco (max drawdown, max stake por aposta).
- Implementa processo de aporte: quando adicionar capital, quanto adicionar, e de onde (conta bancária → bookmaker).
- Estabelece regras de levantamento: quando retirar lucros, quanto retirar, e para onde (bookmaker → conta bancária).
- Define alocação de capital por bookmaker, por estratégia, e por mercado para diversificação de risco.
- Implementa alertas de bankroll: quando a banca atinge thresholds de aviso ou ação.

## Porque existe
- **Sustentabilidade**: Sem gestão de banca rigorosa, mesmo uma estratégia com edge positivo pode levar à ruína devido à variância. O Kelly Criterion otimiza o crescimento enquanto minimiza o risco de ruína.
- **Liquidez**: A banca deve estar distribuída estrategicamente por múltiplos bookmakers para garantir liquidez quando surgem oportunidades de valor.
- **Disciplina**: Regras escritas de aporte e levantamento evitam decisões emocionais (ex: apostar mais após uma sequência de wins, ou recuperar perdas após losses).
- **Compliance**: Movimentos de capital entre contas devem ser documentados para fins fiscais e anti-lavagem de dinheiro (AML).

---

## Políticas de Stake Sizing

### Kelly Fracionado
```python
class KellyCriterion:
    """
    Implementa Kelly Criterion para stake sizing ótimo.
    """
    def __init__(self, kelly_fraction=0.25):
        """
        kelly_fraction: Fracionamento do Kelly (0.25 = Kelly/4)
        Valores comuns: 0.25 (conservador), 0.5 (moderado), 1.0 (agressivo)
        """
        self.kelly_fraction = kelly_fraction

    def calculate_kelly_stake(self, bankroll, decimal_odd, true_probability):
        """
        Calcula stake ótima usando Kelly Criterion.

        f* = (bp - q) / b

        Onde:
        - b = decimal_odd - 1 (net odds)
        - p = true_probability (probabilidade real de win)
        - q = 1 - p (probabilidade de loss)
        """
        b = decimal_odd - 1
        p = true_probability
        q = 1 - p

        if b <= 0 or p <= 0 or p >= 1:
            return 0

        kelly_fraction = (b * p - q) / b

        # Kelly nunca deve ser negativo (edge negativo)
        if kelly_fraction < 0:
            return 0

        # Aplicar fracionamento
        adjusted_fraction = kelly_fraction * self.kelly_fraction

        # Limitar a máximo de 5% da banca por aposta
        max_fraction = 0.05
        adjusted_fraction = min(adjusted_fraction, max_fraction)

        stake = bankroll * adjusted_fraction
        return round(stake, 2)

    def calculate_stake_from_edge(self, bankroll, decimal_odd, edge_percent):
        """
        Calcula stake baseada em edge percentual.

        edge_percent = (decimal_odd * implied_probability - 1) * 100
        """
        if edge_percent <= 0:
            return 0

        # Regra simples: 1% da banca por 1% de edge (max 5%)
        stake_fraction = min(edge_percent / 100, 0.05)

        # Aplicar fracionamento Kelly
        stake_fraction *= self.kelly_fraction

        stake = bankroll * stake_fraction
        return round(stake, 2)
```

### Limites de Stake
```python
class StakeLimiter:
    """
    Aplica limites de stake para gestão de risco.
    """
    def __init__(self, config):
        self.config = config

    def validate_stake(self, stake, bankroll):
        """
        Valida se o stake está dentro dos limites permitidos.
        """
        stake_fraction = stake / bankroll

        # Limite máximo por aposta
        if stake_fraction > self.config["max_stake_fraction"]:
            raise StakeLimitError(
                f"Stake excede máximo de {self.config['max_stake_fraction']*100}% da banca"
            )

        # Limite máximo por dia
        daily_stake = self._get_daily_stake()
        if daily_stake + stake > self.config["max_daily_stake"]:
            raise StakeLimitError(
                f"Stake diário excede máximo de {self.config['max_daily_stake']}€"
            )

        # Limite máximo por mercado
        market_stake = self._get_market_stake()
        if market_stake + stake > self.config["max_market_stake"]:
            raise StakeLimitError(
                f"Stake no mercado excede máximo de {self.config['max_market_stake']}€"
            )

        return True

    def get_adjusted_stake(self, calculated_stake, bankroll):
        """
        Ajusta o stake calculado para respeitar todos os limites.
        """
        max_stake = bankroll * self.config["max_stake_fraction"]
        return min(calculated_stake, max_stake)
```

---

## Aporte de Capital (Deposits)

### Política de Aporte
```python
class DepositPolicy:
    """
    Define quando e quanto adicionar capital à banca.
    """
    def __init__(self, config):
        self.config = config

    def should_deposit(self, current_bankroll, min_bankroll):
        """
        Determina se deve fazer um aporte.
        """
        # Aporte se banca cair abaixo do mínimo
        if current_bankroll < min_bankroll:
            return {
                "should_deposit": True,
                "reason": "BELOW_MINIMUM",
                "current": current_bankroll,
                "minimum": min_bankroll,
                "suggested_amount": min_bankroll - current_bankroll
            }

        # Aporte se oportunidade de crescimento (discrição do owner)
        # Ex: se ROI últimos 3 meses > 10%
        recent_roi = self._get_recent_roi(months=3)
        if recent_roi > self.config["growth_roi_threshold"]:
            return {
                "should_deposit": True,
                "reason": "GROWTH_OPPORTUNITY",
                "recent_roi": recent_roi,
                "suggested_amount": current_bankroll * 0.20  # 20% da banca atual
            }

        return {"should_deposit": False}

    def calculate_deposit_amount(self, current_bankroll, target_bankroll):
        """
        Calcula valor do aporte para atingir banca alvo.
        """
        deposit = target_bankroll - current_bankroll
        return max(0, round(deposit, 2))

    def execute_deposit(self, amount, from_account, to_bookmaker):
        """
        Executa transferência de aporte.
        """
        # 1. Validar saldo na conta de origem
        if not self._validate_balance(from_account, amount):
            raise InsufficientFundsError()

        # 2. Criar registro de transação
        transaction = {
            "type": "DEPOSIT",
            "amount": amount,
            "from_account": from_account,
            "to_bookmaker": to_bookmaker,
            "status": "PENDING",
            "created_at": datetime.utcnow()
        }

        # 3. Executar transferência (via API bancária ou manual)
        # Implementação depende do banco/bookmaker

        # 4. Atualizar status
        transaction["status"] = "COMPLETED"
        transaction["completed_at"] = datetime.utcnow()

        return transaction
```

### Regras de Aporte
| Condição | Ação | Valor |
|----------|------|-------|
| Banca < 80% do mínimo | Aporte obrigatório | Restaurar para 100% do mínimo |
| ROI últimos 3 meses > 10% | Aporte opcional | +20% da banca atual |
| ROI últimos 6 meses > 20% | Aporte recomendado | +30% da banca atual |
| Drawdown > 20% | Pausa de aportes | Revisão de estratégia |

---

## Levantamento de Lucros (Withdrawals)

### Política de Levantamento
```python
class WithdrawalPolicy:
    """
    Define quando e quanto levantar lucros.
    """
    def __init__(self, config):
        self.config = config

    def should_withdraw(self, current_bankroll, initial_bankroll):
        """
        Determina se deve fazer um levantamento.
        """
        profit = current_bankroll - initial_bankroll
        profit_percentage = (profit / initial_bankroll) * 100

        # Levantamento se lucro > threshold
        if profit_percentage > self.config["withdraw_profit_threshold"]:
            return {
                "should_withdraw": True,
                "reason": "PROFIT_THRESHOLD",
                "profit": profit,
                "profit_percentage": profit_percentage
            }

        # Levantamento periódico (mensal)
        if self._is_monthly_withdrawal_due():
            return {
                "should_withdraw": True,
                "reason": "MONTHLY_SCHEDULED",
                "profit": profit
            }

        return {"should_withdraw": False}

    def calculate_withdrawal_amount(self, current_bankroll, initial_bankroll):
        """
        Calcula valor do levantamento.
        """
        profit = current_bankroll - initial_bankroll

        # Levantar 50% do lucro
        withdrawal_amount = profit * 0.5

        # Manter mínimo de banca
        min_bankroll = initial_bankroll * self.config["min_bankroll_ratio"]
        if current_bankroll - withdrawal_amount < min_bankroll:
            withdrawal_amount = current_bankroll - min_bankroll

        return max(0, round(withdrawal_amount, 2))

    def execute_withdrawal(self, amount, from_bookmaker, to_account):
        """
        Executa levantamento.
        """
        # 1. Validar saldo no bookmaker
        if not self._validate_bookmaker_balance(from_bookmaker, amount):
            raise InsufficientFundsError()

        # 2. Criar registro de transação
        transaction = {
            "type": "WITHDRAWAL",
            "amount": amount,
            "from_bookmaker": from_bookmaker,
            "to_account": to_account,
            "status": "PENDING",
            "created_at": datetime.utcnow()
        }

        # 3. Executar levantamento (via API do bookmaker)
        # Implementação depende do bookmaker

        # 4. Atualizar status
        transaction["status"] = "COMPLETED"
        transaction["completed_at"] = datetime.utcnow()

        return transaction
```

### Regras de Levantamento
| Condição | Ação | Valor |
|----------|------|-------|
| Lucro > 50% da banca inicial | Levantamento automático | 50% do lucro |
| Lucro > 100% da banca inicial | Levantamento automático | 75% do lucro |
| Fim do mês | Levantamento periódico | 25% do lucro mensal |
| Banca > 2x inicial | Levantamento agressivo | Manter 1.5x inicial, levantar resto |

---

## Alocação de Capital

### Distribuição por Bookmaker
```python
class CapitalAllocation:
    """
    Gerencia alocação de capital por bookmaker.
    """
    def __init__(self, config):
        self.config = config

    def calculate_allocation(self, total_bankroll):
        """
        Calcula alocação ótima por bookmaker.
        """
        allocation = {}

        # Distribuição baseada em:
        # 1. Liquidez do bookmaker
        # 2. Limites de aposta
        # 3. Histórico de sucesso

        for bookmaker, weight in self.config["bookmaker_weights"].items():
            allocation[bookmaker] = total_bankroll * weight

        return allocation

    def rebalance_portfolio(self, current_allocations, target_allocations):
        """
        Calcula transferências necessárias para rebalancear.
        """
        transfers = []

        for bookmaker in target_allocations:
            current = current_allocations.get(bookmaker, 0)
            target = target_allocations[bookmaker]
            diff = target - current

            if abs(diff) > self.config["rebalance_threshold"]:
                transfers.append({
                    "bookmaker": bookmaker,
                    "action": "DEPOSIT" if diff > 0 else "WITHDRAW",
                    "amount": abs(diff)
                })

        return transfers
```

### Pesos de Alocação Sugeridos
| Bookmaker | Peso Sugerido | Justificativa |
|-----------|---------------|---------------|
| Betfair | 40% | Maior liquidez, melhores odds |
| Pinnacle | 30% | Limites altos, sharp |
| Betano | 15% | Mercado português, bónus |
| Bwin | 10% | Diversificação |
| Outros | 5% | Oportunidades específicas |

---

## Alertas de Bankroll

### Sistema de Alertas
```python
class BankrollAlerts:
    """
    Gera alertas baseados em thresholds de bankroll.
    """
    def __init__(self, config):
        self.config = config

    def check_alerts(self, current_bankroll, initial_bankroll):
        """
        Verifica se deve gerar alertas.
        """
        alerts = []
        drawdown = (initial_bankroll - current_bankroll) / initial_bankroll

        # Alerta de drawdown
        if drawdown > self.config["drawdown_warning_threshold"]:
            alerts.append({
                "type": "DRAWDOWN_WARNING",
                "severity": "WARNING",
                "message": f"Drawdown de {drawdown*100:.1f}% detetado",
                "current_bankroll": current_bankroll,
                "initial_bankroll": initial_bankroll
            })

        if drawdown > self.config["drawdown_critical_threshold"]:
            alerts.append({
                "type": "DRAWDOWN_CRITICAL",
                "severity": "CRITICAL",
                "message": f"Drawdown crítico de {drawdown*100:.1f}%! Pausar apostas.",
                "action": "PAUSE_BETTING"
            })

        # Alerta de banca baixa
        if current_bankroll < self.config["min_bankroll"]:
            alerts.append({
                "type": "LOW_BANKROLL",
                "severity": "WARNING",
                "message": f"Banca abaixo do mínimo ({current_bankroll}€ < {self.config['min_bankroll']}€)",
                "action": "CONSIDER_DEPOSIT"
            })

        # Alerta de crescimento
        growth = (current_bankroll / initial_bankroll) - 1
        if growth > self.config["growth_celebration_threshold"]:
            alerts.append({
                "type": "GROWTH_MILESTONE",
                "severity": "INFO",
                "message": f"Banca cresceu {growth*100:.1f}%! Considerar levantamento.",
                "current_bankroll": current_bankroll
            })

        return alerts
```

### Thresholds de Alerta
| Métrica | Warning | Critical | Ação |
|---------|---------|----------|------|
| Drawdown | 15% | 25% | Pausar apostas se crítico |
| Banca vs Mínimo | 90% | 80% | Aporte se abaixo de 80% |
| Crescimento | 50% | 100% | Levantamento parcial |
| Apostas consecutivas loss | 5 | 10 | Reduzir stake 50% |

---

## Gestão de Emergência

### Plano de Recuperação
```python
class EmergencyRecovery:
    """
    Plano de recuperação em caso de drawdown severo.
    """
    def __init__(self, config):
        self.config = config

    def trigger_recovery_plan(self, current_bankroll, initial_bankroll):
        """
        Ativa plano de recuperação se drawdown severo.
        """
        drawdown = (initial_bankroll - current_bankroll) / initial_bankroll

        if drawdown < self.config["recovery_threshold"]:
            return None

        recovery_actions = []

        # 1. Reduzir stakes drasticamente
        recovery_actions.append({
            "action": "REDUCE_STAKES",
            "new_stake_multiplier": 0.25,  # 25% do stake normal
            "reason": "Drawdown severo"
        })

        # 2. Pausar mercados de alto risco
        recovery_actions.append({
            "action": "PAUSE_HIGH_RISK_MARKETS",
            "markets": ["player_props", "live_betting"],
            "reason": "Reduzir variância"
        })

        # 3. Revisar modelo
        recovery_actions.append({
            "action": "REVIEW_MODEL",
            "priority": "HIGH",
            "reason": "Verificar se modelo ainda tem edge"
        })

        # 4. Considerar aporte de capital (após revisão)
        if drawdown > 0.30:
            recovery_actions.append({
                "action": "CONSIDER_DEPOSIT",
                "condition": "Após revisão e validação do modelo",
                "reason": "Recuperar banca para níveis operacionais"
            })

        return recovery_actions
```

---

## Thresholds e Tabelas

| Parâmetro | Valor Inicial | Valor Mínimo | Valor Máximo | Ajuste |
|-----------|---------------|--------------|--------------|--------|
| Banca Inicial | 1000€ | 500€ | 50000€ | Revisão trimestral |
| Kelly Fraction | 0.25 | 0.10 | 0.50 | Baseado em confiança |
| Max Stake por Aposta | 5% | 2% | 10% | Baseado em risco |
| Max Stake Diário | 20% | 10% | 30% | Baseado em variância |
| Min Bankroll Ratio | 0.8 | 0.5 | 1.0 | Baseado em tolerância |

| Evento | Threshold | Ação Automática | Ação Manual |
|--------|-----------|-----------------|-------------|
| Drawdown > 15% | Warning | Reduzir stakes 25% | Revisar apostas |
| Drawdown > 25% | Critical | Pausar apostas | Revisão completa |
| Lucro > 50% | Milestone | Alerta | Decisão levantamento |
| 5 losses consecutivos | Warning | Reduzir stakes 50% | Revisar estratégia |
| 10 losses consecutivos | Critical | Pausar apostas | Revisão modelo |

---

## Links Cruzados

- [[PNL_TRACKING]] → Rastreamento de PnL
- [[08_Risk_Management/KELLY_FRACIONADO]] → Detalhes do Kelly Criterion
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controlo de drawdown
- [[TAX_REPORTING]] → Impostos sobre lucros
- [[FINANCIAL_REPORTS]] → Relatórios de banca