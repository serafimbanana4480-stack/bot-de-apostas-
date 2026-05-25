---
ID: FT-005
tags: #status/active #financial #reports #kpi #dashboard #analytics
---

# Relatórios Financeiros e KPIs

## Objetivo
Definir o sistema completo de relatórios financeiros, KPIs (Key Performance Indicators), e dashboards para monitorização da saúde financeira do negócio de value betting NBA. Os relatórios devem fornecer visibilidade em tempo real, suportar tomada de decisão, e permitir comparação com objetivos orçamentais.

## O que faz
- Define KPIs financeiros críticos: MRR (Monthly Recurring Revenue), Churn Rate, CAC (Customer Acquisition Cost), LTV (Lifetime Value), ROI de apostas, e margem líquida.
- Implementa geração de relatórios automáticos: diário, semanal, mensal, trimestral, e anual.
- Especifica estrutura de dashboards: visão executiva, visão operacional, e visão de apostas.
- Define processo de orçamentação: comparação de real vs. orçamento, análise de desvios, e ajustes.
- Estabelece alertas automáticos quando KPIs excedem thresholds definidos.

## Porque existe
- **Tomada de Decisão**: Sem métricas claras, decisões são baseadas em intuição em vez de dados. KPIs fornecem base objetiva para ajustes de estratégia.
- **Detecção Precoce de Problemas**: Alertas automáticos permitem corrigir problemas (ex: churn elevado, ROI em queda) antes que se tornem críticos.
- **Accountability**: Relatórios regulares criam responsabilidade e permitem rastrear progresso em relação a objetivos.
- **Investor/Stakeholder Communication**: Relatórios profissionais são essenciais para comunicar com investidores, parceiros, ou para fins de compliance.

---

## KPIs Financeiros

### KPIs de Receitas
```python
class RevenueKPIs:
    """
    Calcula KPIs de receitas.
    """
    def __init__(self, db):
        self.db = db

    def calculate_mrr(self, month, year):
        """
        Monthly Recurring Revenue - Receita recorrente mensal.
        """
        active_subscriptions = self.db.get_active_subscriptions(month, year)

        mrr = sum(sub["amount_eur"] for sub in active_subscriptions)

        return {
            "mrr": round(mrr, 2),
            "active_subscribers": len(active_subscriptions),
            "arpu": round(mrr / len(active_subscriptions), 2) if active_subscriptions else 0  # Average Revenue Per User
        }

    def calculate_arr(self, year):
        """
        Annual Recurring Revenue - Receita recorrente anual.
        """
        mrr_january = self.calculate_mrr(1, year)["mrr"]
        arr = mrr_january * 12

        return round(arr, 2)

    def calculate_revenue_growth(self, current_period, previous_period):
        """
        Crescimento de receita entre períodos.
        """
        current_revenue = self.db.get_total_revenue(current_period["start"], current_period["end"])
        previous_revenue = self.db.get_total_revenue(previous_period["start"], previous_period["end"])

        if previous_revenue == 0:
            growth_rate = 0
        else:
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100

        return {
            "current_revenue": round(current_revenue, 2),
            "previous_revenue": round(previous_revenue, 2),
            "growth_rate": round(growth_rate, 2)
        }
```

### KPIs de Retenção
```python
class RetentionKPIs:
    """
    Calcula KPIs de retenção de clientes.
    """
    def __init__(self, db):
        self.db = db

    def calculate_churn_rate(self, month, year):
        """
        Churn Rate - Taxa de cancelamento.
        """
        # Subscritores ativos no início do mês
        start_of_month = datetime(year, month, 1)
        subscribers_at_start = self.db.get_active_subscribers_at_date(start_of_month)

        # Subscritores que cancelaram durante o mês
        end_of_month = datetime(year, month + 1, 1) - timedelta(days=1)
        cancelled_during_month = self.db.get_cancelled_subscriptions(start_of_month, end_of_month)

        if subscribers_at_start == 0:
            churn_rate = 0
        else:
            churn_rate = (len(cancelled_during_month) / subscribers_at_start) * 100

        return {
            "churn_rate": round(churn_rate, 2),
            "subscribers_at_start": subscribers_at_start,
            "cancelled": len(cancelled_during_month)
        }

    def calculate_ltv(self, year):
        """
        Lifetime Value - Valor vitalício do cliente.
        """
        # ARPU (Average Revenue Per User)
        total_revenue = self.db.get_total_revenue_for_year(year)
        total_subscribers = self.db.get_total_subscribers_for_year(year)
        arpu = total_revenue / total_subscribers if total_subscribers > 0 else 0

        # Churn rate mensal
        avg_churn_rate = sum(self.calculate_churn_rate(m, year)["churn_rate"] for m in range(1, 13)) / 12

        # LTV = ARPU / Churn Rate
        if avg_churn_rate > 0:
            ltv = arpu / (avg_churn_rate / 100)
        else:
            ltv = arpu * 12  # Assumir 12 meses se churn for 0

        return {
            "arpu": round(arpu, 2),
            "avg_churn_rate": round(avg_churn_rate, 2),
            "ltv": round(ltv, 2)
        }
```

### KPIs de Aquisição
```python
class AcquisitionKPIs:
    """
    Calcula KPIs de aquisição de clientes.
    """
    def __init__(self, db):
        self.db = db

    def calculate_cac(self, period_start, period_end):
        """
        Customer Acquisition Cost - Custo de aquisição de cliente.
        """
        # Custos de marketing
        marketing_costs = self.db.get_marketing_costs(period_start, period_end)

        # Novos subscritores
        new_subscribers = self.db.get_new_subscribers(period_start, period_end)

        if new_subscribers == 0:
            cac = 0
        else:
            cac = marketing_costs / new_subscribers

        return {
            "marketing_costs": round(marketing_costs, 2),
            "new_subscribers": new_subscribers,
            "cac": round(cac, 2)
        }

    def calculate_ltv_cac_ratio(self, ltv, cac):
        """
        Ratio LTV/CAC - Indica se o custo de aquisição é justificado.
        """
        if cac == 0:
            return 0

        ratio = ltv / cac
        return round(ratio, 2)
```

### KPIs de Apostas
```python
class BettingKPIs:
    """
    Calcula KPIs de performance de apostas.
    """
    def __init__(self, db):
        self.db = db

    def calculate_roi(self, period_start, period_end):
        """
        Return on Investment - Retorno sobre investimento em apostas.
        """
        bets = self.db.get_bets_between_dates(period_start, period_end)

        total_stake = sum(b["stake"] for b in bets)
        total_pnl = sum(b.get("net_pnl", 0) for b in bets)

        if total_stake == 0:
            roi = 0
        else:
            roi = (total_pnl / total_stake) * 100

        return {
            "total_stake": round(total_stake, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round(roi, 2)
        }

    def calculate_sharpe_ratio(self, period_start, period_end):
        """
        Sharpe Ratio - Mede retorno ajustado ao risco.
        """
        bets = self.db.get_bets_between_dates(period_start, period_end)

        returns = [b["net_pnl"] / b["stake"] for b in bets if b["stake"] > 0]

        if not returns:
            return 0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        sharpe = mean_return / std_return

        return round(sharpe, 2)

    def calculate_max_drawdown(self, period_start, period_end):
        """
        Maximum Drawdown - Maior queda de banca.
        """
        bets = self.db.get_bets_between_dates(period_start, period_end)
        bets.sort(key=lambda x: x["placed_at"])

        running_pnl = 0
        peak = 0
        max_drawdown = 0

        for bet in bets:
            running_pnl += bet.get("net_pnl", 0)
            peak = max(peak, running_pnl)
            drawdown = (peak - running_pnl) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        return round(max_drawdown * 100, 2)
```

---

## Relatórios Automáticos

### Relatório Diário
```python
class DailyReport:
    """
    Gera relatório diário executivo.
    """
    def generate(self, date):
        """
        Gera relatório para uma data específica.
        """
        # KPIs do dia
        revenue_kpis = RevenueKPIs(self.db).calculate_mrr(date.month, date.year)
        betting_kpis = BettingKPIs(self.db).calculate_roi(date, date)

        # Novos subscritores
        new_subscribers = self.db.get_new_subscribers(date, date)

        # Cancelamentos
        cancellations = self.db.get_cancelled_subscriptions(date, date)

        # Sinais enviados
        signals_sent = self.db.get_signals_sent(date, date)

        return {
            "date": date.strftime("%Y-%m-%d"),
            "revenue": revenue_kpis,
            "betting": betting_kpis,
            "subscribers": {
                "new": new_subscribers,
                "cancelled": cancellations,
                "net": new_subscribers - cancellations
            },
            "signals": signals_sent
        }
```

### Relatório Semanal
```python
class WeeklyReport:
    """
    Gera relatório semanal.
    """
    def generate(self, week_start, week_end):
        """
        Gera relatório para uma semana.
        """
        # KPIs da semana
        betting_kpis = BettingKPIs(self.db).calculate_roi(week_start, week_end)
        sharpe = BettingKPIs(self.db).calculate_sharpe_ratio(week_start, week_end)
        max_dd = BettingKPIs(self.db).calculate_max_drawdown(week_start, week_end)

        # Crescimento de subscritores
        subs_start = self.db.get_active_subscribers_at_date(week_start)
        subs_end = self.db.get_active_subscribers_at_date(week_end)
        subs_growth = ((subs_end - subs_start) / subs_start * 100) if subs_start > 0 else 0

        # Receita da semana
        revenue = self.db.get_total_revenue(week_start, week_end)

        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "betting": {
                "roi": betting_kpis["roi"],
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd
            },
            "subscribers": {
                "at_start": subs_start,
                "at_end": subs_end,
                "growth_rate": round(subs_growth, 2)
            },
            "revenue": round(revenue, 2)
        }
```

### Relatório Mensal
```python
class MonthlyReport:
    """
    Gera relatório mensal completo.
    """
    def generate(self, year, month):
        """
        Gera relatório para um mês.
        """
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        # KPIs de receitas
        revenue_kpis = RevenueKPIs(self.db).calculate_mrr(month, year)

        # KPIs de retenção
        retention_kpis = RetentionKPIs(self.db).calculate_churn_rate(month, year)

        # KPIs de apostas
        betting_kpis = BettingKPIs(self.db).calculate_roi(start_date, end_date)

        # Custos operacionais
        operational_costs = self.db.get_operational_costs(start_date, end_date)

        # Margem líquida
        net_margin = (revenue_kpis["mrr"] - operational_costs) / revenue_kpis["mrr"] * 100 if revenue_kpis["mrr"] > 0 else 0

        return {
            "year": year,
            "month": month,
            "revenue": revenue_kpis,
            "retention": retention_kpis,
            "betting": betting_kpis,
            "costs": round(operational_costs, 2),
            "net_margin": round(net_margin, 2)
        }
```

---

## Dashboards

### Dashboard Executivo
```python
class ExecutiveDashboard:
    """
    Dashboard para visão executiva do negócio.
    """
    def get_data(self, date):
        """
    Obtém dados para o dashboard executivo.
        """
        # MRR atual
        current_mrr = RevenueKPIs(self.db).calculate_mrr(date.month, date.year)["mrr"]

        # MRR do mês anterior (para comparação)
        prev_month = date - timedelta(days=30)
        prev_mrr = RevenueKPIs(self.db).calculate_mrr(prev_month.month, prev_month.year)["mrr"]

        # Crescimento MRR
        mrr_growth = ((current_mrr - prev_mrr) / prev_mrr * 100) if prev_mrr > 0 else 0

        # Churn rate
        churn = RetentionKPIs(self.db).calculate_churn_rate(date.month, date.year)["churn_rate"]

        # ROI de apostas (últimos 30 dias)
        thirty_days_ago = date - timedelta(days=30)
        roi = BettingKPIs(self.db).calculate_roi(thirty_days_ago, date)["roi"]

        # Banca atual
        current_bankroll = self.db.get_current_bankroll()

        # Subscritores ativos
        active_subscribers = self.db.get_active_subscribers(date.month, date.year)

        return {
            "mrr": {
                "current": round(current_mrr, 2),
                "previous": round(prev_mrr, 2),
                "growth": round(mrr_growth, 2)
            },
            "churn_rate": churn,
            "betting_roi": roi,
            "bankroll": round(current_bankroll, 2),
            "active_subscribers": active_subscribers
        }
```

### Dashboard Operacional
```python
class OperationalDashboard:
    """
    Dashboard para visão operacional.
    """
    def get_data(self, date):
        """
        Obtém dados para o dashboard operacional.
        """
        # Sinais enviados hoje
        signals_today = self.db.get_signals_sent(date, date)

        # Apostas executadas hoje
        bets_today = self.db.get_bets_between_dates(date, date)

        # Taxa de execução (apostas / sinais)
        execution_rate = (len(bets_today) / signals_today * 100) if signals_today > 0 else 0

        # Tempo médio de execução
        avg_execution_time = self.db.get_avg_execution_time(date, date)

        # Erros do sistema
        system_errors = self.db.get_system_errors(date, date)

        # Uptime do bot
        bot_uptime = self.db.get_bot_uptime(date, date)

        return {
            "signals_sent": signals_today,
            "bets_executed": len(bets_today),
            "execution_rate": round(execution_rate, 2),
            "avg_execution_time": round(avg_execution_time, 2),
            "system_errors": system_errors,
            "bot_uptime": round(bot_uptime, 2)
        }
```

### Dashboard de Apostas
```python
class BettingDashboard:
    """
    Dashboard para visão de performance de apostas.
    """
    def get_data(self, date):
        """
        Obtém dados para o dashboard de apostas.
        """
        # ROI últimos 7 dias
        seven_days_ago = date - timedelta(days=7)
        roi_7d = BettingKPIs(self.db).calculate_roi(seven_days_ago, date)["roi"]

        # ROI últimos 30 dias
        thirty_days_ago = date - timedelta(days=30)
        roi_30d = BettingKPIs(self.db).calculate_roi(thirty_days_ago, date)["roi"]

        # Sharpe ratio últimos 30 dias
        sharpe = BettingKPIs(self.db).calculate_sharpe_ratio(thirty_days_ago, date)

        # Max drawdown últimos 30 dias
        max_dd = BettingKPIs(self.db).calculate_max_drawdown(thirty_days_ago, date)

        # Performance por mercado
        market_performance = self.db.get_market_performance(thirty_days_ago, date)

        # CLV médio
        avg_clv = self.db.get_avg_clv(thirty_days_ago, date)

        return {
            "roi": {
                "7_days": round(roi_7d, 2),
                "30_days": round(roi_30d, 2)
            },
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "market_performance": market_performance,
            "avg_clv": round(avg_clv, 2)
        }
```

---

## Orçamentação

### Comparação Real vs. Orçamento
```python
class BudgetComparison:
    """
    Compara resultados reais com orçamento.
    """
    def compare(self, period_start, period_end):
        """
        Compara receitas e custos com orçamento.
        """
        # Valores reais
        actual_revenue = self.db.get_total_revenue(period_start, period_end)
        actual_costs = self.db.get_total_costs(period_start, period_end)
        actual_profit = actual_revenue - actual_costs

        # Valores orçamentados
        budget_revenue = self.db.get_budgeted_revenue(period_start, period_end)
        budget_costs = self.db.get_budgeted_costs(period_start, period_end)
        budget_profit = budget_revenue - budget_costs

        # Variação
        revenue_variance = actual_revenue - budget_revenue
        cost_variance = actual_costs - budget_costs
        profit_variance = actual_profit - budget_profit

        # Percentagem de variação
        revenue_variance_pct = (revenue_variance / budget_revenue * 100) if budget_revenue > 0 else 0
        cost_variance_pct = (cost_variance / budget_costs * 100) if budget_costs > 0 else 0

        return {
            "revenue": {
                "actual": round(actual_revenue, 2),
                "budgeted": round(budget_revenue, 2),
                "variance": round(revenue_variance, 2),
                "variance_pct": round(revenue_variance_pct, 2)
            },
            "costs": {
                "actual": round(actual_costs, 2),
                "budgeted": round(budget_costs, 2),
                "variance": round(cost_variance, 2),
                "variance_pct": round(cost_variance_pct, 2)
            },
            "profit": {
                "actual": round(actual_profit, 2),
                "budgeted": round(budget_profit, 2),
                "variance": round(profit_variance, 2)
            }
        }
```

---

## Alertas Automáticos

### Sistema de Alertas
```python
class FinancialAlerts:
    """
    Gera alertas quando KPIs excedem thresholds.
    """
    def __init__(self, config):
        self.config = config

    def check_alerts(self, date):
        """
        Verifica todos os KPIs e gera alertas se necessário.
        """
        alerts = []

        # Alerta de churn elevado
        churn = RetentionKPIs(self.db).calculate_churn_rate(date.month, date.year)["churn_rate"]
        if churn > self.config["churn_warning_threshold"]:
            alerts.append({
                "type": "HIGH_CHURN",
                "severity": "WARNING",
                "value": churn,
                "threshold": self.config["churn_warning_threshold"],
                "message": f"Churn rate de {churn}% excede threshold de {self.config['churn_warning_threshold']}%"
            })

        # Alerta de ROI negativo
        thirty_days_ago = date - timedelta(days=30)
        roi = BettingKPIs(self.db).calculate_roi(thirty_days_ago, date)["roi"]
        if roi < self.config["roi_critical_threshold"]:
            alerts.append({
                "type": "NEGATIVE_ROI",
                "severity": "CRITICAL",
                "value": roi,
                "threshold": self.config["roi_critical_threshold"],
                "message": f"ROI de {roi}% é inferior ao threshold crítico de {self.config['roi_critical_threshold']}%"
            })

        # Alerta de drawdown severo
        max_dd = BettingKPIs(self.db).calculate_max_drawdown(thirty_days_ago, date)
        if max_dd > self.config["drawdown_warning_threshold"]:
            alerts.append({
                "type": "HIGH_DRAWDOWN",
                "severity": "WARNING",
                "value": max_dd,
                "threshold": self.config["drawdown_warning_threshold"],
                "message": f"Drawdown de {max_dd}% excede threshold de {self.config['drawdown_warning_threshold']}%"
            })

        # Alerta de MRR em declínio
        current_mrr = RevenueKPIs(self.db).calculate_mrr(date.month, date.year)["mrr"]
        prev_month = date - timedelta(days=30)
        prev_mrr = RevenueKPIs(self.db).calculate_mrr(prev_month.month, prev_month.year)["mrr"]
        mrr_decline = ((prev_mrr - current_mrr) / prev_mrr * 100) if prev_mrr > 0 else 0
        if mrr_decline > self.config["mrr_decline_threshold"]:
            alerts.append({
                "type": "MRR_DECLINE",
                "severity": "WARNING",
                "value": mrr_decline,
                "threshold": self.config["mrr_decline_threshold"],
                "message": f"MRR declinou {mrr_decline}% em relação ao mês anterior"
            })

        return alerts
```

---

## Thresholds e Tabelas

| KPI | Bom | Alerta | Crítico | Ação |
|-----|-----|--------|---------|------|
| MRR Growth | > 5% | < 0% | < -10% | Revisar estratégia |
| Churn Rate | < 3% | > 5% | > 10% | Investigar causas |
| ROI 30 dias | > 3% | < 1% | < -2% | Revisar modelo |
| Sharpe Ratio | > 1.0 | < 0.5 | < 0 | Revisar risco |
| Max Drawdown | < 10% | > 15% | > 25% | Reduzir stakes |
| LTV/CAC Ratio | > 3:1 | < 2:1 | < 1:1 | Revisar aquisição |
| Net Margin | > 40% | < 20% | < 0% | Reduzir custos |

| Relatório | Frequência | Destinatários | Formato |
|-----------|------------|---------------|---------|
| Executivo Diário | Diário | CEO, Ops Lead | Email |
| Operacional Diário | Diário | Dev, Ops | Slack |
| Performance Semanal | Semanal | Todos | Email + Dashboard |
| Financeiro Mensal | Mensal | CEO, Financeiro | PDF |
| Trimestral | Trimestral | Todos | PDF + Apresentação |

---

## Links Cruzados

- [[PNL_TRACKING]] → Dados de PnL para KPIs |
- [[BANKROLL_MANAGEMENT]] → Dados de banca |
- [[TAX_REPORTING]] → Dados fiscais |
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES]] → Orçamentos e projeções |
- [[10_Monitoring/DASHBOARD_NEGOCIO]] → Dashboard de monitorização