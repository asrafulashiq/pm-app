"""Tests for TaskManager."""

import pytest
from datetime import datetime, timedelta

from pm.core.task import TaskType, TaskStatus, TaskPriority, CheckFrequency


class TestTaskManager:
    """Test TaskManager class."""

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert manager._tasks == {}

    def test_create_task(self, manager):
        """Test creating a task."""
        task = manager.create_task(
            title="Test Task",
            description="Test description",
            task_type=TaskType.DAT_TICKET,
            priority=TaskPriority.HIGH,
        )

        assert task is not None
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.type == TaskType.DAT_TICKET
        assert task.priority == TaskPriority.HIGH
        assert task.id in manager._tasks

    def test_create_task_with_defaults(self, manager):
        """Test creating task uses config defaults."""
        task = manager.create_task(title="Simple Task")

        assert task.priority == TaskPriority.MEDIUM  # default
        assert task.check_frequency == CheckFrequency.WEEKLY  # default
        assert task.status == TaskStatus.TODO

    def test_get_task(self, manager):
        """Test getting a task by ID."""
        task = manager.create_task(title="Test Task")

        retrieved = manager.get_task(task.id)

        assert retrieved is not None
        assert retrieved.id == task.id
        assert retrieved.title == task.title

    def test_get_nonexistent_task(self, manager):
        """Test getting a task that doesn't exist."""
        result = manager.get_task("nonexistent-id")
        assert result is None

    def test_get_all_tasks(self, manager, multiple_tasks):
        """Test getting all tasks."""
        # Create multiple tasks
        for task in multiple_tasks:
            manager._tasks[task.id] = task
            manager.storage.save_task(task)

        all_tasks = manager.get_all_tasks()

        assert len(all_tasks) == len(multiple_tasks)
        assert all(isinstance(t, type(multiple_tasks[0])) for t in all_tasks)

    def test_update_task(self, manager):
        """Test updating a task."""
        task = manager.create_task(title="Original Title")

        updated = manager.update_task(
            task.id,
            title="Updated Title",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.priority == TaskPriority.HIGH

    def test_update_nonexistent_task(self, manager):
        """Test updating a task that doesn't exist."""
        result = manager.update_task("nonexistent-id", title="New Title")
        assert result is None

    def test_update_task_partial(self, manager):
        """Test partial task update (only some fields)."""
        task = manager.create_task(
            title="Original",
            priority=TaskPriority.LOW,
            status=TaskStatus.TODO,
        )

        # Update only priority
        updated = manager.update_task(task.id, priority=TaskPriority.HIGH)

        assert updated.title == "Original"  # unchanged
        assert updated.status == TaskStatus.TODO  # unchanged
        assert updated.priority == TaskPriority.HIGH  # changed

    def test_delete_task(self, manager):
        """Test deleting a task."""
        task = manager.create_task(title="To Delete")

        result = manager.delete_task(task.id)

        assert result is True
        assert task.id not in manager._tasks
        assert manager.get_task(task.id) is None

    def test_delete_nonexistent_task(self, manager):
        """Test deleting a task that doesn't exist."""
        result = manager.delete_task("nonexistent-id")
        assert result is False

    def test_add_note(self, manager):
        """Test adding a note to a task."""
        task = manager.create_task(title="Task with note")

        updated = manager.add_note(task.id, "This is a note")

        assert updated is not None
        assert len(updated.notes) == 1
        assert updated.notes[0].content == "This is a note"

    def test_add_note_to_nonexistent_task(self, manager):
        """Test adding note to nonexistent task."""
        result = manager.add_note("nonexistent-id", "Note")
        assert result is None

    def test_mark_done(self, manager):
        """Test marking task as done."""
        task = manager.create_task(title="To Complete")

        completed = manager.mark_done(task.id)

        assert completed is not None
        assert completed.status == TaskStatus.DONE

    def test_mark_in_progress(self, manager):
        """Test marking task as in progress."""
        task = manager.create_task(title="To Start")

        started = manager.mark_in_progress(task.id)

        assert started is not None
        assert started.status == TaskStatus.IN_PROGRESS

    def test_filter_by_status(self, manager, multiple_tasks):
        """Test filtering tasks by status."""
        for task in multiple_tasks:
            manager._tasks[task.id] = task

        # Filter by TODO
        todo_tasks = manager.filter_tasks(status=TaskStatus.TODO)
        assert all(t.status == TaskStatus.TODO for t in todo_tasks)

        # Filter by WAITING
        waiting_tasks = manager.filter_tasks(status=TaskStatus.WAITING)
        assert all(t.status == TaskStatus.WAITING for t in waiting_tasks)

    def test_filter_by_type(self, manager, multiple_tasks):
        """Test filtering tasks by type."""
        for task in multiple_tasks:
            manager._tasks[task.id] = task

        dat_tasks = manager.filter_tasks(task_type=TaskType.DAT_TICKET)
        assert all(t.type == TaskType.DAT_TICKET for t in dat_tasks)

    def test_filter_by_priority(self, manager, multiple_tasks):
        """Test filtering tasks by priority."""
        for task in multiple_tasks:
            manager._tasks[task.id] = task

        high_priority = manager.filter_tasks(priority=TaskPriority.HIGH)
        assert all(t.priority == TaskPriority.HIGH for t in high_priority)

    def test_filter_by_tags(self, manager):
        """Test filtering tasks by tags."""
        task1 = manager.create_task(title="Task 1", tags=["urgent", "dat"])
        task2 = manager.create_task(title="Task 2", tags=["dat"])
        task3 = manager.create_task(title="Task 3", tags=["training"])

        # Filter by single tag
        dat_tasks = manager.filter_tasks(tags=["dat"])
        assert len(dat_tasks) == 2

        # Filter by tag that doesn't exist
        none_tasks = manager.filter_tasks(tags=["nonexistent"])
        assert len(none_tasks) == 0

    def test_filter_by_search(self, manager):
        """Test searching tasks by title/description."""
        task1 = manager.create_task(title="DAT Ticket Check", description="Check labeling")
        task2 = manager.create_task(title="Training Run", description="WaitNet training")
        task3 = manager.create_task(title="Review", description="Review DAT results")
        task4 = manager.create_task(title="Model Refactor", description="Start training new model")

        # Search for "DAT"
        results = manager.filter_tasks(search="DAT")
        assert len(results) == 2

        # Search for "training" (case insensitive) - should match task2 and task4
        results = manager.filter_tasks(search="training")
        assert len(results) == 2

    def test_filter_combined(self, manager):
        """Test filtering with multiple criteria."""
        task1 = manager.create_task(
            title="High Priority DAT",
            task_type=TaskType.DAT_TICKET,
            priority=TaskPriority.HIGH,
            status=TaskStatus.TODO,
        )
        task2 = manager.create_task(
            title="Medium Priority DAT",
            task_type=TaskType.DAT_TICKET,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO,
        )

        # Filter by type and priority
        results = manager.filter_tasks(
            task_type=TaskType.DAT_TICKET,
            priority=TaskPriority.HIGH,
        )

        assert len(results) == 1
        assert results[0].id == task1.id

    def test_get_overdue_tasks(self, manager):
        """Test getting overdue tasks."""
        # Create task with past ETA
        task1 = manager.create_task(
            title="Overdue Task",
            eta=datetime.now() - timedelta(days=1),
        )

        # Create task with future ETA
        task2 = manager.create_task(
            title="Future Task",
            eta=datetime.now() + timedelta(days=1),
        )

        overdue = manager.get_overdue_tasks()

        assert len(overdue) == 1
        assert overdue[0].id == task1.id

    def test_get_tasks_needing_check(self, manager):
        """Test getting tasks that need status check."""
        # Task never checked
        task1 = manager.create_task(title="Never Checked")

        # Task checked recently
        task2 = manager.create_task(title="Recently Checked")
        task2.last_checked = datetime.now()
        manager._tasks[task2.id] = task2

        # Task checked long ago
        task3 = manager.create_task(title="Checked Long Ago")
        task3.last_checked = datetime.now() - timedelta(days=10)
        manager._tasks[task3.id] = task3

        needs_check = manager.get_tasks_needing_check()

        # task1 and task3 should need check
        assert len(needs_check) >= 2

    def test_get_tasks_needing_notification(self, manager):
        """Test getting tasks that need notification."""
        # Task with past notify_at
        task1 = manager.create_task(
            title="Needs Notification",
            notify_at=datetime.now() - timedelta(hours=1),
        )

        # Task with future notify_at
        task2 = manager.create_task(
            title="Future Notification",
            notify_at=datetime.now() + timedelta(hours=1),
        )

        needs_notify = manager.get_tasks_needing_notification()

        assert len(needs_notify) == 1
        assert needs_notify[0].id == task1.id

    def test_get_summary(self, manager, multiple_tasks):
        """Test getting summary statistics."""
        for task in multiple_tasks:
            manager._tasks[task.id] = task

        summary = manager.get_summary()

        assert summary["total"] == len(multiple_tasks)
        assert "by_status" in summary
        assert "by_priority" in summary
        assert "by_type" in summary
        assert "overdue" in summary
        assert "needs_check" in summary

        # Check counts
        assert summary["by_status"]["todo"] >= 1
        assert summary["by_type"]["dat_ticket"] >= 1

    def test_reload_tasks(self, manager):
        """Test reloading tasks from storage."""
        # Create task
        task = manager.create_task(title="Original Task")

        # Manually modify storage
        task.title = "Modified Title"
        manager.storage.save_task(task)

        # Reload
        manager.reload_tasks()

        # Should have the modified version
        reloaded = manager.get_task(task.id)
        assert reloaded.title == "Modified Title"

    def test_task_persistence(self, manager):
        """Test that tasks persist to storage."""
        task = manager.create_task(
            title="Persistent Task",
            description="Should be saved",
            priority=TaskPriority.HIGH,
        )

        # Check file exists
        assert manager.storage.task_exists(task.id)

        # Load from storage directly
        loaded_tasks = manager.storage.load_all_tasks()
        assert task.id in loaded_tasks
        assert loaded_tasks[task.id].title == "Persistent Task"
