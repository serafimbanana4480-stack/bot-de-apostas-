"""
Order Tracker Module.
Tracks the lifecycle of orders (PENDING, PLACED, FILLED, REJECTED, PARTIAL_FILL).
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class OrderTracker:
    """Tracks and manages the lifecycle of bet orders."""
    
    def __init__(self):
        self.orders: Dict[str, Dict[str, Any]] = {}
        
    def create_order(self, decision: Dict[str, Any]) -> str:
        """Initialize a new order based on a decision."""
        order_id = f"ord_{decision['match_id']}_{int(datetime.utcnow().timestamp())}"
        
        self.orders[order_id] = {
            "order_id": order_id,
            "match_id": decision["match_id"],
            "market": decision["market"],
            "selection": decision["selection"],
            "requested_odds": decision.get("current_odds", 0.0),
            "requested_stake": decision.get("recommended_stake_amount", 0.0),
            "status": "PENDING",
            "filled_odds": 0.0,
            "filled_stake": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return order_id
        
    def update_status(self, order_id: str, status: str, filled_odds: float = 0.0, filled_stake: float = 0.0) -> None:
        """Update order status after execution attempt."""
        if order_id not in self.orders:
            logger.error(f"Cannot update unknown order: {order_id}")
            return
            
        order = self.orders[order_id]
        order["status"] = status
        order["updated_at"] = datetime.utcnow().isoformat()
        
        if filled_stake > 0:
            order["filled_stake"] = filled_stake
        if filled_odds > 0:
            order["filled_odds"] = filled_odds
            
        logger.info(f"Order {order_id} status updated to {status}")
        
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Retrieve order details."""
        return self.orders.get(order_id, {})
