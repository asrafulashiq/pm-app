"""Tests for MCP task tools."""

import pytest
from datetime import datetime

from pm.mcp.tools.task_tools import (
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    add_task_note,
    mark_task_done,
    mark_task_in_progress,
)


class TestCreateTask:
    """Test create_task MCP tool."""

    def test_create_task_basic(self, mcp_manager):
        """Test creating a basic task."""
        result = create_task(title="Test Task")

        assert result["title"] == "Test Task"
        assert result["description"] == ""
        assert result["type"] == "general"
        assert result["status"] == "todo"
        assert result["priority"] == "medium"
        assert result["check_frequency"] == "weekly"
        assert "id" in result
        assert result["tags"] == []
        assert result["dependencies"] == []

    def test_create_task_with_all_fields(self, mcp_manager):
        """Test creating a task with all fields."""
        result = create_task(
            title="DAT Ticket Task",
            description="Review labeling quality",
            task_type="dat_ticket",
            priority="high",
            status="in_progress",
            check_frequency="daily",
            eta="2026-01-15T17:00:00",
            notify_at="2026-01-15T16:00:00",
            tags=["urgent", "labeling"],
            dependencies=["task-abc123"],
        )

        assert result["title"] == "DAT Ticket Task"
        assert result["description"] == "Review labeling quality"
        assert result["type"] == "dat_ticket"
        assert result["status"] == "in_progress"
        assert result["priority"] == "high"
        assert result["check_frequency"] == "daily"
        assert result["eta"] == "2026-01-15T17:00:00"
        assert result["notify_at"] == "2026-01-15T16:00:00"
        assert result["tags"] == ["urgent", "labeling"]
        assert result["dependencies"] == ["task-abc123"]

    def test_create_task_with_invalid_type(self, mcp_manager):
        """Test creating task with invalid type raises error."""
        with pytest.raises(ValueError):
            create_task(title="Bad Task", task_type="invalid_type")

    def test_create_task_with_invalid_priority(self, mcp_manager):
        """Test creating task with invalid priority raises error."""
        with pytest.raises(ValueError):
            create_task(title="Bad Task", priority="super_high")

    def test_create_task_with_invalid_status(self, mcp_manager):
        """Test creating task with invalid status raises error."""
        with pytest.raises(ValueError):
            create_task(title="Bad Task", status="completed")

    def test_create_task_with_invalid_check_frequency(self, mcp_manager):
        """Test creating task with invalid check frequency raises error."""
        with pytest.raises(ValueError):
            create_task(title="Bad Task", check_frequency="hourly")

    def test_create_task_with_invalid_eta(self, mcp_manager):
        """Test creating task with invalid ETA format."""
        # Invalid datetime should return None for eta
        result = create_task(title="Task", eta="not-a-date")
        assert result["eta"] is None


class TestListTasks:
    """Test list_tasks MCP tool."""

    def test_list_tasks_no_filter(self, mcp_manager):
        """Test listing all tasks without filters."""
        # Create some tasks
        create_task(title="Task 1", status="todo")
        create_task(title="Task 2", status="in_progress")
        create_task(title="Task 3", status="done")

        result = list_tasks()

        assert isinstance(result, list)
        assert len(result) == 3
        titles = [task["title"] for task in result]
        assert "Task 1" in titles
        assert "Task 2" in titles
        assert "Task 3" in titles

    def test_list_tasks_with_status_filter(self, mcp_manager):
        """Test listing tasks filtered by status."""
        create_task(title="Todo Task", status="todo")
        create_task(title="In Progress Task", status="in_progress")
        create_task(title="Done Task", status="done")

        result = list_tasks(status="in_progress")

        assert len(result) == 1
        assert result[0]["title"] == "In Progress Task"
        assert result[0]["status"] == "in_progress"

    def test_list_tasks_with_type_filter(self, mcp_manager):
        """Test listing tasks filtered by type."""
        create_task(title="DAT Task", task_type="dat_ticket")
        create_task(title="Project Task", task_type="project")
        create_task(title="General Task", task_type="general")

        result = list_tasks(task_type="dat_ticket")

        assert len(result) == 1
        assert result[0]["title"] == "DAT Task"
        assert result[0]["type"] == "dat_ticket"

    def test_list_tasks_with_priority_filter(self, mcp_manager):
        """Test listing tasks filtered by priority."""
        create_task(title="High Priority", priority="high")
        create_task(title="Medium Priority", priority="medium")
        create_task(title="Low Priority", priority="low")

        result = list_tasks(priority="high")

        assert len(result) == 1
        assert result[0]["title"] == "High Priority"
        assert result[0]["priority"] == "high"

    def test_list_tasks_with_tags_filter(self, mcp_manager):
        """Test listing tasks filtered by tags."""
        create_task(title="Tagged Task 1", tags=["urgent", "review"])
        create_task(title="Tagged Task 2", tags=["review"])
        create_task(title="Untagged Task", tags=[])

        result = list_tasks(tags=["urgent"])

        assert len(result) == 1
        assert result[0]["title"] == "Tagged Task 1"

    def test_list_tasks_with_search(self, mcp_manager):
        """Test listing tasks with search term."""
        create_task(title="Review DAT-12345", description="Data labeling review")
        create_task(title="Update model", description="Train new model")
        create_task(title="Meeting notes", description="Weekly sync")

        result = list_tasks(search="review")

        assert len(result) == 1
        assert "Review" in result[0]["title"]

    def test_list_tasks_empty(self, mcp_manager):
        """Test listing tasks when none exist."""
        result = list_tasks()

        assert result == []

    def test_list_tasks_with_multiple_filters(self, mcp_manager):
        """Test listing tasks with multiple filters combined."""
        create_task(title="High Priority DAT", task_type="dat_ticket", priority="high", status="todo")
        create_task(title="High Priority Project", task_type="project", priority="high", status="todo")
        create_task(title="Low Priority DAT", task_type="dat_ticket", priority="low", status="todo")

        result = list_tasks(task_type="dat_ticket", priority="high")

        assert len(result) == 1
        assert result[0]["title"] == "High Priority DAT"


class TestGetTask:
    """Test get_task MCP tool."""

    def test_get_task_exists(self, mcp_manager):
        """Test getting an existing task."""
        created = create_task(title="Test Task", description="Test description")
        task_id = created["id"]

        result = get_task(task_id)

        assert result is not None
        assert result["id"] == task_id
        assert result["title"] == "Test Task"
        assert result["description"] == "Test description"

    def test_get_task_not_found(self, mcp_manager):
        """Test getting a non-existent task."""
        result = get_task("nonexistent-id")

        assert result is None

    def test_get_task_with_notes(self, mcp_manager):
        """Test getting task with notes."""
        created = create_task(title="Task with notes")
        task_id = created["id"]

        # Add notes
        add_task_note(task_id, "First note")
        add_task_note(task_id, "Second note")

        result = get_task(task_id)

        assert len(result["notes"]) == 2
        assert "First note" in result["notes"][0]
        assert "Second note" in result["notes"][1]


class TestUpdateTask:
    """Test update_task MCP tool."""

    def test_update_task_title(self, mcp_manager):
        """Test updating task title."""
        created = create_task(title="Original Title")
        task_id = created["id"]

        result = update_task(task_id, title="Updated Title")

        assert result is not None
        assert result["title"] == "Updated Title"

    def test_update_task_status(self, mcp_manager):
        """Test updating task status."""
        created = create_task(title="Task", status="todo")
        task_id = created["id"]

        result = update_task(task_id, status="in_progress")

        assert result["status"] == "in_progress"

    def test_update_task_multiple_fields(self, mcp_manager):
        """Test updating multiple task fields."""
        created = create_task(title="Task", priority="low", status="todo")
        task_id = created["id"]

        result = update_task(
            task_id,
            title="Updated Task",
            priority="high",
            status="in_progress",
            tags=["updated"],
        )

        assert result["title"] == "Updated Task"
        assert result["priority"] == "high"
        assert result["status"] == "in_progress"
        assert result["tags"] == ["updated"]

    def test_update_task_not_found(self, mcp_manager):
        """Test updating non-existent task."""
        result = update_task("nonexistent-id", title="New Title")

        assert result is None

    def test_update_task_with_eta(self, mcp_manager):
        """Test updating task ETA."""
        created = create_task(title="Task")
        task_id = created["id"]

        result = update_task(task_id, eta="2026-01-20T12:00:00")

        assert result["eta"] == "2026-01-20T12:00:00"

    def test_update_task_clear_dependencies(self, mcp_manager):
        """Test clearing task dependencies."""
        created = create_task(title="Task", dependencies=["task-1", "task-2"])
        task_id = created["id"]

        result = update_task(task_id, dependencies=[])

        assert result["dependencies"] == []


class TestDeleteTask:
    """Test delete_task MCP tool."""

    def test_delete_task_exists(self, mcp_manager):
        """Test deleting an existing task."""
        created = create_task(title="Task to delete")
        task_id = created["id"]

        result = delete_task(task_id)

        assert result is True

        # Verify task is gone
        assert get_task(task_id) is None

    def test_delete_task_not_found(self, mcp_manager):
        """Test deleting non-existent task."""
        result = delete_task("nonexistent-id")

        assert result is False


class TestAddTaskNote:
    """Test add_task_note MCP tool."""

    def test_add_task_note(self, mcp_manager):
        """Test adding a note to a task."""
        created = create_task(title="Task")
        task_id = created["id"]

        result = add_task_note(task_id, "This is a test note")

        assert result is not None
        assert len(result["notes"]) == 1
        assert "This is a test note" in result["notes"][0]

    def test_add_multiple_notes(self, mcp_manager):
        """Test adding multiple notes to a task."""
        created = create_task(title="Task")
        task_id = created["id"]

        add_task_note(task_id, "First note")
        add_task_note(task_id, "Second note")
        result = add_task_note(task_id, "Third note")

        assert len(result["notes"]) == 3

    def test_add_note_to_nonexistent_task(self, mcp_manager):
        """Test adding note to non-existent task."""
        result = add_task_note("nonexistent-id", "Note")

        assert result is None


class TestMarkTaskDone:
    """Test mark_task_done MCP tool."""

    def test_mark_task_done(self, mcp_manager):
        """Test marking a task as done."""
        created = create_task(title="Task", status="in_progress")
        task_id = created["id"]

        result = mark_task_done(task_id)

        assert result is not None
        assert result["status"] == "done"

    def test_mark_task_done_already_done(self, mcp_manager):
        """Test marking an already done task."""
        created = create_task(title="Task", status="done")
        task_id = created["id"]

        result = mark_task_done(task_id)

        assert result["status"] == "done"

    def test_mark_task_done_not_found(self, mcp_manager):
        """Test marking non-existent task as done."""
        result = mark_task_done("nonexistent-id")

        assert result is None


class TestMarkTaskInProgress:
    """Test mark_task_in_progress MCP tool."""

    def test_mark_task_in_progress(self, mcp_manager):
        """Test marking a task as in progress."""
        created = create_task(title="Task", status="todo")
        task_id = created["id"]

        result = mark_task_in_progress(task_id)

        assert result is not None
        assert result["status"] == "in_progress"

    def test_mark_task_in_progress_already_in_progress(self, mcp_manager):
        """Test marking an already in-progress task."""
        created = create_task(title="Task", status="in_progress")
        task_id = created["id"]

        result = mark_task_in_progress(task_id)

        assert result["status"] == "in_progress"

    def test_mark_task_in_progress_not_found(self, mcp_manager):
        """Test marking non-existent task as in progress."""
        result = mark_task_in_progress("nonexistent-id")

        assert result is None
