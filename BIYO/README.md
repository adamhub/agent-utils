
## Agent Developer Notes

Prompt to have AI read the docs and add features to the util:

```
Biyo is a POS (Point of Sale) system.
The utility script is biyo.py and it contains:
- Sales summary by date range
- Product listing with pagination
- Product search by name or barcode
- Product detail by ID

The Biyo API is documented in the SKILL.md file at BIYO/BIYO_SKILL----to-delete/SKILL.md
Read it with browser-use MCP when you need to add a new feature to the script.
```

## Usage

### Get Sales Summary

```bash
# Today
python BIYO/biyo.py sales

# Date range (Biyo format: MonthDD,YYYY)
python BIYO/biyo.py sales --start "April19,2026" --end "April19,2026"

# Raw JSON output
python BIYO/biyo.py sales --start "January01,2026" --end "January31,2026" --raw
```

### List Products

```bash
# First page (default page size: 50)
python BIYO/biyo.py products

# Specific page with custom page size
python BIYO/biyo.py products --page 2 --page-size 100

# Raw JSON output
python BIYO/biyo.py products --raw
```

### Search Products

```bash
# Search by name or barcode
python BIYO/biyo.py search "coffee"

# Search with pagination
python BIYO/biyo.py search "coffee" --page 2

# Raw JSON output
python BIYO/biyo.py search "coffee" --raw
```

### Get Product Details

```bash
# Get product by ID
python BIYO/biyo.py product 123

# Raw JSON output
python BIYO/biyo.py product 123 --raw
```
