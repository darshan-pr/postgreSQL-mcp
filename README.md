# PostgreSQL MCP Server

A Model Context Protocol (MCP) server that provides secure, read-only access to PostgreSQL databases with optional data insertion capabilities.

## Features

- ✅ **Read-only SQL queries** with automatic validation
- 🔍 **Schema inspection** to understand database structure
- 🔗 **Relationship mapping** for foreign keys
- ➕ **Safe data insertion** with validation
- 🛡️ **Built-in security** prevents destructive operations
- ⚡ **Query size limits** to prevent overwhelming results
- 📊 **Result estimation** before execution

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Database credentials with appropriate permissions

## Installation

1. **Clone or download the files**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
```

## Usage

### Start the MCP Server

```bash
python server.py
```

The server will start on `http://localhost:8000` by default.

### Available Tools

#### 1. `get_schema`
Get the complete database schema including tables, columns, data types, and constraints.

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_schema",
    "arguments": {}
  }
}
```

#### 2. `get_relationships`
Get foreign key relationships between tables.

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_relationships",
    "arguments": {}
  }
}
```

#### 3. `run_sql`
Execute read-only SELECT queries. INSERT/UPDATE/DELETE are blocked.

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "run_sql",
    "arguments": {
      "query": "SELECT * FROM users WHERE active = true LIMIT 10"
    }
  }
}
```

**Important:** Always include a LIMIT clause for queries that might return more than 1000 rows.

#### 4. `insert_data`
Insert new records into a table. This is the ONLY way to add data.

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "insert_data",
    "arguments": {
      "table": "users",
      "data": [
        {
          "name": "John Doe",
          "email": "john@example.com",
          "age": 30
        },
        {
          "name": "Jane Smith",
          "email": "jane@example.com",
          "age": 28
        }
      ]
    }
  }
}
```

## Security Features

### Query Validation
- Only `SELECT` queries are allowed in `run_sql`
- Forbidden keywords: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`
- Table names are validated to prevent SQL injection

### Result Size Protection
- Queries are analyzed before execution
- Queries estimated to return >1000 rows are rejected
- User must add explicit `LIMIT` clause

### Connection Management
- Automatic connection pooling
- Proper cleanup of database resources
- Connection timeout protection (10 seconds)

## PostgreSQL-Specific Features

This MCP server is optimized for PostgreSQL and includes:

- **Information Schema queries** for metadata
- **EXPLAIN ANALYZE** for query planning
- **RETURNING clauses** for insert operations
- **Primary key detection** for auto-generated IDs
- **Schema-qualified names** (defaults to `public` schema)

## Differences from MySQL Version

| Feature | MySQL | PostgreSQL |
|---------|-------|------------|
| Connection library | `mysql.connector` | `psycopg2` |
| Default port | 3306 | 5432 |
| Query parameterization | `%s` | `%s` |
| Schema name | `DATABASE()` | `'public'` |
| Primary key detection | `AUTO_INCREMENT` | `SERIAL`/`IDENTITY` |
| EXPLAIN format | Standard | JSON format |

## Common Use Cases

### 1. Explore Database Structure
```python
# First, get the schema
get_schema()

# Then, understand relationships
get_relationships()
```

### 2. Query Data
```python
# Always check schema first
get_schema()

# Then run your query with LIMIT
run_sql("SELECT * FROM products WHERE price > 100 LIMIT 50")
```

### 3. Insert New Records
```python
# Check schema for column names
get_schema()

# Insert data
insert_data("customers", [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
])
```

## Error Handling

The server returns JSON-RPC error responses:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Error description here"
  }
}
```

Common errors:
- **"Only SELECT queries are allowed"** - Use `insert_data` for adding data
- **"Query contains forbidden keyword"** - Attempting destructive operation
- **"Table does not exist"** - Check table name with `get_schema`
- **"Query may return too many rows"** - Add LIMIT clause

## Testing

You can test the server with curl:

```bash
# Initialize
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# List tools
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'

# Get schema
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_schema", "arguments": {}}}'
```

## Troubleshooting

### Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env` file
- Ensure database exists: `psql -l`
- Check firewall settings for port 5432

### Query Execution Issues
- **"Failed to connect"** - Check database credentials
- **"Permission denied"** - User needs SELECT permission
- **"Table not found"** - Verify schema with `get_schema`

### Performance Issues
- Add indexes on frequently queried columns
- Use LIMIT clauses to reduce result sizes
- Consider using EXPLAIN to analyze query plans

## Development

### File Structure
```
.
├── server.py              # FastAPI MCP server
├── postgresql_tools.py    # Database operations
├── mcp.json              # MCP tool definitions
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
└── README.md            # This file
```

### Extending the Server

To add new tools:

1. Add function to `postgresql_tools.py`
2. Add tool definition to `TOOLS` dict in `server.py`
3. Add handler in `mcp_endpoint()` function
4. Update `mcp.json` with tool specification

## License

This MCP server is provided as-is for database access via the Model Context Protocol.

## Support

For issues related to:
- **PostgreSQL:** [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- **psycopg2:** [psycopg2 Documentation](https://www.psycopg.org/docs/)
- **FastAPI:** [FastAPI Documentation](https://fastapi.tiangolo.com/)
- **MCP Protocol:** [MCP Specification](https://spec.modelcontextprotocol.io/)