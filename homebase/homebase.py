#!/usr/bin/env python3
"""
Homebase utility script for checking employee status, labor costs, and timecards.

This script provides a simplified interface to interact with the Homebase
Public API. Supports viewing which employees are currently working, when
they are off, who's coming on next, labor costs grouped by role or employee,
and timecard records.

Usage:
    python homebase.py working [options]
    python homebase.py labor [options]
    python homebase.py employees [options]
    python homebase.py timecards [options]

Commands:
    working             Show which employees are currently working, off, and coming next
    labor               Show labor costs grouped by role for a date range
    employees           Show labor costs grouped by employee for a date range
    timecards           Show timecard records (clock-in/out) for a date range

Working options:
    --location-uuid TEXT   Location UUID (default: from env HOMEBASE_LOCATION_UUID_MURPHYS)

Labor options:
    --location-uuid TEXT   Location UUID (default: from env HOMEBASE_LOCATION_UUID_MURPHYS)
    --start-date TEXT      Start date in ISO 8601 format (default: today)
    --end-date TEXT        End date in ISO 8601 format (default: today)

Employees options:
    --location-uuid TEXT   Location UUID (default: from env HOMEBASE_LOCATION_UUID_MURPHYS)
    --start-date TEXT      Start date in ISO 8601 format (default: today)
    --end-date TEXT        End date in ISO 8601 format (default: today)

Timecards options:
    --location-uuid TEXT   Location UUID (default: from env HOMEBASE_LOCATION_UUID_MURPHYS)
    --start-date TEXT      Start date in ISO 8601 format (default: today)
    --end-date TEXT        End date in ISO 8601 format (default: today)
    --date-filter TEXT     Filter field: clock_in, clock_out, created_at, updated_at (default: clock_in)

Environment variables (in .env or system):
    HOMEBASE_API_KEY                    Homebase API key (Bearer token)
    HOMEBASE_LOCATION_UUID_MURPHYS      Location UUID for Murphy's location

Requirements:
    pip install requests

Examples:
    # Show who's working now
    python homebase.py working

    # Show labor costs by role for today
    python homebase.py labor

    # Show labor costs by employee for today
    python homebase.py employees

    # Show timecards for today
    python homebase.py timecards

    # Show timecards for a specific date range
    python homebase.py timecards --start-date "2026-05-25T00:00:00Z" --end-date "2026-05-29T23:59:59Z"
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, date
from pathlib import Path

import requests


HOMEBASE_API_HOST = "app.joinhomebase.com"
HOMEBASE_API_BASE = f"https://{HOMEBASE_API_HOST}/api/public"


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
        'HOMEBASE_API_KEY',
    ]
    optional_keys = {
        'HOMEBASE_LOCATION_UUID_MURPHYS': None,
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


def homebase_api_call(config, method, path, params=None, data=None):
    """
    Make an HTTP request to the Homebase API.

    Parameters
    ----------
    config : dict
        Configuration dict with HOMEBASE_API_KEY.
    method : str
        HTTP method (GET, POST, etc.).
    path : str
        API path relative to base (e.g., '/locations/{uuid}/shifts').
    params : dict, optional
        Query string parameters.
    data : dict, optional
        JSON body for POST requests.

    Returns
    -------
    dict or list or None
        Parsed JSON response, or None on failure.
    """
    url = f"{HOMEBASE_API_BASE}{path}"
    headers = {
        'Authorization': f"Bearer {config['HOMEBASE_API_KEY']}",
        'Accept': 'application/vnd.homebase-v1+json',
        'Content-Type': 'application/json',
    }
    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=15,
        )
        resp.raise_for_status()
        # Some endpoints return empty body on success (e.g., 201 Created)
        if resp.status_code == 201 and not resp.text.strip():
            return {"status": "created"}
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = resp.json()
            print(f"Homebase API error ({resp.status_code}): {json.dumps(error_detail, indent=2)}")
        except (ValueError, json.JSONDecodeError):
            print(f"Homebase API error ({resp.status_code}): {e}")
        return None
    except Exception as e:
        print(f"Homebase API call failed: {e}")
        return None


def get_today_data(config, location_uuid):
    """
    Fetch today's shifts and timecards for a given location.

    The shifts endpoint provides schedule info (start_at, end_at, role, name)
    but does NOT include the timecard object with clock_in/clock_out data.
    The timecards endpoint provides actual clock-in/out timestamps.

    We fetch both and cross-reference them by user_id to determine who is
    currently clocked in.

    Parameters
    ----------
    config : dict
        Configuration dict.
    location_uuid : str
        Location UUID.

    Returns
    -------
    tuple (list, list) or (None, None)
        (shifts, timecards), or (None, None) on failure.
    """
    today = date.today()
    start_date = today.strftime('%Y-%m-%dT00:00:00Z')
    end_date = today.strftime('%Y-%m-%dT23:59:59Z')

    shifts = homebase_api_call(
        config,
        'GET',
        f"/locations/{location_uuid}/shifts",
        params={
            'start_date': start_date,
            'end_date': end_date,
            'per_page': 100,
        },
    )
    if shifts is None:
        return None, None

    timecards = homebase_api_call(
        config,
        'GET',
        f"/locations/{location_uuid}/timecards",
        params={
            'start_date': start_date,
            'end_date': end_date,
            'per_page': 100,
        },
    )
    if timecards is None:
        return None, None

    return shifts, timecards


def show_working(config, location_uuid=None):
    """
    Show which employees are currently working, who is off, and who's coming next.

    Uses the timecards endpoint to determine clocked-in status (since the
    shifts endpoint does not include timecard clock_in/clock_out data),
    and the shifts endpoint for schedule information.

    Parameters
    ----------
    config : dict
        Configuration dict.
    location_uuid : str, optional
        Location UUID. Defaults to config value.
    """
    if location_uuid is None:
        location_uuid = config.get('HOMEBASE_LOCATION_UUID_MURPHYS')
        if not location_uuid:
            print("Error: No location UUID provided. Set HOMEBASE_LOCATION_UUID_MURPHYS in .env or pass --location-uuid.")
            return

    shifts, timecards = get_today_data(config, location_uuid)
    if shifts is None or timecards is None:
        print("Failed to fetch data from Homebase API.")
        return

    now = datetime.now(timezone.utc)

    # Build a set of user_ids that are currently clocked in (clock_in set, no clock_out)
    clocked_in_user_ids = set()
    clocked_in_details = {}  # user_id -> {clock_in, role, first_name, last_name}
    for tc in timecards:
        clock_in_str = tc.get('clock_in')
        clock_out_str = tc.get('clock_out')
        if clock_in_str and not clock_out_str:
            uid = tc.get('user_id')
            if uid:
                clocked_in_user_ids.add(uid)
                clocked_in_details[uid] = {
                    'clock_in': clock_in_str,
                    'first_name': tc.get('first_name', ''),
                    'last_name': tc.get('last_name', ''),
                    'role': tc.get('role', ''),
                }

    currently_working = []
    off_duty = []
    coming_next = []

    for shift in shifts:
        first_name = shift.get('first_name', 'Unknown')
        last_name = shift.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        role = shift.get('role', '')
        user_id = shift.get('user_id')
        start_at_str = shift.get('start_at')
        end_at_str = shift.get('end_at')

        # Parse times
        start_at = None
        end_at = None
        if start_at_str:
            try:
                start_at = datetime.fromisoformat(start_at_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        if end_at_str:
            try:
                end_at = datetime.fromisoformat(end_at_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Determine if currently clocked in via timecards data
        clocked_in = user_id in clocked_in_user_ids

        entry = {
            'name': name,
            'role': role,
            'start_at': start_at,
            'end_at': end_at,
            'shift': shift,
        }

        if clocked_in:
            # Add clock_in time from timecard for display
            details = clocked_in_details.get(user_id, {})
            if details.get('clock_in'):
                try:
                    entry['clock_in'] = datetime.fromisoformat(details['clock_in'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    entry['clock_in'] = None
            currently_working.append(entry)
        elif start_at and start_at > now:
            coming_next.append(entry)
        else:
            off_duty.append(entry)

    # Sort coming next by start time
    coming_next.sort(key=lambda x: x['start_at'] if x['start_at'] else datetime.max.replace(tzinfo=timezone.utc))

    print("=" * 60)
    print("  HOMEBASE - EMPLOYEE STATUS")
    print("=" * 60)

    # Currently Working
    print(f"\n  \033[1;32m● Currently Working ({len(currently_working)})\033[0m")
    print("  " + "-" * 56)
    if currently_working:
        for emp in currently_working:
            role_str = f" [{emp['role']}]" if emp['role'] else ""
            start_str = emp['start_at'].strftime('%I:%M %p').lstrip('0') if emp['start_at'] else '?'
            end_str = emp['end_at'].strftime('%I:%M %p').lstrip('0') if emp['end_at'] else '?'
            clock_in = emp.get('clock_in')
            if clock_in:
                clock_in_time = clock_in.strftime('%I:%M %p').lstrip('0')
                print(f"    {emp['name']}{role_str}")
                print(f"      Shift: {start_str} - {end_str}  (clocked in at {clock_in_time})")
            else:
                print(f"    {emp['name']}{role_str}")
                print(f"      Shift: {start_str} - {end_str}")
    else:
        print("    No one is currently clocked in.")

    # Coming Next
    print(f"\n  \033[1;34m→ Coming Next ({len(coming_next)})\033[0m")
    print("  " + "-" * 56)
    if coming_next:
        for emp in coming_next:
            role_str = f" [{emp['role']}]" if emp['role'] else ""
            start_str = emp['start_at'].strftime('%I:%M %p').lstrip('0') if emp['start_at'] else '?'
            end_str = emp['end_at'].strftime('%I:%M %p').lstrip('0') if emp['end_at'] else '?'
            print(f"    {emp['name']}{role_str}")
            print(f"      Shift: {start_str} - {end_str}")
    else:
        print("    No upcoming shifts.")

    # Off Duty
    print(f"\n  \033[1;33m● Off Duty ({len(off_duty)})\033[0m")
    print("  " + "-" * 56)
    if off_duty:
        for emp in off_duty:
            role_str = f" [{emp['role']}]" if emp['role'] else ""
            start_str = emp['start_at'].strftime('%I:%M %p').lstrip('0') if emp['start_at'] else '?'
            end_str = emp['end_at'].strftime('%I:%M %p').lstrip('0') if emp['end_at'] else '?'
            print(f"    {emp['name']}{role_str}")
            print(f"      Shift: {start_str} - {end_str}")
    else:
        print("    No one is off duty today.")

    print()


def show_labor_by_role(config, start_date=None, end_date=None, location_uuid=None):
    """
    Show aggregate labor costs grouped by role for a date range.

    Parameters
    ----------
    config : dict
        Configuration dict.
    start_date : str, optional
        Start date in ISO 8601 format. Defaults to today start.
    end_date : str, optional
        End date in ISO 8601 format. Defaults to today end.
    location_uuid : str, optional
        Location UUID. Defaults to config value.
    """
    if location_uuid is None:
        location_uuid = config.get('HOMEBASE_LOCATION_UUID_MURPHYS')
        if not location_uuid:
            print("Error: No location UUID provided. Set HOMEBASE_LOCATION_UUID_MURPHYS in .env or pass --location-uuid.")
            return

    if start_date is None:
        start_date = date.today().strftime('%Y-%m-%dT00:00:00Z')
    if end_date is None:
        end_date = date.today().strftime('%Y-%m-%dT23:59:59Z')

    roles = homebase_api_call(
        config,
        'GET',
        f"/locations/{location_uuid}/labor/by_role",
        params={
            'start_date': start_date,
            'end_date': end_date,
        },
    )
    if roles is None:
        print("Failed to fetch labor data.")
        return

    if not roles:
        print("No labor data found for the specified date range.")
        return

    # Parse dates for display
    try:
        start_display = datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime('%b %d')
    except (ValueError, AttributeError):
        start_display = start_date[:10]
    try:
        end_display = datetime.fromisoformat(end_date.replace('Z', '+00:00')).strftime('%b %d')
    except (ValueError, AttributeError):
        end_display = end_date[:10]

    print("=" * 60)
    print(f"  HOMEBASE - LABOR BY ROLE")
    print(f"  {start_display} - {end_display}")
    print("=" * 60)

    total_costs = 0.0
    total_hours = 0.0

    for role in roles:
        role_name = role.get('role_name', 'Unknown')
        labor = role.get('labor', {})

        costs = labor.get('costs', 0) or 0
        paid_hours = labor.get('paid_hours', 0) or 0
        regular_hours = labor.get('regular_hours', 0) or 0
        overtime_hours = labor.get('weekly_overtime', 0) or 0
        scheduled_hours = labor.get('scheduled_hours', 0) or 0

        total_costs += costs
        total_hours += paid_hours

        print(f"\n  \033[1;36m{role_name}\033[0m")
        print(f"    Labor Cost:    ${costs:.2f}")
        print(f"    Paid Hours:    {paid_hours:.1f}")
        print(f"    Regular Hours: {regular_hours:.1f}")
        if overtime_hours:
            print(f"    Overtime:      {overtime_hours:.1f}")
        print(f"    Scheduled:     {scheduled_hours:.1f}")

    print()
    print(f"  \033[1;37mTotal Labor Cost:  ${total_costs:.2f}\033[0m")
    print(f"  \033[1;37mTotal Paid Hours:  {total_hours:.1f}\033[0m")
    print()


def show_labor_by_employee(config, start_date=None, end_date=None, location_uuid=None):
    """
    Show aggregate labor costs grouped by employee for a date range.

    Parameters
    ----------
    config : dict
        Configuration dict.
    start_date : str, optional
        Start date in ISO 8601 format. Defaults to today start.
    end_date : str, optional
        End date in ISO 8601 format. Defaults to today end.
    location_uuid : str, optional
        Location UUID. Defaults to config value.
    """
    if location_uuid is None:
        location_uuid = config.get('HOMEBASE_LOCATION_UUID_MURPHYS')
        if not location_uuid:
            print("Error: No location UUID provided. Set HOMEBASE_LOCATION_UUID_MURPHYS in .env or pass --location-uuid.")
            return

    if start_date is None:
        start_date = date.today().strftime('%Y-%m-%dT00:00:00Z')
    if end_date is None:
        end_date = date.today().strftime('%Y-%m-%dT23:59:59Z')

    employees = homebase_api_call(
        config,
        'GET',
        f"/locations/{location_uuid}/labor/by_employee",
        params={
            'start_date': start_date,
            'end_date': end_date,
        },
    )
    if employees is None:
        print("Failed to fetch labor data.")
        return

    if not employees:
        print("No labor data found for the specified date range.")
        return

    # Parse dates for display
    try:
        start_display = datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime('%b %d')
    except (ValueError, AttributeError):
        start_display = start_date[:10]
    try:
        end_display = datetime.fromisoformat(end_date.replace('Z', '+00:00')).strftime('%b %d')
    except (ValueError, AttributeError):
        end_display = end_date[:10]

    print("=" * 60)
    print(f"  HOMEBASE - LABOR BY EMPLOYEE")
    print(f"  {start_display} - {end_display}")
    print("=" * 60)

    # Sort by last name
    employees.sort(key=lambda e: (e.get('last_name', '') or '').lower())

    total_costs = 0.0
    total_hours = 0.0

    for emp in employees:
        first_name = emp.get('first_name', 'Unknown')
        last_name = emp.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        job = emp.get('job', {})
        role = job.get('default_role', '') if job else ''
        wage_rate = job.get('wage_rate', 0) if job else 0
        labor = emp.get('labor', {})

        costs = labor.get('costs', 0) or 0
        paid_hours = labor.get('paid_hours', 0) or 0
        regular_hours = labor.get('regular_hours', 0) or 0
        overtime_hours = labor.get('weekly_overtime', 0) or 0
        scheduled_hours = labor.get('scheduled_hours', 0) or 0

        total_costs += costs
        total_hours += paid_hours

        role_str = f" [{role}]" if role else ""
        wage_str = f" @ ${wage_rate:.2f}/hr" if wage_rate else ""

        print(f"\n  \033[1;36m{name}{role_str}{wage_str}\033[0m")
        print(f"    Labor Cost:    ${costs:.2f}")
        print(f"    Paid Hours:    {paid_hours:.1f}")
        print(f"    Regular Hours: {regular_hours:.1f}")
        if overtime_hours:
            print(f"    Overtime:      {overtime_hours:.1f}")
        print(f"    Scheduled:     {scheduled_hours:.1f}")

    print()
    print(f"  \033[1;37mTotal Labor Cost:  ${total_costs:.2f}\033[0m")
    print(f"  \033[1;37mTotal Paid Hours:  {total_hours:.1f}\033[0m")
    print()


def show_timecards(config, start_date=None, end_date=None, location_uuid=None,
                   date_filter='clock_in'):
    """
    Show timecards (clock-in/out records) for a date range.

    Parameters
    ----------
    config : dict
        Configuration dict.
    start_date : str, optional
        Start date in ISO 8601 format. Defaults to today start.
    end_date : str, optional
        End date in ISO 8601 format. Defaults to today end.
    location_uuid : str, optional
        Location UUID. Defaults to config value.
    date_filter : str
        Which date field to filter on: clock_in, clock_out, created_at, updated_at.
    """
    if location_uuid is None:
        location_uuid = config.get('HOMEBASE_LOCATION_UUID_MURPHYS')
        if not location_uuid:
            print("Error: No location UUID provided. Set HOMEBASE_LOCATION_UUID_MURPHYS in .env or pass --location-uuid.")
            return

    if start_date is None:
        start_date = date.today().strftime('%Y-%m-%dT00:00:00Z')
    if end_date is None:
        end_date = date.today().strftime('%Y-%m-%dT23:59:59Z')

    timecards = homebase_api_call(
        config,
        'GET',
        f"/locations/{location_uuid}/timecards",
        params={
            'start_date': start_date,
            'end_date': end_date,
            'per_page': 100,
            'date_filter': date_filter,
        },
    )
    if timecards is None:
        print("Failed to fetch timecards.")
        return

    if not timecards:
        print("No timecards found for the specified date range.")
        return

    # Parse dates for display
    try:
        start_display = datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime('%b %d')
    except (ValueError, AttributeError):
        start_display = start_date[:10]
    try:
        end_display = datetime.fromisoformat(end_date.replace('Z', '+00:00')).strftime('%b %d')
    except (ValueError, AttributeError):
        end_display = end_date[:10]

    print("=" * 60)
    print(f"  HOMEBASE - TIMECARDS")
    print(f"  {start_display} - {end_display}  (filter: {date_filter})")
    print("=" * 60)

    # Sort by clock_in descending (most recent first)
    def sort_key(tc):
        ci = tc.get('clock_in')
        if ci:
            try:
                return datetime.fromisoformat(ci.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    timecards.sort(key=sort_key, reverse=True)

    total_costs = 0.0
    total_hours = 0.0

    for tc in timecards:
        first_name = tc.get('first_name', 'Unknown')
        last_name = tc.get('last_name', '')
        name = f"{first_name} {last_name}".strip()
        role = tc.get('role', '')
        clock_in_str = tc.get('clock_in')
        clock_out_str = tc.get('clock_out')
        labor = tc.get('labor', {})
        timebreaks = tc.get('timebreaks', []) or []

        costs = labor.get('costs', 0) or 0
        paid_hours = labor.get('paid_hours', 0) or 0
        regular_hours = labor.get('regular_hours', 0) or 0

        total_costs += costs
        total_hours += paid_hours

        # Parse times for display
        clock_in_display = '?'
        if clock_in_str:
            try:
                clock_in_display = datetime.fromisoformat(clock_in_str.replace('Z', '+00:00')).strftime('%I:%M %p').lstrip('0')
            except (ValueError, AttributeError):
                clock_in_display = clock_in_str

        clock_out_display = '?'
        if clock_out_str:
            try:
                clock_out_display = datetime.fromisoformat(clock_out_str.replace('Z', '+00:00')).strftime('%I:%M %p').lstrip('0')
            except (ValueError, AttributeError):
                clock_out_display = clock_out_str

        # Determine status
        if clock_in_str and not clock_out_str:
            status = '\033[1;32m● Clocked In\033[0m'
        elif clock_in_str and clock_out_str:
            status = '\033[1;33m● Clocked Out\033[0m'
        else:
            status = '\033[1;30m● No Clock\033[0m'

        role_str = f" [{role}]" if role else ""
        print(f"\n  {status}  {name}{role_str}")
        print(f"    Clock In:  {clock_in_display}")
        print(f"    Clock Out: {clock_out_display}")
        print(f"    Cost:      ${costs:.2f}  |  Hours: {paid_hours:.1f}  |  Regular: {regular_hours:.1f}")

        if timebreaks:
            break_count = len(timebreaks)
            break_hours = sum(
                (b.get('duration', 0) or 0) / 60.0 for b in timebreaks
            )
            print(f"    Breaks:    {break_count}  |  Total: {break_hours:.1f}h")

    print()
    print(f"  \033[1;37mTotal Labor Cost:  ${total_costs:.2f}\033[0m")
    print(f"  \033[1;37mTotal Paid Hours:  {total_hours:.1f}\033[0m")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Homebase utility: check employee status, labor costs, and timecards.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='Sub-command')

    # Working sub-command
    working_parser = subparsers.add_parser('working', help='Show which employees are currently working')
    working_parser.add_argument('--location-uuid', help='Location UUID (default: from env)')

    # Labor by role sub-command
    labor_parser = subparsers.add_parser('labor', help='Show labor costs grouped by role')
    labor_parser.add_argument('--location-uuid', help='Location UUID (default: from env)')
    labor_parser.add_argument('--start-date', help='Start date in ISO 8601 format (default: today)')
    labor_parser.add_argument('--end-date', help='End date in ISO 8601 format (default: today)')

    # Labor by employee sub-command
    employees_parser = subparsers.add_parser('employees', help='Show labor costs grouped by employee')
    employees_parser.add_argument('--location-uuid', help='Location UUID (default: from env)')
    employees_parser.add_argument('--start-date', help='Start date in ISO 8601 format (default: today)')
    employees_parser.add_argument('--end-date', help='End date in ISO 8601 format (default: today)')

    # Timecards sub-command
    timecards_parser = subparsers.add_parser('timecards', help='Show timecard records (clock-in/out)')
    timecards_parser.add_argument('--location-uuid', help='Location UUID (default: from env)')
    timecards_parser.add_argument('--start-date', help='Start date in ISO 8601 format (default: today)')
    timecards_parser.add_argument('--end-date', help='End date in ISO 8601 format (default: today)')
    timecards_parser.add_argument('--date-filter', default='clock_in',
                                  choices=['clock_in', 'clock_out', 'created_at', 'updated_at'],
                                  help='Date field to filter on (default: clock_in)')

    args = parser.parse_args()

    # Load config
    try:
        config = load_env()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.command == 'working':
        show_working(
            config=config,
            location_uuid=args.location_uuid,
        )

    elif args.command == 'labor':
        show_labor_by_role(
            config=config,
            start_date=args.start_date,
            end_date=args.end_date,
            location_uuid=args.location_uuid,
        )

    elif args.command == 'employees':
        show_labor_by_employee(
            config=config,
            start_date=args.start_date,
            end_date=args.end_date,
            location_uuid=args.location_uuid,
        )

    elif args.command == 'timecards':
        show_timecards(
            config=config,
            start_date=args.start_date,
            end_date=args.end_date,
            location_uuid=args.location_uuid,
            date_filter=args.date_filter,
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
