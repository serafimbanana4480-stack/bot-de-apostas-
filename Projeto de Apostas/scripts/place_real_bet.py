#!/usr/bin/env python3
"""
Place a real bet on Betfair or Pinnacle via the API.

Supports dry-run mode (verify without executing) and interactive
confirmation for stakes above a safety threshold.

Usage:
  # Dry run (verify credentials + market, no bet placed)
  poetry run python scripts/place_real_bet.py --bookie betfair --market 1.23456789 --selection 12345 --side back --odds 2.10 --stake 0.01 --dry-run

  # Place real bet on Betfair sandbox
  poetry run python scripts/place_real_bet.py --bookie betfair --market 1.23456789 --selection 12345 --side back --odds 2.10 --stake 0.01

  # Place real bet on Pinnacle
  poetry run python scripts/place_real_bet.py --bookie pinnacle --event 12345 --sport football --line-id 67890 --bet-type MONEYLINE --team TEAM1 --odds 2.10 --stake 10.00
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("place_real_bet")

# Safety thresholds from config (settings.CONFIRMATION_THRESHOLD_EUR, settings.MAX_STAKE_EUR)
CONFIRMATION_THRESHOLD_EUR = getattr(settings, "CONFIRMATION_THRESHOLD_EUR", 1.0)
MAX_STAKE_EUR = getattr(settings, "MAX_STAKE_EUR", 50.0)


def _validate_stake(stake: float) -> None:
    """Reject stakes above MAX_STAKE_EUR — prevents typo-driven catastrophic bets."""
    if stake <= 0:
        raise ValueError(f"Stake must be positive, got {stake}")
    if stake > MAX_STAKE_EUR:
        raise ValueError(
            f"Stake {stake:.2f} EUR exceeds MAX_STAKE_EUR={MAX_STAKE_EUR:.2f}. "
            f"Set MAX_STAKE_EUR env var if intentional."
        )


def create_betfair_connector():
    """Create a BetfairRealConnector from settings."""
    from src.execution.adapters.betfair_real import BetfairRealConnector

    return BetfairRealConnector(
        app_key=settings.BETFAIR_APP_KEY,
        cert_path=settings.BETFAIR_CERT_PATH,
        key_path=settings.BETFAIR_KEY_PATH,
        username=settings.BETFAIR_USERNAME,
        password=settings.BETFAIR_PASSWORD,
        sandbox=settings.BETFAIR_SANDBOX,
        commission_rate=settings.BETFAIR_COMMISSION_RATE,
    )


def create_pinnacle_connector():
    """Create a PinnacleRealConnector from settings."""
    from src.execution.adapters.pinnacle_real import PinnacleRealConnector

    return PinnacleRealConnector(
        client_id=settings.PINNACLE_CLIENT_ID,
        password=settings.PINNACLE_PASSWORD,
        commission_rate=settings.PINNACLE_COMMISSION_RATE,
    )


def place_betfair_bet(args: argparse.Namespace) -> dict:
    """Place a bet on Betfair Exchange."""
    _validate_stake(args.stake)
    connector = create_betfair_connector()

    # Authenticate
    logger.info("Authenticating with Betfair (%s)...", "SANDBOX" if args.sandbox else "PRODUCTION")
    connector.authenticate()
    logger.info("Authentication successful")

    # Get balance
    balance_info = connector.get_account_balance()
    available = float(balance_info.get("availableToBetBalance", 0))
    logger.info("Account balance: %.2f", available)

    if available < args.stake:
        logger.error("Insufficient balance: %.2f available, %.2f requested", available, args.stake)
        return {"status": "REJECTED", "reason": "INSUFFICIENT_BALANCE"}

    # Get market book for verification
    if args.dry_run:
        logger.info("DRY RUN: Fetching market book for %s...", args.market)
        book = connector.get_market_book(args.market)
        runners = book.get("runners", [])
        logger.info("Market has %d runners", len(runners))
        for r in runners:
            sel_id = r.get("selectionId")
            ex = r.get("ex", {})
            available_back = ex.get("availableToBack", [])
            available_lay = ex.get("availableToLay", [])
            if available_back:
                best_back = available_back[0]
                logger.info(
                    "  Selection %d: Best back=%.2f size=%.2f",
                    sel_id, best_back.get("price", 0), best_back.get("size", 0),
                )
            if available_lay:
                best_lay = available_lay[0]
                logger.info(
                    "  Selection %d: Best lay=%.2f size=%.2f",
                    sel_id, best_lay.get("price", 0), best_lay.get("size", 0),
                )
        logger.info("DRY RUN complete — no bet placed")
        return {"status": "DRY_RUN", "market_id": args.market}

    # Interactive confirmation for larger stakes
    if args.stake > CONFIRMATION_THRESHOLD_EUR and not args.yes:
        confirm = input(
            f"\n  *** CONFIRM: Place {args.side.upper()} bet at odds {args.odds} "
            f"for stake {args.stake:.2f} EUR? [y/N] "
        )
        if confirm.lower() != "y":
            logger.info("Bet cancelled by user")
            return {"status": "CANCELLED", "reason": "USER_CANCELLED"}

    # Place the order
    logger.info(
        "Placing %s order: market=%s selection=%s odds=%.2f stake=%.2f",
        args.side.upper(), args.market, args.selection, args.odds, args.stake,
    )

    if args.side.lower() == "back":
        result = connector.place_back_order(
            market_id=args.market,
            selection_id=int(args.selection),
            odds=args.odds,
            stake=args.stake,
            customer_order_ref=f"vbq_{int(time.time())}",
        )
    elif args.side.lower() == "lay":
        result = connector.place_lay_order(
            market_id=args.market,
            selection_id=int(args.selection),
            odds=args.odds,
            stake=args.stake,
            customer_order_ref=f"vbq_{int(time.time())}",
        )
    else:
        logger.error("Invalid side: %s (use 'back' or 'lay')", args.side)
        return {"status": "REJECTED", "reason": "INVALID_SIDE"}

    # Reconcile balance
    if result.get("status") not in ("REJECTED",):
        new_balance_info = connector.get_account_balance()
        new_available = float(new_balance_info.get("availableToBetBalance", 0))
        logger.info(
            "Post-bet balance: %.2f (change: %.2f)",
            new_available, new_available - available,
        )

    logger.info("Bet result: %s", json.dumps(result, indent=2, default=str))
    return result


def place_pinnacle_bet(args: argparse.Namespace) -> dict:
    """Place a bet on Pinnacle Sports."""
    _validate_stake(args.stake)
    connector = create_pinnacle_connector()

    # Get balance
    balance_info = connector.get_balance()
    available = float(balance_info.get("availableBalance", 0))
    logger.info("Pinnacle balance: %.2f", available)

    if available < args.stake:
        logger.error("Insufficient balance: %.2f available, %.2f requested", available, args.stake)
        return {"status": "REJECTED", "reason": "INSUFFICIENT_BALANCE"}

    # Dry run
    if args.dry_run:
        sport_id = PinnacleRealConnector.get_sport_id(args.sport)
        odds_data = connector.get_odds(sport_id=sport_id, event_ids=[str(args.event)])
        logger.info("DRY RUN: Fetched odds for event %s", args.event)
        logger.info("DRY RUN complete — no bet placed")
        return {"status": "DRY_RUN", "event_id": args.event}

    # Interactive confirmation
    if args.stake > CONFIRMATION_THRESHOLD_EUR and not args.yes:
        confirm = input(
            f"\n  *** CONFIRM: Place {args.bet_type} bet at odds {args.odds} "
            f"for stake {args.stake:.2f}? [y/N] "
        )
        if confirm.lower() != "y":
            logger.info("Bet cancelled by user")
            return {"status": "CANCELLED", "reason": "USER_CANCELLED"}

    # Place the bet
    sport_id = PinnacleRealConnector.get_sport_id(args.sport)
    result = connector.place_bet(
        event_id=str(args.event),
        sport_id=sport_id,
        line_id=int(args.line_id),
        period_number=int(args.period),
        bet_type=args.bet_type,
        odds=args.odds,
        stake=args.stake,
        team=args.team,
        side=args.side_pinnacle,
        customer_reference=f"vbq_{int(time.time())}",
    )

    logger.info("Bet result: %s", json.dumps(result, indent=2, default=str))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Place a real bet on Betfair or Pinnacle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--bookie", required=True, choices=["betfair", "pinnacle"])
    parser.add_argument("--odds", type=float, required=True, help="Decimal odds (e.g., 2.10)")
    parser.add_argument("--stake", type=float, required=True, help="Stake amount in account currency")
    parser.add_argument("--dry-run", action="store_true", help="Verify without placing bet")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--sandbox", action="store_true", default=True, help="Use sandbox/test mode")

    # Betfair-specific args
    bf_group = parser.add_argument_group("Betfair options")
    bf_group.add_argument("--market", help="Betfair market ID (e.g., 1.23456789)")
    bf_group.add_argument("--selection", type=int, help="Selection ID (runner)")
    bf_group.add_argument("--side", choices=["back", "lay"], default="back", help="Back or Lay")

    # Pinnacle-specific args
    pin_group = parser.add_argument_group("Pinnacle options")
    pin_group.add_argument("--event", type=int, help="Pinnacle event ID")
    pin_group.add_argument("--sport", default="football", help="Sport name (default: football)")
    pin_group.add_argument("--line-id", type=int, help="Line ID from odds response")
    pin_group.add_argument("--period", type=int, default=0, help="Period number (0=full match)")
    pin_group.add_argument("--bet-type", default="MONEYLINE", help="Bet type (MONEYLINE, SPREAD, TOTAL_POINTS)")
    pin_group.add_argument("--team", choices=["TEAM1", "TEAM2"], help="Team selection (for moneyline)")
    pin_group.add_argument("--side-pinnacle", choices=["OVER", "UNDER"], help="Side (for totals)")

    args = parser.parse_args()

    # Validate required args per bookie
    if args.bookie == "betfair":
        if not args.market or not args.selection:
            parser.error("Betfair requires --market and --selection")
        result = place_betfair_bet(args)
    else:
        if not args.event or not args.line_id:
            parser.error("Pinnacle requires --event and --line-id")
        result = place_pinnacle_bet(args)

    # Exit with appropriate code
    status = result.get("status", "UNKNOWN")
    if status in ("FULLY_FILLED", "DRY_RUN"):
        sys.exit(0)
    elif status == "PARTIALLY_FILLED":
        logger.warning("Bet was partially filled")
        sys.exit(2)
    else:
        logger.error("Bet failed: %s", status)
        sys.exit(1)


if __name__ == "__main__":
    main()
