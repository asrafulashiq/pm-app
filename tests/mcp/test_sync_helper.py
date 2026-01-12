"""Tests for MCP sync helper and auto-sync functionality."""

import pytest
from pathlib import Path

from pm.mcp.tools.sync_helper import sync_before_read, sync_before_write, get_synced_manager
from pm.mcp.tools import list_tasks, create_task, get_task, sync_journal
from pm.core.journal import get_current_week


class TestSyncBeforeRead:
    """Test sync_before_read function."""

    def test_sync_before_read_creates_tasks_from_journal(self, journal_with_tasks):
        """Test that sync_before_read creates tasks from NEW: entries in journal."""
        # Before sync, task files shouldn't exist
        tasks_dir = journal_with_tasks["journal_path"].parent.parent / "tasks"

        # Call sync_before_read
        manager = sync_before_read()

        # After sync, tasks should be created
        tasks = manager.get_all_tasks()
        assert len(tasks) == 2

        titles = [t.title for t in tasks]
        assert "First test task" in titles
        assert "Second test task" in titles

    def test_sync_before_read_returns_manager(self, journal_mode_manager):
        """Test that sync_before_read returns a TaskManager instance."""
        from pm.core.manager import TaskManager

        manager = sync_before_read()
        assert isinstance(manager, TaskManager)


class TestSyncBeforeWrite:
    """Test sync_before_write function."""

    def test_sync_before_write_syncs_journal(self, journal_with_tasks):
        """Test that sync_before_write syncs journal before write operations."""
        # Call sync_before_write
        manager, journal_manager = sync_before_write()

        # Tasks should be created from journal
        tasks = manager.get_all_tasks()
        assert len(tasks) == 2

    def test_sync_before_write_returns_both_managers(self, journal_mode_manager):
        """Test that sync_before_write returns TaskManager and JournalManager."""
        from pm.core.manager import TaskManager
        from pm.core.journal_manager import JournalManager

        manager, journal_manager = sync_before_write()
        assert isinstance(manager, TaskManager)
        assert isinstance(journal_manager, JournalManager)


class TestGetSyncedManager:
    """Test get_synced_manager function."""

    def test_get_synced_manager_returns_sync_result(self, journal_with_tasks):
        """Test that get_synced_manager returns sync results."""
        manager, sync_result = get_synced_manager()

        # Should have created 2 tasks
        assert "created" in sync_result
        assert len(sync_result["created"]) == 2

    def test_get_synced_manager_handles_empty_journal(self, journal_mode_manager, mcp_temp_dir):
        """Test get_synced_manager with empty/no journal."""
        # No journal file exists
        manager, sync_result = get_synced_manager()

        # Should return empty results
        assert sync_result["created"] == []
        assert sync_result["deleted"] == []


class TestAutoSyncInMCPTools:
    """Test that MCP tools automatically sync before operations."""

    def test_list_tasks_auto_syncs(self, journal_with_tasks):
        """Test that list_tasks auto-syncs and returns tasks from journal."""
        # list_tasks should auto-sync and return tasks from journal
        tasks = list_tasks()

        assert len(tasks) == 2
        titles = [t["title"] for t in tasks]
        assert "First test task" in titles
        assert "Second test task" in titles

    def test_get_task_auto_syncs(self, journal_with_tasks):
        """Test that get_task auto-syncs before retrieving task."""
        # First, get the task list to get an ID
        tasks = list_tasks()
        task_id = tasks[0]["id"]

        # get_task should work after auto-sync
        task = get_task(task_id)
        assert task is not None
        assert task["id"] == task_id

    def test_create_task_auto_syncs(self, journal_with_tasks):
        """Test that create_task auto-syncs before creating new task.

        Note: Currently, tasks created via MCP are not added to the journal,
        so they will be deleted on the next sync. This test verifies the
        auto-sync happens and the task is created in memory.
        """
        # First sync should create 2 tasks from journal
        tasks_before = list_tasks()
        assert len(tasks_before) == 2

        # Create a new task (should auto-sync first, then create task)
        new_task = create_task(title="New task via MCP", priority="low")
        assert new_task["title"] == "New task via MCP"
        assert "id" in new_task

        # Note: The new task won't persist after next sync because it's not
        # in the journal. This is expected behavior - journal is source of truth.
        # To properly create a task, add it to the journal with NEW: syntax.

    def test_auto_sync_processes_new_entries(self, journal_mode_manager, mcp_temp_dir):
        """Test that auto-sync processes NEW: entries in journal."""
        # Create a journal with NEW: entries
        journal_dir = mcp_temp_dir / "journal"
        journal_dir.mkdir(parents=True, exist_ok=True)

        year, week = get_current_week()
        journal_path = journal_dir / f"{year}-W{week:02d}.md"

        content = f"""# Week {week} - {year}

## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Auto-sync test task (general, high)

---
"""
        journal_path.write_text(content)

        # list_tasks should trigger auto-sync
        tasks = list_tasks()

        assert len(tasks) == 1
        assert tasks[0]["title"] == "Auto-sync test task"

        # Journal should be updated with task ID
        updated_content = journal_path.read_text()
        assert "NEW:" not in updated_content
        assert tasks[0]["id"] in updated_content

    def test_auto_sync_handles_checkbox_changes(self, journal_mode_manager, mcp_temp_dir):
        """Test that auto-sync handles checkbox status changes."""
        # Create a journal and sync to create task
        journal_dir = mcp_temp_dir / "journal"
        journal_dir.mkdir(parents=True, exist_ok=True)

        year, week = get_current_week()
        journal_path = journal_dir / f"{year}-W{week:02d}.md"

        # First, create with unchecked box
        content = f"""# Week {week} - {year}

## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Checkbox test task (general, medium)

---
"""
        journal_path.write_text(content)

        # Sync to create task
        tasks = list_tasks()
        task_id = tasks[0]["id"]

        # Task should be todo status
        task = get_task(task_id)
        assert task["status"] == "todo"

        # Now update journal to check the box
        updated_content = journal_path.read_text()
        checked_content = updated_content.replace("- [ ]", "- [x]")
        journal_path.write_text(checked_content)

        # list_tasks should trigger auto-sync and update status
        tasks = list_tasks()
        task = get_task(task_id)
        assert task["status"] == "done"

    def test_auto_sync_handles_deleted_tasks(self, journal_mode_manager, mcp_temp_dir):
        """Test that auto-sync deletes tasks removed from journal."""
        journal_dir = mcp_temp_dir / "journal"
        journal_dir.mkdir(parents=True, exist_ok=True)

        year, week = get_current_week()
        journal_path = journal_dir / f"{year}-W{week:02d}.md"

        # Create journal with two tasks
        content = f"""# Week {week} - {year}

## Monday, Jan 06

### 📋 Planned
- [ ] NEW: Task to keep (general, high)
- [ ] NEW: Task to delete (general, low)

---
"""
        journal_path.write_text(content)

        # Sync to create tasks
        tasks = list_tasks()
        assert len(tasks) == 2

        # Get task IDs
        task_ids = {t["title"]: t["id"] for t in tasks}

        # Update journal to remove one task
        updated_content = journal_path.read_text()
        lines = updated_content.split("\n")
        lines = [l for l in lines if "Task to delete" not in l]
        journal_path.write_text("\n".join(lines))

        # list_tasks should trigger auto-sync and delete the removed task
        tasks = list_tasks()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task to keep"

        # Deleted task should not be found
        deleted_task = get_task(task_ids["Task to delete"])
        assert deleted_task is None
