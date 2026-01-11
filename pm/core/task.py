"""Task data model for the PM app."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid


class TaskType(str, Enum):
    """Task type categories."""
    DAT_TICKET = "dat_ticket"
    CROSS_TEAM = "cross_team"
    PROJECT = "project"
    TRAINING_RUN = "training_run"
    GENERAL = "general"


class TaskStatus(str, Enum):
    """Task status options."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CheckFrequency(str, Enum):
    """How often to check task status."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class Note:
    """A timestamped note for a task."""
    timestamp: datetime
    content: str

    def __str__(self) -> str:
        """Format note as markdown bullet point."""
        return f"- {self.timestamp.strftime('%Y-%m-%d %H:%M')}: {self.content}"

    @classmethod
    def from_string(cls, note_str: str) -> "Note":
        """Parse note from markdown format."""
        # Format: "- YYYY-MM-DD HH:MM: content"
        if note_str.startswith("- "):
            note_str = note_str[2:].strip()

        parts = note_str.split(": ", 1)
        if len(parts) == 2:
            timestamp_str, content = parts
            timestamp = datetime.fromisoformat(timestamp_str.strip())
            return cls(timestamp=timestamp, content=content.strip())
        else:
            # If parsing fails, use current time
            return cls(timestamp=datetime.now(), content=note_str)


@dataclass
class Task:
    """Task data model."""

    # Required fields
    title: str

    # Auto-generated
    id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Optional fields with defaults
    description: str = ""
    type: TaskType = TaskType.GENERAL
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    check_frequency: CheckFrequency = CheckFrequency.WEEKLY

    # Timestamps
    eta: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    notify_at: Optional[datetime] = None

    # Relationships and metadata
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)

    def add_note(self, content: str) -> None:
        """Add a timestamped note to the task."""
        note = Note(timestamp=datetime.now(), content=content)
        self.notes.append(note)
        self.updated_at = datetime.now()

    def is_overdue(self) -> bool:
        """Check if task is past its ETA."""
        if self.eta is None or self.status == TaskStatus.DONE:
            return False
        return datetime.now() > self.eta

    def needs_check(self) -> bool:
        """Determine if task needs status check based on check_frequency."""
        if self.status == TaskStatus.DONE:
            return False

        if self.last_checked is None:
            return True

        now = datetime.now()
        delta = now - self.last_checked

        frequency_days = {
            CheckFrequency.DAILY: 1,
            CheckFrequency.WEEKLY: 7,
            CheckFrequency.BIWEEKLY: 14,
            CheckFrequency.MONTHLY: 30,
        }

        if self.check_frequency in frequency_days:
            return delta.days >= frequency_days[self.check_frequency]

        return False

    def needs_notification(self) -> bool:
        """Check if notification should be sent."""
        if self.notify_at is None or self.status == TaskStatus.DONE:
            return False
        return datetime.now() >= self.notify_at

    def mark_checked(self) -> None:
        """Mark task as checked now."""
        self.last_checked = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "eta": self.eta.isoformat() if self.eta else None,
            "check_frequency": self.check_frequency.value,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "notify_at": self.notify_at.isoformat() if self.notify_at else None,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "notes": [str(note) for note in self.notes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary."""
        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        eta = datetime.fromisoformat(data["eta"]) if data.get("eta") else None
        last_checked = datetime.fromisoformat(data["last_checked"]) if data.get("last_checked") else None
        notify_at = datetime.fromisoformat(data["notify_at"]) if data.get("notify_at") else None

        # Parse notes
        notes = [Note.from_string(note_str) for note_str in data.get("notes", [])]

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            type=TaskType(data.get("type", "general")),
            status=TaskStatus(data.get("status", "todo")),
            priority=TaskPriority(data.get("priority", "medium")),
            created_at=created_at,
            updated_at=updated_at,
            eta=eta,
            check_frequency=CheckFrequency(data.get("check_frequency", "weekly")),
            last_checked=last_checked,
            notify_at=notify_at,
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            notes=notes,
        )

    def __str__(self) -> str:
        """String representation for display."""
        status_emoji = {
            TaskStatus.TODO: "⭕",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.WAITING: "⏸️",
            TaskStatus.DONE: "✅",
            TaskStatus.BLOCKED: "🚫",
        }

        priority_emoji = {
            TaskPriority.HIGH: "🔴",
            TaskPriority.MEDIUM: "🟡",
            TaskPriority.LOW: "🟢",
        }

        emoji = status_emoji.get(self.status, "")
        priority = priority_emoji.get(self.priority, "")

        return f"{emoji} {priority} [{self.id}] {self.title}"
