---
name: homebase
description: Employee scheduling and time tracking via the Homebase API. Use when the user asks about employee status, who's working now, labor costs, timecards, schedules, or shift information. Triggers for queries like "who's working", "labor costs", "timecards", "employee schedule", "clocked in", "who's on shift", or any Homebase-related staffing questions.
---

# Homebase Skill

The `homebase` command provides access to employee scheduling and time tracking data via the Homebase Public API.

## Prerequisites

The `homebase` CLI is globally available. It reads configuration from a `.env` file located alongside the script, or from environment variables:

- `HOMEBASE_API_KEY` — Homebase API Bearer token (required)
- `HOMEBASE_LOCATION_UUID_MURPHYS` — Location UUID for Murphy's (optional, can be passed via `--location-uuid`)

## Commands

### `homebase working`

Show which employees are currently working, who's off duty, and who's coming next.

```bash
homebase working
homebase working --location-uuid <uuid>
```

Output includes: employee name, role, shift times, and clock-in time for currently working employees.

### `homebase labor`

Show aggregate labor costs grouped by role for a date range.

```bash
# Today
homebase labor

# Date range
homebase labor --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"

# Different location
homebase labor --location-uuid <uuid>
```

Output includes: labor cost, paid hours, regular hours, overtime, and scheduled hours per role.

### `homebase employees`

Show aggregate labor costs grouped by employee for a date range.

```bash
# Today
homebase employees

# Date range
homebase employees --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"
```

Output includes: employee name, role, wage rate, labor cost, paid hours, regular hours, overtime, and scheduled hours.

### `homebase timecards`

Show timecard records (clock-in/out) for a date range.

```bash
# Today (default filter: clock_in)
homebase timecards

# Date range
homebase timecards --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"

# Filter by clock_out date
homebase timecards --date-filter clock_out

# Filter by created_at date
homebase timecards --date-filter created_at
```

Output includes: employee name, role, clock-in/out times, labor cost, hours, breaks, and clocked-in status.

## Common Workflows

### "Who's working right now?"

```bash
homebase working
```

### "What are my labor costs today?"

```bash
homebase labor
homebase employees
```

### "Show me timecards for the past week"

```bash
homebase timecards --start-date "2026-05-22T00:00:00Z" --end-date "2026-05-29T23:59:59Z"
```

### "How much overtime did we have last week?"

```bash
homebase labor --start-date "2026-05-22T00:00:00Z" --end-date "2026-05-29T23:59:59Z"
```

Look for the `Overtime` field in the output per role.

## Notes

- All date parameters use ISO 8601 format.
- Default location is Murphy's (from `HOMEBASE_LOCATION_UUID_MURPHYS`).
- The `--location-uuid` flag overrides the default location for any command.
- The API doc is at `https://app.joinhomebase.com/api/public/swagger_doc.json` if new features need to be added to the script.
