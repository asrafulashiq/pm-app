"""MCP tools for PM app."""

from .sync_helper import sync_before_read, sync_before_write, SyncError

from .task_tools import (
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    add_task_note,
    mark_task_done,
    mark_task_in_progress,
)

from .query_tools import (
    get_overdue_tasks,
    get_tasks_needing_check,
    get_task_summary,
    search_tasks,
)

from .journal_tools import (
    start_journal_day,
    end_journal_day,
    get_current_journal,
    sync_journal,
    generate_week_summary,
    get_quarterly_summary,
    list_journal_backups,
    restore_journal_backup,
)

__all__ = [
    # Task management tools (8)
    "create_task",
    "list_tasks",
    "get_task",
    "update_task",
    "delete_task",
    "add_task_note",
    "mark_task_done",
    "mark_task_in_progress",
    # Query tools (4)
    "get_overdue_tasks",
    "get_tasks_needing_check",
    "get_task_summary",
    "search_tasks",
    # Journal tools (6)
    "start_journal_day",
    "end_journal_day",
    "get_current_journal",
    "sync_journal",
    "generate_week_summary",
    "get_quarterly_summary",
    # Backup tools (2)
    "list_journal_backups",
    "restore_journal_backup",
]
