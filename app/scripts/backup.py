#!/usr/bin/env python3
"""
Backup script — creates timestamped archive of Parquet data and pushes to git.

Supports:
1. Local backup: tar.gz of data/ directory
2. Git push: commit and push any pending changes
3. Cloud upload: S3 or Google Drive (optional, requires configuration)

Usage:
  poetry run python scripts/backup.py                     # Local backup + git push
  poetry run python scripts/backup.py --no-git             # Local backup only
  poetry run python scripts/backup.py --s3                 # Also upload to S3
  poetry run python scripts/backup.py --gdrive             # Also upload to Google Drive
  poetry run python scripts/backup.py --restore latest     # Restore latest backup
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backup")

# Default paths
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
PROJECT_ROOT = Path(__file__).parent.parent


def create_local_backup(data_dir: Path, backup_dir: Path) -> Path:
    """Create a timestamped tar.gz backup of the data directory."""
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"vbq_data_{timestamp}.tar.gz"
    backup_path = backup_dir / backup_filename

    if not data_dir.exists():
        logger.warning("Data directory %s does not exist — nothing to backup", data_dir)
        return backup_path

    logger.info("Creating backup: %s", backup_path)
    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(str(data_dir), arcname="data")

    size_mb = backup_path.stat().st_size / (1024 * 1024)
    logger.info("Backup created: %s (%.1f MB)", backup_path, size_mb)

    # Write metadata
    meta = {
        "timestamp": timestamp,
        "size_mb": round(size_mb, 2),
        "data_dir": str(data_dir),
        "files": sum(1 for _ in data_dir.rglob("*") if _.is_file()),
    }
    meta_path = backup_dir / f"vbq_data_{timestamp}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    # Cleanup old backups (keep last 10)
    backups = sorted(backup_dir.glob("vbq_data_*.tar.gz"))
    if len(backups) > 10:
        for old in backups[:-10]:
            old.unlink()
            meta_old = backup_dir / (old.stem + "_meta.json")
            if meta_old.exists():
                meta_old.unlink()
            logger.info("Removed old backup: %s", old.name)

    return backup_path


def git_push(commit_message: str = "auto: data backup") -> bool:
    """Stage all changes, commit, and push to remote."""
    try:
        # Stage all changes
        subprocess.run(["git", "add", "-A"], cwd=PROJECT_ROOT, check=True, capture_output=True)

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )
        if result.returncode == 0:
            logger.info("No changes to commit")
            return True

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        logger.info("Git commit created: %s", commit_message)

        # Push
        result = subprocess.run(
            ["git", "push"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Git push successful")
            return True
        else:
            logger.warning("Git push failed (no remote?): %s", result.stderr)
            return False

    except subprocess.CalledProcessError as e:
        logger.error("Git operation failed: %s", e)
        return False
    except FileNotFoundError:
        logger.warning("Git not found — skipping git push")
        return False


def upload_to_s3(backup_path: Path, bucket: str = "", prefix: str = "backups/") -> bool:
    """Upload backup to S3 (requires aws CLI configured)."""
    if not bucket:
        bucket = os.getenv("AWS_S3_BUCKET", "")
    if not bucket:
        logger.warning("No S3 bucket configured — skipping S3 upload")
        return False

    s3_key = f"{prefix}{backup_path.name}"
    try:
        subprocess.run(
            ["aws", "s3", "cp", str(backup_path), f"s3://{bucket}/{s3_key}"],
            check=True,
            capture_output=True,
        )
        logger.info("Uploaded to S3: s3://%s/%s", bucket, s3_key)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error("S3 upload failed: %s", e)
        return False


def upload_to_gdrive(backup_path: Path, folder_id: str = "") -> bool:
    """Upload backup to Google Drive (requires rclone configured)."""
    if not folder_id:
        folder_id = os.getenv("GDRIVE_FOLDER_ID", "")
    if not folder_id:
        logger.warning("No Google Drive folder configured — skipping upload")
        return False

    try:
        subprocess.run(
            ["rclone", "copy", str(backup_path), f"gdrive:{folder_id}"],
            check=True,
            capture_output=True,
        )
        logger.info("Uploaded to Google Drive: %s", folder_id)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error("Google Drive upload failed: %s", e)
        return False


def restore_backup(backup_path: Path, data_dir: Path) -> bool:
    """Restore data directory from a backup archive."""
    if not backup_path.exists():
        logger.error("Backup not found: %s", backup_path)
        return False

    logger.info("Restoring backup: %s → %s", backup_path, data_dir)

    # Backup current data first
    if data_dir.exists():
        temp_backup = data_dir.parent / f"{data_dir.name}_pre_restore_{int(datetime.now().timestamp())}"
        shutil.move(str(data_dir), str(temp_backup))
        logger.info("Current data moved to: %s", temp_backup)

    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall(path=data_dir.parent)

    logger.info("Restore complete")
    return True


def find_latest_backup(backup_dir: Path) -> Path:
    """Find the most recent backup file."""
    backups = sorted(backup_dir.glob("vbq_data_*.tar.gz"))
    if not backups:
        raise FileNotFoundError("No backups found in %s" % backup_dir)
    return backups[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="VBQ Data Backup")
    parser.add_argument("--no-git", action="store_true", help="Skip git push")
    parser.add_argument("--s3", action="store_true", help="Upload to S3")
    parser.add_argument("--gdrive", action="store_true", help="Upload to Google Drive")
    parser.add_argument("--restore", nargs="?", const="latest", default=None,
                        help="Restore from backup (specify path or 'latest')")
    parser.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))
    parser.add_argument("--backup-dir", default=os.getenv("BACKUP_DIR", "backups"))

    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    backup_dir = Path(args.backup_dir)

    # Restore mode
    if args.restore is not None:
        if args.restore == "latest":
            backup_path = find_latest_backup(backup_dir)
        else:
            backup_path = Path(args.restore)
        success = restore_backup(backup_path, data_dir)
        sys.exit(0 if success else 1)

    # Backup mode
    backup_path = create_local_backup(data_dir, backup_dir)

    if not args.no_git:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        git_push(f"auto: data backup {timestamp}")

    if args.s3:
        upload_to_s3(backup_path)

    if args.gdrive:
        upload_to_gdrive(backup_path)

    logger.info("Backup complete: %s", backup_path)


if __name__ == "__main__":
    main()
