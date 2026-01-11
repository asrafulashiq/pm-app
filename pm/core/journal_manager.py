"""Journal manager for integrating journals with task management."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import subprocess

from .journal import WeeklyJournal, DaySection, WeeklySummary, get_current_week, get_week_for_date
from .manager import TaskManager
from .task import Task, TaskStatus


class JournalManager:
    """Manages weekly journals and syncs with tasks."""

    def __init__(self, task_manager: TaskManager, journal_dir: Optional[str] = None):
        """Initialize journal manager.

        Args:
            task_manager: TaskManager instance
            journal_dir: Directory for journals (defaults to data_dir/journal)
        """
        self.task_manager = task_manager

        if journal_dir:
            self.journal_dir = Path(journal_dir).expanduser()
        else:
            data_dir = self.task_manager.config.data_path
            self.journal_dir = data_dir / "journal"

        self.journal_dir.mkdir(parents=True, exist_ok=True)

    def get_current_journal(self) -> WeeklyJournal:
        """Get journal for current week."""
        year, week = get_current_week()
        return WeeklyJournal(year, week, self.journal_dir)

    def get_journal_for_date(self, date: datetime) -> WeeklyJournal:
        """Get journal for a specific date."""
        year, week = get_week_for_date(date)
        return WeeklyJournal(year, week, self.journal_dir)

    def open_journal(self, date: Optional[datetime] = None, editor: str = "vim") -> WeeklyJournal:
        """Open journal for a date (defaults to today).

        Args:
            date: Date to open journal for (defaults to today)
            editor: Editor command to use

        Returns:
            WeeklyJournal instance
        """
        if date is None:
            journal = self.get_current_journal()
        else:
            journal = self.get_journal_for_date(date)

        # Load or create journal
        tasks_by_id = {t.id: t for t in self.task_manager.get_all_tasks()}

        if journal.exists():
            journal.load(tasks_by_id)
        else:
            # Initialize with current week's data
            self._populate_new_journal(journal)

        # Save before opening
        journal.save(tasks_by_id)

        # Open in editor
        journal_path = journal.get_file_path()
        subprocess.run([editor, str(journal_path)])

        return journal

    def _populate_new_journal(self, journal: WeeklyJournal) -> None:
        """Populate a new journal with relevant tasks.

        Args:
            journal: WeeklyJournal to populate
        """
        all_tasks = self.task_manager.get_all_tasks()

        # Get tasks that need attention
        in_progress_tasks = [t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]
        needs_check = self.task_manager.get_tasks_needing_check()
        overdue = self.task_manager.get_overdue_tasks()
        blocked = [t for t in all_tasks if t.status == TaskStatus.BLOCKED]

        # Add tasks to appropriate days
        for i in range(7):  # Monday to Sunday
            day_date = journal.week_start + timedelta(days=i)
            day_section = journal.add_day_section(day_date)

            # Monday: Add in-progress and overdue tasks
            if i == 0:  # Monday
                for task in in_progress_tasks:
                    if task.id not in day_section.planned:
                        day_section.planned.append(task.id)

                for task in overdue:
                    if task.id not in day_section.planned:
                        day_section.planned.append(task.id)

            # Add tasks needing check on their day
            for task in needs_check:
                if task.id not in day_section.planned:
                    day_section.planned.append(task.id)

            # Add blocked tasks
            for task in blocked:
                if task.id not in day_section.blocked:
                    day_section.blocked.append(task.id)

    def start_day(self, date: Optional[datetime] = None) -> DaySection:
        """Start a new day in the journal.

        Args:
            date: Date to start (defaults to today)

        Returns:
            DaySection for the day
        """
        if date is None:
            date = datetime.now()

        journal = self.get_journal_for_date(date)
        tasks_by_id = {t.id: t for t in self.task_manager.get_all_tasks()}

        # Load existing journal
        if journal.exists():
            journal.load(tasks_by_id)

        # Get or create day section
        day_section = journal.get_day_section(date)
        if not day_section:
            day_section = journal.add_day_section(date)

            # Auto-populate with tasks needing attention
            in_progress = [t for t in self.task_manager.get_all_tasks()
                          if t.status == TaskStatus.IN_PROGRESS]
            needs_check = self.task_manager.get_tasks_needing_check()
            overdue = self.task_manager.get_overdue_tasks()

            # Add to planned
            for task in in_progress + needs_check + overdue:
                if task.id not in day_section.planned:
                    day_section.planned.append(task.id)

        # Save journal
        journal.save(tasks_by_id)

        return day_section

    def end_day(self, date: Optional[datetime] = None) -> DaySection:
        """End the day and sync tasks.

        Args:
            date: Date to end (defaults to today)

        Returns:
            DaySection for the day
        """
        if date is None:
            date = datetime.now()

        journal = self.get_journal_for_date(date)
        tasks_by_id = {t.id: t for t in self.task_manager.get_all_tasks()}

        # Load journal
        if journal.exists():
            journal.load(tasks_by_id)

        # Sync tasks with checkboxes
        self.sync_journal(journal)

        # Get day section
        day_section = journal.get_day_section(date)

        return day_section

    def sync_journal(self, journal: Optional[WeeklyJournal] = None) -> Dict[str, bool]:
        """Sync journal checkboxes with task statuses.

        Args:
            journal: Journal to sync (defaults to current week)

        Returns:
            Dictionary mapping task IDs to their completion status
        """
        if journal is None:
            journal = self.get_current_journal()

        if not journal.exists():
            return {}

        # Load journal content
        content = journal.get_file_path().read_text()

        # Parse checkboxes
        checkboxes = journal.parse_checkboxes(content)

        # Update task statuses based on checkboxes
        for task_id, is_checked in checkboxes.items():
            task = self.task_manager.get_task(task_id)
            if task:
                if is_checked and task.status != TaskStatus.DONE:
                    # Mark task as done
                    self.task_manager.mark_done(task_id)
                elif not is_checked and task.status == TaskStatus.DONE:
                    # Reopen task
                    self.task_manager.update_task(task_id, status=TaskStatus.TODO)

        # Reload journal to update with new task statuses
        tasks_by_id = {t.id: t for t in self.task_manager.get_all_tasks()}
        journal.load(tasks_by_id)

        # Update completed lists in day sections
        for day_key, day_section in journal.days.items():
            day_section.completed = [
                tid for tid in day_section.planned
                if checkboxes.get(tid, False)
            ]

        # Save updated journal
        journal.save(tasks_by_id)

        return checkboxes

    def generate_week_summary(self, journal: Optional[WeeklyJournal] = None) -> WeeklySummary:
        """Generate summary for a week.

        Args:
            journal: Journal to summarize (defaults to current week)

        Returns:
            WeeklySummary
        """
        if journal is None:
            journal = self.get_current_journal()

        tasks_by_id = {t.id: t for t in self.task_manager.get_all_tasks()}

        # Load journal
        if journal.exists():
            journal.load(tasks_by_id)

        # Collect tasks from all days
        all_planned: Set[str] = set()
        all_completed: Set[str] = set()
        all_blocked: Set[str] = set()

        for day_section in journal.days.values():
            all_planned.update(day_section.planned)
            all_completed.update(day_section.completed)
            all_blocked.update(day_section.blocked)

        # Get in-progress tasks
        in_progress = [tid for tid in all_planned
                      if tid not in all_completed
                      and tasks_by_id.get(tid, None)
                      and tasks_by_id[tid].status == TaskStatus.IN_PROGRESS]

        # Create summary
        summary = WeeklySummary(
            week_start=journal.week_start,
            week_end=journal.week_end,
            tasks_completed=list(all_completed),
            tasks_in_progress=in_progress,
            blockers=[tasks_by_id[tid].title for tid in all_blocked if tid in tasks_by_id]
        )

        # Add summary to journal
        journal.summary = summary

        # Save journal with summary
        journal.save(tasks_by_id)

        # Also save summary to separate file
        self._save_summary_file(journal, summary, tasks_by_id)

        return summary

    def _save_summary_file(self, journal: WeeklyJournal, summary: WeeklySummary, tasks_by_id: Dict[str, Task]) -> None:
        """Save weekly summary to a separate file.

        Args:
            journal: WeeklyJournal instance
            summary: WeeklySummary to save
            tasks_by_id: Dictionary of tasks
        """
        lines = []

        week_range = f"{summary.week_start.strftime('%b %d')} - {summary.week_end.strftime('%b %d, %Y')}"
        lines.append(f"# Week {journal.week} Summary - {journal.year}")
        lines.append("")
        lines.append(f"**Period:** {week_range}")
        lines.append(f"**Completed Tasks:** {summary.tasks_completed_count()}")
        lines.append(f"**In Progress:** {len(summary.tasks_in_progress)}")
        lines.append("")

        lines.append("## ✅ Accomplished This Week")
        lines.append("")
        if summary.tasks_completed:
            for task_id in summary.tasks_completed:
                task = tasks_by_id.get(task_id)
                if task:
                    lines.append(f"- **{task.title}** ({task.type.value})")
        else:
            lines.append("No tasks completed this week.")
        lines.append("")

        lines.append("## 🔄 Still In Progress")
        lines.append("")
        if summary.tasks_in_progress:
            for task_id in summary.tasks_in_progress:
                task = tasks_by_id.get(task_id)
                if task:
                    lines.append(f"- **{task.title}** ({task.type.value})")
                    if task.eta:
                        lines.append(f"  - ETA: {task.eta.strftime('%b %d, %Y')}")
        else:
            lines.append("No tasks in progress.")
        lines.append("")

        if summary.blockers:
            lines.append("## 🚫 Blockers")
            lines.append("")
            for blocker in summary.blockers:
                lines.append(f"- {blocker}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Generated by PM App*")

        # Save to file
        summary_path = journal.get_summary_file_path()
        summary_path.write_text("\n".join(lines))

    def get_quarterly_summary(self, year: int, quarter: int) -> Dict:
        """Get summary for a quarter (Q1-Q4).

        Args:
            year: Year
            quarter: Quarter number (1-4)

        Returns:
            Dictionary with quarterly statistics
        """
        # Determine weeks in quarter
        quarter_start_month = (quarter - 1) * 3 + 1
        quarter_start = datetime(year, quarter_start_month, 1)
        quarter_end = datetime(year, quarter_start_month + 2, 1) + timedelta(days=90)

        # Get all weeks in quarter
        current_date = quarter_start
        weekly_summaries = []

        while current_date <= quarter_end:
            year_week, week_num = get_week_for_date(current_date)
            journal = WeeklyJournal(year_week, week_num, self.journal_dir)

            if journal.exists():
                tasks_by_id = {t.id: t for t in self.task_manager.get_all_tasks()}
                journal.load(tasks_by_id)

                if journal.summary:
                    weekly_summaries.append(journal.summary)

            current_date += timedelta(days=7)

        # Aggregate stats
        total_completed = set()
        total_in_progress = set()
        all_blockers = []

        for summary in weekly_summaries:
            total_completed.update(summary.tasks_completed)
            total_in_progress.update(summary.tasks_in_progress)
            all_blockers.extend(summary.blockers)

        return {
            "year": year,
            "quarter": quarter,
            "weeks_tracked": len(weekly_summaries),
            "total_completed": len(total_completed),
            "total_in_progress": len(total_in_progress),
            "blockers": all_blockers,
            "completed_tasks": list(total_completed),
            "in_progress_tasks": list(total_in_progress),
        }
