#!/usr/bin/env python3
"""Migration script to convert from task files to journal-based storage.

This script migrates existing task files (~/pm-data/tasks/*.md) to the new
journal-based storage format where tasks are stored in weekly journal files
with a Task Registry section.

Usage:
    python -m pm.scripts.migrate_to_journal [--dry-run] [--backup]

Options:
    --dry-run   Show what would be done without making changes
    --backup    Create backup of existing data before migration (default: True)
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from pm.core.storage import TaskStorage, JournalStorage
from pm.core.task import Task
from pm.core.journal import WeeklyJournal, get_week_for_date
from pm.utils.config import get_config


def group_tasks_by_week(tasks: Dict[str, Task]) -> Dict[Tuple[int, int], Dict[str, Task]]:
    """Group tasks by the week they were created.

    Args:
        tasks: Dictionary of all tasks

    Returns:
        Dictionary mapping (year, week) tuples to task dictionaries
    """
    tasks_by_week: Dict[Tuple[int, int], Dict[str, Task]] = {}

    for task_id, task in tasks.items():
        year, week = get_week_for_date(task.created_at)
        key = (year, week)

        if key not in tasks_by_week:
            tasks_by_week[key] = {}

        tasks_by_week[key][task_id] = task

    return tasks_by_week


def migrate_tasks_to_journal(dry_run: bool = False, backup: bool = True) -> Dict:
    """Migrate tasks from individual files to journal format.

    Args:
        dry_run: If True, show what would be done without making changes
        backup: If True, backup existing data before migration

    Returns:
        Dictionary with migration statistics
    """
    config = get_config()
    data_dir = config.data_path

    tasks_dir = data_dir / "tasks"
    journal_dir = data_dir / "journal"
    backup_dir = data_dir / "migration_backup"

    result = {
        "tasks_found": 0,
        "tasks_migrated": 0,
        "journals_created": 0,
        "journals_updated": 0,
        "backup_path": None,
        "errors": [],
    }

    # Check if tasks directory exists
    if not tasks_dir.exists() or not any(tasks_dir.glob("*.md")):
        print("No task files found to migrate.")
        return result

    # Load existing tasks using old storage
    print("Loading existing tasks...")
    old_storage = TaskStorage(str(data_dir), storage_mode="multi_file")
    tasks = old_storage.load_all_tasks()
    result["tasks_found"] = len(tasks)

    if not tasks:
        print("No tasks found to migrate.")
        return result

    print(f"Found {len(tasks)} tasks to migrate.")

    # Create backup if requested
    if backup and not dry_run:
        print(f"\nCreating backup at {backup_dir}...")
        if backup_dir.exists():
            # Add timestamp to existing backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            old_backup = backup_dir.rename(backup_dir.parent / f"migration_backup_{timestamp}")
            print(f"  Renamed existing backup to {old_backup}")

        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup tasks directory
        if tasks_dir.exists():
            shutil.copytree(tasks_dir, backup_dir / "tasks")
            print(f"  Backed up tasks directory")

        # Backup journal directory
        if journal_dir.exists():
            shutil.copytree(journal_dir, backup_dir / "journal")
            print(f"  Backed up journal directory")

        result["backup_path"] = str(backup_dir)

    # Group tasks by week
    print("\nGrouping tasks by creation week...")
    tasks_by_week = group_tasks_by_week(tasks)
    print(f"Tasks span {len(tasks_by_week)} weeks.")

    # Initialize new journal storage
    new_storage = JournalStorage(
        str(data_dir),
        backup_enabled=False,  # Don't create backups during migration
    )

    # Process each week
    for (year, week), week_tasks in sorted(tasks_by_week.items()):
        journal_path = journal_dir / f"{year}-W{week:02d}.md"
        action = "update" if journal_path.exists() else "create"

        print(f"\n  Week {year}-W{week:02d}: {len(week_tasks)} tasks ({action})")

        if dry_run:
            for task_id, task in week_tasks.items():
                print(f"    - {task_id}: {task.title}")
            continue

        try:
            # Load existing journal content if it exists
            if journal_path.exists():
                content = journal_path.read_text()
                existing_tasks = new_storage.parse_task_registry(content)
                # Merge with new tasks
                existing_tasks.update(week_tasks)
                week_tasks = existing_tasks
                result["journals_updated"] += 1
            else:
                result["journals_created"] += 1

            # Create/update journal with Task Registry
            journal = WeeklyJournal(year, week, journal_dir)

            # Set task registry
            journal.task_registry = week_tasks

            # Generate and save content
            journal.save(week_tasks)

            result["tasks_migrated"] += len(week_tasks)

        except Exception as e:
            error_msg = f"Error processing week {year}-W{week:02d}: {e}"
            print(f"    ERROR: {error_msg}")
            result["errors"].append(error_msg)

    # Summary
    print("\n" + "=" * 50)
    print("Migration Summary")
    print("=" * 50)
    print(f"Tasks found:      {result['tasks_found']}")
    print(f"Tasks migrated:   {result['tasks_migrated']}")
    print(f"Journals created: {result['journals_created']}")
    print(f"Journals updated: {result['journals_updated']}")

    if result["errors"]:
        print(f"\nErrors encountered: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"  - {error}")

    if dry_run:
        print("\n(Dry run - no changes made)")
    else:
        print(f"\nBackup location: {result['backup_path']}")
        print("\nMigration complete!")
        print("\nTo verify:")
        print("  1. Run 'sync_journal' MCP tool")
        print("  2. Check that tasks appear correctly")
        print("  3. If everything works, you can delete the old tasks directory:")
        print(f"     rm -rf {tasks_dir}")

    return result


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate from task files to journal-based storage"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before migration",
    )

    args = parser.parse_args()

    migrate_tasks_to_journal(
        dry_run=args.dry_run,
        backup=not args.no_backup,
    )


if __name__ == "__main__":
    main()
