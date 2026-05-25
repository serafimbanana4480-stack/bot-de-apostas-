"""
Main API Module.
Exposes FastAPI endpoints for predictions, status, and manual overrides.
"""
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from src.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VBQ-UNIFIED API",
    description="Quantitative Betting System API",
    version="4.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BetOverrideRequest(BaseModel):
    match_id: str
    action: str  # 'BET', 'SKIP'
    stake_pct: float = 0.0

@app.get("/health", tags=["System"])
async def health_check():
    """System health check."""
    return {"status": "ok", "version": app.version}
    
@app.get("/api/v1/status", tags=["System"])
async def system_status():
    """Current system status, including bankroll and active breakers."""
    return {
        "status": "active",
        "active_model_version": "v4.0.1",
        "circuit_breakers_triggered": [],
        "bankroll_status": "ok"
    }

@app.get("/api/v1/predictions", tags=["Predictions"])
async def get_recent_predictions(limit: int = 50):
    """Get recent model predictions."""
    # In a real implementation, query the DB
    return {"predictions": []}
    
@app.get("/api/v1/decisions", tags=["Decisions"])
async def get_recent_decisions(limit: int = 50):
    """Get recent betting decisions made by the engine."""
    return {"decisions": []}

@app.post("/api/v1/overrides", tags=["Control"])
async def manual_override(request: BetOverrideRequest):
    """Manually override a decision (e.g., force a bet or skip)."""
    logger.warning(f"Manual override received for match {request.match_id}: {request.action}")
    return {"status": "success", "message": f"Override {request.action} registered."}

@app.get("/api/v1/metrics", tags=["Metrics"])
async def get_metrics_summary():
    """Get high-level P&L metrics."""
    return {
        "total_roi": 0.0,
        "active_drawdown": 0.0,
        "win_rate": 0.0,
        "total_bets": 0
    }
