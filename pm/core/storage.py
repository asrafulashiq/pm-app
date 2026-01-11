"""Storage layer for reading/writing tasks to markdown files."""

import frontmatter
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .task import Task


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
