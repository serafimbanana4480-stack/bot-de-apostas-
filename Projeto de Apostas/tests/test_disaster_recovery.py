"""
Disaster recovery tests — verify backup/restore and data integrity.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest


class TestDisasterRecovery:
    """Test disaster recovery scenarios."""

    def test_backup_and_restore_data_dir(self, tmp_path):
        """Backup data/, delete it, then restore and verify contents."""
        from src.data.local_store import LocalDataStore

        # 1. Create a temporary data dir with files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "matches.parquet").write_text("dummy parquet")
        (data_dir / "odds.parquet").write_text("dummy odds")
        subdir = data_dir / "bronze"
        subdir.mkdir()
        (subdir / "file.parquet").write_text("nested file")

        # 2. Backup
        backup_file = tmp_path / "backup.tar.gz"
        import tarfile
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(data_dir, arcname="data")

        # 3. Delete data dir (simulating disaster)
        shutil.rmtree(data_dir)
        assert not data_dir.exists()

        # 4. Restore from backup (extract directly to tmp_path)
        with tarfile.open(backup_file, "r:gz") as tar:
            # filter argument for Python 3.14 compatibility
            tar.extractall(tmp_path, filter="data")

        # 5. Verify all files restored
        assert (data_dir / "matches.parquet").exists()
        assert (data_dir / "odds.parquet").exists()
        assert (subdir / "file.parquet").exists()

    def test_env_recovery(self, tmp_path):
        """Simulate .env file loss and recovery."""
        env_file = tmp_path / ".env"
        env_content = "DB_HOST=localhost\nDB_NAME=test\nSECRET_KEY=abc123\n"
        env_file.write_text(env_content)

        # Simulate loss
        env_backup = tmp_path / ".env.backup"
        shutil.copy(env_file, env_backup)
        os.remove(env_file)
        assert not env_file.exists()

        # Restore
        shutil.copy(env_backup, env_file)
        assert env_file.read_text() == env_content

    def test_model_artifact_recovery(self, tmp_path):
        """Verify model artifacts are backed up and can be restored."""
        import pickle

        model_dir = tmp_path / "models"
        model_dir.mkdir()
        model_file = model_dir / "poisson_football.pkl"
        dummy_model = {"coefs": [1.0, 2.0], "sport": "football"}
        with open(model_file, "wb") as f:
            pickle.dump(dummy_model, f)

        # Backup
        backup_file = tmp_path / "models_backup.tar.gz"
        import tarfile
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(model_dir, arcname="models")

        # Delete
        shutil.rmtree(model_dir)

        # Restore
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        # Verify
        with open(model_file, "rb") as f:
            restored = pickle.load(f)
        assert restored == dummy_model

    def test_database_dump_restore(self, tmp_path):
        """Simulate database dump and restore using SQL dump."""
        # Create a mock SQL dump
        dump_file = tmp_path / "db_dump.sql"
        dump_content = "CREATE TABLE bets (id INT, stake FLOAT);\nINSERT INTO bets VALUES (1, 10.0);\n"
        dump_file.write_text(dump_content)

        # Simulate DB loss and restore
        restored_db = tmp_path / "restored.sql"
        shutil.copy(dump_file, restored_db)

        assert restored_db.read_text() == dump_content
        assert "CREATE TABLE bets" in restored_db.read_text()

    def test_cost_tracking_survives_restart(self, tmp_path):
        """Verify cost tracking data persists across restarts."""
        from src.monitoring.operational_costs import OperationalCostMonitor

        # First session
        monitor1 = OperationalCostMonitor(data_dir=tmp_path / "costs")
        monitor1.record_bet(stake=10.0, commission_rate=0.05, gross_pnl=2.0)
        monitor1.record_api_call(provider="oddsapi", cost=0.01)
        monitor1.close_period()

        # Simulate restart — create new monitor
        monitor2 = OperationalCostMonitor(data_dir=tmp_path / "costs")
        report = monitor2.get_report()
        # Current period is fresh, but history should have the bet
        history = monitor2.get_monthly_summary(months=1)
        assert len(history) > 0
        assert history[0]["num_bets"] == 1
