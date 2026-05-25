import os
import sys

from sqlalchemy import create_engine, text

# Append parent dir to path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings


def create_schemas():
    # Database connection URL
    database_url = (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    
    print(f"[INFO] Connecting to {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}...")
    engine = create_engine(database_url)
    
    schemas = ["bronze", "silver", "gold", "meta"]
    
    try:
        with engine.connect() as conn:
            # Transaction block
            trans = conn.begin()
            try:
                for schema in schemas:
                    print(f"[INFO] Creating schema IF NOT EXISTS '{schema}'...")
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
                trans.commit()
                print("[OK] All database schemas verified/created successfully.")
            except Exception as e:
                trans.rollback()
                print(f"[ERROR] Failed to create schemas: {e}")
                sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("[INFO] Make sure your PostgreSQL server is running and .env is configured correctly.")
        sys.exit(1)

if __name__ == "__main__":
    create_schemas()
