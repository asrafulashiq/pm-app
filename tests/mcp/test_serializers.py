"""Tests for MCP serializers."""

import pytest
from datetime import datetime

from pm.core.task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency, Note
from pm.core.journal import DaySection, WeeklySummary
from pm.mcp.serializers import (
    serialize_task,
    serialize_task_list,
    serialize_day_section,
    serialize_weekly_summary,
)


class TestTaskSerialization:
    """Test task serialization."""

    def test_serialize_task_basic(self, sample_mcp_task):
        """Test basic task serialization."""
        result = serialize_task(sample_mcp_task)

        assert result["id"] == "task-test123"
        assert result["title"] == "Test MCP Task"
        assert result["description"] == "Testing MCP serialization"
        assert result["type"] == "dat_ticket"
        assert result["status"] == "in_progress"
        assert result["priority"] == "high"
        assert result["check_frequency"] == "weekly"

    def test_serialize_task_with_timestamps(self, sample_mcp_task):
        """Test task serialization includes timestamps."""
        result = serialize_task(sample_mcp_task)

        assert result["created_at"] == "2026-01-10T10:00:00"
        assert result["updated_at"] == "2026-01-10T15:30:00"
        assert result["eta"] == "2026-01-17T17:00:00"

    def test_serialize_task_with_none_eta(self):
        """Test task serialization with None ETA."""
        task = Task(title="No ETA Task", eta=None)
        result = serialize_task(task)

        assert result["eta"] is None
        assert result["notify_at"] is None
        assert result["last_checked"] is None

    def test_serialize_task_with_tags(self, sample_mcp_task):
        """Test task serialization includes tags."""
        result = serialize_task(sample_mcp_task)

        assert result["tags"] == ["mcp", "test"]

    def test_serialize_task_with_dependencies(self, sample_mcp_task):
        """Test task serialization includes dependencies."""
        result = serialize_task(sample_mcp_task)

        assert result["dependencies"] == ["task-dep1"]

    def test_serialize_task_with_notes(self):
        """Test task serialization with notes."""
        task = Task(title="Task with notes")
        task.add_note("First note")
        task.add_note("Second note")

        result = serialize_task(task)

        assert "notes" in result
        assert len(result["notes"]) == 2
        assert "First note" in result["notes"][0]
        assert "Second note" in result["notes"][1]

    def test_serialize_task_empty_lists(self):
        """Test task serialization with empty lists."""
        task = Task(title="Empty lists")

        result = serialize_task(task)

        assert result["tags"] == []
        assert result["dependencies"] == []
        assert result["notes"] == []

    def test_serialize_task_list(self):
        """Test serializing a list of tasks."""
        tasks = [
            Task(title="Task 1", id="task-1"),
            Task(title="Task 2", id="task-2"),
            Task(title="Task 3", id="task-3"),
        ]

        result = serialize_task_list(tasks)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["id"] == "task-1"
        assert result[1]["id"] == "task-2"
        assert result[2]["id"] == "task-3"

    def test_serialize_task_list_empty(self):
        """Test serializing empty task list."""
        result = serialize_task_list([])

        assert result == []


class TestDaySectionSerialization:
    """Test day section serialization."""

    def test_serialize_day_section(self, sample_day_section):
        """Test day section serialization."""
        result = serialize_day_section(sample_day_section)

        assert result["date"] == "2026-01-10T00:00:00"
        assert result["planned"] == ["task-abc", "task-def"]
        assert result["completed"] == ["task-abc"]
        assert result["blocked"] == ["task-ghi"]
        assert result["notes"] == "Test notes for the day"

    def test_serialize_day_section_empty(self):
        """Test serializing empty day section."""
        day = DaySection(date=datetime(2026, 1, 10))

        result = serialize_day_section(day)

        assert result["date"] == "2026-01-10T00:00:00"
        assert result["planned"] == []
        assert result["completed"] == []
        assert result["blocked"] == []
        assert result["notes"] == ""


class TestWeeklySummarySerialization:
    """Test weekly summary serialization."""

    def test_serialize_weekly_summary(self, sample_weekly_summary):
        """Test weekly summary serialization."""
        result = serialize_weekly_summary(sample_weekly_summary)

        assert result["week_start"] == "2026-01-06T00:00:00"
        assert result["week_end"] == "2026-01-12T00:00:00"
        assert result["tasks_completed"] == ["task-1", "task-2", "task-3"]
        assert result["tasks_in_progress"] == ["task-4", "task-5"]
        assert result["blockers"] == ["Waiting for API access", "Team dependency"]
        assert result["notes"] == "Good progress this week"
        assert result["completion_count"] == 3

    def test_serialize_weekly_summary_empty(self):
        """Test serializing empty weekly summary."""
        summary = WeeklySummary(
            week_start=datetime(2026, 1, 6),
            week_end=datetime(2026, 1, 12),
            tasks_completed=[],
            tasks_in_progress=[],
            blockers=[],
        )

        result = serialize_weekly_summary(summary)

        assert result["tasks_completed"] == []
        assert result["tasks_in_progress"] == []
        assert result["blockers"] == []
        assert result["completion_count"] == 0
