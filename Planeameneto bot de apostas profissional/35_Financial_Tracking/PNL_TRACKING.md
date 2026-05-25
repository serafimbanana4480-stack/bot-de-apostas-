---
ID: FT-002
tags: #status/active #financial #pnl #tracking #reconciliation #audit
---

# Rastreamento de PnL

## Objetivo
Implementar um sistema rigoroso de rastreamento de Profit and Loss (PnL) para todas as operações de apostas, incluindo reconciliação automática com bookmakers, auditoria de transações, e geração de relatórios de performance. O sistema deve garantir precisão de 99.9% nos cálculos, rastreabilidade completa de cada aposta, e conformidade com requisitos fiscais.

## O que faz
- Registra todas as apostas com metadados completos: sinal original, odd executada, stake, resultado, comissão, e timestamp.
- Calcula PnL em tempo real: gross PnL (antes de comissões), net PnL (após comissões), e PnL acumulado.
- Implementa reconciliação automática: compara dados do sistema com extratos de bookmakers e flaga discrepâncias.
- Define processo de auditoria: revisão manual de apostas disputadas, validação de resultados, e correção de erros.
- Gera relatórios de performance: diário, semanal, mensal, e YTD com métricas avançadas (ROI, yield, CLV, Sharpe ratio).

## Porque existe
- **Precisão Financeira**: Erros de cálculo de PnL podem levar a decisões erradas sobre stake sizing, bankroll management, e estratégia de apostas. Um sistema automatizado elimina erros humanos.
- **Compliance Fiscal**: As autoridades fiscais exigem registos detalhados de todas as transações de apostas para cálculo de impostos. O sistema deve gerar relatórios auditáveis.
- **Otimização de Estratégia**: Análise de PnL por mercado, tipo de aposta, bookmaker, e período permite identificar o que funciona e o que não funciona.
- **Accountability**: Em caso de disputa com um bookmaker ou questionamento de um subscritor, um registo completo e auditável é essencial.

---

## Modelo de Dados

### Tabela: bets
```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(50) UNIQUE,  -- Referência ao sinal original
    game_id VARCHAR(50) NOT NULL,
    game_date TIMESTAMP WITH TIME ZONE NOT NULL,
    market VARCHAR(50) NOT NULL,  -- spread, total, moneyline, player_prop
    selection TEXT NOT NULL,  -- Ex: "Warriors -3.5", "Over 225.5"
    bookmaker VARCHAR(50) NOT NULL,
    odd_signal DECIMAL(10, 4) NOT NULL,  -- Odd do sinal
    odd_executed DECIMAL(10, 4) NOT NULL,  -- Odd realmente obtida
    odd_closed DECIMAL(10, 4),  -- Odd de fechamento do mercado
    stake DECIMAL(10, 2) NOT NULL,  -- Valor apostado em EUR
    stake_units DECIMAL(5, 2) NOT NULL,  -- Stake em unidades (para normalização)
    result VARCHAR(20),  -- WIN, LOSS, PUSH, PENDING, VOID
    gross_pnl DECIMAL(10, 2),  -- PnL antes de comissões
    commission DECIMAL(10, 2) DEFAULT 0,  -- Comissão do bookmaker
    net_pnl DECIMAL(10, 2),  -- PnL após comissões
    clv DECIMAL(5, 2),  -- Closed Line Value: (odd_executed / odd_closed) - 1
    slippage DECIMAL(5, 2),  -- (odd_executed - odd_signal) / odd_signal
    bankroll_before DECIMAL(10, 2),  -- Banca antes da aposta
    bankroll_after DECIMAL(10, 2),  -- Banca após a aposta
    placed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    settled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',  -- Dados adicionais
    is_reconciled BOOLEAN DEFAULT FALSE,  -- Reconciliado com bookmaker
    reconciliation_notes TEXT
);

CREATE INDEX idx_bets_signal_id ON bets(signal_id);
CREATE INDEX idx_bets_game_date ON bets(game_date);
CREATE INDEX idx_bets_result ON bets(result);
CREATE INDEX idx_bets_bookmaker ON bets(bookmaker);
CREATE INDEX idx_bets_market ON bets(market);
CREATE INDEX idx_bets_placed_at ON bets(placed_at);
```

### Tabela: bankroll_transactions
```sql
CREATE TABLE bankroll_transactions (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,  -- Betfair, Betano, etc.
    transaction_type VARCHAR(20) NOT NULL,  -- DEPOSIT, WITHDRAWAL, BET, WIN, LOSS, COMMISSION
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    balance_before DECIMAL(10, 2),
    balance_after DECIMAL(10, 2),
    reference_id VARCHAR(100),  -- ID da transação no bookmaker
    bet_id INTEGER REFERENCES bets(id) ON DELETE SET NULL,
    description TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_reconciled BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_bankroll_transactions_account_id ON bankroll_transactions(account_id);
CREATE INDEX idx_bankroll_transactions_type ON bankroll_transactions(transaction_type);
CREATE INDEX idx_bankroll_transactions_occurred_at ON bankroll_transactions(occurred_at);
```

### Tabela: reconciliation_discrepancies
```sql
CREATE TABLE reconciliation_discrepancies (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER REFERENCES bets(id) ON DELETE SET NULL,
    transaction_id INTEGER REFERENCES bankroll_transactions(id) ON DELETE SET NULL,
    discrepancy_type VARCHAR(50) NOT NULL,  -- AMOUNT_MISMATCH, RESULT_MISMATCH, MISSING_BET, DUPLICATE_BET
    expected_value DECIMAL(10, 2),
    actual_value DECIMAL(10, 2),
    difference DECIMAL(10, 2),
    severity VARCHAR(20),  -- LOW, MEDIUM, HIGH, CRITICAL
    status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, UNDER_REVIEW, RESOLVED, IGNORED
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by INTEGER,
    resolution_notes TEXT
);

CREATE INDEX idx_reconciliation_discrepancies_status ON reconciliation_discrepancies(status);
CREATE INDEX idx_reconciliation_discrepancies_severity ON reconciliation_discrepancies(severity);
```

---

## Cálculo de PnL

### Fórmulas de Cálculo
```python
class PnLCalculator:
    """
    Calcula PnL para apostas individuais e agregadas.
    """
    def calculate_bet_pnl(self, bet):
        """
        Calcula PnL para uma aposta individual.
        """
        odd = bet["odd_executed"]
        stake = bet["stake"]
        result = bet["result"]

        if result == "WIN":
            gross_pnl = stake * (odd - 1)
        elif result == "LOSS":
            gross_pnl = -stake
        elif result == "PUSH":
            gross_pnl = 0
        elif result == "VOID":
            gross_pnl = 0
        else:  # PENDING
            gross_pnl = 0

        commission = bet.get("commission", 0)
        net_pnl = gross_pnl - commission

        return {
            "gross_pnl": round(gross_pnl, 2),
            "net_pnl": round(net_pnl, 2),
            "commission": round(commission, 2)
        }

    def calculate_clv(self, odd_executed, odd_closed):
        """
        Calcula Closed Line Value.
        CLV > 0 indica que a aposta foi feita a uma melhor odd que o fechamento.
        """
        if odd_closed is None or odd_closed == 0:
            return 0

        clv = (odd_executed / odd_closed) - 1
        return round(clv * 100, 2)  # Em percentagem

    def calculate_slippage(self, odd_signal, odd_executed):
        """
        Calcula slippage (diferença entre odd do sinal e odd executada).
        Slippage negativo indica pior odd que o sinal.
        """
        if odd_signal == 0:
            return 0

        slippage = (odd_executed - odd_signal) / odd_signal
        return round(slippage * 100, 2)  # Em percentagem

    def calculate_aggregate_pnl(self, bets, start_date=None, end_date=None):
        """
        Calcula PnL agregado para um conjunto de apostas.
        """
        filtered_bets = bets
        if start_date:
            filtered_bets = [b for b in filtered_bets if b["placed_at"] >= start_date]
        if end_date:
            filtered_bets = [b for b in filtered_bets if b["placed_at"] <= end_date]

        total_stake = sum(b["stake"] for b in filtered_bets)
        total_gross_pnl = sum(b["gross_pnl"] for b in filtered_bets)
        total_net_pnl = sum(b["net_pnl"] for b in filtered_bets)
        total_commission = sum(b["commission"] for b in filtered_bets)

        wins = sum(1 for b in filtered_bets if b["result"] == "WIN")
        losses = sum(1 for b in filtered_bets if b["result"] == "LOSS")
        pushes = sum(1 for b in filtered_bets if b["result"] == "PUSH")
        total = len(filtered_bets)

        win_rate = wins / total if total > 0 else 0
        roi = (total_net_pnl / total_stake * 100) if total_stake > 0 else 0
        yield = roi  # Yield é sinónimo de ROI em betting

        return {
            "total_bets": total,
            "total_stake": round(total_stake, 2),
            "total_gross_pnl": round(total_gross_pnl, 2),
            "total_net_pnl": round(total_net_pnl, 2),
            "total_commission": round(total_commission, 2),
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": round(win_rate * 100, 2),
            "roi": round(roi, 2),
            "yield": round(yield, 2)
        }
```

---

## Reconciliação Automática

### Processo de Reconciliação
```python
class ReconciliationEngine:
    """
    Reconcilia dados do sistema com extratos de bookmakers.
    """
    def __init__(self, db, bookmaker_apis):
        self.db = db
        self.bookmaker_apis = bookmaker_apis

    async def reconcile_account(self, account_id, start_date, end_date):
        """
        Reconcilia todas as transações de uma conta num período.
        """
        # 1. Obter transações do sistema
        system_transactions = await self.db.get_bankroll_transactions(
            account_id, start_date, end_date
        )

        # 2. Obter transações do bookmaker
        bookmaker_transactions = await self.bookmaker_apis.get_transactions(
            account_id, start_date, end_date
        )

        # 3. Comparar e detetar discrepâncias
        discrepancies = self._compare_transactions(
            system_transactions,
            bookmaker_transactions
        )

        # 4. Registrar discrepâncias
        for discrepancy in discrepancies:
            await self.db.insert("reconciliation_discrepancies", discrepancy)

        return {
            "total_system": len(system_transactions),
            "total_bookmaker": len(bookmaker_transactions),
            "discrepancies": len(discrepancies)
        }

    def _compare_transactions(self, system_txs, bookmaker_txs):
        """
        Compara transações e deteta discrepâncias.
        """
        discrepancies = []
        system_by_ref = {tx["reference_id"]: tx for tx in system_txs}
        bookmaker_by_ref = {tx["reference_id"]: tx for tx in bookmaker_txs}

        # Transações no sistema mas não no bookmaker
        for ref_id, system_tx in system_by_ref.items():
            if ref_id not in bookmaker_by_ref:
                discrepancies.append({
                    "discrepancy_type": "MISSING_IN_BOOKMAKER",
                    "transaction_id": system_tx["id"],
                    "expected_value": system_tx["amount"],
                    "actual_value": None,
                    "severity": "HIGH",
                    "description": f"Transação {ref_id} não encontrada no bookmaker"
                })

        # Transações no bookmaker mas não no sistema
        for ref_id, bookmaker_tx in bookmaker_by_ref.items():
            if ref_id not in system_by_ref:
                discrepancies.append({
                    "discrepancy_type": "MISSING_IN_SYSTEM",
                    "expected_value": None,
                    "actual_value": bookmaker_tx["amount"],
                    "severity": "MEDIUM",
                    "description": f"Transação {ref_id} não encontrada no sistema"
                })

        # Transações com valores diferentes
        common_refs = set(system_by_ref.keys()) & set(bookmaker_by_ref.keys())
        for ref_id in common_refs:
            system_tx = system_by_ref[ref_id]
            bookmaker_tx = bookmaker_by_ref[ref_id]

            if abs(system_tx["amount"] - bookmaker_tx["amount"]) > 0.01:
                discrepancies.append({
                    "discrepancy_type": "AMOUNT_MISMATCH",
                    "transaction_id": system_tx["id"],
                    "expected_value": system_tx["amount"],
                    "actual_value": bookmaker_tx["amount"],
                    "difference": bookmaker_tx["amount"] - system_tx["amount"],
                    "severity": "HIGH" if abs(bookmaker_tx["amount"] - system_tx["amount"]) > 10 else "MEDIUM",
                    "description": f"Valor mismatch para {ref_id}"
                })

        return discrepancies

    async def reconcile_bet_results(self):
        """
        Reconcilia resultados de apostas com resultados oficiais.
        """
        pending_bets = await self.db.get_pending_bets()

        for bet in pending_bets:
            # Obter resultado oficial
            official_result = await self._get_official_result(bet["game_id"])

            if official_result:
                # Determinar resultado da aposta
                bet_result = self._determine_bet_result(bet, official_result)

                # Atualizar aposta
                await self.db.update_bet(bet["id"], {
                    "result": bet_result,
                    "settled_at": datetime.utcnow()
                })

                # Calcular PnL
                pnl = PnLCalculator().calculate_bet_pnl(bet)
                await self.db.update_bet(bet["id"], pnl)
```

---

## Auditoria

### Processo de Auditoria
```python
class AuditEngine:
    """
    Realiza auditoria de apostas e transações.
    """
    def __init__(self, db):
        self.db = db

    async def audit_daily_bets(self, date):
        """
        Audita todas as apostas de um dia.
        """
        bets = await self.db.get_bets_by_date(date)

        audit_report = {
            "date": date,
            "total_bets": len(bets),
            "issues": [],
            "warnings": []
        }

        # Verificar apostas sem resultado
        pending_bets = [b for b in bets if b["result"] == "PENDING"]
        if pending_bets:
            audit_report["warnings"].append({
                "type": "PENDING_BETS",
                "count": len(pending_bets),
                "message": f"{len(pending_bets)} apostas ainda pendentes"
            })

        # Verificar apostas com slippage excessivo
        high_slippage = [b for b in bets if b.get("slippage", 0) < -10]
        if high_slippage:
            audit_report["issues"].append({
                "type": "HIGH_SLIPPAGE",
                "count": len(high_slippage),
                "message": f"{len(high_slippage)} apostas com slippage > 10%"
            })

        # Verificar apostas sem reconciliação
        unreconciled = [b for b in bets if not b["is_reconciled"]]
        if unreconciled:
            audit_report["issues"].append({
                "type": "UNRECONCILED",
                "count": len(unreconciled),
                "message": f"{len(unreconciled)} apostas não reconciliadas"
            })

        # Verificar consistência de banca
        bankroll_issues = await self._audit_bankroll_consistency(date)
        if bankroll_issues:
            audit_report["issues"].extend(bankroll_issues)

        return audit_report

    async def _audit_bankroll_consistency(self, date):
        """
        Verifica se a banca evolui consistentemente.
        """
        transactions = await self.db.get_bankroll_transactions_by_date(date)
        issues = []

        # Ordenar por timestamp
        transactions.sort(key=lambda x: x["occurred_at"])

        # Verificar sequência de saldos
        for i in range(1, len(transactions)):
            prev_tx = transactions[i - 1]
            curr_tx = transactions[i]

            expected_balance = prev_tx["balance_after"]
            actual_balance = curr_tx["balance_before"]

            if abs(expected_balance - actual_balance) > 0.01:
                issues.append({
                    "type": "BANKROLL_INCONSISTENCY",
                    "transaction_id": curr_tx["id"],
                    "message": f"Inconsistência de banca entre transações {prev_tx['id']} e {curr_tx['id']}"
                })

        return issues
```

---

## Relatórios de Performance

### Métricas Calculadas
```python
class PerformanceReporter:
    """
    Gera relatórios de performance com métricas avançadas.
    """
    def __init__(self, db, pnl_calculator):
        self.db = db
        self.pnl_calculator = pnl_calculator

    async def generate_daily_report(self, date):
        """
        Gera relatório diário de performance.
        """
        bets = await self.db.get_bets_by_date(date)
        aggregate = self.pnl_calculator.calculate_aggregate_pnl(bets)

        # Calcular CLV médio
        clv_values = [b.get("clv", 0) for b in bets if b.get("clv") is not None]
        avg_clv = sum(clv_values) / len(clv_values) if clv_values else 0

        # Calcular Sharpe ratio (simplificado)
        if len(bets) > 1:
            returns = [b["net_pnl"] / b["stake"] for b in bets]
            sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe = 0

        # Performance por mercado
        market_performance = self._calculate_market_performance(bets)

        return {
            "date": date,
            "summary": aggregate,
            "avg_clv": round(avg_clv, 2),
            "sharpe_ratio": round(sharpe, 2),
            "market_performance": market_performance
        }

    def _calculate_market_performance(self, bets):
        """
        Calcula performance por mercado.
        """
        markets = {}
        for bet in bets:
            market = bet["market"]
            if market not in markets:
                markets[market] = {
                    "bets": 0,
                    "stake": 0,
                    "pnl": 0,
                    "wins": 0,
                    "losses": 0
                }

            markets[market]["bets"] += 1
            markets[market]["stake"] += bet["stake"]
            markets[market]["pnl"] += bet.get("net_pnl", 0)
            if bet["result"] == "WIN":
                markets[market]["wins"] += 1
            elif bet["result"] == "LOSS":
                markets[market]["losses"] += 1

        # Calcular ROI por mercado
        for market in markets.values():
            market["roi"] = round(market["pnl"] / market["stake"] * 100, 2) if market["stake"] > 0 else 0
            market["win_rate"] = round(market["wins"] / market["bets"] * 100, 2) if market["bets"] > 0 else 0

        return markets

    async def generate_monthly_report(self, year, month):
        """
        Gera relatório mensal de performance.
        """
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        bets = await self.db.get_bets_between_dates(start_date, end_date)
        aggregate = self.pnl_calculator.calculate_aggregate_pnl(bets)

        # Performance semanal
        weekly_performance = self._calculate_weekly_performance(bets, year, month)

        # Top 5 melhores apostas
        best_bets = sorted(bets, key=lambda x: x.get("net_pnl", 0), reverse=True)[:5]

        # Top 5 piores apostas
        worst_bets = sorted(bets, key=lambda x: x.get("net_pnl", 0))[:5]

        return {
            "year": year,
            "month": month,
            "summary": aggregate,
            "weekly_performance": weekly_performance,
            "best_bets": best_bets,
            "worst_bets": worst_bets
        }
```

---

## Thresholds e Tabelas

| Métrica | Threshold Bom | Threshold Alerta | Threshold Crítico | Ação |
|---------|---------------|------------------|-------------------|------|
| ROI diário | > 2% | < 0% | < -5% | Revisar estratégia |
| Win rate | > 55% | < 50% | < 45% | Revisar modelo |
| CLV médio | > 2% | < 0% | < -2% | Revisar timing |
| Slippage médio | < 2% | > 5% | > 10% | Revisar execução |
| Discrepâncias reconciliação | 0 | > 5 | > 20 | Investigar manualmente |
| Apostas pendentes (> 24h) | 0 | > 5 | > 20 | Revisar resultados |

| Tipo de Discrepância | Severidade Padrão | SLA Resolução | Responsável |
|----------------------|-------------------|----------------|-------------|
| AMOUNT_MISMATCH | HIGH | 24 horas | Financeiro |
| RESULT_MISMATCH | HIGH | 24 horas | Operations |
| MISSING_BET | MEDIUM | 48 horas | Operations |
| DUPLICATE_BET | LOW | 72 horas | Operations |
| BANKROLL_INCONSISTENCY | CRITICAL | 4 horas | Financeiro |

---

## Links Cruzados

- [[PLANILHA_PnL]] → Estrutura base da planilha
- [[BANKROLL_MANAGEMENT]] → Gestão de banca
- [[TAX_REPORTING]] → Relatórios fiscais
- [[FINANCIAL_REPORTS]] → Relatórios executivos
- [[06_Backtesting/INDEX]] → Backtesting de estratégias