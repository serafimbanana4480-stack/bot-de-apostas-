import logging
import os
import sys
from collections import Counter

# Add parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import SessionLocal
from src.database.models import RawGame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("verify_data_quality")

def run_data_quality_checks():
    db = SessionLocal()
    
    logger.info("Initializing Data Quality Checks on bronze.raw_games...")
    
    try:
        games = db.query(RawGame).all()
        total_records = len(games)
        
        if total_records == 0:
            logger.warning("[WARNING] No records found in bronze.raw_games. Ingestion might be empty.")
            print("\n=== DATA QUALITY REPORT ===")
            print("Status: WARNING")
            print("Total Records: 0")
            print("Ensure ingestion runs before validating quality.")
            return
            
        print("\n=== DATA QUALITY REPORT ===")
        print(f"Total Records Analyzed: {total_records}")
        
        # 1. Duplicate checks
        game_ids = [g.game_id for g in games]
        id_counts = Counter(game_ids)
        duplicates = {gid: count for gid, count in id_counts.items() if count > 1}
        
        print("\n1. Uniqueness Checks:")
        print(f"  - Unique Game IDs: {len(id_counts)}")
        print(f"  - Duplicate Game IDs: {len(duplicates)}")
        if duplicates:
            print(f"  [ERROR] Found duplicates: {duplicates}")
        else:
            print("  [OK] 0 duplicates found.")

        # 2. Missing/Null values checks
        null_game_ids = sum(1 for g in games if g.game_id is None)
        null_seasons = sum(1 for g in games if g.season is None)
        null_dates = sum(1 for g in games if g.game_date is None)
        null_homes = sum(1 for g in games if g.home_team is None)
        null_aways = sum(1 for g in games if g.away_team is None)
        null_raw = sum(1 for g in games if g.raw_data is None)
        
        print("\n2. Null Column Analysis:")
        print(f"  - NULL game_id: {null_game_ids} ({null_game_ids/total_records*100:.2f}%)")
        print(f"  - NULL season: {null_seasons} ({null_seasons/total_records*100:.2f}%)")
        print(f"  - NULL game_date: {null_dates} ({null_dates/total_records*100:.2f}%)")
        print(f"  - NULL home_team: {null_homes} ({null_homes/total_records*100:.2f}%)")
        print(f"  - NULL away_team: {null_aways} ({null_aways/total_records*100:.2f}%)")
        print(f"  - NULL raw_data: {null_raw} ({null_raw/total_records*100:.2f}%)")

        # 3. Payload Integrity Checks (inspect raw JSON)
        missing_matchup = 0
        missing_game_date_raw = 0
        missing_details = 0
        
        for g in games:
            payload = g.raw_data or {}
            details = payload.get("game_details", [])
            metadata = payload.get("ingestion_metadata", {})
            
            if not details:
                missing_details += 1
            if not metadata.get("matchup"):
                missing_matchup += 1
            
        print("\n3. JSON Payload Integrity:")
        print(f"  - Missing 'game_details' inside raw_data: {missing_details} ({missing_details/total_records*100:.2f}%)")
        print(f"  - Missing 'matchup' inside metadata: {missing_matchup} ({missing_matchup/total_records*100:.2f}%)")

        # 4. Pass/Fail Decision
        critical_failures = (
            len(duplicates) > 0 or 
            null_game_ids > 0 or 
            null_dates > 0 or 
            null_raw > 0 or 
            (missing_details / total_records) > 0.05
        )
        
        print("\n4. Final Assessment:")
        if critical_failures:
            print("  Status: FAILED")
            print("  Reason: Critical errors found (duplicates, null primaries or >5% missing payloads).")
            sys.exit(1)
        else:
            print("  Status: PASSED")
            print("  All data quality criteria met (<5% missing, 0 duplicates).")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error during validation: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_data_quality_checks()
