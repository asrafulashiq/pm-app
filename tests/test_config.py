"""Tests for Configuration."""

import pytest
import yaml
from pathlib import Path

from pm.utils.config import (
    Config,
    ConfigManager,
    EmailConfig,
    TerminalConfig,
    NotificationConfig,
    SchedulerConfig,
    DefaultsConfig,
)


class TestConfigDataClasses:
    """Test configuration dataclasses."""

    def test_email_config_defaults(self):
        """Test EmailConfig default values."""
        config = EmailConfig()

        assert config.enabled is True
        assert config.smtp_server == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.sender == ""
        assert config.password == ""
        assert config.recipient == ""

    def test_terminal_config_defaults(self):
        """Test TerminalConfig default values."""
        config = TerminalConfig()

        assert config.enabled is True
        assert config.show_on_login is True

    def test_scheduler_config_defaults(self):
        """Test SchedulerConfig default values."""
        config = SchedulerConfig()

        assert config.check_interval == 3600
        assert config.daily_summary_time == "09:00"
        assert config.weekly_summary_day == "Monday"

    def test_defaults_config_defaults(self):
        """Test DefaultsConfig default values."""
        config = DefaultsConfig()

        assert config.check_frequency == "weekly"
        assert config.priority == "medium"

    def test_config_defaults(self):
        """Test Config default values."""
        config = Config()

        assert config.data_dir == "~/pm-data"
        assert config.storage_mode == "multi_file"
        assert isinstance(config.notifications, NotificationConfig)
        assert isinstance(config.scheduler, SchedulerConfig)
        assert isinstance(config.defaults, DefaultsConfig)

    def test_config_data_path(self, temp_dir):
        """Test Config.data_path property."""
        config = Config(data_dir=str(temp_dir))
        assert config.data_path == temp_dir


class TestConfigManager:
    """Test ConfigManager class."""

    def test_config_manager_no_file(self, temp_dir):
        """Test ConfigManager with no config file (uses defaults)."""
        # Use non-existent path
        config_file = temp_dir / "nonexistent.yaml"

        manager = ConfigManager(config_file=str(config_file))

        assert manager.config is not None
        assert manager.config.data_dir == "~/pm-data"

    def test_config_manager_load_file(self, temp_dir):
        """Test ConfigManager loading from file."""
        # Create config file
        config_file = temp_dir / "config.yaml"
        config_data = {
            "data_dir": str(temp_dir / "tasks"),
            "storage_mode": "single_file",
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.test.com",
                },
            },
            "defaults": {
                "priority": "high",
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file=str(config_file))

        assert manager.config.data_dir == str(temp_dir / "tasks")
        assert manager.config.storage_mode == "single_file"
        assert manager.config.notifications.email.enabled is False
        assert manager.config.notifications.email.smtp_server == "smtp.test.com"
        assert manager.config.defaults.priority == "high"

    def test_config_manager_save(self, temp_dir):
        """Test saving configuration."""
        config_file = temp_dir / "config.yaml"

        manager = ConfigManager(config_file=str(config_file))

        # Modify config
        manager.config.data_dir = str(temp_dir / "my-tasks")
        manager.config.notifications.email.sender = "test@example.com"

        # Save
        manager.save_config()

        # Verify file was created
        assert config_file.exists()

        # Load and verify
        new_manager = ConfigManager(config_file=str(config_file))
        assert new_manager.config.data_dir == str(temp_dir / "my-tasks")
        assert new_manager.config.notifications.email.sender == "test@example.com"

    def test_config_manager_partial_config(self, temp_dir):
        """Test loading partial config (missing fields use defaults)."""
        config_file = temp_dir / "config.yaml"

        # Minimal config
        config_data = {
            "data_dir": str(temp_dir),
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file=str(config_file))

        # Specified field
        assert manager.config.data_dir == str(temp_dir)

        # Default fields
        assert manager.config.storage_mode == "multi_file"
        assert manager.config.scheduler.check_interval == 3600

    def test_config_manager_invalid_yaml(self, temp_dir):
        """Test handling of invalid YAML file."""
        config_file = temp_dir / "config.yaml"

        # Write invalid YAML
        config_file.write_text("invalid: yaml: content: [[[")

        # Should use defaults instead of crashing
        manager = ConfigManager(config_file=str(config_file))

        assert manager.config.data_dir == "~/pm-data"

    def test_config_manager_nested_notifications(self, temp_dir):
        """Test loading nested notification config."""
        config_file = temp_dir / "config.yaml"

        config_data = {
            "notifications": {
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender": "user@example.com",
                    "password": "secret",
                    "recipient": "user@example.com",
                },
                "terminal": {
                    "enabled": False,
                    "show_on_login": False,
                },
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file=str(config_file))

        assert manager.config.notifications.email.enabled is True
        assert manager.config.notifications.email.smtp_server == "smtp.gmail.com"
        assert manager.config.notifications.email.sender == "user@example.com"
        assert manager.config.notifications.terminal.enabled is False
        assert manager.config.notifications.terminal.show_on_login is False

    def test_config_manager_scheduler_settings(self, temp_dir):
        """Test loading scheduler settings."""
        config_file = temp_dir / "config.yaml"

        config_data = {
            "scheduler": {
                "check_interval": 7200,
                "daily_summary_time": "08:30",
                "weekly_summary_day": "Friday",
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file=str(config_file))

        assert manager.config.scheduler.check_interval == 7200
        assert manager.config.scheduler.daily_summary_time == "08:30"
        assert manager.config.scheduler.weekly_summary_day == "Friday"

    def test_config_roundtrip(self, temp_dir):
        """Test saving and loading config preserves all data."""
        config_file = temp_dir / "config.yaml"

        # Create manager with custom config
        manager = ConfigManager(config_file=str(config_file))
        manager.config.data_dir = str(temp_dir / "data")
        manager.config.storage_mode = "single_file"
        manager.config.notifications.email.enabled = True
        manager.config.notifications.email.sender = "test@example.com"
        manager.config.scheduler.check_interval = 1800
        manager.config.defaults.priority = "low"

        # Save
        manager.save_config()

        # Load fresh
        new_manager = ConfigManager(config_file=str(config_file))

        # Verify all fields
        assert new_manager.config.data_dir == str(temp_dir / "data")
        assert new_manager.config.storage_mode == "single_file"
        assert new_manager.config.notifications.email.enabled is True
        assert new_manager.config.notifications.email.sender == "test@example.com"
        assert new_manager.config.scheduler.check_interval == 1800
        assert new_manager.config.defaults.priority == "low"

    def test_get_config(self, temp_dir):
        """Test get_config convenience function."""
        from pm.utils.config import get_config

        config_file = temp_dir / "config.yaml"
        config_data = {"data_dir": str(temp_dir)}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = get_config(config_file=str(config_file))

        assert isinstance(config, Config)
        assert config.data_dir == str(temp_dir)
