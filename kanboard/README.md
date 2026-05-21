

## Agent Developer Notes
Prompt to have AI read the docs and add features to the util:

```
Kanboard is a task management system. 
The utility script is kanboard.py and it contains:
- Task creations
- Task status lookups
- Task listing
- more coming soon...

The kanboard API doc is here: https://docs.kanboard.org/v1/api/
Read it with browser-use MCP when you need to add a new feature to the script.
```

## Usage

### Create a task

```bash
python utils/kanboard/kanboard.py create --title "My task"
python utils/kanboard/kanboard.py create --title "Bake sourdough" --desc "Mix flour, water, starter." --due "2026-05-20 14:00"
python utils/kanboard/kanboard.py create --title "Test" --dry-run
```

### Check task status

```bash
python utils/kanboard/kanboard.py status 42
python utils/kanboard/kanboard.py status 42 --project-id 2
```

### List tasks

```bash
python utils/kanboard/kanboard.py list
python utils/kanboard/kanboard.py list --project-id 2
python utils/kanboard/kanboard.py list --project-id 2 --all
```
