
## Agent Developer Notes
Prompt to have AI read the docs and add features to the util:

```
Homebase is an employee scheduling and time tracking system.
The utility script is homebase.py and it contains:
- Employee status lookups (who's working, off, coming next)
- Labor costs grouped by role
- Labor costs grouped by employee
- Timecard records (clock-in/out)

The Homebase API doc is here: https://app.joinhomebase.com/api/public/swagger_doc.json
Read it with browser-use MCP when you need to add a new feature to the script.
```

## Usage

### Show who's working now

```bash
python homebase/homebase.py working
```

### Show labor costs by role

```bash
# Today
python homebase/homebase.py labor

# Date range
python homebase/homebase.py labor --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"
```

### Show labor costs by employee

```bash
# Today
python homebase/homebase.py employees

# Date range
python homebase/homebase.py employees --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"
```

### Show timecards

```bash
# Today (default filter: clock_in)
python homebase/homebase.py timecards

# Date range
python homebase/homebase.py timecards --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"

# Filter by clock_out date
python homebase/homebase.py timecards --date-filter clock_out

# Filter by created_at date
python homebase/homebase.py timecards --date-filter created_at
```
