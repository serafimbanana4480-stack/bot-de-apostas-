import argparse
import logging
import os
import sys
from datetime import datetime, timezone

# Append project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import SessionLocal
from src.database.models import RawGame
from src.ingestion.nba_client import NBAIngestionClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ingest_nba_data")

SEASONS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

def parse_args():
    parser = argparse.ArgumentParser(description="Ingest historical NBA games data into PostgreSQL bronze schema.")
    parser.add_argument("--seasons", nargs="+", default=SEASONS, help="List of seasons to ingest, e.g. 2023-24")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of games to fetch detail logs for (useful for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to database")
    return parser.parse_args()

def ingest_seasons(seasons, limit=None, dry_run=False):
    client = NBAIngestionClient()
    db = SessionLocal()
    
    try:
        for season in seasons:
            logger.info(f"Starting ingestion for season {season}...")
            
            # Fetch games for season (both Regular Season and Playoffs)
            regular_games = client.fetch_games_for_season(season, "Regular Season")
            playoff_games = client.fetch_games_for_season(season, "Playoffs")
            all_games_raw = regular_games + playoff_games
            
            if not all_games_raw:
                logger.warning(f"No games found for season {season}.")
                continue
                
            logger.info(f"Found total {len(all_games_raw)} game records for season {season} (regular + playoffs).")
            
            # Deduplicate by game_id from raw api records
            # Note: NBA API returns 2 rows per game (one for each team)
            # We want to store a unified game record with home and away
            unique_games = {}
            for row in all_games_raw:
                game_id = row.get("GAME_ID")
                if not game_id:
                    continue
                
                # Check if we already have it in local dictionary
                if game_id not in unique_games:
                    unique_games[game_id] = []
                unique_games[game_id].append(row)
            
            logger.info(f"Grouped into {len(unique_games)} unique game matches.")
            
            # Load existing game IDs in DB to prevent duplicate calls and database inserts
            existing_ids = set()
            if not dry_run:
                try:
                    result = db.execute(text("SELECT game_id FROM bronze.raw_games"))
                    existing_ids = {r[0] for r in result.fetchall()}
                    logger.info(f"Found {len(existing_ids)} games already present in database.")
                except Exception as e:
                    logger.warning(f"Could not check existing games in DB: {e}. Proceeding assuming empty.")
            
            count = 0
            for game_id, rows in unique_games.items():
                if game_id in existing_ids:
                    continue
                
                if limit and count >= limit:
                    logger.info(f"Reached limit of {limit} games. Stopping.")
                    break
                
                # Parse home and away teams from the rows
                # Row mapping: MATCHUP example: 'BOS vs. LAL' or 'BOS @ LAL'
                # 'vs.' indicates home vs away, '@' indicates away at home
                row_0 = rows[0]
                matchup = row_0.get("MATCHUP", "")
                game_date_str = row_0.get("GAME_DATE", "")
                
                try:
                    game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                except ValueError:
                    game_date = datetime.now().date()
                
                home_team = ""
                away_team = ""
                
                # Deduce home/away from matchup
                if "vs." in matchup:
                    # e.g., 'BOS vs. LAL' means BOS is home, LAL is away
                    parts = matchup.split(" vs. ")
                    home_team = parts[0]
                    away_team = parts[1]
                elif "@" in matchup:
                    # e.g., 'BOS @ LAL' means BOS is away, LAL is home
                    parts = matchup.split(" @ ")
                    home_team = parts[1]
                    away_team = parts[0]
                else:
                    home_team = row_0.get("TEAM_ABBREVIATION", "HOME")
                    away_team = "AWAY"
                
                logger.info(f"Processing Game {game_id}: {matchup} on {game_date}")
                
                # Assemble raw game object
                raw_game = RawGame(
                    game_id=game_id,
                    season=season,
                    game_date=game_date,
                    home_team=home_team,
                    away_team=away_team,
                    status="Final", # Default for historical data
                    raw_data={
                        "game_details": rows,
                        "ingestion_metadata": {
                            "ingested_at": datetime.now(timezone.utc).isoformat(),
                            "matchup": matchup
                        }
                    }
                )
                
                if not dry_run:
                    db.merge(raw_game) # merge acts as an upsert (insert or update)
                
                count += 1
                
            if not dry_run:
                db.commit()
                logger.info(f"Successfully committed {count} new games for season {season}.")
            else:
                logger.info(f"[DRY-RUN] Would have ingested {count} new games for season {season}.")
                
    except Exception as e:
        db.rollback()
        logger.error(f"Failed during ingestion: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    from sqlalchemy import text
    args = parse_args()
    ingest_seasons(args.seasons, limit=args.limit, dry_run=args.dry_run)
