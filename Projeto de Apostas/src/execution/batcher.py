import logging
import time
from typing import Any, Callable, Dict, List

logger = logging.getLogger("order_batcher")

class OrderBatcher:
    """
    Groups and schedules multiple orders, spacing executions out by a safe
    interval (e.g. 100ms) to ensure compliance with server rate-limiting bounds.
    """
    def __init__(self, delay_between_orders_ms: float = 100.0):
        self.delay_seconds = delay_between_orders_ms / 1000.0

    def execute_batch(
        self, 
        orders: List[Dict[str, Any]], 
        execution_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Executes orders sequentially, applying a delay between each call.
        """
        results = []
        for i, order in enumerate(orders):
            if i > 0:
                time.sleep(self.delay_seconds)
                
            logger.info(f"Executing batch order {i+1}/{len(orders)}: {order.get('event_id')}")
            try:
                res = execution_func(order)
                results.append({"order": order, "result": res, "status": "SUCCESS"})
            except Exception as e:
                logger.error(f"Failed to execute order {order.get('event_id')}: {e}")
                results.append({"order": order, "result": {}, "status": "FAILED", "error": str(e)})
                
        return results
