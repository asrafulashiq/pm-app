"""Tests for TaskStorage."""

import pytest
from pathlib import Path
from datetime import datetime

from pm.core.storage import TaskStorage
from pm.core.task import Task, TaskType, TaskStatus, TaskPriority


class TestTaskStorage:
    """Test TaskStorage class."""

    def test_storage_initialization(self, temp_dir):
        """Test storage initialization creates directories."""
        storage = TaskStorage(data_dir=str(temp_dir))

        assert storage.data_dir.exists()
        assert storage.tasks_dir.exists()
        assert storage.storage_mode == "multi_file"

    def test_save_task(self, storage, sample_task):
        """Test saving a task."""
        storage.save_task(sample_task)

        # Check file was created
        task_file = storage.tasks_dir / f"{sample_task.id}.md"
        assert task_file.exists()

    def test_save_and_load_task(self, storage, sample_task):
        """Test saving and loading a task."""
        # Add some data to task
        sample_task.add_note("Test note 1")
        sample_task.add_note("Test note 2")

        # Save task
        storage.save_task(sample_task)

        # Load all tasks
        tasks = storage.load_all_tasks()

        assert sample_task.id in tasks
        loaded_task = tasks[sample_task.id]

        assert loaded_task.title == sample_task.title
        assert loaded_task.description == sample_task.description
        assert loaded_task.type == sample_task.type
        assert loaded_task.status == sample_task.status
        assert loaded_task.priority == sample_task.priority
        assert len(loaded_task.notes) == 2

    def test_load_empty_directory(self, storage):
        """Test loading from empty directory."""
        tasks = storage.load_all_tasks()
        assert tasks == {}

    def test_load_multiple_tasks(self, storage, multiple_tasks):
        """Test loading multiple tasks."""
        # Save multiple tasks
        for task in multiple_tasks:
            storage.save_task(task)

        # Load all
        loaded = storage.load_all_tasks()

        assert len(loaded) == len(multiple_tasks)

        for task in multiple_tasks:
            assert task.id in loaded
            assert loaded[task.id].title == task.title

    def test_delete_task(self, storage, sample_task):
        """Test deleting a task."""
        # Save task first
        storage.save_task(sample_task)

        # Verify it exists
        assert storage.task_exists(sample_task.id)

        # Delete it
        result = storage.delete_task(sample_task.id)

        assert result is True
        assert not storage.task_exists(sample_task.id)

    def test_delete_nonexistent_task(self, storage):
        """Test deleting a task that doesn't exist."""
        result = storage.delete_task("nonexistent-task")
        assert result is False

    def test_task_exists(self, storage, sample_task):
        """Test checking if task exists."""
        assert not storage.task_exists(sample_task.id)

        storage.save_task(sample_task)

        assert storage.task_exists(sample_task.id)

    def test_get_task_file_path(self, storage):
        """Test getting task file path."""
        task_id = "task-123"
        path = storage.get_task_file_path(task_id)

        assert path == storage.tasks_dir / f"{task_id}.md"

    def test_task_with_description(self, storage):
        """Test task with description is saved and loaded correctly."""
        task = Task(
            title="Test Task",
            description="This is a detailed description\nwith multiple lines",
            type=TaskType.PROJECT,
        )

        storage.save_task(task)
        loaded = storage.load_all_tasks()[task.id]

        assert loaded.description == task.description

    def test_task_with_eta(self, storage):
        """Test task with ETA is saved and loaded correctly."""
        task = Task(
            title="Task with ETA",
            eta=datetime(2026, 3, 15, 10, 0, 0),
        )

        storage.save_task(task)
        loaded = storage.load_all_tasks()[task.id]

        assert loaded.eta == task.eta

    def test_task_with_dependencies(self, storage):
        """Test task with dependencies."""
        task = Task(
            title="Dependent Task",
            dependencies=["task-001", "task-002"],
        )

        storage.save_task(task)
        loaded = storage.load_all_tasks()[task.id]

        assert loaded.dependencies == ["task-001", "task-002"]

    def test_task_with_tags(self, storage):
        """Test task with tags."""
        task = Task(
            title="Tagged Task",
            tags=["important", "urgent", "dat"],
        )

        storage.save_task(task)
        loaded = storage.load_all_tasks()[task.id]

        assert loaded.tags == ["important", "urgent", "dat"]

    def test_update_existing_task(self, storage, sample_task):
        """Test updating an existing task."""
        # Save initial version
        storage.save_task(sample_task)

        # Modify task
        sample_task.title = "Updated Title"
        sample_task.status = TaskStatus.IN_PROGRESS
        sample_task.add_note("Updated the task")

        # Save again
        storage.save_task(sample_task)

        # Load and verify
        loaded = storage.load_all_tasks()[sample_task.id]

        assert loaded.title == "Updated Title"
        assert loaded.status == TaskStatus.IN_PROGRESS
        assert len(loaded.notes) == 1

    def test_storage_with_special_characters(self, storage):
        """Test tasks with special characters in title/description."""
        task = Task(
            title="Task: DAT-12345 [URGENT]",
            description="Description with special chars: @#$%^&*()",
        )

        storage.save_task(task)
        loaded = storage.load_all_tasks()[task.id]

        assert loaded.title == task.title
        assert loaded.description == task.description

    def test_corrupted_file_handling(self, storage, sample_task):
        """Test handling of corrupted task file."""
        # Save valid task
        storage.save_task(sample_task)

        # Corrupt the file
        task_file = storage.tasks_dir / f"{sample_task.id}.md"
        task_file.write_text("corrupted content")

        # Loading should not crash, just skip the corrupted file
        tasks = storage.load_all_tasks()

        # The corrupted task may or may not be loaded depending on error handling
        # Main thing is it shouldn't crash
        assert isinstance(tasks, dict)

    def test_markdown_frontmatter_format(self, storage, sample_task):
        """Test that saved files have correct markdown frontmatter format."""
        storage.save_task(sample_task)

        task_file = storage.tasks_dir / f"{sample_task.id}.md"
        content = task_file.read_text()

        # Check it starts with frontmatter
        assert content.startswith("---")

        # Check it has required fields in frontmatter
        assert f"id: {sample_task.id}" in content
        assert f"title: {sample_task.title}" in content
        assert f"type: {sample_task.type.value}" in content
