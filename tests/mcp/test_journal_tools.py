"""Tests for MCP journal tools."""

import pytest
from datetime import datetime, timedelta

from pm.mcp.tools.task_tools import create_task
from pm.mcp.tools.journal_tools import (
    start_journal_day,
    end_journal_day,
    get_current_journal,
    sync_journal,
    generate_week_summary,
    get_quarterly_summary,
)


class TestStartJournalDay:
    """Test start_journal_day MCP tool."""

    def test_start_journal_day(self, mcp_manager, mcp_temp_dir):
        """Test starting a journal day."""
        # Create some tasks first
        create_task(title="Task 1", status="in_progress")
        create_task(title="Task 2", status="todo")

        result = start_journal_day()

        assert isinstance(result, dict)
        assert "journal_path" in result
        assert "day" in result
        assert "planned_tasks" in result
        assert len(result["planned_tasks"]) >= 2

    def test_start_journal_day_creates_file(self, mcp_manager, mcp_temp_dir):
        """Test that starting journal day creates the journal file."""
        result = start_journal_day()

        # Check that journal file was created
        journal_dir = mcp_temp_dir / "journal"
        assert journal_dir.exists()

        # Journal file should exist (named like 2026-W02.md)
        journal_files = list(journal_dir.glob("*.md"))
        assert len(journal_files) > 0


class TestEndJournalDay:
    """Test end_journal_day MCP tool."""

    def test_end_journal_day(self, mcp_manager, mcp_temp_dir):
        """Test ending a journal day."""
        # Start a day first
        start_journal_day()

        # End the day
        result = end_journal_day()

        assert isinstance(result, dict)
        assert "day" in result
        assert "completed_tasks" in result

    def test_end_journal_day_without_start(self, mcp_manager, mcp_temp_dir):
        """Test ending a day without starting it first."""
        # Should handle gracefully or start implicitly
        result = end_journal_day()

        assert isinstance(result, dict)


class TestGetCurrentJournal:
    """Test get_current_journal MCP tool."""

    def test_get_current_journal(self, mcp_manager, mcp_temp_dir):
        """Test getting current journal."""
        # Start a journal day
        start_journal_day()

        result = get_current_journal()

        assert isinstance(result, dict)
        assert "journal_path" in result
        assert "content" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0

    def test_get_current_journal_without_journal(self, mcp_manager, mcp_temp_dir):
        """Test getting journal when none exists."""
        result = get_current_journal()

        # Should create a new journal or return info about missing journal
        assert isinstance(result, dict)

    def test_get_current_journal_has_days(self, mcp_manager, mcp_temp_dir):
        """Test that journal content includes day sections."""
        start_journal_day()

        result = get_current_journal()

        content = result["content"]
        # Should have day headers like ## Monday or ## Tuesday
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        has_day_header = any(f"## {day}" in content for day in days_of_week)
        assert has_day_header


class TestSyncJournal:
    """Test sync_journal MCP tool."""

    def test_sync_journal(self, mcp_manager, mcp_temp_dir):
        """Test syncing journal with task statuses."""
        # Create tasks
        task1 = create_task(title="Task 1", status="todo")
        task2 = create_task(title="Task 2", status="done")

        # Start journal
        start_journal_day()

        # Sync journal
        result = sync_journal()

        assert isinstance(result, dict)
        assert "synced_tasks" in result

    def test_sync_journal_without_journal(self, mcp_manager, mcp_temp_dir):
        """Test syncing when no journal exists."""
        result = sync_journal()

        # Should handle gracefully
        assert isinstance(result, dict)


class TestGenerateWeekSummary:
    """Test generate_week_summary MCP tool."""

    def test_generate_week_summary(self, mcp_manager, mcp_temp_dir):
        """Test generating weekly summary."""
        # Create some completed tasks
        create_task(title="Completed Task 1", status="done")
        create_task(title="Completed Task 2", status="done")
        create_task(title="In Progress Task", status="in_progress")

        # Start and end a day to create journal content
        start_journal_day()
        end_journal_day()

        result = generate_week_summary()

        assert isinstance(result, dict)
        assert "summary" in result or "week_start" in result

    def test_generate_week_summary_without_journal(self, mcp_manager, mcp_temp_dir):
        """Test generating summary when no journal exists."""
        result = generate_week_summary()

        # Should handle gracefully or create empty summary
        assert isinstance(result, dict)


class TestGetQuarterlySummary:
    """Test get_quarterly_summary MCP tool."""

    def test_get_quarterly_summary(self, mcp_manager, mcp_temp_dir):
        """Test getting quarterly summary."""
        # Create some tasks with different timestamps
        create_task(title="Q1 Task", status="done")

        result = get_quarterly_summary(year=2026, quarter=1)

        assert isinstance(result, dict)
        assert "year" in result
        assert "quarter" in result
        assert "total_completed" in result or "achievements" in result

    def test_get_quarterly_summary_current_quarter(self, mcp_manager, mcp_temp_dir):
        """Test getting current quarter summary."""
        # Should default to current quarter
        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1

        result = get_quarterly_summary()

        assert isinstance(result, dict)
        # Should use current year/quarter if not specified

    def test_get_quarterly_summary_empty(self, mcp_manager, mcp_temp_dir):
        """Test quarterly summary with no completed tasks."""
        result = get_quarterly_summary(year=2025, quarter=1)

        assert isinstance(result, dict)
        assert result.get("total_completed", 0) == 0 or isinstance(result.get("achievements", []), list)

    def test_get_quarterly_summary_invalid_quarter(self, mcp_manager, mcp_temp_dir):
        """Test quarterly summary with invalid quarter."""
        with pytest.raises(ValueError):
            get_quarterly_summary(year=2026, quarter=5)

    def test_get_quarterly_summary_invalid_year(self, mcp_manager, mcp_temp_dir):
        """Test quarterly summary with invalid year."""
        with pytest.raises(ValueError):
            get_quarterly_summary(year=1900, quarter=1)
