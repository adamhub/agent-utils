---
name: biyo
description: Interact with Biyo POS API to manage sales, products, inventory, and reports
homepage: https://biyopos.com/
metadata: {"nanobot":{"emoji":"💰","requires":{"bins":["curl","jq"]}}}
---

# Biyo API Skill

This skill provides functionality to interact with Biyo POS through its REST API. 
Just use curl to read and write information. Don't write scripts. 

## Connection
See connection variables (email, password, and base URL) in ``../../.env``

Load env vars to access authentication info:
```bash
./../../../../load_vars.sh
```
If this doesn't work, stop and ask user for input.

## Authentication

Biyo API uses OAuth2 token-based authentication. You need to obtain an access token first:

```bash
# Obtain access token
curl -s -X POST "https://aria.biyo.co/api/v1/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"email":"${BIYO_EMAIL}","password":"${BIYO_PASSWORD}"}'

# The response will contain an access_token that should be used in subsequent requests:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "expires_in": 36000,
#   "token_type": "Bearer",
#   "employee": "Employee Name"
# }

# Use the token in subsequent requests
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/sales_summary/?start=April19,2026&end=April19,2026"
```

## Usage Examples

### Get Sales Summary
Get sales summary for a date range (date format: MonthDD,YYYY):

```bash
# Get sales summary for a specific date
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/sales_summary/?start=April19,2026&end=April19,2026"

# Get sales summary for a date range
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/sales_summary/?start=January01,2026&end=January31,2026"
```

### List Products
Get a list of all products with pagination:

```bash
# List all products (first page)
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/products/"

# Search products by name or barcode
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/products/?query=coffee"

# Get specific page
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/products/?page=2"
```

### Get Product Details
Retrieve details for a specific product:

```bash
# Get product by ID
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/products/123/"
```

### Create New Product
Create a new product:

```bash
curl -s -X POST "https://aria.biyo.co/api/v1/products/create/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Product Name",
    "price": "19.99",
    "cost": "10.00",
    "description": "Product description",
    "barcode": "123456789012",
    "categories": [1, 2]
  }'
```

### Update Product (Full Update - PUT)
Fully update a product with PUT method (replaces all fields):

**Note:** PUT requires sending all required fields, while PATCH only updates specified fields.

```bash
curl -s -X PUT "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Product Name",
    "price": "24.99",
    "cost": "12.50",
    "description": "Updated product description",
    "barcode": "987654321098",
    "categories": [1, 3],
    "tax_rate": 1,
    "archived": false
  }'
```

### Update Product (Partial Update - PATCH)
Partially update a product with PATCH method (updates only specified fields):

**Note:** PATCH is preferred for partial updates as it only modifies the fields you specify.

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "price": "29.99",
    "description": "New improved description"
  }'
```

### Update Product Price Only
Update just the price of a product:

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"price": "34.99"}'
```

### Update Product Stock Level
Update the stock quantity of a product:

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"stock": "150.50"}'
```

### Archive/Unarchive Product
Archive a product (soft delete):

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"archived": true}'
```

Unarchive a product:

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"archived": false}'
```

### Update Product Categories
Update product categories:

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/products/123/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"categories": [2, 4, 5]}'
```

### List Orders
Get orders with date range filtering:

```bash
# List orders for a date range
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/orders/?start=April19,2026&end=April19,2026"

# List orders with pagination
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/orders/?start=April19,2026&end=April19,2026&page=1&page_size=50"
```

### Get Order Details
Retrieve a specific order:

```bash
# Get order by ID
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/orders/456/"
```

### Create New Order
Create a new order:

```bash
curl -s -X POST "https://aria.biyo.co/api/v1/orders/create/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product": 123,
        "quantity": 2,
        "price": "19.99",
        "name": "Product Name"
      }
    ],
    "customer": 789,
    "subtotal": "39.98",
    "tax_total": "3.20",
    "grand_total": "43.18"
  }'
```

### Update Order (Full Update - PUT)
Fully update an order with PUT method:

**Note:** PUT replaces the entire order with the new data. All required fields must be included.

```bash
curl -s -X PUT "https://aria.biyo.co/api/v1/orders/456/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product": 123,
        "quantity": 3,
        "price": "19.99",
        "name": "Product Name"
      },
      {
        "product": 124,
        "quantity": 1,
        "price": "9.99",
        "name": "Another Product"
      }
    ],
    "customer": 789,
    "subtotal": "69.96",
    "tax_total": "5.60",
    "grand_total": "75.56",
    "status": 2
  }'
```

### Update Order (Partial Update - PATCH)
Partially update an order with PATCH method:

**Note:** PATCH allows updating specific fields without affecting other order data.

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/orders/456/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": 3,
    "discount_total": "5.00"
  }'
```

### Update Order Status Only
Update just the order status:
- Status 1: Open
- Status 2: Paid
- Status 3: Completed
- Status 4: Cancelled

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/orders/456/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status": 2}'
```

### Add Discount to Order
Add a discount to an existing order:

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/orders/456/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"discount_total": "10.00"}'
```

### Get Discount Summary
Get discount summary report:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/discount_summary/?start=April19,2026&end=April19,2026"
```

### Get Tax Summary
Get tax summary report:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/taxes_summary/?start=April19,2026&end=April19,2026"
```

### Get Item Sales Report
Get item sales report:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/item/sales/?start=April19,2026&end=April19,2026"
```

### Get Modifier Sales Report
Get modifier sales report:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/modifier/sales/?start=April19,2026&end=April19,2026"
```

### Get Hourly Sales Heatmap
Get hourly sales heatmap data:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/hourly-sales-heatmap/?start=April19,2026&end=April19,2026"
```

### List Categories
Get all product categories:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/categories/"
```

### List Customers
Get all customers:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/customers/"
```

### Create Customer
Create a new customer:

```bash
curl -s -X POST "https://aria.biyo.co/api/v1/customers/create/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  }'
```

### Update Customer (Full Update - PUT)
Fully update a customer with PUT method:

**Note:** PUT requires all customer fields to be included in the request.

```bash
curl -s -X PUT "https://aria.biyo.co/api/v1/customers/789/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Johnathan",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "phone": "+1987654321"
  }'
```

### Update Customer (Partial Update - PATCH)
Partially update a customer with PATCH method:

**Note:** PATCH is ideal for updating specific customer information like email or phone.

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/customers/789/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new.email@example.com",
    "phone": "+1122334455"
  }'
```

### Update Customer Email Only
Update just the email address:

```bash
curl -s -X PATCH "https://aria.biyo.co/api/v1/customers/789/update/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"email": "updated@example.com"}'
```

### Inventory Management - Stock Movements
List stock movements:

```bash
# List all stock movements
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/stock-movements/"

# Filter by date range and movement type
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/stock-movements/?date_from=2026-04-01&date_to=2026-04-30&movement_type=stock_in"
```

### Create Stock Movement
Create a new stock movement:

```bash
curl -s -X POST "https://aria.biyo.co/api/v1/stock-movements/create/" \
  -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "movement_type": "stock_in",
    "store": 1,
    "notes": "Received new inventory",
    "status": "draft"
  }'
```

### Purchase Orders
List purchase orders:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/purchase-orders/"
```

### Get Employee Information
Get current employee information:

```bash
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/employees/whoami/"
```

## Helper Functions

### Get Token and Store in Variable
```bash
# Get token and extract it
response=$(curl -s -X POST "https://aria.biyo.co/api/v1/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"email":"${BIYO_EMAIL}","password":"${BIYO_PASSWORD}"}')
  
access_token=$(echo $response | jq -r '.access_token')

# Use the token
curl -s -H "Authorization: Bearer $access_token" \
  "https://aria.biyo.co/api/v1/reports/sales_summary/?start=April19,2026&end=April19,2026"
```

### Format JSON Responses
```bash
# Pipe to jq for pretty printing
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/products/123/" | jq '.'

# Extract specific fields
curl -s -H "Authorization: Bearer ${BIYO_ACCESS_TOKEN}" \
  "https://aria.biyo.co/api/v1/reports/sales_summary/?start=April19,2026&end=April19,2026" | \
  jq '.sales.total_net_sales'
```

## Date Format Notes
- Biyo API uses `MonthDD,YYYY` format for date parameters (e.g., `April19,2026`)
- For stock movements, use `YYYY-MM-DD` format
- Always URL-encode date parameters if they contain spaces (though Biyo format doesn't have spaces)

## Error Handling

If the API returns an error, you will receive a response with error details:
```json
{
  "detail": "Invalid token.",
  "code": "token_not_valid"
}
```

Common errors:
- `401 Unauthorized`: Invalid or expired token - refresh or obtain new token
- `400 Bad Request`: Invalid parameters or missing required fields
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server-side issue

Always check the response status code and error details when making API calls.

## Supported Operations

### Reporting
- Sales summary
- Discount summary
- Tax summary
- Item sales report
- Modifier sales report
- Hourly sales heatmap
- Shifts summary
- Voided items report

### Products & Inventory
- List, create, update products (full PUT and partial PATCH updates)
- Product categories
- Stock movements
- Purchase orders
- Suppliers

### Orders & Customers
- List, create, update orders (full PUT and partial PATCH updates)
- List, create, update customers (full PUT and partial PATCH updates)
- Customer groups



### System Management
- Stores
- Terminals
- Printers
- Tax rates
- Employees
- Discounts
- Modifiers and modifier groups

## Rate Limiting
The Biyo API may have rate limits. If you encounter `429 Too Many Requests` errors, implement appropriate delays between requests.

## Best Practices
1. Always store tokens securely and refresh when expired
2. Use pagination for large datasets (`page` and `page_size` parameters)
3. Filter data by date ranges to reduce response size
4. Handle errors gracefully with appropriate retry logic
5. Cache frequently accessed data when appropriate
6. Use PATCH for partial updates instead of PUT when only modifying specific fields
7. When updating prices, include cost updates if applicable to maintain profit margins
8. Regularly archive discontinued products instead of deleting them to preserve historical data
9. Remember: PUT replaces entire resources, PATCH modifies only specified fields
