"""MCP tools for journal management."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from ...core.manager import TaskManager
from ...core.journal_manager import JournalManager
from ...core.backup import BackupManager
from ...utils.config import get_config
from ..serializers import serialize_day_section, serialize_weekly_summary


def start_journal_day() -> Dict[str, Any]:
    """Start a new journal day.

    Creates or updates the current week's journal with today's section,
    auto-populating tasks that need attention.

    Returns:
        Dictionary with journal path, day name, and planned tasks
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # Start today's journal - returns DaySection
    day_section = journal_manager.start_day()

    # Get current journal to access path
    journal = journal_manager.get_journal_for_date(datetime.now())

    return {
        "journal_path": str(journal.get_file_path()),
        "day": datetime.now().strftime("%A"),
        "planned_tasks": day_section.planned,
    }


def end_journal_day() -> Dict[str, Any]:
    """End the current journal day.

    Finalizes today's section and syncs task statuses based on
    checkbox completion in the journal.

    Returns:
        Dictionary with day name and completed task IDs
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # End today's journal - returns DaySection or None
    day_section = journal_manager.end_day()

    return {
        "day": datetime.now().strftime("%A"),
        "completed_tasks": day_section.completed if day_section else [],
        "blocked_tasks": day_section.blocked if day_section else [],
    }


def get_current_journal() -> Dict[str, Any]:
    """Get the current week's journal content.

    Returns:
        Dictionary with journal path and content (full markdown)
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # Get current journal
    now = datetime.now()
    journal = journal_manager.get_journal_for_date(now)
    journal_path = journal.get_file_path()

    # Read journal content (create if doesn't exist)
    if not journal_path.exists():
        journal_manager.start_day()

    content = journal_path.read_text() if journal_path.exists() else ""

    return {
        "journal_path": str(journal_path),
        "year": journal.year,
        "week": journal.week,
        "content": content,
    }


def sync_journal() -> Dict[str, Any]:
    """Sync journal with task system (bidirectional).

    This performs a full bidirectional sync:
    - Updates task statuses based on checkbox completion
    - Creates new tasks from NEW: entries in the journal
    - Deletes tasks that were removed from the journal
    - Creates a backup before making changes

    Returns:
        Dictionary with sync results:
        - synced_tasks: Number of tasks with status changes
        - created_tasks: Number of newly created tasks
        - deleted_tasks: Number of deleted tasks
        - backup_path: Path to backup file (if created)
        - created_ids: List of newly created task IDs
        - deleted_ids: List of deleted task IDs
        - updated_ids: List of task IDs with status changes
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # Sync current journal (returns detailed results)
    result = journal_manager.sync_journal()

    errors = result.get("errors", [])

    return {
        "synced_tasks": len(result.get("updated", [])),
        "created_tasks": len(result.get("created", [])),
        "deleted_tasks": len(result.get("deleted", [])),
        "backup_path": result.get("backup_path"),
        "created_ids": result.get("created", []),
        "deleted_ids": result.get("deleted", []),
        "updated_ids": result.get("updated", []),
        "errors": errors,
        "has_errors": len(errors) > 0,
    }


def generate_week_summary() -> Dict[str, Any]:
    """Generate summary for the current week.

    Creates a weekly summary section with completed tasks,
    in-progress tasks, and blockers.

    Returns:
        Serialized weekly summary dictionary
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # Generate summary for current week (no notes parameter)
    summary = journal_manager.generate_week_summary()

    return serialize_weekly_summary(summary)


def get_quarterly_summary(
    year: Optional[int] = None,
    quarter: Optional[int] = None,
) -> Dict[str, Any]:
    """Get quarterly achievement summary.

    Aggregates completed tasks and achievements for a given quarter.

    Args:
        year: Year (defaults to current year)
        quarter: Quarter 1-4 (defaults to current quarter)

    Returns:
        Dictionary with quarterly stats and achievements

    Raises:
        ValueError: If quarter is not 1-4 or year is invalid
    """
    # Default to current quarter
    now = datetime.now()
    if year is None:
        year = now.year
    if quarter is None:
        quarter = (now.month - 1) // 3 + 1

    # Validate inputs
    if not 1 <= quarter <= 4:
        raise ValueError(f"Quarter must be 1-4, got {quarter}")
    if year < 2000 or year > 2100:
        raise ValueError(f"Year must be between 2000-2100, got {year}")

    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # Get quarterly summary
    summary_data = journal_manager.get_quarterly_summary(year, quarter)

    return {
        "year": year,
        "quarter": quarter,
        "total_completed": len(summary_data["completed_tasks"]),
        "achievements": summary_data["completed_tasks"],
        "total_in_progress": len(summary_data.get("in_progress_tasks", [])),
        "in_progress": summary_data.get("in_progress_tasks", []),
    }


def list_journal_backups(
    year: Optional[int] = None,
    week: Optional[int] = None,
) -> Dict[str, Any]:
    """List available backups for a week's journal.

    Args:
        year: Year (defaults to current year)
        week: Week number 1-52 (defaults to current week)

    Returns:
        Dictionary with:
        - year: The year
        - week: The week number
        - backups: List of backup info dictionaries
    """
    # Default to current week
    now = datetime.now()
    if year is None:
        year = now.isocalendar()[0]
    if week is None:
        week = now.isocalendar()[1]

    # Get config and initialize backup manager
    config = get_config()
    backup_dir = config.data_path / "backups"

    backup_manager = BackupManager(
        backup_dir=backup_dir,
        max_backups_per_week=config.backup.max_backups_per_week,
        retention_days=config.backup.retention_days,
    )

    # Get backups for the week
    backups = backup_manager.list_backups(year, week)

    return {
        "year": year,
        "week": week,
        "backup_count": len(backups),
        "backups": [backup.to_dict() for backup in backups],
    }


def restore_journal_backup(backup_path: str) -> Dict[str, Any]:
    """Restore a journal from a backup file.

    Creates a backup of the current state before restoring.

    Args:
        backup_path: Path to the backup file to restore

    Returns:
        Dictionary with:
        - restored_from: Path of the backup that was restored
        - current_backup: Path to backup of current state (before restore)
        - journal_path: Path to the restored journal

    Raises:
        FileNotFoundError: If backup file doesn't exist
        ValueError: If backup_path is invalid
    """
    backup_file = Path(backup_path).expanduser()

    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    # Extract week from backup path (e.g., backups/2026-W02/2026-01-11T10-30-00.md)
    # The parent directory name is the week identifier
    week_str = backup_file.parent.name  # e.g., "2026-W02"

    # Parse year and week
    try:
        parts = week_str.split("-W")
        year = int(parts[0])
        week = int(parts[1])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid backup path format: {backup_path}")

    # Get config and paths
    config = get_config()
    journal_dir = config.data_path / "journal"
    journal_path = journal_dir / f"{week_str}.md"
    backup_dir = config.data_path / "backups"

    backup_manager = BackupManager(
        backup_dir=backup_dir,
        max_backups_per_week=config.backup.max_backups_per_week,
        retention_days=config.backup.retention_days,
    )

    # Restore from backup (creates backup of current state first)
    current_backup = backup_manager.restore_backup(backup_file, journal_path)

    return {
        "restored_from": str(backup_file),
        "current_backup": str(current_backup) if current_backup else None,
        "journal_path": str(journal_path),
        "year": year,
        "week": week,
    }
