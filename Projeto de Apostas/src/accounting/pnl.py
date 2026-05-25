from typing import Any, Dict, List, Optional


class FinancialAccountingEngine:
    """
    Computes precise realised P&L, commissions, slippage costs, tax liabilities,
    and handles FX currency conversions to support multi-bookmaker bankrolls.
    Commission rates are configurable per bookmaker (Tier C).
    """
    def __init__(
        self,
        tax_rate: float = 0.15,
        base_currency: str = "EUR",
        exchange_rates: Optional[Dict[str, float]] = None,
    ):
        self.tax_rate = tax_rate
        self.base_currency = base_currency
        # Base currency exchange rates relative to 1 unit of foreign currency
        self.exchange_rates = exchange_rates or {"EUR": 1.0, "USD": 0.92, "GBP": 1.16}
        self.ledger: List[Dict[str, Any]] = []

    def record_transaction(
        self, 
        event_id: str, 
        stake: float, 
        odds_predicted: float, 
        odds_executed: float, 
        won: bool, 
        provider: str = "Pinnacle",
        currency: str = "EUR",
        commission_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculates net return and adds transaction to the financial ledger,
        converting all values to the base_currency.
        
        Args:
            commission_rate: Override commission rate for this transaction.
                If None, uses default rates per provider:
                - Betfair: 5% on gross profit (only when won)
                - Pinnacle: 0% (no commission)
                - Other: 0%
        """
        fx_rate = self.exchange_rates.get(currency.upper(), 1.0)
        
        # Calculations in transaction currency
        tx_slippage = (odds_predicted - odds_executed) * stake
        
        if won:
            tx_gross = stake * (odds_executed - 1.0)
        else:
            tx_gross = -stake
            
        # Commission calculation
        tx_commission = 0.0
        if commission_rate is not None:
            # Explicit rate provided
            if won and commission_rate > 0:
                tx_commission = tx_gross * commission_rate
        else:
            # Default rates per provider
            provider_lower = provider.lower()
            if provider_lower == "betfair" and won:
                tx_commission = tx_gross * 0.05
            elif provider_lower == "smarkets" and won:
                tx_commission = tx_gross * 0.02
            # Pinnacle, bet365, etc. have no exchange commission
            
        tx_net = tx_gross - tx_commission
        tx_tax = max(0.0, tx_net * self.tax_rate)
        tx_realized = tx_net - tx_tax
        
        # Convert to Base Currency
        record = {
            "event_id": event_id,
            "provider": provider,
            "currency": currency.upper(),
            "fx_rate": fx_rate,
            "stake": stake * fx_rate,
            "odds_predicted": odds_predicted,
            "odds_executed": odds_executed,
            "slippage_cost": tx_slippage * fx_rate,
            "gross_pnl": tx_gross * fx_rate,
            "commission": tx_commission * fx_rate,
            "commission_rate": commission_rate if commission_rate is not None else (
                0.05 if provider.lower() == "betfair" else 0.0
            ),
            "net_pnl": tx_net * fx_rate,
            "tax_liability": tx_tax * fx_rate,
            "realized_profit": tx_realized * fx_rate
        }
        
        self.ledger.append(record)
        return record

    def get_portfolio_summary(self) -> Dict[str, float]:
        """
        Compiles total P&L performance metrics in base_currency.
        """
        if not self.ledger:
            return {"total_realized_profit": 0.0, "total_commission": 0.0, "total_slippage_cost": 0.0}
            
        return {
            "total_gross_pnl": float(sum(r["gross_pnl"] for r in self.ledger)),
            "total_commission": float(sum(r["commission"] for r in self.ledger)),
            "total_net_pnl": float(sum(r["net_pnl"] for r in self.ledger)),
            "total_tax_liability": float(sum(r["tax_liability"] for r in self.ledger)),
            "total_realized_profit": float(sum(r["realized_profit"] for r in self.ledger)),
            "total_slippage_cost": float(sum(r["slippage_cost"] for r in self.ledger))
        }
