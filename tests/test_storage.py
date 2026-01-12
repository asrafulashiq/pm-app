"""Tests for TaskStorage and JournalStorage."""

import pytest
import textwrap
from pathlib import Path
from datetime import datetime

from pm.core.storage import TaskStorage, JournalStorage
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


class TestJournalStorage:
    """Test JournalStorage class."""

    @pytest.fixture
    def journal_storage(self, temp_dir):
        """Create a JournalStorage instance for testing."""
        return JournalStorage(data_dir=str(temp_dir), backup_enabled=False)

    def test_storage_initialization(self, temp_dir):
        """Test storage initialization creates directories."""
        storage = JournalStorage(data_dir=str(temp_dir))

        assert storage.data_dir.exists()
        assert storage.journal_dir.exists()
        assert storage.tasks_dir.exists()

    def test_detect_new_tasks_valid_entries(self, journal_storage):
        """Test detecting valid NEW: entries."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: First task (general, high)
- [ ] NEW: Second task (project, medium)
- [ ] NEW: Third task (dat_ticket, low)
"""
        new_tasks, errors = journal_storage.detect_new_tasks(content)

        assert len(new_tasks) == 3
        assert len(errors) == 0

        assert new_tasks[0]["title"] == "First task"
        assert new_tasks[0]["type"] == "general"
        assert new_tasks[0]["priority"] == "high"

        assert new_tasks[1]["title"] == "Second task"
        assert new_tasks[1]["type"] == "project"
        assert new_tasks[1]["priority"] == "medium"

        assert new_tasks[2]["title"] == "Third task"
        assert new_tasks[2]["type"] == "dat_ticket"
        assert new_tasks[2]["priority"] == "low"

    def test_detect_new_tasks_malformed_missing_format(self, journal_storage):
        """Test detecting malformed NEW: entries missing type/priority."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Task without format
- [ ] NEW: Another task missing parens
"""
        new_tasks, errors = journal_storage.detect_new_tasks(content)

        assert len(new_tasks) == 0
        assert len(errors) == 2

        assert "Line 5" in errors[0]
        assert "Malformed NEW entry" in errors[0]
        assert "Line 6" in errors[1]

    def test_detect_new_tasks_invalid_type(self, journal_storage):
        """Test detecting NEW: entries with invalid task type."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Task with bad type (invalid_type, high)
"""
        new_tasks, errors = journal_storage.detect_new_tasks(content)

        assert len(new_tasks) == 0
        assert len(errors) == 1
        assert "Invalid task type 'invalid_type'" in errors[0]
        assert "Valid types:" in errors[0]

    def test_detect_new_tasks_invalid_priority(self, journal_storage):
        """Test detecting NEW: entries with invalid priority."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Task with bad priority (general, super_high)
"""
        new_tasks, errors = journal_storage.detect_new_tasks(content)

        assert len(new_tasks) == 0
        assert len(errors) == 1
        assert "Invalid priority 'super_high'" in errors[0]
        assert "Valid priorities:" in errors[0]

    def test_detect_new_tasks_mixed_valid_and_invalid(self, journal_storage):
        """Test detecting mix of valid and invalid NEW: entries."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Valid task one (general, high)
- [ ] NEW: Invalid no parens
- [ ] NEW: Invalid type (badtype, medium)
- [ ] NEW: Valid task two (project, low)
- [ ] NEW: Invalid priority (general, badpriority)
"""
        new_tasks, errors = journal_storage.detect_new_tasks(content)

        # Should have 2 valid tasks
        assert len(new_tasks) == 2
        assert new_tasks[0]["title"] == "Valid task one"
        assert new_tasks[1]["title"] == "Valid task two"

        # Should have 3 errors
        assert len(errors) == 3

    def test_detect_new_tasks_includes_line_numbers(self, journal_storage):
        """Test that error messages include line numbers."""
        content = """Line 1
Line 2
Line 3
- [ ] NEW: Bad entry on line 4
Line 5
- [ ] NEW: Another bad entry on line 6
"""
        new_tasks, errors = journal_storage.detect_new_tasks(content)

        assert len(errors) == 2
        assert "Line 4" in errors[0]
        assert "Line 6" in errors[1]

    def test_process_new_task_entries_creates_files(self, journal_storage):
        """Test that process_new_task_entries creates task files."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Task to create (general, high)
"""
        updated_content, created_tasks, errors = journal_storage.process_new_task_entries(content)

        assert len(created_tasks) == 1
        assert len(errors) == 0

        # Task file should be created
        task = created_tasks[0]
        task_path = journal_storage.tasks_dir / f"{task.id}.md"
        assert task_path.exists()

        # Content should be updated with task ID
        assert "NEW:" not in updated_content
        assert task.id in updated_content

    def test_process_new_task_entries_returns_errors(self, journal_storage):
        """Test that process_new_task_entries returns errors for malformed entries."""
        content = """
## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Valid task (general, high)
- [ ] NEW: Malformed entry
- [ ] NEW: Invalid type (badtype, high)
"""
        updated_content, created_tasks, errors = journal_storage.process_new_task_entries(content)

        # Only 1 valid task should be created
        assert len(created_tasks) == 1
        assert created_tasks[0].title == "Valid task"

        # Should have 2 errors
        assert len(errors) == 2

    def test_get_journal_task_ids(self, journal_storage):
        """Test extracting task IDs from journal content."""
        content = textwrap.dedent("""\
            ## Monday, Jan 06

            ### 📋 Planned
            - [ ] task-abc12300: First task (general, high)
            - [x] task-def45600: Second task (project, medium)
            - [ ] task-0a1b2c3d: Third task (general, low)
            """)
        task_ids = journal_storage.get_journal_task_ids(content)

        assert len(task_ids) == 3
        assert "task-abc12300" in task_ids
        assert "task-def45600" in task_ids
        assert "task-0a1b2c3d" in task_ids

    def test_parse_checkboxes(self, journal_storage):
        """Test parsing checkbox states from journal content."""
        content = textwrap.dedent("""\
            - [ ] task-aaa11111: Unchecked task (general, high)
            - [x] task-bbb22222: Checked task (project, medium)
            - [ ] task-ccc33333: Another unchecked (general, low)
            """)
        checkboxes = journal_storage.parse_checkboxes(content)

        assert len(checkboxes) == 3
        assert checkboxes["task-aaa11111"] is False
        assert checkboxes["task-bbb22222"] is True
        assert checkboxes["task-ccc33333"] is False

    def test_detect_deleted_tasks(self, journal_storage):
        """Test detecting tasks deleted from journal."""
        content = textwrap.dedent("""\
            - [ ] task-abc00001: Kept task (general, high)
            """)
        known_ids = {"task-abc00001", "task-abc00002", "task-abc00003"}

        deleted = journal_storage.detect_deleted_tasks(content, known_ids)

        assert len(deleted) == 2
        assert "task-abc00002" in deleted
        assert "task-abc00003" in deleted
        assert "task-abc00001" not in deleted


class TestJournalStorageErrorMessages:
    """Test error message quality for JournalStorage."""

    @pytest.fixture
    def journal_storage(self, temp_dir):
        """Create a JournalStorage instance for testing."""
        return JournalStorage(data_dir=str(temp_dir), backup_enabled=False)

    def test_error_message_includes_expected_format(self, journal_storage):
        """Test that error messages include the expected format."""
        content = """
- [ ] NEW: Bad entry
"""
        _, errors = journal_storage.detect_new_tasks(content)

        assert len(errors) == 1
        assert "Expected format: '- [ ] NEW: Task title (type, priority)'" in errors[0]

    def test_error_message_includes_valid_types(self, journal_storage):
        """Test that error messages list valid task types."""
        content = """
- [ ] NEW: Task with bad type (badtype, high)
"""
        _, errors = journal_storage.detect_new_tasks(content)

        assert len(errors) == 1
        assert "dat_ticket" in errors[0]
        assert "cross_team" in errors[0]
        assert "project" in errors[0]
        assert "training_run" in errors[0]
        assert "general" in errors[0]

    def test_error_message_includes_valid_priorities(self, journal_storage):
        """Test that error messages list valid priorities."""
        content = """
- [ ] NEW: Task with bad priority (general, badpriority)
"""
        _, errors = journal_storage.detect_new_tasks(content)

        assert len(errors) == 1
        assert "high" in errors[0]
        assert "medium" in errors[0]
        assert "low" in errors[0]

    def test_error_message_shows_actual_input(self, journal_storage):
        """Test that error messages show what was actually entered."""
        content = """
- [ ] NEW: My malformed task entry
"""
        _, errors = journal_storage.detect_new_tasks(content)

        assert len(errors) == 1
        assert "- [ ] NEW: My malformed task entry" in errors[0]
