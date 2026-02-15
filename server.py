"""
MCP Server for PostgreSQL database access.
Optimized version with automatic query execution and better error handling.
"""

from fastapi import FastAPI, Request
from postgresql_tools import (
    run_sql, get_schema, get_relationships, insert_data, 
    list_databases, get_query_stats, DatabaseError
)
import json
from typing import Dict, Any

app = FastAPI()


class MCPResponse:
    """Helper class for creating MCP responses."""
    
    @staticmethod
    def error(request_id: int, message: str, code: int = -32603) -> Dict[str, Any]:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    @staticmethod
    def success(request_id: int, result: Any) -> Dict[str, Any]:
        """Create a JSON-RPC success response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    @staticmethod
    def text_content(text: str) -> Dict[str, Any]:
        """Create text content for MCP response."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }


class ResultFormatter:
    """Formats database results for display."""
    
    @staticmethod
    def databases(databases: list) -> str:
        """Format list of databases."""
        if not databases:
            return "No accessible databases found."
        
        lines = [
            "Accessible Databases:",
            "=" * 50,
            ""
        ]
        
        for db in databases:
            lines.append(f"  • {db}")
        
        lines.extend([
            "",
            f"Total: {len(databases)} database(s)",
            "",
            "Usage: Specify 'database' parameter in tool calls",
            "Example: get_schema(database='mydb')"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def schema(schema: dict, db_info: str = "") -> str:
        """Format schema information."""
        if not schema:
            return f"No tables found{db_info}."
        
        lines = [f"Database Schema{db_info}:", "=" * 50, ""]
        
        for table_name in sorted(schema.keys()):
            lines.append(f"📋 Table: {table_name}")
            lines.append("-" * 40)
            
            for col in schema[table_name]:
                key_badge = f" [{col['key']}]" if col['key'] else ""
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                lines.append(f"  • {col['column']}: {col['type']} {nullable}{key_badge}")
            
            lines.append("")
        
        lines.append(f"Total: {len(schema)} table(s)")
        return "\n".join(lines)
    
    @staticmethod
    def relationships(relationships: list, db_info: str = "") -> str:
        """Format relationship information."""
        if not relationships:
            return f"No foreign key relationships found{db_info}."
        
        lines = [f"Foreign Key Relationships{db_info}:", "=" * 50, ""]
        
        for rel in relationships:
            lines.append(
                f"🔗 {rel['table']}.{rel['column']} → "
                f"{rel['referenced_table']}.{rel['referenced_column']}"
            )
        
        lines.append("")
        lines.append(f"Total: {len(relationships)} relationship(s)")
        return "\n".join(lines)
    
    @staticmethod
    def query_result(result: list, query: str, db_info: str = "") -> str:
        """Format query results."""
        row_count = len(result)
        
        lines = [
            f"✅ Query executed successfully{db_info}",
            f"📊 Rows returned: {row_count}",
            "",
            "Query:",
            "-" * 50,
            query,
            "",
            "Results:",
            "=" * 50
        ]
        
        if not result:
            lines.append("(No rows returned)")
        else:
            lines.append(json.dumps(result, indent=2, default=str))
        
        return "\n".join(lines)
    
    @staticmethod
    def insert_result(result: dict, db_info: str = "") -> str:
        """Format insert operation results."""
        lines = [
            f"Insert Operation{db_info}:",
            "=" * 50,
            f"✅ {result['message']}",
            f"📝 Records inserted: {result['inserted_count']}"
        ]
        
        if result.get('last_insert_id'):
            lines.append(f"🆔 Last insert ID: {result['last_insert_id']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def query_stats(stats: dict, db_info: str = "") -> str:
        """Format query statistics."""
        lines = [
            f"Query Analysis{db_info}:",
            "=" * 50,
            f"📊 Estimated rows: {stats.get('estimated_rows', 'N/A')}",
            f"💰 Estimated cost: {stats.get('estimated_cost', 'N/A')}",
            f"🔍 Plan type: {stats.get('plan_type', 'N/A')}"
        ]
        
        if 'full_plan' in stats:
            lines.extend([
                "",
                "Full Execution Plan:",
                "-" * 50,
                json.dumps(stats['full_plan'], indent=2)
            ])
        
        return "\n".join(lines)


# Tool definitions with clear descriptions
TOOLS = {
    "list_databases": {
        "description": "List all accessible PostgreSQL databases. Use this to see available databases before querying.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_schema": {
        "description": "Get complete database schema (tables, columns, types, keys). USE THIS FIRST to understand structure before writing queries. Supports complex databases with JOINs and relationships.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Optional: Database name (e.g., 'mydb'). Uses default if not specified."
                }
            },
            "required": []
        }
    },
    "get_relationships": {
        "description": "Get foreign key relationships between tables. Use this before writing JOIN queries to understand table connections.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Optional: Database name. Uses default if not specified."
                }
            },
            "required": []
        }
    },
    "run_sql": {
        "description": "Execute READ-ONLY queries (SELECT, WITH, EXPLAIN). Supports complex queries: JOINs, subqueries, CTEs, window functions, aggregations. Automatically executes without permission prompts. Cannot modify data - use insert_data for that.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query (SELECT, WITH, EXPLAIN). Supports complex queries with JOINs, CTEs, subqueries. Add LIMIT for large result sets."
                },
                "database": {
                    "type": "string",
                    "description": "Optional: Database name. Uses default if not specified."
                }
            },
            "required": ["query"]
        }
    },
    "get_query_stats": {
        "description": "Analyze query execution plan and get statistics without running the query. Useful for understanding performance of complex queries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to analyze"
                },
                "database": {
                    "type": "string",
                    "description": "Optional: Database name"
                }
            },
            "required": ["query"]
        }
    },
    "insert_data": {
        "description": "INSERT new records into a table. This is the ONLY way to add data (run_sql cannot insert). Use after calling get_schema to verify column names. Example: insert_data('users', [{'name': 'John', 'email': 'john@example.com'}])",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "Table name (must exist in schema)"
                },
                "data": {
                    "type": "array",
                    "description": "Array of objects. Each object is a row with column names as keys. Example: [{'name': 'John', 'age': 30}]",
                    "items": {
                        "type": "object"
                    }
                },
                "database": {
                    "type": "string",
                    "description": "Optional: Database name"
                }
            },
            "required": ["table", "data"]
        }
    }
}


@app.post("/")
async def mcp_endpoint(req: Request):
    """Main MCP endpoint handling all requests."""
    
    try:
        body = await req.json()
    except Exception as e:
        return MCPResponse.error(0, f"Invalid JSON: {str(e)}")
    
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id", 0)

    # Handle initialization
    if method == "initialize":
        return MCPResponse.success(request_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "postgresql-mcp-server",
                "version": "2.0.0"
            }
        })

    # Handle tools list
    if method == "tools/list":
        tools_list = [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["input_schema"]
            }
            for name, tool in TOOLS.items()
        ]
        return MCPResponse.success(request_id, {"tools": tools_list})

    # Handle tool execution
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if not tool_name:
            return MCPResponse.error(request_id, "Missing tool name")

        if tool_name not in TOOLS:
            return MCPResponse.error(request_id, f"Unknown tool: {tool_name}")

        try:
            database = args.get("database")
            db_suffix = f" (database: {database})" if database else ""
            
            # Execute tool
            if tool_name == "list_databases":
                result = list_databases()
                text = ResultFormatter.databases(result)
                
            elif tool_name == "get_schema":
                result = get_schema(database)
                text = ResultFormatter.schema(result, db_suffix)
                
            elif tool_name == "get_relationships":
                result = get_relationships(database)
                text = ResultFormatter.relationships(result, db_suffix)
                
            elif tool_name == "run_sql":
                query = args.get("query")
                if not query:
                    return MCPResponse.error(request_id, "Missing 'query' parameter")
                
                # Execute automatically without permission prompt
                result = run_sql(query, database)
                text = ResultFormatter.query_result(result, query, db_suffix)
                
            elif tool_name == "get_query_stats":
                query = args.get("query")
                if not query:
                    return MCPResponse.error(request_id, "Missing 'query' parameter")
                
                result = get_query_stats(query, database)
                text = ResultFormatter.query_stats(result, db_suffix)
                
            elif tool_name == "insert_data":
                table = args.get("table")
                data = args.get("data")
                
                if not table:
                    return MCPResponse.error(request_id, "Missing 'table' parameter")
                if not data:
                    return MCPResponse.error(request_id, "Missing 'data' parameter")
                
                result = insert_data(table, data, database)
                text = ResultFormatter.insert_result(result, db_suffix)
            
            else:
                return MCPResponse.error(request_id, f"Tool not implemented: {tool_name}")
            
            return MCPResponse.success(request_id, MCPResponse.text_content(text))

        except DatabaseError as e:
            return MCPResponse.error(request_id, f"Database error: {str(e)}")
        except Exception as e:
            return MCPResponse.error(request_id, f"Unexpected error: {str(e)}")

    # Unknown method
    return MCPResponse.error(request_id, f"Unknown method: {method}")


if __name__ == "__main__":
    import sys
    import asyncio

    print("PostgreSQL MCP Server v2.0 - Optimized", file=sys.stderr)
    print("Supports: Complex SELECT queries, JOINs, CTEs, auto-execution", file=sys.stderr)

    async def stdio_loop():
        """Handle STDIO communication for Claude Desktop integration."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line)
                
                # Create fake request object
                class FakeRequest:
                    async def json(self):
                        return request

                response = await mcp_endpoint(FakeRequest())
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": 0,
                    "error": {"code": -32700, "message": "Parse error"}
                }), flush=True)
            except Exception as e:
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": 0,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                }), flush=True)

    asyncio.run(stdio_loop())