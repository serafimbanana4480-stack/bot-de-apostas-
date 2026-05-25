"""
Prefect daily flow — delegates to PipelineOrchestrator (unified).
"""
import asyncio
import logging

from prefect import flow, task

from src.core.config import settings
from src.pipeline.orchestrator import PipelineOrchestrator
from src.telegram.bot import send_signal_alert

logger = logging.getLogger("daily_flow")


@task(retries=2, retry_delay_seconds=10)
def run_orchestrator_task(sport: str = "football"):
    orch = PipelineOrchestrator(sport, mode="live")
    return orch.run_daily()


@task
def run_all_sports_task():
    return PipelineOrchestrator.run_all_sports(mode="live")


@task
def alert_from_decisions(summary: dict):
    decisions = summary.get("decisions", [])
    for dec in decisions:
        if dec.get("decision") not in ("BET_NOW", "BET"):
            continue
        payload = {
            "game_id": dec.get("match_id", ""),
            "bet_side": dec.get("predicted_outcome", dec.get("bet_side", "")),
            "bookmaker_odds": dec.get("bookmaker_odds", 0),
            "predicted_prob": dec.get("calibrated_prob", 0),
            "expected_edge": dec.get("edge", 0),
            "stake_size": dec.get("recommended_stake_usd", 0),
            "approved": dec.get("decision") == "BET_NOW",
            "decision_reason": dec.get("decision_reason", ""),
        }
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.info("Signal: %s", payload)
            continue
        try:
            asyncio.run(send_signal_alert(payload))
        except Exception as e:
            logger.error("Telegram failed: %s", e)


@flow(name="Daily Betting Pipeline")
def daily_betting_flow(sport: str = "football", run_all: bool = False):
    logger.info("Daily flow (orchestrator) zero_cost=%s", settings.ZERO_COST_MODE)
    if run_all:
        results = run_all_sports_task()
        for s, summary in results.items():
            if isinstance(summary, dict) and summary.get("decisions"):
                alert_from_decisions(summary)
    else:
        summary = run_orchestrator_task(sport)
        alert_from_decisions(summary)

    try:
        import os
        import subprocess
        import sys
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        subprocess.run([sys.executable, os.path.join(root, "scripts", "daily_report.py")], cwd=root, check=False)
    except Exception as e:
        logger.warning("daily_report skipped: %s", e)


if __name__ == "__main__":
    daily_betting_flow()
