"""Weekly journal management for daily task tracking."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import re

from .task import Task, TaskStatus


@dataclass
class DaySection:
    """Represents a single day's section in the weekly journal."""
    date: datetime
    planned: List[str] = field(default_factory=list)  # Task IDs
    completed: List[str] = field(default_factory=list)  # Task IDs
    blocked: List[str] = field(default_factory=list)  # Task IDs
    notes: str = ""


@dataclass
class WeeklySummary:
    """Weekly summary data."""
    week_start: datetime
    week_end: datetime
    tasks_completed: List[str]  # Task IDs
    tasks_in_progress: List[str]  # Task IDs
    blockers: List[str]  # Task IDs or descriptions
    notes: str = ""

    def tasks_completed_count(self) -> int:
        """Count of completed tasks."""
        return len(self.tasks_completed)

    def completion_rate(self, total_planned: int) -> float:
        """Calculate completion rate."""
        if total_planned == 0:
            return 0.0
        return (len(self.tasks_completed) / total_planned) * 100


class WeeklyJournal:
    """Manages a weekly journal file."""

    def __init__(self, year: int, week: int, journal_dir: Path):
        """Initialize weekly journal.

        Args:
            year: Year number
            week: ISO week number (1-53)
            journal_dir: Directory for journal files
        """
        self.year = year
        self.week = week
        self.journal_dir = journal_dir
        self.journal_dir.mkdir(parents=True, exist_ok=True)

        # Calculate week start/end
        self.week_start = self._get_week_start(year, week)
        self.week_end = self.week_start + timedelta(days=6)

        self.days: Dict[str, DaySection] = {}
        self.summary: Optional[WeeklySummary] = None

    @staticmethod
    def _get_week_start(year: int, week: int) -> datetime:
        """Get the Monday of a given ISO week."""
        # January 4th is always in week 1
        jan4 = datetime(year, 1, 4)
        week_start = jan4 - timedelta(days=jan4.weekday())  # Go to Monday of week 1
        week_start += timedelta(weeks=week - 1)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_file_path(self) -> Path:
        """Get the path to this week's journal file."""
        return self.journal_dir / f"{self.year}-W{self.week:02d}.md"

    def get_summary_file_path(self) -> Path:
        """Get the path to this week's summary file."""
        return self.journal_dir / f"{self.year}-W{self.week:02d}-summary.md"

    def exists(self) -> bool:
        """Check if journal file exists."""
        return self.get_file_path().exists()

    def get_day_name(self, date: datetime) -> str:
        """Get day name (Monday, Tuesday, etc.)."""
        return date.strftime("%A")

    def get_day_key(self, date: datetime) -> str:
        """Get day key for internal storage."""
        return date.strftime("%Y-%m-%d")

    def add_day_section(self, date: datetime) -> DaySection:
        """Add a new day section to the journal."""
        day_key = self.get_day_key(date)
        if day_key not in self.days:
            self.days[day_key] = DaySection(date=date)
        return self.days[day_key]

    def get_day_section(self, date: datetime) -> Optional[DaySection]:
        """Get a day section if it exists."""
        day_key = self.get_day_key(date)
        return self.days.get(day_key)

    def generate_content(self, tasks_by_id: Dict[str, Task]) -> str:
        """Generate markdown content for the journal.

        Args:
            tasks_by_id: Dictionary mapping task IDs to Task objects

        Returns:
            Markdown content
        """
        lines = []

        # Header
        week_range = f"{self.week_start.strftime('%b %d')} - {self.week_end.strftime('%b %d, %Y')}"
        lines.append(f"# Week {self.week} - {self.year} ({week_range})")
        lines.append("")

        # Daily sections
        for i in range(7):  # Monday to Sunday
            day_date = self.week_start + timedelta(days=i)
            day_key = self.get_day_key(day_date)
            day_name = self.get_day_name(day_date)
            date_str = day_date.strftime("%b %d")

            lines.append(f"## {day_name}, {date_str}")
            lines.append("")

            # Get or create day section
            day_section = self.days.get(day_key, DaySection(date=day_date))

            # Planned tasks
            lines.append("### 📋 Planned")
            if day_section.planned:
                for task_id in day_section.planned:
                    task = tasks_by_id.get(task_id)
                    if task:
                        checkbox = "x" if task_id in day_section.completed else " "
                        lines.append(f"- [{checkbox}] {task_id}: {task.title} ({task.type.value}, {task.priority.value})")
            else:
                lines.append("<!-- Add tasks for today -->")
            lines.append("")

            # In Progress (multi-day tasks)
            in_progress = [tid for tid in day_section.planned
                          if tid in tasks_by_id and
                          tasks_by_id[tid].status == TaskStatus.IN_PROGRESS and
                          tid not in day_section.completed]
            if in_progress:
                lines.append("### 🔄 In Progress")
                for task_id in in_progress:
                    task = tasks_by_id[task_id]
                    lines.append(f"- {task_id}: {task.title}")
                    if task.notify_at:
                        lines.append(f"  - ETA: {task.notify_at.strftime('%b %d, %H:%M')}")
                lines.append("")

            # Blocked
            if day_section.blocked:
                lines.append("### 🚫 Blocked")
                for task_id in day_section.blocked:
                    task = tasks_by_id.get(task_id)
                    if task:
                        lines.append(f"- {task_id}: {task.title}")
                lines.append("")

            # Completed
            if day_section.completed:
                lines.append("### ✅ Completed")
                for task_id in day_section.completed:
                    task = tasks_by_id.get(task_id)
                    if task:
                        lines.append(f"- {task_id}: {task.title}")
                lines.append("")

            # Notes
            lines.append("### 📝 Notes")
            if day_section.notes:
                lines.append(day_section.notes)
            else:
                lines.append("<!-- Add notes for the day -->")
            lines.append("")

            lines.append("---")
            lines.append("")

        # Summary section (if exists)
        if self.summary:
            lines.append("## 📊 Week Summary")
            lines.append("")
            lines.append(f"**Week:** {week_range}")
            lines.append(f"**Completed:** {len(self.summary.tasks_completed)} tasks")
            lines.append(f"**In Progress:** {len(self.summary.tasks_in_progress)} tasks")
            lines.append("")

            if self.summary.tasks_completed:
                lines.append("### ✅ Accomplished This Week")
                for task_id in self.summary.tasks_completed:
                    task = tasks_by_id.get(task_id)
                    if task:
                        lines.append(f"- {task.title}")
                lines.append("")

            if self.summary.tasks_in_progress:
                lines.append("### 🔄 Still In Progress")
                for task_id in self.summary.tasks_in_progress:
                    task = tasks_by_id.get(task_id)
                    if task:
                        lines.append(f"- {task.title}")
                lines.append("")

            if self.summary.blockers:
                lines.append("### 🚫 Blockers")
                for blocker in self.summary.blockers:
                    lines.append(f"- {blocker}")
                lines.append("")

            if self.summary.notes:
                lines.append("### 📌 Notes")
                lines.append(self.summary.notes)
                lines.append("")

        return "\n".join(lines)

    def save(self, tasks_by_id: Dict[str, Task]) -> None:
        """Save journal to file.

        Args:
            tasks_by_id: Dictionary mapping task IDs to Task objects
        """
        content = self.generate_content(tasks_by_id)
        self.get_file_path().write_text(content)

    def parse_checkboxes(self, content: str) -> Dict[str, bool]:
        """Parse checkboxes from markdown content.

        Returns:
            Dictionary mapping task IDs to checked status
        """
        checkbox_pattern = r'- \[([ x])\] (task-[a-f0-9]+):'
        checkboxes = {}

        for match in re.finditer(checkbox_pattern, content):
            checked = match.group(1) == 'x'
            task_id = match.group(2)
            checkboxes[task_id] = checked

        return checkboxes

    def load(self, tasks_by_id: Dict[str, Task]) -> None:
        """Load journal from file and parse content.

        Args:
            tasks_by_id: Dictionary mapping task IDs to Task objects
        """
        if not self.exists():
            return

        content = self.get_file_path().read_text()

        # Parse checkboxes to determine completed tasks
        checkboxes = self.parse_checkboxes(content)

        # Parse day sections (simplified - just look for task IDs in each day)
        current_day = None
        current_section = None

        for line in content.split('\n'):
            # Detect day header
            day_match = re.match(r'## (\w+), (\w+ \d+)', line)
            if day_match:
                # Find the date for this day
                for i in range(7):
                    day_date = self.week_start + timedelta(days=i)
                    if self.get_day_name(day_date) == day_match.group(1):
                        current_day = self.add_day_section(day_date)
                        break
                continue

            # Detect section
            if line.startswith('### 📋 Planned'):
                current_section = 'planned'
            elif line.startswith('### 🚫 Blocked'):
                current_section = 'blocked'
            elif line.startswith('### ✅ Completed'):
                current_section = 'completed'
            elif line.startswith('### 📝 Notes'):
                current_section = 'notes'
            elif line.startswith('###') or line.startswith('##'):
                current_section = None

            # Parse task IDs
            if current_day and current_section and current_section != 'notes':
                task_match = re.search(r'(task-[a-f0-9]+):', line)
                if task_match:
                    task_id = task_match.group(1)

                    if current_section == 'planned' and task_id not in current_day.planned:
                        current_day.planned.append(task_id)
                        # Check if completed based on checkbox
                        if checkboxes.get(task_id, False):
                            if task_id not in current_day.completed:
                                current_day.completed.append(task_id)
                    elif current_section == 'blocked' and task_id not in current_day.blocked:
                        current_day.blocked.append(task_id)


def get_current_week() -> tuple:
    """Get current ISO year and week number.

    Returns:
        Tuple of (year, week)
    """
    now = datetime.now()
    iso_calendar = now.isocalendar()
    return iso_calendar[0], iso_calendar[1]


def get_week_for_date(date: datetime) -> tuple:
    """Get ISO year and week number for a date.

    Args:
        date: Date to get week for

    Returns:
        Tuple of (year, week)
    """
    iso_calendar = date.isocalendar()
    return iso_calendar[0], iso_calendar[1]
