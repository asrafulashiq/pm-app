"""Configuration management for PM app."""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class EmailConfig:
    """Email notification configuration."""
    enabled: bool = True
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender: str = ""
    password: str = ""
    recipient: str = ""


@dataclass
class TerminalConfig:
    """Terminal notification configuration."""
    enabled: bool = True
    show_on_login: bool = True


@dataclass
class NotificationConfig:
    """Notification settings."""
    email: EmailConfig = field(default_factory=EmailConfig)
    terminal: TerminalConfig = field(default_factory=TerminalConfig)


@dataclass
class SchedulerConfig:
    """Background scheduler configuration."""
    check_interval: int = 3600  # seconds
    daily_summary_time: str = "09:00"
    weekly_summary_day: str = "Monday"


@dataclass
class DefaultsConfig:
    """Default values for new tasks."""
    check_frequency: str = "weekly"
    priority: str = "medium"


@dataclass
class Config:
    """Main configuration."""
    data_dir: str = "~/pm-data"
    storage_mode: str = "multi_file"
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

    @property
    def data_path(self) -> Path:
        """Get expanded data directory path."""
        return Path(self.data_dir).expanduser()


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize config manager.

        Args:
            config_file: Path to config file. If None, uses default locations.
        """
        self.config_file = self._find_config_file(config_file)
        self.config = self._load_config()

    def _find_config_file(self, config_file: Optional[str]) -> Path:
        """Find configuration file.

        Looks in:
        1. Provided path
        2. ~/.config/pm/config.yaml
        3. Current directory/config.yaml
        """
        if config_file:
            return Path(config_file).expanduser()

        # Check standard locations
        locations = [
            Path.home() / ".config" / "pm" / "config.yaml",
            Path.cwd() / "config.yaml",
        ]

        for location in locations:
            if location.exists():
                return location

        # Return default location (may not exist yet)
        return Path.home() / ".config" / "pm" / "config.yaml"

    def _load_config(self) -> Config:
        """Load configuration from file or use defaults."""
        if not self.config_file.exists():
            # Use default configuration
            return Config()

        try:
            with open(self.config_file, "r") as f:
                data = yaml.safe_load(f) or {}

            return self._parse_config(data)

        except Exception as e:
            print(f"Warning: Failed to load config from {self.config_file}: {e}")
            print("Using default configuration")
            return Config()

    def _parse_config(self, data: Dict[str, Any]) -> Config:
        """Parse configuration dictionary."""
        # Parse email config
        email_data = data.get("notifications", {}).get("email", {})
        email_config = EmailConfig(
            enabled=email_data.get("enabled", True),
            smtp_server=email_data.get("smtp_server", "smtp.gmail.com"),
            smtp_port=email_data.get("smtp_port", 587),
            sender=email_data.get("sender", ""),
            password=email_data.get("password", ""),
            recipient=email_data.get("recipient", ""),
        )

        # Parse terminal config
        terminal_data = data.get("notifications", {}).get("terminal", {})
        terminal_config = TerminalConfig(
            enabled=terminal_data.get("enabled", True),
            show_on_login=terminal_data.get("show_on_login", True),
        )

        # Parse notification config
        notification_config = NotificationConfig(
            email=email_config,
            terminal=terminal_config,
        )

        # Parse scheduler config
        scheduler_data = data.get("scheduler", {})
        scheduler_config = SchedulerConfig(
            check_interval=scheduler_data.get("check_interval", 3600),
            daily_summary_time=scheduler_data.get("daily_summary_time", "09:00"),
            weekly_summary_day=scheduler_data.get("weekly_summary_day", "Monday"),
        )

        # Parse defaults config
        defaults_data = data.get("defaults", {})
        defaults_config = DefaultsConfig(
            check_frequency=defaults_data.get("check_frequency", "weekly"),
            priority=defaults_data.get("priority", "medium"),
        )

        return Config(
            data_dir=data.get("data_dir", "~/pm-data"),
            storage_mode=data.get("storage_mode", "multi_file"),
            notifications=notification_config,
            scheduler=scheduler_config,
            defaults=defaults_config,
        )

    def save_config(self) -> None:
        """Save current configuration to file."""
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert config to dict
        data = {
            "data_dir": self.config.data_dir,
            "storage_mode": self.config.storage_mode,
            "notifications": {
                "email": {
                    "enabled": self.config.notifications.email.enabled,
                    "smtp_server": self.config.notifications.email.smtp_server,
                    "smtp_port": self.config.notifications.email.smtp_port,
                    "sender": self.config.notifications.email.sender,
                    "password": self.config.notifications.email.password,
                    "recipient": self.config.notifications.email.recipient,
                },
                "terminal": {
                    "enabled": self.config.notifications.terminal.enabled,
                    "show_on_login": self.config.notifications.terminal.show_on_login,
                },
            },
            "scheduler": {
                "check_interval": self.config.scheduler.check_interval,
                "daily_summary_time": self.config.scheduler.daily_summary_time,
                "weekly_summary_day": self.config.scheduler.weekly_summary_day,
            },
            "defaults": {
                "check_frequency": self.config.defaults.check_frequency,
                "priority": self.config.defaults.priority,
            },
        }

        # Write to file
        with open(self.config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_config(self) -> Config:
        """Get current configuration."""
        return self.config


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """Get or create global config manager."""
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager(config_file)

    return _config_manager


def get_config(config_file: Optional[str] = None) -> Config:
    """Get configuration."""
    return get_config_manager(config_file).get_config()
