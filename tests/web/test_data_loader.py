"""Tests for JournalDataLoader."""

import pytest
from datetime import datetime

from pm.web.data_loader import JournalDataLoader, TaskDisplayData, DaySectionData, WeeklyJournalData


class TestJournalDataLoader:
    """Test cases for JournalDataLoader."""

    def test_get_current_week(self, web_manager, web_temp_dir):
        """Test get_current_week returns valid year and week."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        year, week = loader.get_current_week()

        assert isinstance(year, int)
        assert isinstance(week, int)
        assert 1 <= week <= 53
        assert year >= 2020

    def test_get_available_weeks_empty(self, web_manager, web_temp_dir):
        """Test get_available_weeks with no journals."""
        journal_dir = web_temp_dir / "journal"
        journal_dir.mkdir(parents=True, exist_ok=True)

        loader = JournalDataLoader(journal_dir=str(journal_dir))
        weeks = loader.get_available_weeks()

        assert weeks == []

    def test_get_available_weeks_with_journals(self, web_manager, web_temp_dir, sample_journal):
        """Test get_available_weeks finds journal files."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        weeks = loader.get_available_weeks()

        assert len(weeks) == 1
        year, week, display = weeks[0]
        assert year == 2026
        assert week == 2
        assert "2026-W02" in display

    def test_get_journal_data_not_found(self, web_manager, web_temp_dir):
        """Test get_journal_data returns None for missing journal."""
        journal_dir = web_temp_dir / "journal"
        journal_dir.mkdir(parents=True, exist_ok=True)

        loader = JournalDataLoader(journal_dir=str(journal_dir))
        result = loader.get_journal_data(2026, 99)

        assert result is None

    def test_get_journal_data_found(self, web_manager, web_temp_dir, sample_journal, sample_tasks):
        """Test get_journal_data returns journal data."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        result = loader.get_journal_data(2026, 2)

        assert result is not None
        assert isinstance(result, WeeklyJournalData)
        assert result.year == 2026
        assert result.week == 2
        assert len(result.days) == 7  # Monday to Sunday

    def test_journal_data_has_week_info(self, web_manager, web_temp_dir, sample_journal):
        """Test journal data includes week range info."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        result = loader.get_journal_data(2026, 2)

        assert result.week_range_str is not None
        assert "Jan" in result.week_range_str  # Week 2 of 2026 is in January

    def test_journal_data_has_day_sections(self, web_manager, web_temp_dir, sample_journal, sample_tasks):
        """Test journal data includes day sections with tasks."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        result = loader.get_journal_data(2026, 2)

        # Find Monday's data
        monday_key = sample_journal.get_day_key(sample_journal.week_start)
        assert monday_key in result.days

        monday_data = result.days[monday_key]
        assert isinstance(monday_data, DaySectionData)
        assert monday_data.day_name == "Monday"
        assert len(monday_data.planned_tasks) > 0

    def test_task_display_data_structure(self, web_manager, web_temp_dir, sample_journal, sample_tasks):
        """Test TaskDisplayData has correct fields."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        result = loader.get_journal_data(2026, 2)

        monday_key = sample_journal.get_day_key(sample_journal.week_start)
        monday_data = result.days[monday_key]

        # Check planned tasks
        assert len(monday_data.planned_tasks) > 0
        task = monday_data.planned_tasks[0]

        assert isinstance(task, TaskDisplayData)
        assert task.id.startswith("task-")
        assert task.title is not None
        assert task.type in ["dat_ticket", "cross_team", "project", "training_run", "general"]
        assert task.priority in ["high", "medium", "low"]
        assert task.status in ["todo", "in_progress", "waiting", "blocked", "done"]

    def test_completed_tasks_tracked(self, web_manager, web_temp_dir, sample_journal, sample_tasks):
        """Test completed tasks are correctly tracked."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        result = loader.get_journal_data(2026, 2)

        monday_key = sample_journal.get_day_key(sample_journal.week_start)
        monday_data = result.days[monday_key]

        # First task should be completed
        assert len(monday_data.completed_tasks) == 1
        completed_task = monday_data.completed_tasks[0]
        assert completed_task.is_completed is True

    def test_total_counts(self, web_manager, web_temp_dir, sample_journal, sample_tasks):
        """Test total planned and completed counts."""
        loader = JournalDataLoader(journal_dir=str(web_temp_dir / "journal"))
        result = loader.get_journal_data(2026, 2)

        # 3 tasks planned on Monday
        assert result.total_planned == 3
        # 1 task completed
        assert result.total_completed == 1


class TestTaskDisplayData:
    """Test TaskDisplayData dataclass."""

    def test_create_task_display_data(self):
        """Test creating TaskDisplayData."""
        data = TaskDisplayData(
            id="task-abc123",
            title="Test Task",
            type="project",
            priority="high",
            status="in_progress",
            is_completed=False,
            eta="2026-01-15",
            notes_count=2
        )

        assert data.id == "task-abc123"
        assert data.title == "Test Task"
        assert data.is_completed is False
        assert data.eta == "2026-01-15"

    def test_task_display_data_optional_fields(self):
        """Test TaskDisplayData with optional fields."""
        data = TaskDisplayData(
            id="task-xyz",
            title="Simple Task",
            type="general",
            priority="low",
            status="todo",
            is_completed=False
        )

        assert data.eta is None
        assert data.notes_count == 0


class TestDaySectionData:
    """Test DaySectionData dataclass."""

    def test_create_day_section_data(self):
        """Test creating DaySectionData."""
        data = DaySectionData(
            date=datetime(2026, 1, 6),
            day_name="Monday",
            date_str="Jan 06",
            planned_tasks=[],
            completed_tasks=[],
            blocked_tasks=[],
            in_progress_tasks=[],
            notes="Test notes"
        )

        assert data.day_name == "Monday"
        assert data.notes == "Test notes"


class TestWeeklyJournalData:
    """Test WeeklyJournalData dataclass."""

    def test_create_weekly_journal_data(self):
        """Test creating WeeklyJournalData."""
        data = WeeklyJournalData(
            year=2026,
            week=2,
            week_start=datetime(2026, 1, 6),
            week_end=datetime(2026, 1, 12),
            week_range_str="Jan 06 - Jan 12, 2026",
            days={},
            total_planned=10,
            total_completed=7
        )

        assert data.year == 2026
        assert data.week == 2
        assert data.total_planned == 10
        assert data.total_completed == 7
