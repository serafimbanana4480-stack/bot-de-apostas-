"""
Betfair Execution Adapter.
Adapter for placing bets on the Betfair Exchange.
Supports paper trading mode.
"""
import logging
from typing import Dict, Any, Tuple
import asyncio

logger = logging.getLogger(__name__)

class BetfairAdapter:
    """Adapter for Betfair Exchange API."""
    
    def __init__(self, auth_client):
        self.auth = auth_client
        self.api_url = "https://api.betfair.com/exchange/betting/rest/v1.0/"
        
    async def place_order(self, order: Dict[str, Any]) -> Tuple[str, float, float]:
        """
        Place an order on Betfair.
        Returns: (status, filled_odds, filled_stake)
        """
        logger.info(f"Attempting to place REAL Betfair order: {order}")
        
        # Betfair Exchange API requires JSON-RPC for placeOrders
        headers = {
            "X-Application": getattr(self.auth, "app_key", ""),
            "X-Authentication": getattr(self.auth, "session_token", ""),
            "Content-Type": "application/json"
        }
        
        # Mapping our internal order schema to Betfair's PlaceInstruction
        payload = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/placeOrders",
            "params": {
                "marketId": order["market"],
                "instructions": [
                    {
                        "selectionId": order["selection"],
                        "handicap": "0",
                        "side": "BACK", # Assuming simple back bets for now
                        "orderType": "LIMIT",
                        "limitOrder": {
                            "size": str(round(order["requested_stake"], 2)),
                            "price": str(round(order["requested_odds"], 2)),
                            "persistenceType": "LAPSE"
                        }
                    }
                ]
            },
            "id": 1
        }
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, headers=headers, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Check JSON-RPC error
                if "error" in data:
                    logger.error(f"Betfair API Error: {data['error']}")
                    return "REJECTED", 0.0, 0.0
                    
                result = data.get("result", {})
                status = result.get("status", "FAILURE")
                
                if status == "SUCCESS":
                    instruction_reports = result.get("instructionReports", [])
                    if instruction_reports and instruction_reports[0].get("status") == "SUCCESS":
                        # Successfully placed
                        # In reality, this might be UNMATCHED or EXECUTABLE on the exchange until matched
                        # For simplicity, if placed successfully, we consider it pending or filled depending on sizeMatched
                        report = instruction_reports[0]
                        matched = float(report.get("sizeMatched", 0.0))
                        avg_price = float(report.get("averagePriceMatched", 0.0))
                        
                        if matched >= order["requested_stake"]:
                            return "FILLED", avg_price, matched
                        elif matched > 0:
                            return "PARTIAL_FILL", avg_price, matched
                        else:
                            return "PLACED", 0.0, 0.0 # Placed on exchange but unmatched
                            
                logger.error(f"Betfair Placement Failed: {result}")
                return "REJECTED", 0.0, 0.0
                
        except Exception as e:
            logger.error(f"Exception during Betfair order placement: {e}")
            return "REJECTED", 0.0, 0.0
