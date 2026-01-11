"""MCP server for PM app.

Exposes task management, queries, and journal operations via Model Context Protocol.
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools import (
    # Task management
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    add_task_note,
    mark_task_done,
    mark_task_in_progress,
    # Queries
    get_overdue_tasks,
    get_tasks_needing_check,
    get_task_summary,
    search_tasks,
    # Journal
    start_journal_day,
    end_journal_day,
    get_current_journal,
    sync_journal,
    generate_week_summary,
    get_quarterly_summary,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create MCP server instance
app = Server("pm-app")


# Tool definitions with JSON schemas
TOOLS = [
    # Task Management Tools
    Tool(
        name="create_task",
        description="Create a new task in the PM system with title, description, type, priority, status, and optional metadata like tags and dependencies",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title (required)"},
                "description": {"type": "string", "description": "Task description"},
                "task_type": {
                    "type": "string",
                    "enum": ["dat_ticket", "cross_team", "project", "training_run", "general"],
                    "description": "Type of task",
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Task priority",
                },
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "waiting", "blocked", "done"],
                    "description": "Task status",
                },
                "check_frequency": {
                    "type": "string",
                    "enum": ["daily", "weekly", "biweekly", "monthly"],
                    "description": "How often to check on this task",
                },
                "eta": {"type": "string", "description": "Expected completion time (ISO datetime format)"},
                "notify_at": {"type": "string", "description": "When to send notification (ISO datetime format)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Task tags"},
                "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Task IDs this task depends on"},
            },
            "required": ["title"],
        },
    ),
    Tool(
        name="list_tasks",
        description="List all tasks with optional filters by status, type, priority, tags, or search query",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "in_progress", "waiting", "blocked", "done"]},
                "task_type": {"type": "string", "enum": ["dat_ticket", "cross_team", "project", "training_run", "general"]},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "tags": {"type": "array", "items": {"type": "string"}},
                "search": {"type": "string", "description": "Search in title/description"},
            },
        },
    ),
    Tool(
        name="get_task",
        description="Get detailed information about a specific task by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="update_task",
        description="Update a task's properties (title, description, status, priority, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to update"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "task_type": {"type": "string", "enum": ["dat_ticket", "cross_team", "project", "training_run", "general"]},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "status": {"type": "string", "enum": ["todo", "in_progress", "waiting", "blocked", "done"]},
                "check_frequency": {"type": "string", "enum": ["daily", "weekly", "biweekly", "monthly"]},
                "eta": {"type": "string"},
                "notify_at": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "dependencies": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="delete_task",
        description="Delete a task by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to delete"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="add_task_note",
        description="Add a timestamped note to a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "note": {"type": "string", "description": "Note content"},
            },
            "required": ["task_id", "note"],
        },
    ),
    Tool(
        name="mark_task_done",
        description="Mark a task as completed",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="mark_task_in_progress",
        description="Mark a task as in progress",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
            },
            "required": ["task_id"],
        },
    ),
    # Query Tools
    Tool(
        name="get_overdue_tasks",
        description="Get all tasks that are past their ETA and not yet completed",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_tasks_needing_check",
        description="Get tasks that are due for periodic check based on their check frequency",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_task_summary",
        description="Get summary statistics of all tasks grouped by status, type, and priority",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="search_tasks",
        description="Search for tasks by keyword in title or description",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    ),
    # Journal Tools
    Tool(
        name="start_journal_day",
        description="Start a new journal day, creating or updating the current week's journal with today's section and auto-populating tasks that need attention",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="end_journal_day",
        description="End the current journal day, finalizing today's section and syncing task statuses based on checkbox completion",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_current_journal",
        description="Get the current week's journal content (full markdown)",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="sync_journal",
        description="Sync journal checkboxes with task statuses, reading the current journal and updating task statuses",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="generate_week_summary",
        description="Generate summary for the current week with completed tasks, in-progress tasks, and blockers",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_quarterly_summary",
        description="Get quarterly achievement summary with completed tasks and stats for a given quarter",
        inputSchema={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Year (defaults to current year)"},
                "quarter": {"type": "integer", "enum": [1, 2, 3, 4], "description": "Quarter 1-4 (defaults to current quarter)"},
            },
        },
    ),
]


# Map tool names to functions
TOOL_HANDLERS = {
    "create_task": create_task,
    "list_tasks": list_tasks,
    "get_task": get_task,
    "update_task": update_task,
    "delete_task": delete_task,
    "add_task_note": add_task_note,
    "mark_task_done": mark_task_done,
    "mark_task_in_progress": mark_task_in_progress,
    "get_overdue_tasks": get_overdue_tasks,
    "get_tasks_needing_check": get_tasks_needing_check,
    "get_task_summary": get_task_summary,
    "search_tasks": search_tasks,
    "start_journal_day": start_journal_day,
    "end_journal_day": end_journal_day,
    "get_current_journal": get_current_journal,
    "sync_journal": sync_journal,
    "generate_week_summary": generate_week_summary,
    "get_quarterly_summary": get_quarterly_summary,
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Call a tool with the given arguments."""
    logger.info(f"Calling tool: {name} with args: {arguments}")

    if name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {name}")

    try:
        # Call the tool function
        handler = TOOL_HANDLERS[name]
        result = handler(**arguments)

        # Format result as JSON string
        import json
        result_text = json.dumps(result, indent=2)

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        error_msg = f"Error: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Run the MCP server."""
    logger.info("Starting PM MCP server...")
    logger.info(f"Registered {len(TOOLS)} tools")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run_server():
    """Entry point for running the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
