#!/usr/bin/env python3
"""
Kanboard utility script for creating tasks, checking status, listing tasks,
and finding overdue tasks.

This script provides a simplified interface to interact with Kanboard
via its JSON-RPC API. Supports creating tasks, viewing task status,
listing tasks, and listing overdue tasks in a project.

Usage:
    python kanboard.py create <title> [options]
    python kanboard.py status <task-id> [options]
    python kanboard.py list [options]
    python kanboard.py overdue [options]

Commands:
    create              Create a new Kanboard task
    status              Show the status of a Kanboard task
    list                List tasks in a project
    overdue             List overdue tasks (past due date) in a project

Create options:
    --title TEXT        Task title (required)
    --desc TEXT         Task description (optional)
    --due TEXT          Due date/time in format 'YYYY-MM-DD HH:MM' (optional)
    --project-id INT    Kanboard project ID (default: from env or 2)
    --column-id INT     Kanboard column ID (default: 6 = Ready)
    --swimlane-id INT   Kanboard swimlane ID (omit for default swimlane)
    --dry-run           Preview without creating

Status options:
    task-id             Task ID (positional argument, required)
    --project-id INT    Kanboard project ID (default: from env or 2)

List options:
    --project-id INT    Kanboard project ID (default: from env or 2)
    --all               Include closed/inactive tasks (default: active only)

Overdue options:
    --project-id INT    Kanboard project ID (default: from env or 2)
    --all               Include closed/inactive tasks when checking for overdue
    --overdue-by INT    Show tasks overdue by at least N days (default: 0 = any overdue)

Environment variables (in .env or system):
    KANBOARD_URL        Kanboard API endpoint URL
    KANBOARD_USERNAME   Kanboard API username
    KANBOARD_API_TOKEN  Kanboard API token
    KANBOARD_PROJECT_ID (optional, default 2)

Requirements:
    pip install requests

Examples:
    # Create a simple task
    python kanboard.py create --title "Test task"

    # Create a task with description and due date
    python kanboard.py create \
        --title "Bake sourdough" \
        --desc "Mix flour, water, starter. Bake at 450F." \
        --due "2026-05-20 14:00"

    # Dry run to preview
    python kanboard.py create --title "Test" --dry-run

    # Check task status
    python kanboard.py status 42

    # Check task status with explicit project (for column name resolution)
    python kanboard.py status 42 --project-id 2

    # List active tasks in the default project
    python kanboard.py list

    # List all tasks (including closed) in a specific project
    python kanboard.py list --project-id 2 --all

    # List overdue tasks
    python kanboard.py overdue

    # List overdue tasks in a specific project
    python kanboard.py overdue --project-id 2

    # List tasks overdue by at least 3 days
    python kanboard.py overdue --overdue-by 3

    # Include closed tasks when checking for overdue
    python kanboard.py overdue --all
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests


def load_env():
    """Load configuration from .env file and environment variables."""
    env_vars = {}
    # Resolve .env relative to the script's location, not the working directory
    env_path = Path(__file__).resolve().parent / '.env'
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        env_vars[key.strip()] = value.strip().strip('"')
    except FileNotFoundError:
        pass

    required_keys = [
        'KANBOARD_URL',
        'KANBOARD_USERNAME',
        'KANBOARD_API_TOKEN',
    ]
    optional_keys = {
        'KANBOARD_PROJECT_ID': '2',
    }

    config = {}
    missing = []
    for key in required_keys:
        value = os.environ.get(key) or env_vars.get(key)
        if value is None:
            missing.append(key)
        else:
            config[key] = value

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please set them in .env file or environment variables."
        )

    for key, default in optional_keys.items():
        value = os.environ.get(key) or env_vars.get(key)
        config[key] = value if value is not None else default

    return config


def kanboard_api_call(url, auth, method, params):
    """Make a JSON-RPC call to the Kanboard API."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params,
    }
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if 'error' in result:
            print(f"Kanboard API error: {result['error']}")
            return None
        # Kanboard may return result: false on failure without an error field
        if result.get('result') is False:
            print(f"Kanboard API returned false for method '{method}' with params: {json.dumps(params, indent=2)}")
            return None
        return result.get('result')
    except Exception as e:
        print(f"Kanboard API call failed: {e}")
        return None


def create_task(config, title, description=None, due_datetime=None,
                project_id=None, column_id=6, swimlane_id=None, dry_run=False):
    """
    Create a task in Kanboard.

    Parameters
    ----------
    config : dict
        Configuration dict with KANBOARD_URL, KANBOARD_USERNAME, KANBOARD_API_TOKEN.
    title : str
        Task title.
    description : str, optional
        Task description (Markdown supported).
    due_datetime : datetime, optional
        Due date/time.
    project_id : int, optional
        Kanboard project ID. Defaults to config value.
    column_id : int
        Kanboard column ID (default: 6 = Ready).
    swimlane_id : int, optional
        Kanboard swimlane ID. Omit for default swimlane.
    dry_run : bool
        If True, print what would be done without making API call.

    Returns
    -------
    dict or None
        The created task dict, or None on failure.
    """
    if project_id is None:
        project_id = int(config.get('KANBOARD_PROJECT_ID', 2))

    url = config['KANBOARD_URL']
    auth = (config['KANBOARD_USERNAME'], config['KANBOARD_API_TOKEN'])

    params = {
        "title": title,
        "project_id": project_id,
        "column_id": column_id,
    }
    if description:
        params['description'] = description
    if due_datetime:
        params['date_due'] = due_datetime.strftime('%Y-%m-%d %H:%M')
    if swimlane_id is not None:
        params['swimlane_id'] = swimlane_id

    if dry_run:
        print("[DRY RUN] Would create task with params:")
        print(json.dumps(params, indent=2))
        return None

    task = kanboard_api_call(url, auth, "createTask", params)
    if task:
        print(f"Task created: #{task['id']} - {task['title']}")
    return task


def get_task_status(config, task_id, project_id=None):
    """
    Get the status (column name) of a Kanboard task.

    Parameters
    ----------
    config : dict
        Configuration dict with KANBOARD_URL, KANBOARD_USERNAME, KANBOARD_API_TOKEN.
    task_id : int
        The task ID to look up.
    project_id : int, optional
        Kanboard project ID. Used to resolve column names. Defaults to config value.

    Returns
    -------
    str or None
        The column name, or None on failure.
    """
    if project_id is None:
        project_id = int(config.get('KANBOARD_PROJECT_ID', 2))

    url = config['KANBOARD_URL']
    auth = (config['KANBOARD_USERNAME'], config['KANBOARD_API_TOKEN'])

    task = kanboard_api_call(url, auth, "getTask", {"task_id": task_id})
    if task is None:
        print(f"Task #{task_id} not found or API error.")
        return None

    column = kanboard_api_call(url, auth, "getColumn", {"column_id": int(task['column_id'])})
    column_name = column['title'] if column else f"Column #{task['column_id']}"

    print(column_name)
    return column_name


def list_tasks(config, project_id=None, show_all=False):
    """
    List tasks in a Kanboard project.

    Fetches all tasks via getAllTasks and prints each task's ID, title,
    and column name.

    Parameters
    ----------
    config : dict
        Configuration dict with KANBOARD_URL, KANBOARD_USERNAME, KANBOARD_API_TOKEN.
    project_id : int, optional
        Kanboard project ID. Defaults to config value.
    show_all : bool
        If True, include closed/inactive tasks. Defaults to False (active only).

    Returns
    -------
    list or None
        The list of task dicts, or None on failure.
    """
    if project_id is None:
        project_id = int(config.get('KANBOARD_PROJECT_ID', 2))

    url = config['KANBOARD_URL']
    auth = (config['KANBOARD_USERNAME'], config['KANBOARD_API_TOKEN'])

    status_id = 0 if show_all else 1
    tasks = kanboard_api_call(url, auth, "getAllTasks", {
        "project_id": project_id,
        "status_id": status_id,
    })
    if tasks is None:
        print(f"Failed to fetch tasks for project {project_id}.")
        return None

    if not tasks:
        label = "active" if not show_all else "all"
        print(f"No {label} tasks found in project {project_id}.")
        return tasks

    # Fetch column map for this project so we can resolve column_id -> name
    columns = kanboard_api_call(url, auth, "getColumns", {"project_id": project_id})
    column_map = {}
    if columns:
        for col in columns:
            column_map[int(col['id'])] = col['title']

    for task in tasks:
        col_id = int(task['column_id'])
        col_name = column_map.get(col_id, f"Column #{col_id}")
        print(f"#{task['id']} [{col_name}] {task['title']}")

    return tasks


def list_overdue_tasks(config, project_id=None, show_all=False, overdue_by_days=0):
    """
    List overdue tasks (past their due date) in a Kanboard project.

    Fetches active (or all) tasks via getAllTasks, filters those with a
    ``date_due`` that is in the past, and prints each task's ID, title,
    column name, and due date.

    Parameters
    ----------
    config : dict
        Configuration dict with KANBOARD_URL, KANBOARD_USERNAME, KANBOARD_API_TOKEN.
    project_id : int, optional
        Kanboard project ID. Defaults to config value.
    show_all : bool
        If True, include closed/inactive tasks when checking for overdue.
        Defaults to False (active only).
    overdue_by_days : int
        Minimum number of days past the due date (default: 0 = any overdue).

    Returns
    -------
    list or None
        The list of overdue task dicts, or None on failure.
    """
    if project_id is None:
        project_id = int(config.get('KANBOARD_PROJECT_ID', 2))

    url = config['KANBOARD_URL']
    auth = (config['KANBOARD_USERNAME'], config['KANBOARD_API_TOKEN'])

    status_id = 0 if show_all else 1
    tasks = kanboard_api_call(url, auth, "getAllTasks", {
        "project_id": project_id,
        "status_id": status_id,
    })
    if tasks is None:
        print(f"Failed to fetch tasks for project {project_id}.")
        return None

    if not tasks:
        print(f"No tasks found in project {project_id}.")
        return tasks

    # Fetch column map for this project so we can resolve column_id -> name
    columns = kanboard_api_call(url, auth, "getColumns", {"project_id": project_id})
    column_map = {}
    if columns:
        for col in columns:
            column_map[int(col['id'])] = col['title']

    now = datetime.now()
    overdue_tasks = []

    for task in tasks:
        date_due = task.get('date_due')
        if not date_due:
            continue

        # Kanboard returns date_due as a Unix timestamp (seconds since epoch)
        try:
            due_dt = datetime.fromtimestamp(int(date_due))
        except (ValueError, TypeError, OSError):
            continue

        # Calculate how many days overdue (negative if not yet due)
        delta = now - due_dt
        days_overdue = delta.total_seconds() / 86400.0

        if days_overdue >= overdue_by_days:
            col_id = int(task['column_id'])
            col_name = column_map.get(col_id, f"Column #{col_id}")
            overdue_tasks.append(task)
            print(
                f"#{task['id']} [{col_name}] {task['title']} "
                f"(due: {due_dt.strftime('%Y-%m-%d %H:%M')} "
            )

    if not overdue_tasks:
        print("No overdue tasks found.")

    return overdue_tasks


def main():
    parser = argparse.ArgumentParser(
        description='Kanboard utility: create tasks and check task status.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='Sub-command')

    # Create sub-command
    create_parser = subparsers.add_parser('create', help='Create a new Kanboard task')
    create_parser.add_argument('--title', required=True, help='Task title')
    create_parser.add_argument('--desc', help='Task description (Markdown supported)')
    create_parser.add_argument('--due', help='Due date/time (format: YYYY-MM-DD HH:MM)')
    create_parser.add_argument('--project-id', type=int, help='Kanboard project ID (default: from env)')
    create_parser.add_argument('--column-id', type=int, default=6, help='Kanboard column ID (default: 6 = Ready)')
    create_parser.add_argument('--swimlane-id', type=int, default=None, help='Kanboard swimlane ID (omit for default swimlane)')
    create_parser.add_argument('--dry-run', action='store_true', help='Preview without creating')

    # Status sub-command
    status_parser = subparsers.add_parser('status', help='Show the status of a Kanboard task')
    status_parser.add_argument('task_id', type=int, help='Task ID to look up')
    status_parser.add_argument('--project-id', type=int, help='Kanboard project ID (default: from env)')

    # List sub-command
    list_parser = subparsers.add_parser('list', help='List tasks in a project')
    list_parser.add_argument('--project-id', type=int, help='Kanboard project ID (default: from env)')
    list_parser.add_argument('--all', action='store_true', help='Include closed/inactive tasks')

    # Overdue sub-command
    overdue_parser = subparsers.add_parser('overdue', help='List overdue tasks in a project')
    overdue_parser.add_argument('--project-id', type=int, help='Kanboard project ID (default: from env)')
    overdue_parser.add_argument('--all', action='store_true', help='Include closed/inactive tasks when checking for overdue')
    overdue_parser.add_argument('--overdue-by', type=int, default=0, help='Show tasks overdue by at least N days (default: 0 = any overdue)')

    args = parser.parse_args()

    # Load config
    try:
        config = load_env()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.command == 'create':
        # Parse due datetime if provided
        due_datetime = None
        if args.due:
            try:
                due_datetime = datetime.strptime(args.due, '%Y-%m-%d %H:%M')
            except ValueError:
                print(f"Error: Invalid due date format '{args.due}'. Expected format: YYYY-MM-DD HH:MM")
                sys.exit(1)

        # Create the task
        create_task(
            config=config,
            title=args.title,
            description=args.desc,
            due_datetime=due_datetime,
            project_id=args.project_id,
            column_id=args.column_id,
            swimlane_id=args.swimlane_id,
            dry_run=args.dry_run,
        )

    elif args.command == 'status':
        get_task_status(
            config=config,
            task_id=args.task_id,
            project_id=args.project_id,
        )

    elif args.command == 'list':
        list_tasks(
            config=config,
            project_id=args.project_id,
            show_all=args.all,
        )

    elif args.command == 'overdue':
        list_overdue_tasks(
            config=config,
            project_id=args.project_id,
            show_all=args.all,
            overdue_by_days=args.overdue_by,
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
