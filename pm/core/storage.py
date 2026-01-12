"""Storage layer for reading/writing tasks to markdown files."""

import frontmatter
import logging
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from .task import Task, TaskType, TaskStatus, TaskPriority, CheckFrequency
from .backup import BackupManager

logger = logging.getLogger(__name__)


class TaskStorage:
    """Handles task persistence using markdown files with YAML frontmatter."""

    def __init__(self, data_dir: str, storage_mode: str = "multi_file"):
        """Initialize storage.

        Args:
            data_dir: Directory where task files are stored
            storage_mode: 'multi_file' or 'single_file'
        """
        self.data_dir = Path(data_dir).expanduser()
        self.storage_mode = storage_mode
        self.tasks_dir = self.data_dir / "tasks"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def load_all_tasks(self) -> Dict[str, Task]:
        """Load all tasks from storage.

        Returns:
            Dictionary mapping task IDs to Task objects
        """
        tasks = {}

        if self.storage_mode == "single_file":
            tasks = self._load_from_single_file()
        else:
            tasks = self._load_from_multi_file()

        return tasks

    def _load_from_multi_file(self) -> Dict[str, Task]:
        """Load tasks from individual markdown files."""
        tasks = {}

        for task_file in self.tasks_dir.glob("*.md"):
            try:
                task = self._read_task_file(task_file)
                if task:
                    tasks[task.id] = task
            except Exception as e:
                print(f"Warning: Failed to load task from {task_file}: {e}")

        return tasks

    def _load_from_single_file(self) -> Dict[str, Task]:
        """Load tasks from a single tasks.md file."""
        tasks = {}
        tasks_file = self.data_dir / "tasks.md"

        if not tasks_file.exists():
            return tasks

        try:
            # Read the file and split by task sections
            content = tasks_file.read_text()

            # Split by markdown headers (## Task: ...)
            sections = content.split("\n## Task: ")

            for section in sections[1:]:  # Skip first empty section
                try:
                    task = self._parse_task_section(section)
                    if task:
                        tasks[task.id] = task
                except Exception as e:
                    print(f"Warning: Failed to parse task section: {e}")

        except Exception as e:
            print(f"Warning: Failed to load tasks from {tasks_file}: {e}")

        return tasks

    def _read_task_file(self, file_path: Path) -> Optional[Task]:
        """Read a single task file."""
        post = frontmatter.load(file_path)

        # Extract frontmatter data
        metadata = post.metadata
        content = post.content

        # Parse description and notes from content
        description = ""
        notes = []

        if content.strip():
            # Normalize content - ensure ## Notes has a newline before it for consistent splitting
            normalized_content = content
            if content.strip().startswith("## Notes"):
                normalized_content = "\n" + content

            sections = normalized_content.split("\n## Notes")

            if sections:
                # Handle description section (everything before first ## Notes)
                desc_section = sections[0]
                if desc_section.strip():
                    if desc_section.strip().startswith("## Description"):
                        desc_section = desc_section.replace("## Description", "", 1).strip()
                    description = desc_section.strip()

            # Parse all notes sections (handle multiple ## Notes sections from malformed files)
            if len(sections) > 1:
                all_note_lines = []
                for i in range(1, len(sections)):
                    notes_section = sections[i]
                    # Extract lines that start with "-" (bullet points)
                    for line in notes_section.split("\n"):
                        line = line.strip()
                        if line and line.startswith("-"):
                            all_note_lines.append(line)
                notes = all_note_lines

        # Add parsed content to metadata
        metadata["description"] = description
        metadata["notes"] = notes

        # Create task from metadata
        return Task.from_dict(metadata)

    def _parse_task_section(self, section: str) -> Optional[Task]:
        """Parse a task from a section in single-file mode."""
        # This is for single_file mode - not implementing fully for now
        # as we'll focus on multi_file mode
        pass

    def save_task(self, task: Task) -> None:
        """Save a task to storage.

        Args:
            task: Task to save
        """
        if self.storage_mode == "single_file":
            self._save_to_single_file(task)
        else:
            self._save_to_multi_file(task)

    def _save_to_multi_file(self, task: Task) -> None:
        """Save task to individual markdown file."""
        file_path = self.tasks_dir / f"{task.id}.md"

        # Prepare metadata (frontmatter)
        metadata = task.to_dict()

        # Remove description and notes from metadata (they go in content)
        description = metadata.pop("description", "")
        notes_data = metadata.pop("notes", [])

        # Build content
        content_parts = []

        if description:
            content_parts.append("## Description")
            content_parts.append(description)
            content_parts.append("")

        if notes_data:
            content_parts.append("## Notes")
            for note in notes_data:
                content_parts.append(note)

        content = "\n".join(content_parts)

        # Create frontmatter post
        post = frontmatter.Post(content, **metadata)

        # Write to file
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

    def _save_to_single_file(self, task: Task) -> None:
        """Save task to single tasks.md file."""
        # Not implementing fully for now - focus on multi_file mode
        pass

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from storage.

        Args:
            task_id: ID of task to delete

        Returns:
            True if deleted, False if not found
        """
        if self.storage_mode == "single_file":
            return self._delete_from_single_file(task_id)
        else:
            return self._delete_from_multi_file(task_id)

    def _delete_from_multi_file(self, task_id: str) -> bool:
        """Delete task file."""
        file_path = self.tasks_dir / f"{task_id}.md"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def _delete_from_single_file(self, task_id: str) -> bool:
        """Delete task from single file."""
        # Not implementing fully for now
        return False

    def get_task_file_path(self, task_id: str) -> Path:
        """Get the file path for a task.

        Args:
            task_id: Task ID

        Returns:
            Path to task file
        """
        if self.storage_mode == "single_file":
            return self.data_dir / "tasks.md"
        else:
            return self.tasks_dir / f"{task_id}.md"

    def task_exists(self, task_id: str) -> bool:
        """Check if a task exists in storage.

        Args:
            task_id: Task ID

        Returns:
            True if task exists
        """
        return self.get_task_file_path(task_id).exists()


class JournalStorage:
    """Hybrid storage: journal is source of truth, task files store details.

    The journal markdown contains lightweight task references (ID + title + checkbox).
    Full task metadata is stored in individual task files in the tasks/ folder.

    When the journal is synced:
    - Checkbox changes update task status in task files
    - Removed tasks are deleted from task files
    - NEW: entries create new task files
    """

    NEW_TASK_PATTERN = re.compile(
        r'- \[ \] NEW:\s*(.+?)\s*\((\w+),\s*(\w+)\)',
        re.MULTILINE
    )

    CHECKBOX_PATTERN = re.compile(
        r'- \[([ x])\] (task-[a-f0-9]+):\s*(.+?)(?:\s*\(|$)',
        re.MULTILINE
    )

    def __init__(
        self,
        data_dir: str,
        backup_enabled: bool = True,
        max_backups_per_week: int = 50,
        retention_days: int = 90,
    ):
        """Initialize journal storage.

        Args:
            data_dir: Base directory for data storage
            backup_enabled: Whether to create backups before modifications
            max_backups_per_week: Maximum backups to keep per week
            retention_days: Days to retain backups
        """
        self.data_dir = Path(data_dir).expanduser()
        self.journal_dir = self.data_dir / "journal"
        self.tasks_dir = self.data_dir / "tasks"
        self.backup_dir = self.data_dir / "backups"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        # Use TaskStorage for reading/writing individual task files
        self._task_storage = TaskStorage(data_dir, storage_mode="multi_file")

        # Initialize backup manager
        self.backup_enabled = backup_enabled
        if backup_enabled:
            self.backup_manager = BackupManager(
                backup_dir=self.backup_dir,
                max_backups_per_week=max_backups_per_week,
                retention_days=retention_days,
            )
        else:
            self.backup_manager = None

    def get_journal_path(self, year: int, week: int) -> Path:
        """Get path to journal file for a specific week.

        Args:
            year: Year (e.g., 2026)
            week: Week number (1-52)

        Returns:
            Path to journal file
        """
        return self.journal_dir / f"{year}-W{week:02d}.md"

    def get_current_journal_path(self) -> Path:
        """Get path to current week's journal file."""
        now = datetime.now()
        year, week, _ = now.isocalendar()
        return self.get_journal_path(year, week)

    def load_all_tasks(self) -> Dict[str, Task]:
        """Load all tasks from task files.

        Task files are the detailed storage; journal is the source of truth
        for which tasks exist and their status.

        Returns:
            Dictionary mapping task IDs to Task objects
        """
        return self._task_storage.load_all_tasks()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Load a single task from its file.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        tasks = self._task_storage.load_all_tasks()
        return tasks.get(task_id)

    def detect_new_tasks(self, content: str) -> Tuple[List[Dict], List[str]]:
        """Find NEW: entries in daily sections.

        Args:
            content: Journal markdown content

        Returns:
            Tuple of (list of parsed new task info, list of error messages)
        """
        new_tasks = []
        errors = []

        # Also look for malformed NEW: entries to report errors
        malformed_pattern = re.compile(r'- \[ \] NEW:\s*(.+)$', re.MULTILINE)

        for match in malformed_pattern.finditer(content):
            line = match.group(0)
            line_num = content[:match.start()].count('\n') + 1

            # Check if it matches the proper format
            proper_match = self.NEW_TASK_PATTERN.match(line)
            if proper_match:
                # Valid format - extract data
                title = proper_match.group(1).strip()
                task_type = proper_match.group(2).strip().lower()
                priority = proper_match.group(3).strip().lower()

                # Validate task type
                valid_types = [t.value for t in TaskType]
                if task_type not in valid_types:
                    errors.append(
                        f"Line {line_num}: Invalid task type '{task_type}'. "
                        f"Valid types: {', '.join(valid_types)}"
                    )
                    continue

                # Validate priority
                valid_priorities = [p.value for p in TaskPriority]
                if priority not in valid_priorities:
                    errors.append(
                        f"Line {line_num}: Invalid priority '{priority}'. "
                        f"Valid priorities: {', '.join(valid_priorities)}"
                    )
                    continue

                new_tasks.append({
                    "title": title,
                    "type": task_type,
                    "priority": priority,
                    "match_start": match.start(),
                    "match_end": match.end(),
                    "original_line": line,
                    "line_num": line_num,
                })
            else:
                # Malformed - report error
                errors.append(
                    f"Line {line_num}: Malformed NEW entry. Expected format: "
                    f"'- [ ] NEW: Task title (type, priority)'. Got: '{line}'"
                )

        return new_tasks, errors

    def get_journal_task_ids(self, content: str) -> Set[str]:
        """Extract all task IDs mentioned in a journal.

        Args:
            content: Journal markdown content

        Returns:
            Set of task IDs found in journal
        """
        task_ids = set()
        for match in self.CHECKBOX_PATTERN.finditer(content):
            task_ids.add(match.group(2))
        return task_ids

    def detect_deleted_tasks(
        self,
        content: str,
        known_task_ids: Set[str],
    ) -> Set[str]:
        """Find tasks that were removed from the journal.

        A task is considered deleted if it was in the known set
        but no longer appears anywhere in the journal.

        Args:
            content: Journal markdown content
            known_task_ids: Set of task IDs that should exist

        Returns:
            Set of task IDs that were deleted
        """
        current_ids = self.get_journal_task_ids(content)
        deleted = known_task_ids - current_ids
        return deleted

    def parse_checkboxes(self, content: str) -> Dict[str, bool]:
        """Parse checkbox states from journal content.

        Args:
            content: Journal markdown content

        Returns:
            Dictionary mapping task IDs to checked status
        """
        checkboxes = {}

        for match in self.CHECKBOX_PATTERN.finditer(content):
            is_checked = match.group(1) == 'x'
            task_id = match.group(2)
            checkboxes[task_id] = is_checked

        return checkboxes

    def save_task(self, task: Task, year: int = None, week: int = None) -> None:
        """Save a task to the task files.

        Args:
            task: Task to save
            year: Unused (kept for API compatibility)
            week: Unused (kept for API compatibility)
        """
        self._task_storage.save_task(task)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from task files.

        Args:
            task_id: ID of task to delete

        Returns:
            True if task was found and deleted
        """
        return self._task_storage.delete_task(task_id)

    def process_new_task_entries(self, content: str) -> Tuple[str, List[Task], List[str]]:
        """Process NEW: entries and create tasks.

        Creates task files for new entries and updates the journal content.

        Args:
            content: Journal markdown content

        Returns:
            Tuple of (updated content, list of created tasks, list of errors)
        """
        new_entries, errors = self.detect_new_tasks(content)
        created_tasks = []

        # Log any errors found
        for error in errors:
            logger.warning(error)

        # Process in reverse order to maintain string positions
        for entry in reversed(new_entries):
            try:
                # Create new task
                task = Task(
                    title=entry["title"],
                    type=TaskType(entry["type"]),
                    priority=TaskPriority(entry["priority"]),
                    status=TaskStatus.TODO,
                )

                # Save to task file
                self._task_storage.save_task(task)
                created_tasks.append(task)

                # Replace NEW: line with proper task reference
                new_line = f"- [ ] {task.id}: {task.title} ({task.type.value}, {task.priority.value})"
                content = (
                    content[:entry["match_start"]] +
                    new_line +
                    content[entry["match_end"]:]
                )

                logger.info(f"Created task {task.id}: {task.title}")

            except Exception as e:
                line_num = entry.get("line_num", "?")
                error_msg = f"Line {line_num}: Failed to create task: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Reverse to maintain creation order
        created_tasks.reverse()

        return content, created_tasks, errors
