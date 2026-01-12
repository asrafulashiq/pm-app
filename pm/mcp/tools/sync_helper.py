"""Helper module for auto-syncing journal before MCP operations."""

import logging
from typing import Dict, Any, Optional

from ...core.manager import TaskManager
from ...core.journal_manager import JournalManager

logger = logging.getLogger(__name__)


class SyncError(Exception):
    """Error during journal sync."""
    pass


def get_synced_manager() -> tuple[TaskManager, Dict[str, Any]]:
    """Get a TaskManager with journal synced first.

    This ensures the task files are up-to-date with the journal
    before any MCP operation reads or modifies tasks.

    Returns:
        Tuple of (TaskManager, sync_result dict)

    Raises:
        SyncError: If sync fails due to malformed markdown
    """
    task_manager = TaskManager()
    journal_manager = JournalManager(task_manager)

    try:
        sync_result = journal_manager.sync_journal()

        # Log sync activity
        created = len(sync_result.get("created", []))
        deleted = len(sync_result.get("deleted", []))
        updated = len(sync_result.get("updated", []))

        if created or deleted or updated:
            logger.info(
                f"Auto-sync: created={created}, deleted={deleted}, updated={updated}"
            )

        # Log any parsing errors that were collected
        errors = sync_result.get("errors", [])
        for error in errors:
            logger.warning(f"Journal parse warning: {error}")

        return task_manager, sync_result

    except Exception as e:
        logger.error(f"Journal sync failed: {e}")
        raise SyncError(f"Failed to sync journal: {e}") from e


def sync_before_read() -> TaskManager:
    """Sync journal and return TaskManager for read operations.

    Returns:
        TaskManager with synced tasks
    """
    task_manager, _ = get_synced_manager()
    return task_manager


def sync_before_write() -> tuple[TaskManager, JournalManager]:
    """Sync journal and return managers for write operations.

    Returns:
        Tuple of (TaskManager, JournalManager)
    """
    task_manager, _ = get_synced_manager()
    journal_manager = JournalManager(task_manager)
    return task_manager, journal_manager
