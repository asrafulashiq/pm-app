# MCP Server for PM App

The PM app includes a Model Context Protocol (MCP) server that exposes task management, queries, and journal operations to AI agents like Claude.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how AI applications access external data and tools. It enables AI assistants to interact with your PM app to create tasks, query your work, and manage your journal.

## Starting the Server

```bash
# From the pm-app directory
pm mcp-server
```

The server runs in the foreground and communicates via stdio (standard input/output). Press Ctrl+C to stop the server.

## Available Tools

The MCP server provides **18 tools** organized into three categories:

### Task Management Tools (8)

1. **create_task** - Create a new task with title, description, type, priority, status, tags, and dependencies
2. **list_tasks** - List all tasks with optional filters (status, type, priority, tags, search)
3. **get_task** - Get detailed information about a specific task by ID
4. **update_task** - Update task properties
5. **delete_task** - Delete a task by ID
6. **add_task_note** - Add a timestamped note to a task
7. **mark_task_done** - Mark a task as completed
8. **mark_task_in_progress** - Set a task to in-progress status

### Query Tools (4)

9. **get_overdue_tasks** - List tasks past their ETA
10. **get_tasks_needing_check** - Get tasks due for periodic check
11. **get_task_summary** - Get statistics (counts by status, type, priority)
12. **search_tasks** - Full-text search in title and description

### Journal Tools (6)

13. **start_journal_day** - Initialize today's journal section with auto-populated tasks
14. **end_journal_day** - Finalize today's section and sync task statuses
15. **get_current_journal** - Get current week's journal content (full markdown)
16. **sync_journal** - Manual sync of journal checkboxes with task statuses
17. **generate_week_summary** - Create weekly summary with completed/blocked tasks
18. **get_quarterly_summary** - Aggregate completed tasks for a quarter

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pm": {
      "command": "pm",
      "args": ["mcp-server"],
      "cwd": "/home/aislam/projects-personal/pm-app"
    }
  }
}
```

After adding the configuration, restart Claude Desktop.

### Cline (VS Code Extension)

In VS Code settings (`.vscode/settings.json` or user settings):

```json
{
  "cline.mcpServers": {
    "pm": {
      "command": "pm",
      "args": ["mcp-server"],
      "cwd": "/home/aislam/projects-personal/pm-app"
    }
  }
}
```

### Other MCP Clients

Any MCP client that supports stdio transport can connect. The basic configuration requires:

- **Command**: `pm` (or full path to pm executable)
- **Args**: `["mcp-server"]`
- **Transport**: stdio
- **Working Directory**: Path to pm-app directory (to use correct venv)

## Example Usage

Once configured, you can ask your AI assistant natural language queries like:

**Creating tasks:**
```
"Create a high-priority DAT ticket task for reviewing labeling quality with ETA next Friday"
```

**Querying tasks:**
```
"Show me all overdue tasks"
"What tasks do I have in progress?"
"Search for tasks related to WaitNet"
```

**Managing journal:**
```
"Start my journal for today"
"What's in my current journal?"
"Generate this week's summary"
```

**Getting insights:**
```
"Give me a summary of my tasks by status"
"What did I accomplish last quarter?"
```

## Tool Details

### create_task

**Parameters:**
- `title` (required): Task title
- `description`: Detailed description
- `task_type`: One of: `dat_ticket`, `cross_team`, `project`, `training_run`, `general` (default: `general`)
- `priority`: One of: `high`, `medium`, `low` (default: `medium`)
- `status`: One of: `todo`, `in_progress`, `waiting`, `blocked`, `done` (default: `todo`)
- `check_frequency`: One of: `daily`, `weekly`, `biweekly`, `monthly` (default: `weekly`)
- `eta`: ISO datetime string (e.g., `"2026-01-20T17:00:00"`)
- `notify_at`: ISO datetime string
- `tags`: Array of strings
- `dependencies`: Array of task IDs

**Returns:** Serialized task object with ID and all properties

### list_tasks

**Parameters (all optional):**
- `status`: Filter by status
- `task_type`: Filter by type
- `priority`: Filter by priority
- `tags`: Array of tags (any match)
- `search`: Search string for title/description

**Returns:** Array of task objects

### get_task

**Parameters:**
- `task_id` (required): Task ID to retrieve

**Returns:** Task object or null if not found

### update_task

**Parameters:**
- `task_id` (required): Task ID to update
- All other parameters from `create_task` (optional)

**Returns:** Updated task object or null if not found

### delete_task

**Parameters:**
- `task_id` (required): Task ID to delete

**Returns:** Boolean (true if deleted, false if not found)

### add_task_note

**Parameters:**
- `task_id` (required): Task ID
- `note` (required): Note content

**Returns:** Updated task with new note appended

### mark_task_done / mark_task_in_progress

**Parameters:**
- `task_id` (required): Task ID

**Returns:** Updated task with new status

### get_overdue_tasks

**Parameters:** None

**Returns:** Array of tasks past their ETA (excludes done tasks)

### get_tasks_needing_check

**Parameters:** None

**Returns:** Array of tasks due for periodic check based on check_frequency

### get_task_summary

**Parameters:** None

**Returns:** Statistics object:
```json
{
  "total": 42,
  "by_status": {"todo": 15, "in_progress": 10, ...},
  "by_type": {"dat_ticket": 20, "project": 12, ...},
  "by_priority": {"high": 8, "medium": 25, "low": 9}
}
```

### search_tasks

**Parameters:**
- `query` (required): Search string

**Returns:** Array of tasks matching query in title or description (case-insensitive)

### start_journal_day

**Parameters:** None

**Returns:**
```json
{
  "journal_path": "/path/to/2026-W02.md",
  "day": "Friday",
  "planned_tasks": ["task-123", "task-456"]
}
```

### end_journal_day

**Parameters:** None

**Returns:**
```json
{
  "day": "Friday",
  "completed_tasks": ["task-123"],
  "blocked_tasks": ["task-789"]
}
```

### get_current_journal

**Parameters:** None

**Returns:**
```json
{
  "journal_path": "/path/to/2026-W02.md",
  "year": 2026,
  "week": 2,
  "content": "# Week 2, 2026\n## Monday\n..."
}
```

### sync_journal

**Parameters:** None

**Returns:**
```json
{
  "synced_tasks": 5,
  "task_ids": ["task-123", "task-456", ...]
}
```

### generate_week_summary

**Parameters:** None

**Returns:** Weekly summary object with:
- `week_start`, `week_end`: ISO datetime strings
- `tasks_completed`: Array of task IDs
- `tasks_in_progress`: Array of task IDs
- `blockers`: Array of blocker descriptions
- `notes`: Summary notes

### get_quarterly_summary

**Parameters (both optional):**
- `year`: Year (default: current year)
- `quarter`: Quarter 1-4 (default: current quarter)

**Returns:**
```json
{
  "year": 2026,
  "quarter": 1,
  "total_completed": 45,
  "achievements": ["task-1", "task-2", ...],
  "total_in_progress": 12,
  "in_progress": ["task-x", "task-y", ...]
}
```

## Concurrency and File Watching

The MCP server creates a fresh `TaskManager` and `JournalManager` instance for each tool call. This ensures that:

1. **Manual edits are always visible** - If you edit a task markdown file directly, the next MCP call will see those changes
2. **No stale data** - Each request loads the latest state from disk
3. **Safe concurrent access** - You can use the CLI and MCP server simultaneously

The storage layer uses atomic file writes to prevent corruption.

## Troubleshooting

### Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:** Ensure MCP is installed:
```bash
pip install mcp>=0.9.0
```

**Error:** `pm: command not found`

**Solution:** Activate the virtual environment or use full path to pm:
```bash
# In MCP config
"command": "/full/path/to/venv/bin/pm"
```

### Client Can't Connect

1. Check that the `cwd` in MCP config points to the pm-app directory
2. Verify pm executable is in PATH or use full path
3. Check client logs for connection errors
4. Try running `pm mcp-server` manually to see error messages

### Tasks Not Updating

1. Ensure you're using the correct data directory
2. Check file permissions on `~/pm-data`
3. Verify no other process is locking the files
4. Check server logs for errors

### Performance Issues

Each MCP call creates a new TaskManager and loads all tasks from disk. For large task sets (1000+ tasks):

1. Consider archiving old completed tasks
2. Use filtered queries (`list_tasks` with filters) instead of loading all tasks
3. Use `search_tasks` with specific queries

## Development

### Running Tests

```bash
# All MCP tests (80 tests)
pytest tests/mcp/ -v

# Specific test suite
pytest tests/mcp/test_task_tools.py -v
pytest tests/mcp/test_query_tools.py -v
pytest tests/mcp/test_journal_tools.py -v
```

### Adding New Tools

1. Create the tool function in appropriate module (`task_tools.py`, `query_tools.py`, `journal_tools.py`)
2. Add comprehensive tests
3. Export from `tools/__init__.py`
4. Add tool definition to `TOOLS` list in `server.py`
5. Add handler to `TOOL_HANDLERS` dict
6. Update this documentation

## Security Notes

- The MCP server runs **locally only** (stdio transport)
- No network exposure - can't be accessed remotely
- No authentication required (assumes local trust)
- File access limited to configured data directory (`~/pm-data`)
- No remote code execution - only predefined tools callable

## Architecture

```
┌─────────────┐
│ MCP Client  │ (Claude Desktop, Cline, etc.)
│ (AI Agent)  │
└──────┬──────┘
       │ stdio (stdin/stdout)
       ├─ Tool Requests (JSON-RPC)
       └─ Tool Responses (JSON)
       │
┌──────▼──────┐
│  MCP Server │ (pm mcp-server)
│  server.py  │
└──────┬──────┘
       │
       ├─ Task Tools (8)
       ├─ Query Tools (4)
       └─ Journal Tools (6)
       │
┌──────▼────────┐
│  Core Modules │
│  TaskManager  │
│ JournalManager│
└──────┬────────┘
       │
┌──────▼──────┐
│   Storage   │ (Markdown files + YAML frontmatter)
│  ~/pm-data  │
└─────────────┘
```

## Changelog

**v1.0.0** (2026-01-11)
- Initial MCP server implementation
- 18 tools across task management, queries, and journal operations
- stdio transport with Claude Desktop support
- Comprehensive test suite (80 tests)
- Full documentation

## License

Same as PM app - see main README.md

## Support

For issues, questions, or feature requests related to the MCP server, please open an issue on GitHub or contact the maintainer.
