"""
Environment Variables Verification Script
Checks if .env exists, parses all required keys from .env.example,
and warns if any keys are missing or contain placeholder values.
"""
import sys
from pathlib import Path


def parse_env_file(path: Path) -> dict:
    """Parses key-value pairs from an env file."""
    kv_pairs = {}
    if not path.exists():
        return kv_pairs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                kv_pairs[key.strip()] = val.strip()
    return kv_pairs

def main():
    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / ".env"
    env_example_file = project_root / ".env.example"

    print("[INFO] Checking environment configuration...")

    if not env_example_file.exists():
        print(f"[ERROR] Error: {env_example_file} does not exist!")
        sys.exit(1)

    required_keys = list(parse_env_file(env_example_file).keys())

    if not env_file.exists():
        print("[WARN] Warning: .env file not found. Copying .env.example to .env...")
        try:
            import shutil
            shutil.copy2(env_example_file, env_file)
            print("[OK] Created .env from .env.example template.")
            print("[INFO] Please edit the .env file with your actual secret credentials.")
        except Exception as e:
            print(f"[ERROR] Error copying env file: {e}")
            sys.exit(1)

    # Reload variables from env file
    current_env = parse_env_file(env_file)
    missing_keys = []
    placeholder_keys = []

    placeholders = {
        "your_secure_postgres_password_here",
        "your_secure_redis_password_here",
        "your_32_character_hex_secret_key_here",
        "your_cryptography_fernet_key_here",
        "your_nba_api_key_here",
        "your_betfair_app_key_here",
        "your_betfair_username_here",
        "your_betfair_password_here",
        "your_telegram_bot_token_here",
        "your_telegram_chat_id_here",
        "your_odds_api_key_here"
    }

    for key in required_keys:
        if key not in current_env:
            missing_keys.append(key)
        else:
            val = current_env[key]
            # Check for placeholder values
            if val in placeholders or "here" in val.lower() or val == "":
                placeholder_keys.append(key)

    if missing_keys:
        print("\n[ERROR] The following required environment keys are missing from your .env:")
        for key in missing_keys:
            print(f"  - {key}")

    if placeholder_keys:
        print("\n[WARN] The following keys still contain placeholder or empty values:")
        for key in placeholder_keys:
            print(f"  - {key}")

    if missing_keys:
        sys.exit(1)

    if placeholder_keys:
        print("\n[WARN] Verification complete: Environment has warnings but is loadable.")
        sys.exit(0)

    print("\n[OK] Success: All environment variables verified and configured correctly.")
    sys.exit(0)

if __name__ == "__main__":
    main()
