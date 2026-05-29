---
name: biyo
description: Point of Sale (POS) system queries via the Biyo REST API. Use when the user asks about sales data, product information, inventory, or POS-related questions. Triggers for queries like "sales summary", "how much did we sell", "list products", "search products", "product details", "inventory", "barcode lookup", or any Biyo POS-related questions.
---

# Biyo POS Skill

The `biyo` command provides access to Point of Sale data via the Biyo REST API.

## Prerequisites

The `biyo` CLI is globally available. It reads configuration from a `.env` file located alongside the script, or from environment variables:

- `BIYO_EMAIL` — Biyo account email (required)
- `BIYO_PASSWORD` — Biyo account password (required)

The CLI handles OAuth2 authentication automatically on each invocation.

## Commands

### `biyo sales`

Get sales summary for a date range.

```bash
# Today
biyo sales

# Date range (Biyo format: MonthDD,YYYY)
biyo sales --start "April19,2026" --end "April19,2026"

# Raw JSON output
biyo sales --start "January01,2026" --end "January31,2026" --raw
```

Output includes: gross sales, discounts, tax, refunds, net sales, total orders, total items sold, and average order value.

### `biyo products`

List products with optional pagination.

```bash
# First page (default page size: 50)
biyo products

# Specific page with custom page size
biyo products --page 2 --page-size 100

# Raw JSON output
biyo products --raw
```

Output includes: product ID, name, price, stock level, barcode, and archived status.

### `biyo search`

Search products by name or barcode.

```bash
# Search by name or barcode
biyo search "coffee"

# Search with pagination
biyo search "coffee" --page 2

# Raw JSON output
biyo search "coffee" --raw
```

### `biyo product`

Get detailed product information by ID.

```bash
# Get product by ID
biyo product 123

# Raw JSON output
biyo product 123 --raw
```

Output includes: ID, name, description, price, cost, margin percentage, stock, barcode, categories, tax rate, and archived status.

## Common Workflows

### "How were sales today?"

```bash
biyo sales
```

### "What were sales for a specific date range?"

```bash
biyo sales --start "May1,2026" --end "May29,2026"
```

### "Show me all products"

```bash
biyo products
```

### "Find a product by name"

```bash
biyo search "coffee"
```

### "Look up a product by barcode"

```bash
biyo search "8901234567890"
```

### "Get details on a specific product"

```bash
biyo product 42
```

### "Check inventory levels"

```bash
biyo products --page-size 200
```

## Notes

- Date format is `MonthDD,YYYY` (e.g., `April19,2026`, `January01,2026`). No spaces between month and day.
- Default date range is today when `--start` and `--end` are omitted.
- Use `--raw` to get raw JSON output for programmatic consumption.
- The API doc is referenced in the existing skill at `BIYO/.BIYO_SKILL----to-delete/SKILL.md` if new features need to be added to the script.
