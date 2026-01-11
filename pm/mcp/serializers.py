"""Serializers for converting PM objects to JSON-safe dictionaries."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.task import Task
from ..core.journal import DaySection, WeeklySummary


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string.

    Args:
        dt: Datetime object or None

    Returns:
        ISO format string or None
    """
    if dt is None:
        return None
    return dt.isoformat()


def serialize_task(task: Task) -> Dict[str, Any]:
    """Serialize a Task object to JSON-safe dictionary.

    Args:
        task: Task object to serialize

    Returns:
        Dictionary representation of the task
    """
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "type": task.type.value,
        "status": task.status.value,
        "priority": task.priority.value,
        "check_frequency": task.check_frequency.value,
        "created_at": serialize_datetime(task.created_at),
        "updated_at": serialize_datetime(task.updated_at),
        "eta": serialize_datetime(task.eta),
        "last_checked": serialize_datetime(task.last_checked),
        "notify_at": serialize_datetime(task.notify_at),
        "tags": task.tags,
        "dependencies": task.dependencies,
        "notes": [str(note) for note in task.notes],
    }


def serialize_task_list(tasks: List[Task]) -> List[Dict[str, Any]]:
    """Serialize a list of Task objects.

    Args:
        tasks: List of Task objects

    Returns:
        List of serialized task dictionaries
    """
    return [serialize_task(task) for task in tasks]


def serialize_day_section(day: DaySection) -> Dict[str, Any]:
    """Serialize a DaySection object.

    Args:
        day: DaySection object

    Returns:
        Dictionary representation of the day section
    """
    return {
        "date": serialize_datetime(day.date),
        "planned": day.planned,
        "completed": day.completed,
        "blocked": day.blocked,
        "notes": day.notes,
    }


def serialize_weekly_summary(summary: WeeklySummary) -> Dict[str, Any]:
    """Serialize a WeeklySummary object.

    Args:
        summary: WeeklySummary object

    Returns:
        Dictionary representation of the summary
    """
    return {
        "week_start": serialize_datetime(summary.week_start),
        "week_end": serialize_datetime(summary.week_end),
        "tasks_completed": summary.tasks_completed,
        "tasks_in_progress": summary.tasks_in_progress,
        "blockers": summary.blockers,
        "notes": summary.notes,
        "completion_count": summary.tasks_completed_count(),
    }
