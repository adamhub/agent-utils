#!/usr/bin/env python3
"""
Biyo POS utility script for querying sales, products, and inventory.

This script provides a simplified Python wrapper around the Biyo POS REST API.
Supports sales by date range, listing products, searching products, and
getting product details by ID.

Usage:
    python biyo.py sales --start <date> --end <date> [options]
    python biyo.py products [options]
    python biyo.py search <query> [options]
    python biyo.py product <id> [options]

Commands:
    sales               Get sales summary for a date range
    products            List products (with optional pagination)
    search              Search products by name or barcode
    product             Get product details by ID

Sales options:
    --start TEXT        Start date in Biyo format: MonthDD,YYYY (default: today)
    --end TEXT          End date in Biyo format: MonthDD,YYYY (default: today)
    --raw               Output raw JSON instead of formatted table

Products options:
    --page INT          Page number for pagination (default: 1)
    --page-size INT     Items per page (default: 50)
    --raw               Output raw JSON instead of formatted table

Search options:
    query               Search query (positional, required)
    --page INT          Page number for pagination (default: 1)
    --raw               Output raw JSON instead of formatted table

Product options:
    id                  Product ID (positional, required)
    --raw               Output raw JSON instead of formatted table

Environment variables (in .env or system):
    BIYO_EMAIL          Biyo account email
    BIYO_PASSWORD       Biyo account password

Requirements:
    pip install requests

Examples:
    # Get sales summary for today
    python biyo.py sales

    # Get sales summary for a date range
    python biyo.py sales --start "April19,2026" --end "April19,2026"

    # List all products (page 1)
    python biyo.py products

    # List products with pagination
    python biyo.py products --page 2 --page-size 100

    # Search products by name or barcode
    python biyo.py search "coffee"

    # Get product details by ID
    python biyo.py product 123

    # Output raw JSON
    python biyo.py sales --raw
    python biyo.py products --raw
"""

import os
import sys
import json
import argparse
from datetime import datetime, date
from pathlib import Path

import requests


BIYO_API_BASE = "https://aria.biyo.co/api/v1"


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
        'BIYO_EMAIL',
        'BIYO_PASSWORD',
    ]

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

    return config


def get_access_token(config):
    """
    Obtain an OAuth2 access token from the Biyo API.

    Parameters
    ----------
    config : dict
        Configuration dict with BIYO_EMAIL and BIYO_PASSWORD.

    Returns
    -------
    str or None
        The access token, or None on failure.
    """
    url = f"{BIYO_API_BASE}/auth/token/"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'email': config['BIYO_EMAIL'],
        'password': config['BIYO_PASSWORD'],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        token = data.get('access_token')
        if not token:
            print("Error: No access_token in Biyo auth response.")
            print(json.dumps(data, indent=2))
            return None
        return token
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = resp.json()
            print(f"Biyo auth error ({resp.status_code}): {json.dumps(error_detail, indent=2)}")
        except (ValueError, json.JSONDecodeError):
            print(f"Biyo auth error ({resp.status_code}): {e}")
        return None
    except Exception as e:
        print(f"Biyo auth request failed: {e}")
        return None


def biyo_api_call(token, method, path, params=None, data=None):
    """
    Make an authenticated HTTP request to the Biyo API.

    Parameters
    ----------
    token : str
        OAuth2 access token.
    method : str
        HTTP method (GET, POST, etc.).
    path : str
        API path relative to base (e.g., '/reports/sales_summary/').
    params : dict, optional
        Query string parameters.
    data : dict, optional
        JSON body for POST/PUT/PATCH requests.

    Returns
    -------
    dict or list or None
        Parsed JSON response, or None on failure.
    """
    url = f"{BIYO_API_BASE}{path}"
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30,
        )
        resp.raise_for_status()
        # Some endpoints return empty body on success
        if not resp.text.strip():
            return {"status": "success"}
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = resp.json()
            print(f"Biyo API error ({resp.status_code}): {json.dumps(error_detail, indent=2)}")
        except (ValueError, json.JSONDecodeError):
            print(f"Biyo API error ({resp.status_code}): {e}")
        return None
    except Exception as e:
        print(f"Biyo API call failed: {e}")
        return None


def get_sales_summary(token, start_date, end_date):
    """
    Get sales summary for a date range.

    Parameters
    ----------
    token : str
        OAuth2 access token.
    start_date : str
        Start date in Biyo format: MonthDD,YYYY (e.g., 'April19,2026').
    end_date : str
        End date in Biyo format: MonthDD,YYYY (e.g., 'April19,2026').

    Returns
    -------
    dict or None
        Sales summary data, or None on failure.
    """
    return biyo_api_call(
        token,
        'GET',
        '/reports/sales_summary/',
        params={'start': start_date, 'end': end_date},
    )


def list_products(token, page=1, page_size=50):
    """
    List products with pagination.

    Parameters
    ----------
    token : str
        OAuth2 access token.
    page : int
        Page number (default: 1).
    page_size : int
        Items per page (default: 50).

    Returns
    -------
    dict or None
        Products data, or None on failure.
    """
    return biyo_api_call(
        token,
        'GET',
        '/products/',
        params={'page': page, 'page_size': page_size},
    )


def search_products(token, query, page=1):
    """
    Search products by name or barcode.

    Parameters
    ----------
    token : str
        OAuth2 access token.
    query : str
        Search query (name or barcode).
    page : int
        Page number (default: 1).

    Returns
    -------
    dict or None
        Products data, or None on failure.
    """
    return biyo_api_call(
        token,
        'GET',
        '/products/',
        params={'query': query, 'page': page},
    )


def get_product_by_id(token, product_id):
    """
    Get product details by ID.

    Parameters
    ----------
    token : str
        OAuth2 access token.
    product_id : int
        Product ID.

    Returns
    -------
    dict or None
        Product data, or None on failure.
    """
    return biyo_api_call(
        token,
        'GET',
        f'/products/{product_id}/',
    )


def format_sales_summary(data):
    """Format sales summary data for human-readable output."""
    if not data:
        print("No sales data returned.")
        return

    print("=" * 60)
    print("  BIYO - SALES SUMMARY")
    print("=" * 60)

    # The response structure may vary; handle both nested and flat formats
    sales = data.get('sales', data)

    total_net_sales = sales.get('total_net_sales', 0) or 0
    total_gross_sales = sales.get('total_gross_sales', 0) or 0
    total_tax = sales.get('total_tax', 0) or 0
    total_discounts = sales.get('total_discounts', 0) or 0
    total_refunds = sales.get('total_refunds', 0) or 0
    total_orders = sales.get('total_orders', 0) or 0
    total_items_sold = sales.get('total_items_sold', 0) or 0

    print(f"\n  {'Gross Sales:':<25} ${total_gross_sales:>8.2f}")
    print(f"  {'Discounts:':<25} ${total_discounts:>8.2f}")
    print(f"  {'Tax:':<25} ${total_tax:>8.2f}")
    print(f"  {'Refunds:':<25} ${total_refunds:>8.2f}")
    print(f"  {'Net Sales:':<25} ${total_net_sales:>8.2f}")
    print()
    print(f"  {'Total Orders:':<25} {total_orders:>8}")
    print(f"  {'Total Items Sold:':<25} {total_items_sold:>8}")

    # Average order value
    if total_orders > 0:
        avg_order = total_net_sales / total_orders
        print(f"  {'Avg Order Value:':<25} ${avg_order:>8.2f}")

    print()


def format_products(data):
    """Format products list for human-readable output."""
    if not data:
        print("No products returned.")
        return

    # Handle both paginated response and direct list
    if isinstance(data, dict):
        results = data.get('results', data.get('products', []))
        count = data.get('count', len(results))
        next_page = data.get('next')
        previous = data.get('previous')
    else:
        results = data
        count = len(results)
        next_page = None
        previous = None

    if not results:
        print("No products found.")
        return

    print("=" * 60)
    print(f"  BIYO - PRODUCTS ({count} total)")
    print("=" * 60)

    for product in results:
        product_id = product.get('id', '?')
        name = product.get('name', 'Unknown')
        price = product.get('price', 0) or 0
        barcode = product.get('barcode', '')
        stock = product.get('stock', 0) or 0
        archived = product.get('archived', False)

        barcode_str = f"  [{barcode}]" if barcode else ""
        archived_str = "  [ARCHIVED]" if archived else ""

        print(f"\n  #{product_id} {name}{archived_str}")
        print(f"    Price: ${float(price):.2f}  |  Stock: {stock}{barcode_str}")

    print()

    if next_page:
        print(f"  Next page available. Use --page to navigate.")
    print()


def format_product_detail(data):
    """Format a single product detail for human-readable output."""
    if not data:
        print("No product data returned.")
        return

    product_id = data.get('id', '?')
    name = data.get('name', 'Unknown')
    price = data.get('price', 0) or 0
    cost = data.get('cost', 0) or 0
    barcode = data.get('barcode', '')
    stock = data.get('stock', 0) or 0
    description = data.get('description', '')
    archived = data.get('archived', False)
    categories = data.get('categories', [])
    tax_rate = data.get('tax_rate')

    print("=" * 60)
    print(f"  BIYO - PRODUCT DETAIL")
    print("=" * 60)

    print(f"\n  ID:          #{product_id}")
    print(f"  Name:        {name}")
    if description:
        print(f"  Description: {description}")
    print(f"  Price:       ${float(price):.2f}")
    print(f"  Cost:        ${float(cost):.2f}")
    if float(price) > 0:
        margin = ((float(price) - float(cost)) / float(price)) * 100
        print(f"  Margin:      {margin:.1f}%")
    print(f"  Stock:       {stock}")
    if barcode:
        print(f"  Barcode:     {barcode}")
    if categories:
        cat_names = [str(c) for c in categories]
        print(f"  Categories:  {', '.join(cat_names)}")
    if tax_rate:
        print(f"  Tax Rate:    {tax_rate}")
    print(f"  Archived:    {'Yes' if archived else 'No'}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description='Biyo POS utility: query sales, products, and inventory.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='Sub-command')

    # Sales sub-command
    sales_parser = subparsers.add_parser('sales', help='Get sales summary for a date range')
    sales_parser.add_argument('--start', help='Start date in Biyo format: MonthDD,YYYY (default: today)')
    sales_parser.add_argument('--end', help='End date in Biyo format: MonthDD,YYYY (default: today)')
    sales_parser.add_argument('--raw', action='store_true', help='Output raw JSON')

    # Products sub-command
    products_parser = subparsers.add_parser('products', help='List products')
    products_parser.add_argument('--page', type=int, default=1, help='Page number (default: 1)')
    products_parser.add_argument('--page-size', type=int, default=50, help='Items per page (default: 50)')
    products_parser.add_argument('--raw', action='store_true', help='Output raw JSON')

    # Search sub-command
    search_parser = subparsers.add_parser('search', help='Search products by name or barcode')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--page', type=int, default=1, help='Page number (default: 1)')
    search_parser.add_argument('--raw', action='store_true', help='Output raw JSON')

    # Product detail sub-command
    product_parser = subparsers.add_parser('product', help='Get product details by ID')
    product_parser.add_argument('id', type=int, help='Product ID')
    product_parser.add_argument('--raw', action='store_true', help='Output raw JSON')

    args = parser.parse_args()

    # Load config
    try:
        config = load_env()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Authenticate
    token = get_access_token(config)
    if token is None:
        print("Failed to obtain Biyo access token.")
        sys.exit(1)

    if args.command == 'sales':
        # Default to today if no dates provided
        today = date.today()
        start = args.start if args.start else today.strftime('%B%d,%Y')
        end = args.end if args.end else today.strftime('%B%d,%Y')

        data = get_sales_summary(token, start, end)
        if data is None:
            sys.exit(1)

        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            format_sales_summary(data)

    elif args.command == 'products':
        data = list_products(token, page=args.page, page_size=args.page_size)
        if data is None:
            sys.exit(1)

        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            format_products(data)

    elif args.command == 'search':
        data = search_products(token, args.query, page=args.page)
        if data is None:
            sys.exit(1)

        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            format_products(data)

    elif args.command == 'product':
        data = get_product_by_id(token, args.id)
        if data is None:
            sys.exit(1)

        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            format_product_detail(data)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
