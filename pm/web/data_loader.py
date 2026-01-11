"""Data loader for Streamlit web UI.

Provides read-only access to journal data through JournalManager.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pm.core.manager import TaskManager
from pm.core.journal_manager import JournalManager
from pm.core.journal import WeeklyJournal, DaySection, get_current_week
from pm.core.task import Task, TaskStatus


@dataclass
class TaskDisplayData:
    """UI-friendly task representation."""
    id: str
    title: str
    type: str
    priority: str
    status: str
    is_completed: bool
    eta: Optional[str] = None
    notes_count: int = 0


@dataclass
class DaySectionData:
    """UI-friendly day section representation."""
    date: datetime
    day_name: str
    date_str: str
    planned_tasks: List[TaskDisplayData]
    completed_tasks: List[TaskDisplayData]
    blocked_tasks: List[TaskDisplayData]
    in_progress_tasks: List[TaskDisplayData]
    notes: str


@dataclass
class WeeklyJournalData:
    """UI-friendly weekly journal representation."""
    year: int
    week: int
    week_start: datetime
    week_end: datetime
    week_range_str: str
    days: Dict[str, DaySectionData]
    total_planned: int = 0
    total_completed: int = 0


class JournalDataLoader:
    """Loads and caches journal data for Streamlit UI."""

    def __init__(self, journal_dir: Optional[str] = None):
        """Initialize data loader.

        Args:
            journal_dir: Optional custom journal directory path
        """
        self._task_manager = TaskManager()
        self._journal_manager = JournalManager(
            self._task_manager,
            journal_dir=journal_dir
        )

    def get_available_weeks(self) -> List[Tuple[int, int, str]]:
        """Get list of available journal weeks.

        Returns:
            List of (year, week, display_string) tuples, sorted newest first
        """
        journal_dir = self._journal_manager.journal_dir
        weeks = []

        for file in journal_dir.glob("????-W??.md"):
            # Parse filename like "2026-W02.md"
            try:
                stem = file.stem  # "2026-W02"
                year = int(stem[:4])
                week = int(stem[6:8])

                # Get week date range for display
                week_start = WeeklyJournal._get_week_start(year, week)
                week_end = week_start + timedelta(days=6)
                display = f"{year}-W{week:02d} ({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})"

                weeks.append((year, week, display))
            except (ValueError, IndexError):
                continue

        # Sort by year and week descending (newest first)
        weeks.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return weeks

    def get_journal_data(self, year: int, week: int) -> Optional[WeeklyJournalData]:
        """Load journal data for a specific week.

        Args:
            year: Year number
            week: ISO week number

        Returns:
            WeeklyJournalData or None if journal doesn't exist
        """
        journal = WeeklyJournal(year, week, self._journal_manager.journal_dir)

        if not journal.exists():
            return None

        # Load tasks for reference
        tasks_by_id = {t.id: t for t in self._task_manager.get_all_tasks()}
        journal.load(tasks_by_id)

        # Convert to UI-friendly format
        return self._convert_journal(journal, tasks_by_id)

    def _convert_journal(
        self,
        journal: WeeklyJournal,
        tasks_by_id: Dict[str, Task]
    ) -> WeeklyJournalData:
        """Convert WeeklyJournal to WeeklyJournalData."""
        week_range = f"{journal.week_start.strftime('%b %d')} - {journal.week_end.strftime('%b %d, %Y')}"

        days_data = {}
        total_planned = 0
        total_completed = 0

        for i in range(7):  # Monday to Sunday
            day_date = journal.week_start + timedelta(days=i)
            day_key = journal.get_day_key(day_date)
            day_section = journal.days.get(day_key)

            if day_section:
                day_data = self._convert_day_section(day_section, tasks_by_id)
                total_planned += len(day_data.planned_tasks)
                total_completed += len(day_data.completed_tasks)
            else:
                day_data = DaySectionData(
                    date=day_date,
                    day_name=day_date.strftime("%A"),
                    date_str=day_date.strftime("%b %d"),
                    planned_tasks=[],
                    completed_tasks=[],
                    blocked_tasks=[],
                    in_progress_tasks=[],
                    notes=""
                )

            days_data[day_key] = day_data

        return WeeklyJournalData(
            year=journal.year,
            week=journal.week,
            week_start=journal.week_start,
            week_end=journal.week_end,
            week_range_str=week_range,
            days=days_data,
            total_planned=total_planned,
            total_completed=total_completed
        )

    def _convert_day_section(
        self,
        section: DaySection,
        tasks_by_id: Dict[str, Task]
    ) -> DaySectionData:
        """Convert DaySection to DaySectionData."""
        def task_to_display(task_id: str, completed: bool = False) -> Optional[TaskDisplayData]:
            task = tasks_by_id.get(task_id)
            if not task:
                return None
            return TaskDisplayData(
                id=task.id,
                title=task.title,
                type=task.type.value,
                priority=task.priority.value,
                status=task.status.value,
                is_completed=completed or task_id in section.completed,
                eta=task.eta.strftime("%Y-%m-%d") if task.eta else None,
                notes_count=len(task.notes)
            )

        planned = [t for t in (task_to_display(tid) for tid in section.planned) if t]
        completed = [t for t in (task_to_display(tid, True) for tid in section.completed) if t]
        blocked = [t for t in (task_to_display(tid) for tid in section.blocked) if t]

        # Identify in-progress tasks (planned but not completed, with in_progress status)
        in_progress = [
            t for t in planned
            if not t.is_completed and tasks_by_id.get(t.id)
            and tasks_by_id[t.id].status == TaskStatus.IN_PROGRESS
        ]

        return DaySectionData(
            date=section.date,
            day_name=section.date.strftime("%A"),
            date_str=section.date.strftime("%b %d"),
            planned_tasks=planned,
            completed_tasks=completed,
            blocked_tasks=blocked,
            in_progress_tasks=in_progress,
            notes=section.notes
        )

    def get_current_week(self) -> Tuple[int, int]:
        """Get current year and week number."""
        return get_current_week()
