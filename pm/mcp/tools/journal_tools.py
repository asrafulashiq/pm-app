"""MCP tools for journal management."""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ...core.manager import TaskManager
from ...core.journal_manager import JournalManager
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
    """Sync journal checkboxes with task statuses.

    Reads the current journal and updates task statuses based on
    checkbox completion.

    Returns:
        Dictionary with count of synced tasks
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    # Sync current journal
    synced_tasks = journal_manager.sync_journal()

    return {
        "synced_tasks": len(synced_tasks),
        "task_ids": synced_tasks,
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
