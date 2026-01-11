# Personal Project Manager (PM)

A Python-based personal project manager designed for tracking work tasks, especially for deep learning engineers working on autonomous vehicle projects at NVIDIA.

## Features

- **Task Management**: Track DAT tickets, cross-team dependencies, projects, and training runs
- **Weekly Journal**: Track daily progress with automatic weekly journals and quarterly summaries
- **CLI Interface**: Easy-to-use command-line interface with rich formatting
- **Markdown Storage**: Tasks and journals stored in human-readable markdown files
- **Flexible Scheduling**: Configure check frequencies per task (daily, weekly, biweekly, monthly)
- **Timeline Notifications**: Set specific notification times for tasks (e.g., "notify me in 34 hours")
- **Quarterly Tracking**: Automatic aggregation of weekly summaries for quarterly achievement reports
- **Multiple Interfaces**: CLI and markdown editing (MCP and Web UI coming soon)
- **Background Service**: Systemd integration for periodic checks (future feature)
- **Email Notifications**: Get notified about overdue tasks and reminders (future feature)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Install from source

1. Clone or navigate to the pm-app directory:
```bash
cd pm-app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

3. Install the package:
```bash
pip install -e .
```

Or install dependencies directly:
```bash
pip install -r requirements.txt
```

4. Set up configuration (optional):
```bash
mkdir -p ~/.config/pm
cp config.yaml.example ~/.config/pm/config.yaml
# Edit ~/.config/pm/config.yaml with your settings
```

If you don't create a config file, the app will use defaults and store data in `~/pm-data`.

## Usage

### Basic Commands

#### Add a task
```bash
# Simple task
pm add "Review DAT-12345 labeling status"

# DAT ticket with weekly check
pm add "Check DAT-12345" --type dat_ticket --check-freq weekly

# Cross-team dependency with ETA
pm add "Wait for perception team API" --type cross_team --eta "2026-01-20" --priority high

# Training run with notification
pm add "WaitNet training v2.3" --type training_run --notify "2026-01-12 14:00"

# With description and tags
pm add "Update model architecture" --desc "Implement new attention mechanism" --tags "model,research" --priority high
```

#### List tasks
```bash
# List all active tasks
pm list

# List by status
pm list --status in_progress

# List by type
pm list --type dat_ticket

# List by priority
pm list --priority high

# Search tasks
pm list --search "labeling"

# Include done tasks
pm list --done
```

#### View task details
```bash
pm show task-abc123
```

#### Update a task
```bash
# Update status
pm update task-abc123 --status in_progress

# Update ETA
pm update task-abc123 --eta "2026-01-25"

# Update multiple fields
pm update task-abc123 --priority high --status blocked
```

#### Add notes to a task
```bash
pm note task-abc123 "Contacted team, waiting for response"
pm note task-abc123 "Team confirmed ETA is next week"
```

#### Mark task as done
```bash
pm done task-abc123
```

#### Delete a task
```bash
pm delete task-abc123

# Skip confirmation
pm delete task-abc123 --yes
```

#### View status summary
```bash
pm status
```

#### Check for tasks needing attention
```bash
pm check
```

### Task Types

- **dat_ticket**: DAT (data labeling) tickets that need periodic status checks
- **cross_team**: Tasks dependent on other teams
- **project**: Project milestones and deliverables
- **training_run**: DNN training runs with completion notifications
- **general**: General tasks

### Task Properties

Each task has:
- **ID**: Auto-generated unique identifier
- **Title**: Short description
- **Description**: Detailed information
- **Type**: Task category
- **Status**: todo, in_progress, waiting, blocked, done
- **Priority**: high, medium, low
- **Check Frequency**: How often to check (daily, weekly, biweekly, monthly)
- **ETA**: Expected completion date/time
- **Notify At**: Specific notification time
- **Tags**: Custom labels for organization
- **Dependencies**: Other task IDs this depends on
- **Notes**: Timestamped notes and updates

### Markdown File Editing

Tasks are stored as markdown files in the data directory (default: `~/pm-data/tasks/`). You can directly edit these files and the changes will be reflected in the CLI.

Example task file (`task-abc123.md`):
```markdown
---
id: task-abc123
title: Check DAT-12345 labeling status
type: dat_ticket
status: in_progress
priority: medium
created_at: 2026-01-10T10:00:00
updated_at: 2026-01-10T15:30:00
eta: 2026-01-17T17:00:00
check_frequency: weekly
last_checked: 2026-01-10T10:00:00
dependencies: []
tags:
  - dat
  - labeling
---

## Description
Check status of DAT-12345 for pedestrian detection labeling

## Notes
- 2026-01-10 10:00: Created ticket, waiting for team response
- 2026-01-10 15:30: Team confirmed, ETA next week
```

## Weekly Journal Workflow

The PM app includes a powerful journal system for tracking daily progress and generating quarterly summaries.

### Quick Start

```bash
# Morning: Start your day
pm journal-start
# or: pm js

# Open weekly journal in vim/nvim
pm journal
# or: pm j

# End of day: Sync and review
pm journal-end
# or: pm je

# Friday: Generate weekly summary
pm journal-summary
# or: pm jws

# Quarterly review
pm quarterly 2026 1    # Q1 2026 summary
```

### How It Works

- **Weekly Journals**: One markdown file per week (`2026-W02.md`) with sections for each day
- **Daily Sections**: Each day has Planned, In Progress, Completed, Blocked, and Notes sections
- **Checkbox Sync**: Check boxes in the journal to mark tasks done, auto-syncs with task manager
- **Weekly Summaries**: Auto-generated summaries showing accomplishments and blockers
- **Quarterly Reports**: Aggregates weekly summaries for achievement tracking

### Daily Workflow Example

**Morning (8:00 AM)**:
```bash
pm js              # Start day - auto-populates today's tasks
pm j               # Open journal to review and add notes
```

**During the Day**:
- Work in journal or CLI
- Check boxes as you complete tasks
- Add notes for context

**End of Day (6:00 PM)**:
```bash
pm je              # End day - syncs checkboxes with tasks
```

**Friday EOD**:
```bash
pm jws             # Generate weekly summary
```

For detailed journal documentation, see [JOURNAL.md](JOURNAL.md).

## Configuration

Configuration file location: `~/.config/pm/config.yaml`

See `config.yaml.example` for a complete example with all options.

Key settings:
- `data_dir`: Where to store task files (default: `~/pm-data`)
- `storage_mode`: `multi_file` (one file per task) or `single_file` (all in one file)
- Email notification settings (for future features)
- Scheduler settings (for future background service)

## Workflow Examples

### Managing DAT Tickets
```bash
# Add DAT ticket with weekly check
pm add "Review DAT-45678 annotations" --type dat_ticket --check-freq weekly

# Check which DAT tickets need review
pm list --type dat_ticket

# Add status update
pm note task-xyz789 "50% complete, on track for Monday delivery"

# Mark as done when complete
pm done task-xyz789
```

### Tracking Cross-Team Dependencies
```bash
# Add dependency task
pm add "Wait for sensor team calibration data" --type cross_team --status waiting

# Regular updates
pm note task-abc456 "Slacked @sensor-team, they said Wednesday"
pm update task-abc456 --eta "2026-01-15"

# When unblocked
pm update task-abc456 --status in_progress
```

### Training Run Management
```bash
# Training that will finish in 34 hours
pm add "WaitNet v3 QAT training" --type training_run --notify "2026-01-12 10:00"

# Add notes during training
pm note task-train99 "Loss converging well, ETA still on track"

# When complete, check eval
pm add "Check WaitNet v3 eval results" --desc "Review KPIs from training task-train99"
```

### Project Tracking
```bash
# Add project milestone
pm add "Complete Q1 model release" --type project --eta "2026-03-31" --priority high

# Track sub-tasks
pm add "Merge detection improvements" --tags "q1-release" --eta "2026-02-15"
pm add "Run benchmark suite" --tags "q1-release" --eta "2026-02-28"
pm add "Write release notes" --tags "q1-release" --eta "2026-03-28"

# Check progress
pm list --tags "q1-release"
```

## Data Directory Structure

```
~/pm-data/
└── tasks/
    ├── task-abc123.md
    ├── task-def456.md
    └── task-ghi789.md
```

## Future Features

Coming soon:
- **MCP Server**: Integration with AI agents and IDEs
- **Web UI**: Browser-based interface using FastAPI + React
- **Background Service**: Systemd service for automated checks and notifications
- **Email Notifications**: Automated email summaries and reminders
- **Slack Integration**: Send updates to Slack channels
- **JIRA/GitHub Integration**: Sync with external ticket systems
- **Analytics**: Task completion rates, time tracking, reports

## Development

### Running tests

The project has comprehensive unit tests covering all core functionality (84 tests, 100% passing).

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_task.py

# Run tests in quiet mode
pytest tests/ -q
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

### Code formatting
```bash
black pm/
ruff check pm/
```

### Project Structure
```
pm-app/
├── pm/
│   ├── core/           # Core business logic
│   │   ├── task.py     # Task data model
│   │   ├── storage.py  # Markdown I/O
│   │   └── manager.py  # Task CRUD operations
│   ├── cli/            # CLI interface
│   │   └── commands.py # CLI commands
│   └── utils/          # Utilities
│       └── config.py   # Configuration
├── tests/              # Unit tests (84 tests)
│   ├── conftest.py     # Test fixtures
│   ├── test_task.py    # Task model tests
│   ├── test_storage.py # Storage tests
│   ├── test_manager.py # Manager tests
│   └── test_config.py  # Configuration tests
├── service/            # Background service (future)
├── data/              # Task storage (gitignored)
├── pyproject.toml     # Package configuration
├── requirements.txt   # Dependencies
├── README.md
└── TESTING.md         # Testing documentation
```

## Troubleshooting

### Tasks not showing up
- Check data directory: `ls ~/pm-data/tasks/`
- Verify config: `cat ~/.config/pm/config.yaml`
- Try reloading: Just run any `pm` command, it auto-reloads

### Configuration not working
- Ensure config file is at `~/.config/pm/config.yaml`
- Check YAML syntax (indentation matters!)
- Use `config.yaml.example` as reference

### Date parsing issues
- Use ISO format: `2026-01-20` or `2026-01-20 14:30`
- Natural language works too: `next friday`, `tomorrow 2pm`

## License

MIT License

## Contributing

This is a personal project, but suggestions and contributions are welcome!

## Support

For issues or questions, please contact the maintainer or open an issue in the repository.
