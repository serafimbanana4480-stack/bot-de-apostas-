"""
Prometheus Exporter Module.
Exposes core betting and system metrics for Grafana visualization.
"""
from prometheus_client import Counter, Gauge, Histogram
import time

class PrometheusExporter:
    """Manages Prometheus metrics for the betting system."""
    
    def __init__(self):
        # Business Metrics
        self.bets_placed_total = Counter(
            'vbq_bets_placed_total', 
            'Total number of bets placed',
            ['sport', 'market']
        )
        
        self.bets_settled_total = Counter(
            'vbq_bets_settled_total', 
            'Total number of bets settled',
            ['status'] # WON, LOST, PUSH, VOID
        )
        
        self.pnl_gauge = Gauge(
            'vbq_pnl_total', 
            'Total Profit and Loss (EUR)'
        )
        
        self.bankroll_gauge = Gauge(
            'vbq_bankroll_current', 
            'Current Bankroll (EUR)'
        )
        
        self.clv_histogram = Histogram(
            'vbq_clv_percentage', 
            'Closing Line Value percentage',
            buckets=[-10, -5, -2, 0, 2, 5, 10, 20]
        )
        
        self.model_accuracy_gauge = Gauge(
            'vbq_model_accuracy', 
            'Rolling model accuracy (win rate)',
            ['sport']
        )
        
        # System Metrics
        self.pipeline_latency = Histogram(
            'vbq_pipeline_duration_seconds', 
            'Time spent in the main ETL and prediction pipeline'
        )
        
        self.circuit_breaker_trips = Counter(
            'vbq_circuit_breaker_trips_total', 
            'Number of times a circuit breaker was triggered',
            ['breaker_type']
        )
        
    def record_bet_placed(self, sport: str, market: str, stake: float):
        self.bets_placed_total.labels(sport=sport, market=market).inc()
        
    def record_settlement(self, status: str, pnl: float, clv_pct: float = None):
        self.bets_settled_total.labels(status=status).inc()
        self.pnl_gauge.inc(pnl)
        
        if clv_pct is not None:
            self.clv_histogram.observe(clv_pct)
            
    def update_bankroll(self, current_balance: float):
        self.bankroll_gauge.set(current_balance)
        
    def record_circuit_breaker(self, breaker_type: str):
        self.circuit_breaker_trips.labels(breaker_type=breaker_type).inc()
