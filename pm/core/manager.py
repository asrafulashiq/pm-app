"""Task manager for CRUD operations."""

from typing import Dict, List, Optional, Union
from datetime import datetime

from .task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency
from .storage import TaskStorage, JournalStorage
from ..utils.config import get_config


class TaskManager:
    """Manages tasks with CRUD operations."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize task manager.

        Args:
            config_file: Optional path to config file
        """
        self.config = get_config(config_file)

        # Use JournalStorage for journal mode, TaskStorage for legacy modes
        if self.config.storage_mode == "journal":
            self.storage: Union[TaskStorage, JournalStorage] = JournalStorage(
                data_dir=str(self.config.data_path),
                backup_enabled=self.config.backup.enabled,
                max_backups_per_week=self.config.backup.max_backups_per_week,
                retention_days=self.config.backup.retention_days,
            )
        else:
            self.storage = TaskStorage(
                data_dir=str(self.config.data_path),
                storage_mode=self.config.storage_mode
            )

        self._tasks: Dict[str, Task] = {}
        self.load_tasks()

    def load_tasks(self) -> None:
        """Load all tasks from storage."""
        self._tasks = self.storage.load_all_tasks()

    def reload_tasks(self) -> None:
        """Reload tasks from storage (useful after external edits)."""
        self.load_tasks()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks.

        Returns:
            List of all tasks
        """
        return list(self._tasks.values())

    def create_task(
        self,
        title: str,
        description: str = "",
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        status: Optional[TaskStatus] = None,
        check_frequency: Optional[CheckFrequency] = None,
        eta: Optional[datetime] = None,
        notify_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Task:
        """Create a new task.

        Args:
            title: Task title
            description: Task description
            task_type: Type of task
            priority: Task priority
            status: Task status
            check_frequency: How often to check
            eta: Expected completion time
            notify_at: When to send notification
            tags: List of tags
            dependencies: List of dependency task IDs

        Returns:
            Created task
        """
        # Use defaults from config if not provided
        if task_type is None:
            task_type = TaskType.GENERAL

        if priority is None:
            priority = TaskPriority(self.config.defaults.priority)

        if status is None:
            status = TaskStatus.TODO

        if check_frequency is None:
            check_frequency = CheckFrequency(self.config.defaults.check_frequency)

        # Create task
        task = Task(
            title=title,
            description=description,
            type=task_type,
            priority=priority,
            status=status,
            check_frequency=check_frequency,
            eta=eta,
            notify_at=notify_at,
            tags=tags or [],
            dependencies=dependencies or [],
        )

        # Save to storage
        self._tasks[task.id] = task
        self.storage.save_task(task)

        return task

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        status: Optional[TaskStatus] = None,
        check_frequency: Optional[CheckFrequency] = None,
        eta: Optional[datetime] = None,
        notify_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Optional[Task]:
        """Update an existing task.

        Args:
            task_id: ID of task to update
            title: New title
            description: New description
            task_type: New type
            priority: New priority
            status: New status
            check_frequency: New check frequency
            eta: New ETA
            notify_at: New notification time
            tags: New tags
            dependencies: New dependencies

        Returns:
            Updated task if found, None otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return None

        # Update fields if provided
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if task_type is not None:
            task.type = task_type
        if priority is not None:
            task.priority = priority
        if status is not None:
            task.status = status
        if check_frequency is not None:
            task.check_frequency = check_frequency
        if eta is not None:
            task.eta = eta
        if notify_at is not None:
            task.notify_at = notify_at
        if tags is not None:
            task.tags = tags
        if dependencies is not None:
            task.dependencies = dependencies

        # Update timestamp
        task.updated_at = datetime.now()

        # Save to storage
        self.storage.save_task(task)

        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: ID of task to delete

        Returns:
            True if deleted, False if not found
        """
        if task_id not in self._tasks:
            return False

        # Remove from memory
        del self._tasks[task_id]

        # Remove from storage
        return self.storage.delete_task(task_id)

    def add_note(self, task_id: str, note: str) -> Optional[Task]:
        """Add a note to a task.

        Args:
            task_id: Task ID
            note: Note content

        Returns:
            Updated task if found, None otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return None

        task.add_note(note)
        self.storage.save_task(task)

        return task

    def mark_done(self, task_id: str) -> Optional[Task]:
        """Mark a task as done.

        Args:
            task_id: Task ID

        Returns:
            Updated task if found, None otherwise
        """
        return self.update_task(task_id, status=TaskStatus.DONE)

    def mark_in_progress(self, task_id: str) -> Optional[Task]:
        """Mark a task as in progress.

        Args:
            task_id: Task ID

        Returns:
            Updated task if found, None otherwise
        """
        return self.update_task(task_id, status=TaskStatus.IN_PROGRESS)

    def filter_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by various criteria.

        Args:
            status: Filter by status
            task_type: Filter by type
            priority: Filter by priority
            tags: Filter by tags (any match)
            search: Search in title and description

        Returns:
            List of matching tasks
        """
        tasks = self.get_all_tasks()

        if status:
            tasks = [t for t in tasks if t.status == status]

        if task_type:
            tasks = [t for t in tasks if t.type == task_type]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]

        if search:
            search_lower = search.lower()
            tasks = [
                t for t in tasks
                if search_lower in t.title.lower() or search_lower in t.description.lower()
            ]

        return tasks

    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks.

        Returns:
            List of overdue tasks
        """
        return [t for t in self.get_all_tasks() if t.is_overdue()]

    def get_tasks_needing_check(self) -> List[Task]:
        """Get tasks that need status check.

        Returns:
            List of tasks needing check
        """
        return [t for t in self.get_all_tasks() if t.needs_check()]

    def get_tasks_needing_notification(self) -> List[Task]:
        """Get tasks that need notification.

        Returns:
            List of tasks needing notification
        """
        return [t for t in self.get_all_tasks() if t.needs_notification()]

    def get_summary(self) -> Dict:
        """Get summary statistics.

        Returns:
            Dictionary with task counts by status, priority, type
        """
        tasks = self.get_all_tasks()

        summary = {
            "total": len(tasks),
            "by_status": {},
            "by_priority": {},
            "by_type": {},
            "overdue": len(self.get_overdue_tasks()),
            "needs_check": len(self.get_tasks_needing_check()),
        }

        # Count by status
        for status in TaskStatus:
            count = len([t for t in tasks if t.status == status])
            summary["by_status"][status.value] = count

        # Count by priority
        for priority in TaskPriority:
            count = len([t for t in tasks if t.priority == priority])
            summary["by_priority"][priority.value] = count

        # Count by type
        for task_type in TaskType:
            count = len([t for t in tasks if t.type == task_type])
            summary["by_type"][task_type.value] = count

        return summary
