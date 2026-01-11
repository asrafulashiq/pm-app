"""Tests for Task model."""

import pytest
from datetime import datetime, timedelta

from pm.core.task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency, Note


class TestNote:
    """Test Note class."""

    def test_note_creation(self):
        """Test creating a note."""
        now = datetime.now()
        note = Note(timestamp=now, content="Test note")

        assert note.timestamp == now
        assert note.content == "Test note"

    def test_note_string_format(self):
        """Test note string representation."""
        note = Note(timestamp=datetime(2026, 1, 10, 15, 30), content="Test note")
        expected = "- 2026-01-10 15:30: Test note"

        assert str(note) == expected

    def test_note_from_string(self):
        """Test parsing note from string."""
        note_str = "- 2026-01-10 15:30: Test note content"
        note = Note.from_string(note_str)

        assert note.timestamp == datetime(2026, 1, 10, 15, 30)
        assert note.content == "Test note content"

    def test_note_from_string_invalid(self):
        """Test parsing invalid note string."""
        note_str = "Invalid note format"
        note = Note.from_string(note_str)

        # Should create note with current time
        assert note.content == "Invalid note format"
        assert isinstance(note.timestamp, datetime)


class TestTask:
    """Test Task class."""

    def test_task_creation(self, sample_task):
        """Test creating a task."""
        assert sample_task.title == "Test Task"
        assert sample_task.description == "This is a test task"
        assert sample_task.type == TaskType.DAT_TICKET
        assert sample_task.priority == TaskPriority.HIGH
        assert sample_task.status == TaskStatus.TODO
        assert sample_task.check_frequency == CheckFrequency.WEEKLY
        assert "test" in sample_task.tags
        assert "sample" in sample_task.tags

    def test_task_auto_fields(self):
        """Test auto-generated fields."""
        task = Task(title="Test")

        assert task.id.startswith("task-")
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.type == TaskType.GENERAL
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM

    def test_add_note(self, sample_task):
        """Test adding a note to task."""
        initial_notes = len(sample_task.notes)
        sample_task.add_note("First note")

        assert len(sample_task.notes) == initial_notes + 1
        assert sample_task.notes[-1].content == "First note"

    def test_is_overdue_no_eta(self, sample_task):
        """Test is_overdue when no ETA set."""
        assert not sample_task.is_overdue()

    def test_is_overdue_past_eta(self, sample_task):
        """Test is_overdue when ETA is in the past."""
        sample_task.eta = datetime.now() - timedelta(days=1)
        assert sample_task.is_overdue()

    def test_is_overdue_future_eta(self, sample_task):
        """Test is_overdue when ETA is in the future."""
        sample_task.eta = datetime.now() + timedelta(days=1)
        assert not sample_task.is_overdue()

    def test_is_overdue_done_task(self, sample_task):
        """Test is_overdue for done task (should be False)."""
        sample_task.eta = datetime.now() - timedelta(days=1)
        sample_task.status = TaskStatus.DONE
        assert not sample_task.is_overdue()

    def test_needs_check_never_checked(self, sample_task):
        """Test needs_check when never checked."""
        assert sample_task.needs_check()

    def test_needs_check_done_task(self, sample_task):
        """Test needs_check for done task (should be False)."""
        sample_task.status = TaskStatus.DONE
        assert not sample_task.needs_check()

    def test_needs_check_weekly(self, sample_task):
        """Test needs_check with weekly frequency."""
        sample_task.check_frequency = CheckFrequency.WEEKLY

        # Just checked - shouldn't need check
        sample_task.last_checked = datetime.now()
        assert not sample_task.needs_check()

        # Checked 8 days ago - should need check
        sample_task.last_checked = datetime.now() - timedelta(days=8)
        assert sample_task.needs_check()

    def test_needs_check_daily(self, sample_task):
        """Test needs_check with daily frequency."""
        sample_task.check_frequency = CheckFrequency.DAILY

        # Checked 2 days ago - should need check
        sample_task.last_checked = datetime.now() - timedelta(days=2)
        assert sample_task.needs_check()

    def test_needs_notification_no_notify_at(self, sample_task):
        """Test needs_notification when no notify_at set."""
        assert not sample_task.needs_notification()

    def test_needs_notification_future(self, sample_task):
        """Test needs_notification when notify_at is in future."""
        sample_task.notify_at = datetime.now() + timedelta(hours=1)
        assert not sample_task.needs_notification()

    def test_needs_notification_past(self, sample_task):
        """Test needs_notification when notify_at is in past."""
        sample_task.notify_at = datetime.now() - timedelta(hours=1)
        assert sample_task.needs_notification()

    def test_needs_notification_done_task(self, sample_task):
        """Test needs_notification for done task (should be False)."""
        sample_task.notify_at = datetime.now() - timedelta(hours=1)
        sample_task.status = TaskStatus.DONE
        assert not sample_task.needs_notification()

    def test_mark_checked(self, sample_task):
        """Test mark_checked method."""
        before = datetime.now()
        sample_task.mark_checked()
        after = datetime.now()

        assert sample_task.last_checked is not None
        assert before <= sample_task.last_checked <= after
        assert before <= sample_task.updated_at <= after

    def test_to_dict(self, sample_task):
        """Test converting task to dictionary."""
        data = sample_task.to_dict()

        assert data["id"] == sample_task.id
        assert data["title"] == "Test Task"
        assert data["type"] == "dat_ticket"
        assert data["status"] == "todo"
        assert data["priority"] == "high"
        assert data["check_frequency"] == "weekly"
        assert data["tags"] == ["test", "sample"]

    def test_from_dict(self, sample_task):
        """Test creating task from dictionary."""
        data = sample_task.to_dict()
        reconstructed = Task.from_dict(data)

        assert reconstructed.id == sample_task.id
        assert reconstructed.title == sample_task.title
        assert reconstructed.type == sample_task.type
        assert reconstructed.status == sample_task.status
        assert reconstructed.priority == sample_task.priority

    def test_from_dict_with_notes(self):
        """Test creating task from dict with notes."""
        data = {
            "id": "task-123",
            "title": "Test",
            "type": "general",
            "status": "todo",
            "priority": "medium",
            "created_at": "2026-01-10T10:00:00",
            "updated_at": "2026-01-10T11:00:00",
            "eta": None,
            "check_frequency": "weekly",
            "last_checked": None,
            "notify_at": None,
            "dependencies": [],
            "tags": [],
            "notes": [
                "- 2026-01-10 10:30: First note",
                "- 2026-01-10 11:00: Second note",
            ],
        }

        task = Task.from_dict(data)
        assert len(task.notes) == 2
        assert task.notes[0].content == "First note"
        assert task.notes[1].content == "Second note"

    def test_task_string_representation(self, sample_task):
        """Test task string representation."""
        result = str(sample_task)

        assert sample_task.id in result
        assert "Test Task" in result
        # Should have emoji indicators
        assert "⭕" in result or "🔄" in result  # Status emoji
        assert "🔴" in result or "🟡" in result  # Priority emoji

    def test_task_roundtrip(self, sample_task):
        """Test task can be converted to dict and back."""
        sample_task.add_note("Test note")
        sample_task.eta = datetime(2026, 2, 15, 10, 0, 0)

        # Convert to dict and back
        data = sample_task.to_dict()
        reconstructed = Task.from_dict(data)

        # Verify all fields match
        assert reconstructed.id == sample_task.id
        assert reconstructed.title == sample_task.title
        assert reconstructed.description == sample_task.description
        assert reconstructed.type == sample_task.type
        assert reconstructed.status == sample_task.status
        assert reconstructed.priority == sample_task.priority
        assert reconstructed.check_frequency == sample_task.check_frequency
        assert reconstructed.tags == sample_task.tags
        assert len(reconstructed.notes) == len(sample_task.notes)
