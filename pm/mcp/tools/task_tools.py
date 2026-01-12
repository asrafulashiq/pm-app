"""MCP tools for task management."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dateutil import parser as date_parser

from ...core.manager import TaskManager
from ...core.task import TaskType, TaskStatus, TaskPriority, CheckFrequency
from ..serializers import serialize_task, serialize_task_list
from .sync_helper import sync_before_read, sync_before_write


def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime from string."""
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except Exception:
        return None


def create_task(
    title: str,
    description: str = "",
    task_type: str = "general",
    priority: str = "medium",
    status: str = "todo",
    check_frequency: str = "weekly",
    eta: Optional[str] = None,
    notify_at: Optional[str] = None,
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new task.

    Args:
        title: Task title
        description: Task description
        task_type: Type of task (dat_ticket, cross_team, project, training_run, general)
        priority: Priority (high, medium, low)
        status: Status (todo, in_progress, waiting, blocked, done)
        check_frequency: Check frequency (daily, weekly, biweekly, monthly)
        eta: Expected completion datetime (ISO format)
        notify_at: Notification datetime (ISO format)
        tags: List of tags
        dependencies: List of dependency task IDs

    Returns:
        Serialized task dictionary
    """
    # Auto-sync journal before write operation
    manager, _ = sync_before_write()

    # Parse enums
    task_type_enum = TaskType(task_type)
    priority_enum = TaskPriority(priority)
    status_enum = TaskStatus(status)
    check_freq_enum = CheckFrequency(check_frequency)

    # Parse dates
    eta_dt = _parse_datetime(eta)
    notify_dt = _parse_datetime(notify_at)

    # Create task
    task = manager.create_task(
        title=title,
        description=description,
        task_type=task_type_enum,
        priority=priority_enum,
        status=status_enum,
        check_frequency=check_freq_enum,
        eta=eta_dt,
        notify_at=notify_dt,
        tags=tags or [],
        dependencies=dependencies or [],
    )

    return serialize_task(task)


def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List tasks with optional filters.

    Args:
        status: Filter by status
        task_type: Filter by type
        priority: Filter by priority
        tags: Filter by tags (any match)
        search: Search in title/description

    Returns:
        List of serialized task dictionaries
    """
    # Auto-sync journal before read operation
    manager = sync_before_read()

    # Parse enums if provided
    status_enum = TaskStatus(status) if status else None
    type_enum = TaskType(task_type) if task_type else None
    priority_enum = TaskPriority(priority) if priority else None

    # Filter tasks
    tasks = manager.filter_tasks(
        status=status_enum,
        task_type=type_enum,
        priority=priority_enum,
        tags=tags,
        search=search,
    )

    return serialize_task_list(tasks)


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a task by ID.

    Args:
        task_id: Task ID

    Returns:
        Serialized task dictionary or None if not found
    """
    # Auto-sync journal before read operation
    manager = sync_before_read()
    task = manager.get_task(task_id)

    if task is None:
        return None

    return serialize_task(task)


def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    check_frequency: Optional[str] = None,
    eta: Optional[str] = None,
    notify_at: Optional[str] = None,
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Update a task.

    Args:
        task_id: Task ID
        title: New title
        description: New description
        task_type: New type
        priority: New priority
        status: New status
        check_frequency: New check frequency
        eta: New ETA (ISO format)
        notify_at: New notification time (ISO format)
        tags: New tags
        dependencies: New dependencies

    Returns:
        Serialized updated task or None if not found
    """
    # Auto-sync journal before write operation
    manager, _ = sync_before_write()

    # Parse enums if provided
    type_enum = TaskType(task_type) if task_type else None
    priority_enum = TaskPriority(priority) if priority else None
    status_enum = TaskStatus(status) if status else None
    check_freq_enum = CheckFrequency(check_frequency) if check_frequency else None

    # Parse dates
    eta_dt = _parse_datetime(eta) if eta else None
    notify_dt = _parse_datetime(notify_at) if notify_at else None

    # Update task
    task = manager.update_task(
        task_id=task_id,
        title=title,
        description=description,
        task_type=type_enum,
        priority=priority_enum,
        status=status_enum,
        check_frequency=check_freq_enum,
        eta=eta_dt,
        notify_at=notify_dt,
        tags=tags,
        dependencies=dependencies,
    )

    if task is None:
        return None

    return serialize_task(task)


def delete_task(task_id: str) -> bool:
    """Delete a task.

    Args:
        task_id: Task ID

    Returns:
        True if deleted, False if not found
    """
    # Auto-sync journal before write operation
    manager, _ = sync_before_write()
    return manager.delete_task(task_id)


def add_task_note(task_id: str, note: str) -> Optional[Dict[str, Any]]:
    """Add a note to a task.

    Args:
        task_id: Task ID
        note: Note content

    Returns:
        Serialized updated task or None if not found
    """
    # Auto-sync journal before write operation
    manager, _ = sync_before_write()
    task = manager.add_note(task_id, note)

    if task is None:
        return None

    return serialize_task(task)


def mark_task_done(task_id: str) -> Optional[Dict[str, Any]]:
    """Mark a task as done.

    Args:
        task_id: Task ID

    Returns:
        Serialized updated task or None if not found
    """
    # Auto-sync journal before write operation
    manager, _ = sync_before_write()
    task = manager.mark_done(task_id)

    if task is None:
        return None

    return serialize_task(task)


def mark_task_in_progress(task_id: str) -> Optional[Dict[str, Any]]:
    """Mark a task as in progress.

    Args:
        task_id: Task ID

    Returns:
        Serialized updated task or None if not found
    """
    # Auto-sync journal before write operation
    manager, _ = sync_before_write()
    task = manager.mark_in_progress(task_id)

    if task is None:
        return None

    return serialize_task(task)
