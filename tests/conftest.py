"""Shared test fixtures for PM app tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from pm.core.task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency
from pm.core.storage import TaskStorage
from pm.core.manager import TaskManager
from pm.utils.config import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    return Config(
        data_dir=str(temp_dir),
        storage_mode="multi_file",
    )


@pytest.fixture
def storage(temp_dir):
    """Create a TaskStorage instance for testing."""
    return TaskStorage(data_dir=str(temp_dir), storage_mode="multi_file")


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        title="Test Task",
        description="This is a test task",
        type=TaskType.DAT_TICKET,
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
        check_frequency=CheckFrequency.WEEKLY,
        tags=["test", "sample"],
    )


@pytest.fixture
def multiple_tasks():
    """Create multiple sample tasks."""
    return [
        Task(
            title="DAT Ticket Task",
            type=TaskType.DAT_TICKET,
            priority=TaskPriority.HIGH,
            status=TaskStatus.TODO,
        ),
        Task(
            title="Cross Team Task",
            type=TaskType.CROSS_TEAM,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.WAITING,
        ),
        Task(
            title="Project Task",
            type=TaskType.PROJECT,
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
            eta=datetime(2026, 3, 31, 17, 0, 0),
        ),
        Task(
            title="Training Run",
            type=TaskType.TRAINING_RUN,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO,
            notify_at=datetime(2026, 1, 15, 10, 0, 0),
        ),
    ]


@pytest.fixture
def manager(temp_dir, monkeypatch):
    """Create a TaskManager instance for testing."""
    # Mock get_config to return test config
    test_cfg = Config(
        data_dir=str(temp_dir),
        storage_mode="multi_file",
    )

    def mock_get_config(*args, **kwargs):
        return test_cfg

    monkeypatch.setattr("pm.core.manager.get_config", mock_get_config)

    return TaskManager()
