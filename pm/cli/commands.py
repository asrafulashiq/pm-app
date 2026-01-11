"""CLI commands for PM app."""

import typer
from typing import Optional, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from dateutil import parser as date_parser

from ..core.manager import TaskManager
from ..core.task import TaskType, TaskStatus, TaskPriority, CheckFrequency
from ..core.journal_manager import JournalManager


app = typer.Typer(help="Personal Project Manager - Track your work tasks")
console = Console()


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse datetime from string."""
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except Exception as e:
        console.print(f"[red]Error parsing date '{date_str}': {e}[/red]")
        return None


@app.command()
def add(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--desc", "-d", help="Task description"),
    task_type: str = typer.Option("general", "--type", "-t", help="Task type (dat_ticket, cross_team, project, training_run, general)"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority (high, medium, low)"),
    status: str = typer.Option("todo", "--status", "-s", help="Status (todo, in_progress, waiting, blocked, done)"),
    check_frequency: str = typer.Option("weekly", "--check-freq", "-f", help="Check frequency (daily, weekly, biweekly, monthly)"),
    eta: Optional[str] = typer.Option(None, "--eta", "-e", help="Expected completion (e.g., '2026-01-20', 'next friday')"),
    notify_at: Optional[str] = typer.Option(None, "--notify", "-n", help="Notification time (e.g., '2026-01-15 10:00')"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
):
    """Add a new task."""
    manager = TaskManager()

    # Parse enums
    try:
        task_type_enum = TaskType(task_type)
        priority_enum = TaskPriority(priority)
        status_enum = TaskStatus(status)
        check_freq_enum = CheckFrequency(check_frequency)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Parse dates
    eta_dt = parse_datetime(eta) if eta else None
    notify_dt = parse_datetime(notify_at) if notify_at else None

    # Parse tags
    tags_list = [t.strip() for t in tags.split(",")] if tags else []

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
        tags=tags_list,
    )

    console.print(f"[green]✓[/green] Created task: {task.id}")
    console.print(f"  {task}")


@app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Filter by tags (comma-separated)"),
    search: Optional[str] = typer.Option(None, "--search", help="Search in title/description"),
    show_done: bool = typer.Option(False, "--done", help="Include done tasks"),
):
    """List tasks."""
    manager = TaskManager()

    # Parse filters
    status_enum = TaskStatus(status) if status else None
    type_enum = TaskType(task_type) if task_type else None
    priority_enum = TaskPriority(priority) if priority else None
    tags_list = [t.strip() for t in tags.split(",")] if tags else None

    # Get filtered tasks
    tasks = manager.filter_tasks(
        status=status_enum,
        task_type=type_enum,
        priority=priority_enum,
        tags=tags_list,
        search=search,
    )

    # Filter out done unless requested
    if not show_done:
        tasks = [t for t in tasks if t.status != TaskStatus.DONE]

    # Sort by priority and created date
    priority_order = {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 1, TaskPriority.LOW: 2}
    tasks.sort(key=lambda t: (priority_order.get(t.priority, 3), t.created_at))

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    # Create table
    table = Table(title=f"Tasks ({len(tasks)})", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Type", style="blue")
    table.add_column("Status", style="magenta")
    table.add_column("Priority", style="yellow")
    table.add_column("ETA", style="green")

    for task in tasks:
        status_style = {
            TaskStatus.TODO: "white",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.WAITING: "yellow",
            TaskStatus.DONE: "green",
            TaskStatus.BLOCKED: "red",
        }.get(task.status, "white")

        eta_str = task.eta.strftime("%Y-%m-%d") if task.eta else "-"
        if task.is_overdue():
            eta_str = f"[red]{eta_str} (overdue)[/red]"

        table.add_row(
            task.id,
            task.title,
            task.type.value,
            f"[{status_style}]{task.status.value}[/{status_style}]",
            task.priority.value,
            eta_str,
        )

    console.print(table)


@app.command()
def show(task_id: str = typer.Argument(..., help="Task ID")):
    """Show detailed task information."""
    manager = TaskManager()
    task = manager.get_task(task_id)

    if not task:
        console.print(f"[red]Error: Task '{task_id}' not found[/red]")
        raise typer.Exit(1)

    # Build detailed view
    lines = []
    lines.append(f"[bold cyan]ID:[/bold cyan] {task.id}")
    lines.append(f"[bold cyan]Title:[/bold cyan] {task.title}")
    lines.append(f"[bold cyan]Type:[/bold cyan] {task.type.value}")
    lines.append(f"[bold cyan]Status:[/bold cyan] {task.status.value}")
    lines.append(f"[bold cyan]Priority:[/bold cyan] {task.priority.value}")
    lines.append(f"[bold cyan]Created:[/bold cyan] {task.created_at.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"[bold cyan]Updated:[/bold cyan] {task.updated_at.strftime('%Y-%m-%d %H:%M')}")

    if task.eta:
        eta_str = task.eta.strftime('%Y-%m-%d %H:%M')
        if task.is_overdue():
            eta_str = f"[red]{eta_str} (overdue)[/red]"
        lines.append(f"[bold cyan]ETA:[/bold cyan] {eta_str}")

    lines.append(f"[bold cyan]Check Frequency:[/bold cyan] {task.check_frequency.value}")

    if task.last_checked:
        lines.append(f"[bold cyan]Last Checked:[/bold cyan] {task.last_checked.strftime('%Y-%m-%d %H:%M')}")

    if task.notify_at:
        lines.append(f"[bold cyan]Notify At:[/bold cyan] {task.notify_at.strftime('%Y-%m-%d %H:%M')}")

    if task.tags:
        lines.append(f"[bold cyan]Tags:[/bold cyan] {', '.join(task.tags)}")

    if task.dependencies:
        lines.append(f"[bold cyan]Dependencies:[/bold cyan] {', '.join(task.dependencies)}")

    if task.description:
        lines.append(f"\n[bold cyan]Description:[/bold cyan]\n{task.description}")

    if task.notes:
        lines.append(f"\n[bold cyan]Notes:[/bold cyan]")
        for note in task.notes:
            lines.append(f"  {note}")

    panel = Panel("\n".join(lines), title=f"Task: {task.title}", border_style="blue")
    console.print(panel)


@app.command()
def update(
    task_id: str = typer.Argument(..., help="Task ID"),
    title: Optional[str] = typer.Option(None, "--title", help="New title"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="New type"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="New priority"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status"),
    eta: Optional[str] = typer.Option(None, "--eta", "-e", help="New ETA"),
    tags: Optional[str] = typer.Option(None, "--tags", help="New tags (comma-separated)"),
):
    """Update a task."""
    manager = TaskManager()

    # Parse enums if provided
    type_enum = TaskType(task_type) if task_type else None
    priority_enum = TaskPriority(priority) if priority else None
    status_enum = TaskStatus(status) if status else None
    eta_dt = parse_datetime(eta) if eta else None
    tags_list = [t.strip() for t in tags.split(",")] if tags else None

    # Update task
    task = manager.update_task(
        task_id=task_id,
        title=title,
        description=description,
        task_type=type_enum,
        priority=priority_enum,
        status=status_enum,
        eta=eta_dt,
        tags=tags_list,
    )

    if not task:
        console.print(f"[red]Error: Task '{task_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Updated task: {task.id}")
    console.print(f"  {task}")


@app.command()
def done(task_id: str = typer.Argument(..., help="Task ID")):
    """Mark a task as done."""
    manager = TaskManager()
    task = manager.mark_done(task_id)

    if not task:
        console.print(f"[red]Error: Task '{task_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Marked task as done: {task.id}")
    console.print(f"  {task}")


@app.command()
def note(
    task_id: str = typer.Argument(..., help="Task ID"),
    text: str = typer.Argument(..., help="Note text"),
):
    """Add a note to a task."""
    manager = TaskManager()
    task = manager.add_note(task_id, text)

    if not task:
        console.print(f"[red]Error: Task '{task_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Added note to task: {task.id}")


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="Task ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a task."""
    manager = TaskManager()

    # Check task exists
    task = manager.get_task(task_id)
    if not task:
        console.print(f"[red]Error: Task '{task_id}' not found[/red]")
        raise typer.Exit(1)

    # Confirm deletion
    if not yes:
        confirm = typer.confirm(f"Delete task '{task.title}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Delete
    manager.delete_task(task_id)
    console.print(f"[green]✓[/green] Deleted task: {task_id}")


@app.command()
def status():
    """Show overall status summary."""
    manager = TaskManager()
    summary = manager.get_summary()

    # Create summary display
    lines = []
    lines.append(f"[bold]Total Tasks:[/bold] {summary['total']}")
    lines.append("")

    lines.append("[bold cyan]By Status:[/bold cyan]")
    for status, count in summary['by_status'].items():
        if count > 0:
            lines.append(f"  {status}: {count}")

    lines.append("")
    lines.append("[bold cyan]By Priority:[/bold cyan]")
    for priority, count in summary['by_priority'].items():
        if count > 0:
            lines.append(f"  {priority}: {count}")

    lines.append("")
    lines.append("[bold cyan]By Type:[/bold cyan]")
    for task_type, count in summary['by_type'].items():
        if count > 0:
            lines.append(f"  {task_type}: {count}")

    lines.append("")
    if summary['overdue'] > 0:
        lines.append(f"[bold red]Overdue:[/bold red] {summary['overdue']}")

    if summary['needs_check'] > 0:
        lines.append(f"[bold yellow]Needs Check:[/bold yellow] {summary['needs_check']}")

    panel = Panel("\n".join(lines), title="Task Summary", border_style="green")
    console.print(panel)


@app.command()
def check():
    """Check which tasks need attention."""
    manager = TaskManager()

    overdue = manager.get_overdue_tasks()
    needs_check = manager.get_tasks_needing_check()
    needs_notification = manager.get_tasks_needing_notification()

    if not overdue and not needs_check and not needs_notification:
        console.print("[green]All tasks are up to date![/green]")
        return

    if overdue:
        console.print(f"\n[bold red]Overdue Tasks ({len(overdue)}):[/bold red]")
        for task in overdue:
            console.print(f"  • [{task.id}] {task.title}")

    if needs_check:
        console.print(f"\n[bold yellow]Tasks Needing Check ({len(needs_check)}):[/bold yellow]")
        for task in needs_check:
            console.print(f"  • [{task.id}] {task.title} (last checked: {task.last_checked or 'never'})")

    if needs_notification:
        console.print(f"\n[bold blue]Tasks With Pending Notifications ({len(needs_notification)}):[/bold blue]")
        for task in needs_notification:
            console.print(f"  • [{task.id}] {task.title}")


@app.command()
def journal(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date for journal (defaults to today)"),
    editor: str = typer.Option("vim", "--editor", "-e", help="Editor to use (vim/nvim)"),
):
    """Open weekly journal in editor."""
    manager = TaskManager()
    journal_mgr = JournalManager(manager)

    # Parse date if provided
    journal_date = parse_datetime(date) if date else None

    console.print("[cyan]Opening weekly journal...[/cyan]")

    try:
        journal = journal_mgr.open_journal(date=journal_date, editor=editor)
        console.print(f"[green]✓[/green] Opened journal for week {journal.week}, {journal.year}")

        # Sync after closing
        console.print("[cyan]Syncing journal with tasks...[/cyan]")
        journal_mgr.sync_journal(journal)
        console.print("[green]✓[/green] Journal synced")

    except FileNotFoundError:
        console.print(f"[red]Error: Editor '{editor}' not found[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error opening journal: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def journal_start(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date to start (defaults to today)"),
):
    """Start a new day in the journal."""
    manager = TaskManager()
    journal_mgr = JournalManager(manager)

    # Parse date
    start_date = parse_datetime(date) if date else datetime.now()

    day_section = journal_mgr.start_day(start_date)

    date_str = start_date.strftime("%A, %B %d, %Y")
    console.print(f"[green]✓[/green] Started day: {date_str}")
    console.print(f"  Planned tasks: {len(day_section.planned)}")


@app.command()
def journal_end(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date to end (defaults to today)"),
):
    """End the day and sync tasks."""
    manager = TaskManager()
    journal_mgr = JournalManager(manager)

    # Parse date
    end_date = parse_datetime(date) if date else datetime.now()

    day_section = journal_mgr.end_day(end_date)

    date_str = end_date.strftime("%A, %B %d, %Y")
    console.print(f"[green]✓[/green] Ended day: {date_str}")

    if day_section:
        console.print(f"  Completed: {len(day_section.completed)} tasks")
        console.print(f"  Planned: {len(day_section.planned)} tasks")


@app.command()
def journal_sync():
    """Sync journal checkboxes with task statuses."""
    manager = TaskManager()
    journal_mgr = JournalManager(manager)

    console.print("[cyan]Syncing journal with tasks...[/cyan]")

    checkboxes = journal_mgr.sync_journal()

    console.print(f"[green]✓[/green] Synced {len(checkboxes)} task checkboxes")

    # Show summary
    completed = sum(1 for checked in checkboxes.values() if checked)
    console.print(f"  Completed: {completed}")
    console.print(f"  In progress: {len(checkboxes) - completed}")


@app.command()
def journal_summary(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date in week to summarize (defaults to current week)"),
):
    """Generate weekly summary."""
    manager = TaskManager()
    journal_mgr = JournalManager(manager)

    # Get journal for date
    if date:
        summary_date = parse_datetime(date)
        journal = journal_mgr.get_journal_for_date(summary_date)
    else:
        journal = journal_mgr.get_current_journal()

    console.print("[cyan]Generating weekly summary...[/cyan]")

    summary = journal_mgr.generate_week_summary(journal)

    week_range = f"{summary.week_start.strftime('%b %d')} - {summary.week_end.strftime('%b %d, %Y')}"

    lines = []
    lines.append(f"[bold]Week {journal.week}, {journal.year}[/bold]")
    lines.append(f"Period: {week_range}")
    lines.append("")
    lines.append(f"[bold green]✅ Completed:[/bold green] {summary.tasks_completed_count()} tasks")
    lines.append(f"[bold blue]🔄 In Progress:[/bold blue] {len(summary.tasks_in_progress)} tasks")

    if summary.blockers:
        lines.append(f"[bold red]🚫 Blockers:[/bold red] {len(summary.blockers)}")

    panel = Panel("\n".join(lines), title="Week Summary", border_style="green")
    console.print(panel)

    summary_file = journal.get_summary_file_path()
    console.print(f"\n[green]✓[/green] Summary saved to: {summary_file}")


@app.command()
def quarterly(
    year: int = typer.Argument(..., help="Year"),
    quarter: int = typer.Argument(..., help="Quarter (1-4)"),
):
    """Show quarterly summary."""
    if quarter not in [1, 2, 3, 4]:
        console.print("[red]Error: Quarter must be 1-4[/red]")
        raise typer.Exit(1)

    manager = TaskManager()
    journal_mgr = JournalManager(manager)

    console.print(f"[cyan]Generating Q{quarter} {year} summary...[/cyan]")

    summary = journal_mgr.get_quarterly_summary(year, quarter)

    lines = []
    lines.append(f"[bold]Q{quarter} {year} Summary[/bold]")
    lines.append("")
    lines.append(f"Weeks tracked: {summary['weeks_tracked']}")
    lines.append(f"[bold green]✅ Total completed:[/bold green] {summary['total_completed']} tasks")
    lines.append(f"[bold blue]🔄 In progress:[/bold blue] {summary['total_in_progress']} tasks")

    if summary['blockers']:
        lines.append(f"[bold red]🚫 Blockers:[/bold red] {len(summary['blockers'])}")

    panel = Panel("\n".join(lines), title=f"Q{quarter} {year}", border_style="cyan")
    console.print(panel)


# Aliases
@app.command(name="j")
def j_alias(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date for journal"),
    editor: str = typer.Option("vim", "--editor", "-e", help="Editor to use"),
):
    """Alias for 'journal' command."""
    journal(date=date, editor=editor)


@app.command(name="js")
def js_alias(date: Optional[str] = typer.Option(None, "--date", "-d", help="Date to start")):
    """Alias for 'journal-start' command."""
    journal_start(date=date)


@app.command(name="je")
def je_alias(date: Optional[str] = typer.Option(None, "--date", "-d", help="Date to end")):
    """Alias for 'journal-end' command."""
    journal_end(date=date)


@app.command(name="jws")
def jws_alias(date: Optional[str] = typer.Option(None, "--date", "-d", help="Date in week")):
    """Alias for 'journal-summary' command."""
    journal_summary(date=date)


@app.command(name="mcp-server")
def mcp_server():
    """Start MCP server for AI agent integration.

    Runs the Model Context Protocol server that exposes PM app functionality
    to AI agents via stdio transport. Used by Claude Desktop, Cline, and other
    MCP clients.

    The server provides 18 tools for task management, queries, and journal operations.
    """
    from ..mcp.server import run_server

    console.print("[bold green]Starting PM MCP Server...[/bold green]")
    console.print("Server ready for MCP client connections")
    console.print("Press Ctrl+C to stop")

    try:
        run_server()
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")


if __name__ == "__main__":
    app()
