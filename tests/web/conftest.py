"""Test fixtures for web module tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from pm.core.task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency
from pm.core.journal import WeeklyJournal, DaySection
from pm.core.manager import TaskManager
from pm.core.journal_manager import JournalManager


@pytest.fixture
def web_temp_dir():
    """Create a temporary directory for web test data."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def web_manager(web_temp_dir, monkeypatch):
    """TaskManager with test data directory for web tests."""
    import pm.utils.config as config_module
    from pm.utils.config import Config, ConfigManager

    # Reset the global config manager singleton
    config_module._config_manager = None

    test_cfg = Config(
        data_dir=str(web_temp_dir),
        storage_mode="multi_file",
    )

    # Create a test config manager
    test_config_manager = ConfigManager.__new__(ConfigManager)
    test_config_manager.config = test_cfg
    test_config_manager.config_file = web_temp_dir / "test_config.yaml"

    # Patch the global singleton
    config_module._config_manager = test_config_manager

    def mock_get_config(*args, **kwargs):
        return test_cfg

    monkeypatch.setattr("pm.utils.config.get_config", mock_get_config)

    manager = TaskManager()
    yield manager
    config_module._config_manager = None


@pytest.fixture
def sample_tasks(web_manager):
    """Create sample tasks for testing."""
    tasks = []

    task1 = web_manager.create_task(
        title="Review PR #123",
        task_type=TaskType.DAT_TICKET,
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
    )
    tasks.append(task1)

    task2 = web_manager.create_task(
        title="Fix authentication bug",
        task_type=TaskType.PROJECT,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.IN_PROGRESS,
    )
    tasks.append(task2)

    task3 = web_manager.create_task(
        title="Write documentation",
        task_type=TaskType.GENERAL,
        priority=TaskPriority.LOW,
        status=TaskStatus.TODO,
    )
    tasks.append(task3)

    return tasks


@pytest.fixture
def sample_journal(web_temp_dir, sample_tasks):
    """Create a sample journal with tasks for testing."""
    journal_dir = web_temp_dir / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)

    # Create a journal for week 2, 2026
    journal = WeeklyJournal(2026, 2, journal_dir)

    # Add Monday section with tasks
    monday = journal.week_start
    day_section = journal.add_day_section(monday)
    day_section.planned = [t.id for t in sample_tasks]
    day_section.completed = [sample_tasks[0].id]  # First task is done

    # Save the journal
    tasks_by_id = {t.id: t for t in sample_tasks}
    journal.save(tasks_by_id)

    return journal
