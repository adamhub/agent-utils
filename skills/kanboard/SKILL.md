---
name: kanboard
description: Task management via the Kanboard JSON-RPC API. Use when the user asks to create tasks, check task status, list tasks, find overdue tasks, or manage a Kanban board. Triggers for queries like "create a task", "task status", "list tasks", "overdue tasks", "what's on my board", "add a todo", or any Kanboard-related project management questions.
---

# Kanboard Skill

The `kanboard` command provides access to task management via the Kanboard JSON-RPC API.

## Prerequisites

The `kanboard` CLI is globally available. It reads configuration from a `.env` file located alongside the script, or from environment variables:

- `KANBOARD_URL` — Kanboard API endpoint URL (required)
- `KANBOARD_USERNAME` — Kanboard API username (required)
- `KANBOARD_API_TOKEN` — Kanboard API token (required)
- `KANBOARD_PROJECT_ID` — Default project ID (optional, default: 2)

## Commands

### `kanboard create`

Create a new Kanboard task.

```bash
kanboard create --title "My task"
kanboard create --title "Bake sourdough" --desc "Mix flour, water, starter. Bake at 450F." --due "2026-05-20 14:00"
kanboard create --title "Test" --dry-run
```

Options:
- `--title TEXT` — Task title (required)
- `--desc TEXT` — Task description, Markdown supported (optional)
- `--due TEXT` — Due date in format `YYYY-MM-DD HH:MM` (optional)
- `--project-id INT` — Kanboard project ID (default: from env or 2)
- `--column-id INT` — Kanboard column ID (default: 6 = Ready)
- `--swimlane-id INT` — Kanboard swimlane ID (omit for default swimlane)
- `--dry-run` — Preview without creating

### `kanboard status`

Show the status (column name) of a Kanboard task.

```bash
kanboard status 42
kanboard status 42 --project-id 2
```

### `kanboard list`

List tasks in a project.

```bash
# Active tasks only
kanboard list

# All tasks including closed
kanboard list --all

# Specific project
kanboard list --project-id 2
```

### `kanboard overdue`

List overdue tasks (past their due date) in a project.

```bash
# Any overdue tasks
kanboard overdue

# Overdue by at least 3 days
kanboard overdue --overdue-by 3

# Include closed tasks
kanboard overdue --all

# Specific project
kanboard overdue --project-id 2
```

## Common Workflows

### "Create a task for me"

```bash
kanboard create --title "Review Q2 budget" --desc "Go through Q2 financials and prepare summary" --due "2026-06-05 17:00"
```

### "What's on my board?"

```bash
kanboard list
```

### "What's overdue?"

```bash
kanboard overdue
```

### "Check task status"

```bash
kanboard status 42
```

### "Create a task with a dry run first"

```bash
kanboard create --title "New feature" --dry-run
# Then remove --dry-run to actually create
```

## Notes

- Default project ID is 2 (configurable via `KANBOARD_PROJECT_ID` env var).
- Default column for new tasks is 6 (Ready).
- Due dates use `YYYY-MM-DD HH:MM` format.
- The API doc is at `https://docs.kanboard.org/v1/api/` if new features need to be added to the script.
