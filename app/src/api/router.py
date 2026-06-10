import logging
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Prediction, Signal
from src.engine.predict import PredictionEngine

logger = logging.getLogger("api_router")

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("VBQ_API_KEY", "")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="API key authentication is not configured")
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

router = APIRouter(prefix="/api/v1")
prediction_engine = PredictionEngine()

# Pydantic Schemas
class PredictRequest(BaseModel):
    features: Dict[str, Any]
    odds_home: float
    odds_away: float

class PredictResponse(BaseModel):
    raw_prob_home: float
    calibrated_prob_home: float
    calibrated_prob_away: float
    edge_home: float
    edge_away: float
    bet_side: Optional[str]
    expected_edge: float
    meta_approved: bool
    meta_prob: float
    stake_pct: float

class _FeaturesSchema(BaseModel):
    """Strict schema for prediction features to prevent injection."""
    elo_diff: float = 0.0
    rest_diff: float = 0.0
    win_rate_5_diff: float = 0.0
    market_overround: float = 0.04
    form_home: float = 0.0
    form_away: float = 0.0
    h2h_home_win_rate: float = 0.0
    days_since_last: float = 0.0

class SignalGenerateRequest(BaseModel):
    game_id: str
    features: _FeaturesSchema
    odds_home: float
    odds_away: float
    base_bankroll: Optional[float] = 1000.0

class SignalResponse(BaseModel):
    signal_id: str
    game_id: str
    predicted_prob: float
    bookmaker_odds: float
    expected_edge: float
    stake_size: float
    approved: bool
    status: str


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Computes game win probabilities, calibrates them, and calculates expect edges/stakes.
    """
    try:
        res = prediction_engine.predict_match(
            features=request.features,
            odds_home=request.odds_home,
            odds_away=request.odds_away
        )
        return PredictResponse(**res)
    except Exception as e:
        logger.error(f"Error in prediction endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/generate", response_model=Dict[str, Any])
async def generate_signal(request: SignalGenerateRequest, db: Session = Depends(get_db)):
    """
    Evaluates value, applies filters and meta-labeling, saves predictions/signals to DB.
    """
    try:
        # 1. Run inference
        res = prediction_engine.predict_match(
            features=request.features.model_dump(),
            odds_home=request.odds_home,
            odds_away=request.odds_away
        )

        # 2. Persist Prediction Row
        pred_row = Prediction(
            game_id=request.game_id,
            model_version="v4.0.0-xgb",
            predicted_prob_home=Decimal(str(round(res["calibrated_prob_home"], 4))),
            predicted_prob_away=Decimal(str(round(res["calibrated_prob_away"], 4)))
        )
        db.add(pred_row)

        # 3. If there is a bet side, persist Signal Row inside a single transaction
        signal_row = None
        stake_size = 0.0
        try:
            if res["bet_side"] is not None:
                # We construct signal_id as SIG-{game_id}
                sig_id = f"SIG-{request.game_id}"
                
                # Remove any existing signal with the same ID to prevent duplication issues in local testing
                existing_sig = db.query(Signal).filter_by(signal_id=sig_id).first()
                if existing_sig:
                    db.delete(existing_sig)

                stake_size = float(request.base_bankroll) * res["stake_pct"]

                signal_row = Signal(
                    signal_id=sig_id,
                    game_id=request.game_id,
                    predicted_prob=Decimal(str(round(res["selected_prob"], 4))),
                    bookmaker_odds=Decimal(str(round(res["selected_odds"], 4))),
                    expected_edge=Decimal(str(round(res["expected_edge"], 4))),
                    stake_size=Decimal(str(round(stake_size, 2))),
                    approved=res["meta_approved"],
                    status="pending"
                )
                db.add(signal_row)
            
            db.commit()
        except Exception as db_err:
            db.rollback()
            logger.error(f"Database transaction failed: {db_err}")
            raise HTTPException(status_code=500, detail="Database transaction failed")

        # Broadcast to Telegram if a signal was generated (outside DB transaction)
        if signal_row is not None:
            sig_dict = {
                "game_id": request.game_id,
                "bet_side": res["bet_side"],
                "bookmaker_odds": res["selected_odds"],
                "predicted_prob": res["selected_prob"],
                "expected_edge": res["expected_edge"],
                "stake_size": stake_size,
                "approved": res["meta_approved"]
            }
            try:
                from src.telegram.bot import send_signal_alert
                await send_signal_alert(sig_dict)
            except Exception as bot_err:
                logger.error(f"Failed to send Telegram notification: {bot_err}")

        # Build return payload
        return {
            "prediction": {
                "game_id": request.game_id,
                "calibrated_prob_home": res["calibrated_prob_home"],
                "calibrated_prob_away": res["calibrated_prob_away"],
            },
            "signal": {
                "signal_id": signal_row.signal_id if signal_row else None,
                "approved": signal_row.approved if signal_row else False,
                "stake_size": float(signal_row.stake_size) if signal_row else 0.0,
                "expected_edge": float(signal_row.expected_edge) if signal_row else 0.0,
                "bet_side": res["bet_side"]
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals", response_model=List[Dict[str, Any]])
async def get_signals(
    status: Optional[str] = Query(None, description="Filter signals by status (pending, executed, settled)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves history of signals from database.
    """
    try:
        query = db.query(Signal)
        if status:
            query = query.filter(Signal.status == status)
        
        signals = query.order_by(Signal.created_at.desc()).all()
        
        res = []
        for s in signals:
            res.append({
                "signal_id": s.signal_id,
                "game_id": s.game_id,
                "predicted_prob": float(s.predicted_prob),
                "bookmaker_odds": float(s.bookmaker_odds),
                "expected_edge": float(s.expected_edge),
                "stake_size": float(s.stake_size),
                "approved": s.approved,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None
            })
        return res
    except Exception as e:
        logger.error(f"Error querying signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bets/today", response_model=List[Dict[str, Any]])
async def get_todays_bets(
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Secure endpoint that retrieves pending bets for today.
    Requires X-API-Key header.
    """
    try:
        from datetime import datetime, timedelta
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        signals = db.query(Signal).filter(
            Signal.status == "pending",
            Signal.created_at >= today,
            Signal.created_at < tomorrow
        ).all()
        
        return [{
            "signal_id": s.signal_id,
            "game_id": s.game_id,
            "bet_side": "Home" if s.predicted_prob > 0.5 else "Away",
            "odds": float(s.bookmaker_odds),
            "edge": float(s.expected_edge)
        } for s in signals]
    except Exception as e:
        logger.error(f"Error fetching today's bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
