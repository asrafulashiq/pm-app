"""MCP tools for task queries."""

from typing import Dict, Any, List

from ...core.manager import TaskManager
from ..serializers import serialize_task_list
from .sync_helper import sync_before_read


def get_overdue_tasks() -> List[Dict[str, Any]]:
    """Get all overdue tasks.

    Returns tasks that are past their ETA and not yet done.

    Returns:
        List of serialized overdue task dictionaries
    """
    # Auto-sync journal before read operation
    manager = sync_before_read()
    tasks = manager.get_overdue_tasks()
    return serialize_task_list(tasks)


def get_tasks_needing_check() -> List[Dict[str, Any]]:
    """Get tasks that need periodic check.

    Returns tasks that are due for their periodic check based on
    their check_frequency and last_checked timestamp.

    Returns:
        List of serialized task dictionaries needing check
    """
    # Auto-sync journal before read operation
    manager = sync_before_read()
    tasks = manager.get_tasks_needing_check()
    return serialize_task_list(tasks)


def get_task_summary() -> Dict[str, Any]:
    """Get summary statistics of all tasks.

    Returns:
        Dictionary with task counts by status, type, and priority:
        {
            "total": int,
            "by_status": {"todo": int, "in_progress": int, ...},
            "by_type": {"dat_ticket": int, "project": int, ...},
            "by_priority": {"high": int, "medium": int, "low": int}
        }
    """
    # Auto-sync journal before read operation
    manager = sync_before_read()
    summary = manager.get_summary()

    # Filter out zero counts for cleaner output
    by_status = {k: v for k, v in summary["by_status"].items() if v > 0}
    by_type = {k: v for k, v in summary["by_type"].items() if v > 0}
    by_priority = {k: v for k, v in summary["by_priority"].items() if v > 0}

    return {
        "total": summary["total"],
        "by_status": by_status,
        "by_type": by_type,
        "by_priority": by_priority,
    }


def search_tasks(query: str) -> List[Dict[str, Any]]:
    """Search tasks by keyword in title or description.

    Args:
        query: Search query string

    Returns:
        List of serialized task dictionaries matching the query
    """
    # Auto-sync journal before read operation
    manager = sync_before_read()

    # Use filter_tasks with search parameter
    tasks = manager.filter_tasks(search=query)

    return serialize_task_list(tasks)
