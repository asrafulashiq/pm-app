# Weekly Journal Workflow

## Overview

The PM app includes a powerful weekly journal system designed for tracking daily progress and generating quarterly achievement summaries. Each week has a single markdown journal file with sections for each day.

## Key Concepts

### Weekly Journal Structure

- **One file per week**: `2026-W02.md` (ISO week number)
- **Daily sections**: Monday through Sunday
- **Each day includes**:
  - 📋 Planned tasks
  - 🔄 In Progress (multi-day tasks)
  - 🚫 Blocked tasks
  - ✅ Completed tasks
  - 📝 Notes

### Weekly Summary

At the end of each week (typically Friday), you can generate a summary that includes:
- Tasks accomplished
- Tasks still in progress
- Blockers
- Automatically saved to `2026-W02-summary.md`

### Quarterly Tracking

The system aggregates weekly summaries to provide quarterly achievement reports, helping you track progress across Q1, Q2, Q3, and Q4.

## Daily Workflow

### Morning Routine

**Option 1: Start your day**
```bash
pm journal-start
# or short alias:
pm js
```

This creates today's section in the weekly journal and auto-populates it with:
- Tasks that were in progress yesterday
- Tasks needing check today
- Overdue tasks

**Option 2: Open journal in editor**
```bash
pm journal
# or short alias:
pm j
```

This opens the weekly journal in vim/nvim where you can:
- Review tasks for the week
- Check off completed tasks
- Add notes
- Plan upcoming days

### During the Day

Work with your journal in two ways:

**1. Directly in the journal file**:
- Open: `pm journal`
- Check boxes as you complete tasks: `- [x] task-id: Task title`
- Add notes in the Notes section
- Save and close your editor

**2. Via CLI commands**:
```bash
# Mark task as done
pm done task-abc123

# Add a note
pm note task-abc123 "Made progress on labeling"

# Update status
pm update task-abc123 --status in_progress
```

### End of Day

```bash
pm journal-end
# or short alias:
pm je
```

This:
- Syncs checkbox states with task statuses
- Shows you how many tasks were completed vs. planned
- Prepares for tomorrow

### Manual Sync

If you edited the journal file and want to sync checkboxes with tasks:

```bash
pm journal-sync
```

This reads all checkboxes in the journal and updates task statuses accordingly.

## Weekly Workflow

### End of Week (Friday)

Generate your weekly summary:

```bash
pm journal-summary
# or short alias:
pm jws
```

This creates:
1. A summary section in your weekly journal
2. A separate summary file: `2026-W02-summary.md`

The summary includes:
- Total tasks completed
- Tasks still in progress
- Blockers encountered
- Week-over-week comparison

### Reviewing Past Weeks

```bash
# Open specific week's journal
pm journal --date "2026-01-05"

# Generate summary for past week
pm journal-summary --date "2026-01-05"
```

## Quarterly Tracking

### Generate Quarterly Summary

```bash
pm quarterly 2026 1    # Q1 2026
pm quarterly 2026 2    # Q2 2026
```

This aggregates all weekly summaries for the quarter and shows:
- Total weeks tracked
- Total tasks completed
- Tasks in progress
- Common blockers

Perfect for:
- Performance reviews
- Quarterly planning
- Achievement tracking

## Example Journal File

```markdown
# Week 2 - 2026 (Jan 05 - Jan 11, 2026)

## Monday, Jan 05

### 📋 Planned
- [ ] task-abc123: Review DAT-12345 status (dat_ticket, high)
- [ ] task-def456: Complete model training (training_run, medium)

### 📝 Notes
- Started training run, ETA 34 hours

---

## Tuesday, Jan 06

### 📋 Planned
- [x] task-abc123: Review DAT-12345 status (dat_ticket, high)
- [ ] task-def456: Complete model training (training_run, medium)

### 🔄 In Progress
- task-def456: Complete model training
  - ETA: Jan 07, 14:00

### ✅ Completed
- task-abc123: Review DAT-12345 status

### 📝 Notes
- DAT ticket reviewed, labeling 80% complete
- Training progressing well

---

...

## 📊 Week Summary

**Week:** Jan 05 - Jan 11, 2026
**Completed:** 5 tasks
**In Progress:** 2 tasks

### ✅ Accomplished This Week
- Review DAT-12345 labeling status
- Complete WaitNet v3 training
- Submit Q1 model release
- Fix perception API integration
- Update documentation

### 🔄 Still In Progress
- Cross-team API integration
- Performance benchmarking

### 🚫 Blockers
- Waiting on perception team calibration data
```

## Tips & Best Practices

### 1. Daily Consistency

**Start each work day with**:
```bash
pm js      # Start your day
pm j       # Open journal if needed
```

**End each work day with**:
```bash
pm je      # End your day and sync
```

### 2. Multi-Day Tasks

For long-running tasks (like training runs):
- Add them to multiple days
- Use the "In Progress" section to track across days
- Set `notify_at` for when you need to check them

Example:
```bash
pm add "WaitNet training v3" --type training_run --notify "2026-01-12 10:00"
pm update task-xyz --status in_progress
```

The task will appear in "In Progress" sections automatically.

### 3. Effective Notes

Use the Notes section for:
- Key decisions made
- Blockers encountered
- Important conversations
- Links to resources
- Context for future you

### 4. Weekly Review

On Friday:
1. Review what you accomplished
2. Generate weekly summary: `pm jws`
3. Plan next week's priorities
4. Update any carry-over tasks

### 5. Quarterly Planning

At the end of each quarter:
1. Generate quarterly summary: `pm quarterly 2026 1`
2. Review your achievements
3. Identify patterns in blockers
4. Set goals for next quarter

## Keyboard Shortcuts in Vim/Nvim

When editing journal:
- `/Planned` - Jump to Planned section
- `/Notes` - Jump to Notes section
- `x` - Toggle checkbox state (cursor on checkbox line)
- `o` - New line below
- `/task-` - Search for specific task

## Integration with Tasks

### Automatic Task Population

When you start a day, these tasks are automatically added to Planned:
- Tasks marked `in_progress`
- Tasks with ETAs today or past
- Tasks needing periodic check (based on `check_frequency`)
- Overdue tasks

### Checkbox Sync

- Checking a box `[x]` → marks task as `done`
- Unchecking a box `[ ]` → reopens task to `todo`
- Sync happens when you close the editor or run `pm journal-sync`

### Manual Task Addition

You can manually add tasks to your journal:
```markdown
### 📋 Planned
- [ ] task-abc123: Existing task from task manager
- [ ] Write quarterly report (manual entry, not a tracked task)
```

Only lines with `task-XXXXXX` format will sync with the task manager.

## File Locations

```
~/pm-data/
├── tasks/              # Task files
└── journal/            # Journal files
    ├── 2026-W01.md
    ├── 2026-W02.md
    ├── 2026-W02-summary.md
    └── ...
```

## Troubleshooting

### Journal doesn't open in vim

Set your editor preference:
```bash
pm journal --editor nvim    # Use nvim
pm journal --editor vim     # Use vim
```

Or set `EDITOR` environment variable:
```bash
export EDITOR=nvim
pm journal
```

### Checkboxes not syncing

1. Ensure checkbox format is correct: `- [ ] task-abc123: Title`
2. Run manual sync: `pm journal-sync`
3. Check that task ID exists: `pm show task-abc123`

### Week starts on wrong day

The app uses ISO week format (Monday-Sunday). This is standard for business weeks.

## Advanced Usage

### Custom Editor

```bash
pm journal --editor code    # VS Code
pm journal --editor nano    # Nano
```

### Viewing Specific Dates

```bash
# Open journal for a specific week
pm journal --date "2026-01-05"

# Start day for a past date (for catchup)
pm journal-start --date "2026-01-08"
```

### Bulk Operations

To update multiple tasks at once, edit the journal file directly and run:
```bash
pm journal-sync
```

## Future Enhancements

Planned features:
- [ ] Time tracking per task
- [ ] Daily standup format (yesterday/today/blockers)
- [ ] Integration with calendar
- [ ] Automatic daily email summaries
- [ ] Mobile app sync
- [ ] Team journal sharing

## Support

For issues or questions about the journal workflow:
1. Check this documentation
2. Review [README.md](README.md) for general PM app usage
3. Open an issue in the repository
