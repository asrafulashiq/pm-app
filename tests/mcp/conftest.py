"""Test fixtures for MCP tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from pm.core.task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency
from pm.core.journal import WeeklyJournal, DaySection, WeeklySummary
from pm.core.manager import TaskManager
from pm.core.journal_manager import JournalManager


@pytest.fixture
def mcp_temp_dir():
    """Create a temporary directory for MCP test data."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path)


@pytest.fixture(autouse=True)
def clean_test_dir(mcp_temp_dir):
    """Clean test directory before each test."""
    # Clean tasks directory before each test
    tasks_dir = mcp_temp_dir / "tasks"
    if tasks_dir.exists():
        shutil.rmtree(tasks_dir)
    tasks_dir.mkdir(parents=True)
    yield


@pytest.fixture
def mcp_manager(mcp_temp_dir, monkeypatch):
    """TaskManager with test data directory."""
    import pm.utils.config as config_module
    from pm.utils.config import Config, ConfigManager

    # Reset the global config manager singleton
    config_module._config_manager = None

    test_cfg = Config(
        data_dir=str(mcp_temp_dir),
        storage_mode="multi_file",
    )

    # Create a test config manager
    test_config_manager = ConfigManager.__new__(ConfigManager)
    test_config_manager.config = test_cfg
    test_config_manager.config_file = mcp_temp_dir / "test_config.yaml"

    # Patch the global singleton
    config_module._config_manager = test_config_manager

    # Also patch get_config to ensure it returns our test config
    def mock_get_config(*args, **kwargs):
        return test_cfg

    monkeypatch.setattr("pm.utils.config.get_config", mock_get_config)

    # Create and return task manager (which will now use test config)
    manager = TaskManager()

    # Reset singleton after test to avoid affecting other tests
    yield manager

    config_module._config_manager = None


@pytest.fixture
def mcp_journal_manager(mcp_manager, mcp_temp_dir):
    """JournalManager with test data directory."""
    return JournalManager(mcp_manager, journal_dir=str(mcp_temp_dir / "journal"))


@pytest.fixture
def sample_mcp_task():
    """Sample task for MCP testing."""
    return Task(
        id="task-test123",
        title="Test MCP Task",
        description="Testing MCP serialization",
        type=TaskType.DAT_TICKET,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        check_frequency=CheckFrequency.WEEKLY,
        created_at=datetime(2026, 1, 10, 10, 0, 0),
        updated_at=datetime(2026, 1, 10, 15, 30, 0),
        eta=datetime(2026, 1, 17, 17, 0, 0),
        tags=["mcp", "test"],
        dependencies=["task-dep1"],
    )


@pytest.fixture
def sample_day_section():
    """Sample day section for testing."""
    return DaySection(
        date=datetime(2026, 1, 10),
        planned=["task-abc", "task-def"],
        completed=["task-abc"],
        blocked=["task-ghi"],
        notes="Test notes for the day"
    )


@pytest.fixture
def sample_weekly_summary():
    """Sample weekly summary for testing."""
    return WeeklySummary(
        week_start=datetime(2026, 1, 6),
        week_end=datetime(2026, 1, 12),
        tasks_completed=["task-1", "task-2", "task-3"],
        tasks_in_progress=["task-4", "task-5"],
        blockers=["Waiting for API access", "Team dependency"],
        notes="Good progress this week"
    )
