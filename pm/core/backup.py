"""Backup management for journal files."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BackupInfo:
    """Information about a backup file."""
    path: Path
    timestamp: datetime
    trigger: str
    week: str  # e.g., "2026-W02"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "week": self.week,
        }


class BackupManager:
    """Manages backups of journal files."""

    def __init__(
        self,
        backup_dir: Path,
        max_backups_per_week: int = 50,
        retention_days: int = 90,
    ):
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups
            max_backups_per_week: Maximum number of backups to keep per week
            retention_days: Number of days to retain backups
        """
        self.backup_dir = Path(backup_dir).expanduser()
        self.max_backups_per_week = max_backups_per_week
        self.retention_days = retention_days

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        journal_path: Path,
        trigger: str = "manual",
    ) -> Optional[Path]:
        """Create a timestamped backup of a journal file.

        Args:
            journal_path: Path to the journal file to backup
            trigger: What triggered this backup (sync, delete, edit, manual)

        Returns:
            Path to the created backup file, or None if journal doesn't exist
        """
        if not journal_path.exists():
            return None

        # Get week identifier from filename (e.g., "2026-W02" from "2026-W02.md")
        week = journal_path.stem

        # Create week-specific backup directory
        week_dir = self.backup_dir / week
        week_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for backup filename
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%S")

        # Create backup file
        backup_path = week_dir / f"{timestamp_str}.md"
        shutil.copy2(journal_path, backup_path)

        # Write metadata file
        meta_path = week_dir / f"{timestamp_str}.meta"
        meta = {
            "trigger": trigger,
            "original": str(journal_path),
            "timestamp": timestamp.isoformat(),
            "week": week,
        }
        meta_path.write_text(json.dumps(meta, indent=2))

        # Enforce retention policy
        self._enforce_retention(week_dir)

        return backup_path

    def list_backups(self, year: int, week: int) -> List[BackupInfo]:
        """List all backups for a specific week.

        Args:
            year: Year (e.g., 2026)
            week: Week number (1-52)

        Returns:
            List of BackupInfo objects, sorted by timestamp (newest first)
        """
        week_str = f"{year}-W{week:02d}"
        week_dir = self.backup_dir / week_str

        if not week_dir.exists():
            return []

        backups = []
        for backup_file in week_dir.glob("*.md"):
            meta_path = backup_file.with_suffix(".meta")

            # Parse timestamp from filename
            try:
                timestamp_str = backup_file.stem
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
            except ValueError:
                continue

            # Read trigger from metadata if available
            trigger = "unknown"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                    trigger = meta.get("trigger", "unknown")
                except (json.JSONDecodeError, IOError):
                    pass

            backups.append(BackupInfo(
                path=backup_file,
                timestamp=timestamp,
                trigger=trigger,
                week=week_str,
            ))

        # Sort by timestamp, newest first
        backups.sort(key=lambda b: b.timestamp, reverse=True)

        return backups

    def restore_backup(self, backup_path: Path, journal_path: Path) -> Path:
        """Restore a journal from a backup file.

        Creates a backup of the current state before restoring.

        Args:
            backup_path: Path to the backup file to restore
            journal_path: Path to the journal file to restore to

        Returns:
            Path to the backup of the current state (before restore)

        Raises:
            FileNotFoundError: If backup file doesn't exist
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create backup of current state before restoring
        current_backup = None
        if journal_path.exists():
            current_backup = self.create_backup(journal_path, trigger="pre-restore")

        # Restore from backup
        shutil.copy2(backup_path, journal_path)

        return current_backup

    def get_latest_backup(self, year: int, week: int) -> Optional[BackupInfo]:
        """Get the most recent backup for a week.

        Args:
            year: Year
            week: Week number

        Returns:
            BackupInfo for the latest backup, or None if no backups exist
        """
        backups = self.list_backups(year, week)
        return backups[0] if backups else None

    def _enforce_retention(self, week_dir: Path) -> None:
        """Remove old backups beyond retention limits.

        Args:
            week_dir: Directory containing backups for a specific week
        """
        # Get all backup files sorted by modification time
        backup_files = sorted(
            week_dir.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,  # Newest first
        )

        # Keep only max_backups_per_week
        files_to_remove = backup_files[self.max_backups_per_week:]

        for backup_file in files_to_remove:
            backup_file.unlink()
            # Also remove metadata file if exists
            meta_path = backup_file.with_suffix(".meta")
            if meta_path.exists():
                meta_path.unlink()

    def cleanup_old_backups(self) -> int:
        """Remove backups older than retention_days.

        Returns:
            Number of backup files removed
        """
        removed_count = 0
        cutoff = datetime.now().timestamp() - (self.retention_days * 24 * 60 * 60)

        for week_dir in self.backup_dir.iterdir():
            if not week_dir.is_dir():
                continue

            for backup_file in week_dir.glob("*.md"):
                if backup_file.stat().st_mtime < cutoff:
                    backup_file.unlink()
                    meta_path = backup_file.with_suffix(".meta")
                    if meta_path.exists():
                        meta_path.unlink()
                    removed_count += 1

            # Remove empty week directories
            if not any(week_dir.iterdir()):
                week_dir.rmdir()

        return removed_count
