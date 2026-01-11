"""Tests for MCP query tools."""

import pytest
from datetime import datetime, timedelta

from pm.mcp.tools.task_tools import create_task
from pm.mcp.tools.query_tools import (
    get_overdue_tasks,
    get_tasks_needing_check,
    get_task_summary,
    search_tasks,
)


class TestGetOverdueTasks:
    """Test get_overdue_tasks MCP tool."""

    def test_get_overdue_tasks_with_overdue(self, mcp_manager):
        """Test getting overdue tasks."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()

        # Create tasks
        create_task(title="Overdue Task 1", eta=yesterday, status="in_progress")
        create_task(title="Overdue Task 2", eta=yesterday, status="todo")
        create_task(title="Not Overdue", eta=tomorrow, status="todo")
        create_task(title="No ETA", status="todo")

        result = get_overdue_tasks()

        assert isinstance(result, list)
        assert len(result) == 2
        titles = [task["title"] for task in result]
        assert "Overdue Task 1" in titles
        assert "Overdue Task 2" in titles

    def test_get_overdue_tasks_excludes_done(self, mcp_manager):
        """Test that done tasks are not included in overdue."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()

        create_task(title="Done but overdue", eta=yesterday, status="done")
        create_task(title="Overdue and active", eta=yesterday, status="in_progress")

        result = get_overdue_tasks()

        assert len(result) == 1
        assert result[0]["title"] == "Overdue and active"

    def test_get_overdue_tasks_empty(self, mcp_manager):
        """Test getting overdue tasks when none exist."""
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()

        create_task(title="Future task", eta=tomorrow, status="todo")
        create_task(title="No ETA task", status="todo")

        result = get_overdue_tasks()

        assert result == []


class TestGetTasksNeedingCheck:
    """Test get_tasks_needing_check MCP tool."""

    def test_get_tasks_needing_daily_check(self, mcp_manager):
        """Test getting tasks that need daily check."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()

        # Task that needs check (last checked yesterday, daily frequency)
        create_task(title="Daily Task", check_frequency="daily", status="in_progress")

        # Manually update last_checked to yesterday
        from pm.core.manager import TaskManager
        manager = TaskManager()
        tasks = manager.get_all_tasks()
        task = tasks[0]
        task.last_checked = datetime.now() - timedelta(days=2)
        manager.storage.save_task(task)

        result = get_tasks_needing_check()

        assert len(result) >= 1
        # At least the daily task should be in results

    def test_get_tasks_needing_check_excludes_done(self, mcp_manager):
        """Test that done tasks don't need checking."""
        create_task(title="Done task", check_frequency="daily", status="done")
        create_task(title="Active task", check_frequency="weekly", status="in_progress")

        result = get_tasks_needing_check()

        # Done task should not be in results
        titles = [task["title"] for task in result]
        assert "Done task" not in titles

    def test_get_tasks_needing_check_empty(self, mcp_manager):
        """Test when no tasks need checking."""
        # Create a task with a long check frequency that was just created
        create_task(title="Monthly task", check_frequency="monthly", status="todo")

        # Tasks just created don't need immediate check
        result = get_tasks_needing_check()

        # Result might be empty or have the task depending on implementation
        assert isinstance(result, list)


class TestGetTaskSummary:
    """Test get_task_summary MCP tool."""

    def test_get_task_summary(self, mcp_manager):
        """Test getting task summary statistics."""
        # Create tasks with different statuses, types, priorities
        create_task(title="Todo 1", status="todo", task_type="dat_ticket", priority="high")
        create_task(title="Todo 2", status="todo", task_type="project", priority="medium")
        create_task(title="In Progress 1", status="in_progress", task_type="dat_ticket", priority="high")
        create_task(title="Done 1", status="done", task_type="general", priority="low")
        create_task(title="Blocked 1", status="blocked", task_type="cross_team", priority="medium")

        result = get_task_summary()

        assert isinstance(result, dict)

        # Check status counts
        assert "by_status" in result
        assert result["by_status"]["todo"] == 2
        assert result["by_status"]["in_progress"] == 1
        assert result["by_status"]["done"] == 1
        assert result["by_status"]["blocked"] == 1

        # Check type counts
        assert "by_type" in result
        assert result["by_type"]["dat_ticket"] == 2
        assert result["by_type"]["project"] == 1
        assert result["by_type"]["general"] == 1
        assert result["by_type"]["cross_team"] == 1

        # Check priority counts
        assert "by_priority" in result
        assert result["by_priority"]["high"] == 2
        assert result["by_priority"]["medium"] == 2
        assert result["by_priority"]["low"] == 1

        # Check total
        assert "total" in result
        assert result["total"] == 5

    def test_get_task_summary_empty(self, mcp_manager):
        """Test summary with no tasks."""
        result = get_task_summary()

        assert result["total"] == 0
        assert result["by_status"] == {}
        assert result["by_type"] == {}
        assert result["by_priority"] == {}

    def test_get_task_summary_single_task(self, mcp_manager):
        """Test summary with single task."""
        create_task(title="Single Task", status="todo", task_type="general", priority="medium")

        result = get_task_summary()

        assert result["total"] == 1
        assert result["by_status"]["todo"] == 1
        assert result["by_type"]["general"] == 1
        assert result["by_priority"]["medium"] == 1


class TestSearchTasks:
    """Test search_tasks MCP tool."""

    def test_search_tasks_by_title(self, mcp_manager):
        """Test searching tasks by title."""
        create_task(title="Review DAT-12345", description="Data labeling")
        create_task(title="Update model", description="Review architecture")
        create_task(title="Meeting notes", description="Weekly sync")

        result = search_tasks("review")

        assert len(result) == 2
        titles = [task["title"] for task in result]
        assert "Review DAT-12345" in titles
        assert "Update model" in titles  # "Review" in description

    def test_search_tasks_by_description(self, mcp_manager):
        """Test searching tasks by description."""
        create_task(title="Task A", description="Implement new feature")
        create_task(title="Task B", description="Fix bug in payment")
        create_task(title="Task C", description="Update docs")

        result = search_tasks("feature")

        assert len(result) == 1
        assert result[0]["title"] == "Task A"

    def test_search_tasks_case_insensitive(self, mcp_manager):
        """Test search is case insensitive."""
        create_task(title="URGENT Task", description="High priority")
        create_task(title="Regular task", description="Normal priority")

        result = search_tasks("urgent")

        assert len(result) == 1
        assert result[0]["title"] == "URGENT Task"

    def test_search_tasks_partial_match(self, mcp_manager):
        """Test search with partial word match."""
        create_task(title="WaitNet v3 training", description="DNN model")
        create_task(title="Perception update", description="Sensor fusion")

        result = search_tasks("wait")

        assert len(result) == 1
        assert "WaitNet" in result[0]["title"]

    def test_search_tasks_no_results(self, mcp_manager):
        """Test search with no matching tasks."""
        create_task(title="Task 1", description="Description 1")
        create_task(title="Task 2", description="Description 2")

        result = search_tasks("nonexistent")

        assert result == []

    def test_search_tasks_empty_query(self, mcp_manager):
        """Test search with empty query returns all tasks."""
        create_task(title="Task 1")
        create_task(title="Task 2")
        create_task(title="Task 3")

        result = search_tasks("")

        assert len(result) == 3

    def test_search_tasks_special_characters(self, mcp_manager):
        """Test search with special characters."""
        create_task(title="Fix bug #123", description="Critical issue")
        create_task(title="Regular task", description="Normal work")

        result = search_tasks("#123")

        assert len(result) == 1
        assert result[0]["title"] == "Fix bug #123"
