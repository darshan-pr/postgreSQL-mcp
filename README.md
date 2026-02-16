# PostgreSQL MCP Server

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Uvicorn"/>
  <img src="https://img.shields.io/badge/MCP-FF6B6B?style=for-the-badge&logo=protocol&logoColor=white" alt="MCP"/>
</p>

<p align="center">
  <strong>Professional PostgreSQL Database Access for AI Assistants via Model Context Protocol</strong>
</p>

---

## Features

**Core Capabilities**
- Complete schema analysis with tables, columns, constraints, indexes, and relationships
- Advanced SQL query execution (SELECT with JOINs, CTEs, window functions, subqueries)
- Secure data manipulation (INSERT, UPDATE with ACID transaction safety)
- Schema management (CREATE, ALTER, DROP for tables, views, indexes, functions)
- Automatic foreign key relationship mapping and constraint discovery
- Query planning and performance optimization with EXPLAIN ANALYZE
- Multi-schema support for complex database architectures

**Security & Performance**
- Granular operation-level access controls
- ACID-compliant transaction management with rollback safety
- Multi-layer SQL injection prevention
- Connection pooling with psycopg3 for optimal performance
- Row-level security (RLS) support
- Comprehensive validation and error handling

---

## Security Model

### Permitted Operations
- **READ**: SELECT, SHOW, DESCRIBE, EXPLAIN, EXPLAIN ANALYZE
- **WRITE**: INSERT, UPDATE, CREATE, ALTER, DROP (configurable)

### Prohibited Operations
- DELETE, TRUNCATE (can be enabled via configuration)

**Security Features**: Prepared statements, parameterized queries, connection isolation, automatic rollback, input sanitization, read-only transaction mode support

---

## Installation

### Requirements
- Python 3.8+
- PostgreSQL 12+ (including AWS RDS, Google Cloud SQL, Azure Database)
- 512MB RAM recommended

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/postgres-mcp.git
cd postgres-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Launch server
uvicorn server:app --host 127.0.0.1 --port 3333 --reload
```

---

## Configuration

Create `.env` file:

```env
# Database Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_database_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=your_database_name

# Optional: SSL Configuration
POSTGRES_SSLMODE=require
POSTGRES_SSLROOTCERT=/path/to/ca.pem

# Optional: Connection Pooling
POSTGRES_POOL_SIZE=10
POSTGRES_POOL_MAX_OVERFLOW=5
POSTGRES_CONNECT_TIMEOUT=10

# Optional: Query Limits
MAX_ROWS=1000
QUERY_TIMEOUT=30
```

### SSL/TLS Configuration

PostgreSQL supports multiple SSL modes:

```env
# SSL Mode Options
POSTGRES_SSLMODE=disable      # No SSL (not recommended)
POSTGRES_SSLMODE=allow        # Try SSL, fallback to non-SSL
POSTGRES_SSLMODE=prefer       # Prefer SSL (default)
POSTGRES_SSLMODE=require      # Require SSL
POSTGRES_SSLMODE=verify-ca    # Require SSL + verify CA
POSTGRES_SSLMODE=verify-full  # Require SSL + verify CA + hostname
```

---

## VS Code Copilot Integration

### Prerequisites
- VS Code 1.85+
- GitHub Copilot extension with active subscription
- PostgreSQL MCP Server running locally

### Setup via Extensions View (Recommended)

1. **Open Extensions View**
   - Press `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (macOS)
   - Or use Command Palette: `Extensions: Show Extensions`

2. **Search for MCP Servers**
   - Type `@mcp` in the search field
   - Browse available MCP servers from the GitHub MCP Registry

3. **Install Custom MCP Server**
   - If your server isn't in the registry, click the settings icon (⚙️)
   - Select `Add MCP Server...` from the dropdown menu
   - Choose **stdio** as the server type

4. **Configure Server**
   ```
   Name: PostgreSQL Database Server
   Command: /path/to/postgres-mcp/.venv/bin/python
   Arguments: ["/path/to/postgres-mcp/server.py"]
   ```

5. **Choose Installation Scope**
   - **User Settings**: Available across all workspaces
   - **Workspace Settings**: Only for current project (saves to `.vscode/mcp.json`)

6. **Trust the Server**
   - VS Code will prompt you to trust the server configuration
   - Review the server details and click **Trust** to proceed

7. **Verify Connection**
   - Open Copilot Chat (`Ctrl+Alt+I` or `Cmd+Option+I`)
   - Switch to **Agent Mode** using the mode selector
   - Click the **Tools** icon (🛠️) to view available MCP tools
   - You should see PostgreSQL server tools listed

### Setup via Manual Configuration

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "postgresql-database": {
      "type": "stdio",
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/postgres-mcp/server.py"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "your_user",
        "POSTGRES_PASSWORD": "your_password",
        "POSTGRES_DB": "your_database"
      }
    }
  }
}
```

**Note**: Use absolute paths for both command and args. Environment variables in `mcp.json` override `.env` file.

### Using the MCP Server

1. **Enable Agent Mode**
   - Open Copilot Chat
   - Select **Agent** from the mode dropdown
   - Agent mode allows Copilot to use external MCP tools

2. **View Available Tools**
   - Click the **Tools** icon in the chat interface
   - Toggle individual tools on/off as needed
   - Available tools: `get_schema`, `get_relationships`, `run_sql`, `run_write_sql`, `analyze_query`

3. **Use in Prompts**
   - Type `#` in chat to see available tools
   - Select a specific tool or let Copilot choose automatically
   - Examples:
     - "Show me the database schema for the users table"
     - "Find all orders from last month with their customer names"
     - "Analyze the performance of this query: SELECT * FROM large_table"

4. **Manage Tool Permissions**
   - First-time tool use requires explicit permission
   - Choose between:
     - **Continue**: Run once for this request
     - **Current session**: Auto-approve for this chat session
     - **Always allow**: Auto-approve for all sessions (use with caution)

### Advanced Configuration

**Multi-Database Setup** (Connect to multiple PostgreSQL instances):
```json
{
  "mcpServers": {
    "postgres-production": {
      "type": "stdio",
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/postgres-mcp/server.py"],
      "env": {
        "POSTGRES_HOST": "prod.example.com",
        "POSTGRES_DB": "production_db"
      }
    },
    "postgres-staging": {
      "type": "stdio",
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/postgres-mcp/server.py"],
      "env": {
        "POSTGRES_HOST": "staging.example.com",
        "POSTGRES_DB": "staging_db"
      }
    }
  }
}
```

**Toolsets** (Group related tools):
```json
{
  "toolsets": {
    "database-read": {
      "tools": [
        "postgresql-database.get_schema",
        "postgresql-database.run_sql",
        "postgresql-database.analyze_query"
      ]
    },
    "database-write": {
      "tools": ["postgresql-database.run_write_sql"]
    }
  }
}
```

**Copilot Instructions** (`.github/copilot-instructions.md`):
```markdown
When querying the PostgreSQL database:
- Always check the schema first using get_schema
- Use read-only run_sql for SELECT queries
- Only use run_write_sql for INSERT/UPDATE operations
- Leverage PostgreSQL-specific features (CTEs, window functions, JSONB)
- Use EXPLAIN ANALYZE for query optimization
- Respect multi-schema architecture (public, auth, analytics, etc.)
```

### Troubleshooting

**Server not appearing in tools list:**
- Verify server is running: `http://127.0.0.1:3333`
- Check `mcp.json` configuration for syntax errors
- Restart VS Code after configuration changes
- Check Output panel: `View > Output > MCP Servers`

**Connection errors:**
- Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Test connection: `psql -h localhost -U your_user -d your_database`
- Check firewall rules and network connectivity
- Verify `.env` file has correct credentials

**SSL/TLS errors:**
- Ensure POSTGRES_SSLMODE is set correctly
- Verify SSL certificates are valid and accessible
- Check PostgreSQL server SSL configuration
- Use `POSTGRES_SSLMODE=disable` for local development (not recommended for production)

**Permission denied errors:**
- Ensure Python virtual environment is activated
- Verify file paths are absolute, not relative
- Check database user has required permissions
- Review PostgreSQL `pg_hba.conf` authentication settings

**Server fails to start:**
- Review Output panel: `View > Output > MCP Servers`
- Check Python path: `which python` (macOS/Linux) or `where python` (Windows)
- Verify all dependencies installed: `pip list`
- Check for port conflicts: `lsof -i :3333` (macOS/Linux)

---

## Available Tools

| Tool | Description | Operations |
|------|-------------|-----------|
| `get_schema` | Retrieve complete database schema | Tables, columns, indexes, constraints, views, functions |
| `get_relationships` | Map foreign key relationships | Visual relationship graph with cardinality |
| `run_sql` | Execute read queries | SELECT, SHOW, DESCRIBE, EXPLAIN, EXPLAIN ANALYZE |
| `run_write_sql` | Execute write operations | INSERT, UPDATE, CREATE, ALTER, DROP |
| `analyze_query` | Query performance analysis | EXPLAIN ANALYZE with cost estimation |

---

## Usage Examples

### Schema Exploration
```sql
-- Get complete schema
"Show me all tables and their relationships"

-- Specific schema details
"Describe the users table with all constraints"

-- Multi-schema support
"List all tables in the analytics schema"
```

### Data Querying
```sql
-- Basic queries
"Find all active users created in the last 30 days"

-- Complex joins
"Show customers with their order totals and most recent purchase date"

-- Window functions
"Rank products by sales within each category"

-- CTEs (Common Table Expressions)
"Use a CTE to calculate running totals of daily revenue"
```

### Performance Analysis
```sql
-- Query planning
"Analyze the execution plan for this query: SELECT * FROM large_table WHERE status = 'active'"

-- Index suggestions
"What indexes would improve performance for queries filtering by created_at?"
```

### Data Manipulation
```sql
-- Insert data
"Add a new user: email='john@example.com', name='John Doe', role='user'"

-- Batch insert
"Insert multiple products from this JSON array"

-- Update records
"Update all orders from last month to set status='processed'"
```

### Schema Management
```sql
-- Create table
"Create a products table with id (UUID), name (VARCHAR), price (DECIMAL), created_at (TIMESTAMP)"

-- Add constraints
"Add a foreign key constraint from orders.user_id to users.id"

-- Create index
"Create a B-tree index on orders(created_at) for date range queries"

-- Create view
"Create a view showing customer order summaries"
```

### PostgreSQL-Specific Features
```sql
-- JSONB queries
"Find all users where preferences->>'theme' = 'dark'"

-- Array operations
"Select products where 'electronics' = ANY(categories)"

-- Full-text search
"Find articles matching the search term 'postgresql' using tsvector"

-- Recursive CTEs
"Show organizational hierarchy using a recursive query on employees table"
```

---

## PostgreSQL vs MySQL Differences

| Feature | PostgreSQL | MySQL |
|---------|-----------|-------|
| **ACID Compliance** | Full ACID compliance | InnoDB engine only |
| **Data Types** | Rich (JSONB, Arrays, UUID, Ranges) | Basic types |
| **Window Functions** | Full support | Limited (MySQL 8.0+) |
| **CTEs** | Recursive and non-recursive | MySQL 8.0+ only |
| **Full-Text Search** | Native with tsvector | Basic FULLTEXT indexes |
| **Concurrent Writes** | MVCC (better concurrency) | Row-level locking |
| **Extensions** | Rich ecosystem (PostGIS, pg_stat_statements) | Limited plugins |
| **Case Sensitivity** | Identifiers lowercased | Configurable |

---

## License

MIT License - Copyright (c) 2024 Your Organization

See LICENSE file for full terms.

---

## Acknowledgments

Built with [Anthropic's Model Context Protocol](https://modelcontextprotocol.io), FastAPI, and psycopg3.

---

<p align="center">
  <strong>Secure • Efficient • AI-Powered Database Access</strong>
</p>