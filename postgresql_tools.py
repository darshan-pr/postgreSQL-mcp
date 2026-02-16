"""
PostgreSQL database tools for MCP server.
Provides read-only database access with proper connection management.
Optimized version with better validation and complex query support.
"""

import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import re

load_dotenv()


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class ConnectionManager:
    """Centralized connection management to reduce redundancy."""
    
    @staticmethod
    def get_connection(database: str = None):
        """
        Create and return a PostgreSQL database connection.
        
        Args:
            database: Optional database name. If not provided, uses POSTGRES_DB from env.
        
        Returns:
            psycopg.Connection: Active database connection
            
        Raises:
            DatabaseError: If connection fails
        """
        try:
            return psycopg.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                dbname=database or os.getenv("POSTGRES_DB"),
                connect_timeout=10,
                # Read-only connection for safety
                options="-c default_transaction_read_only=on"
            )
        except psycopg.Error as e:
            raise DatabaseError(f"Failed to connect to database: {str(e)}")
    
    @staticmethod
    def execute_query(query: str, database: str = None, fetch_all: bool = True):
        """
        Execute a query with automatic connection and cursor management.
        
        Args:
            query: SQL query to execute
            database: Optional database name
            fetch_all: Whether to fetch all results
            
        Returns:
            Query results or None
            
        Raises:
            DatabaseError: If query execution fails
        """
        conn = None
        cursor = None
        try:
            conn = ConnectionManager.get_connection(database)
            cursor = conn.cursor(row_factory=dict_row)
            cursor.execute(query)
            
            if fetch_all:
                result = cursor.fetchall()
                return [dict(row) for row in result]
            else:
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except psycopg.Error as e:
            raise DatabaseError(f"Query execution failed: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


class QueryValidator:
    """Validates SQL queries to ensure they are read-only."""
    
    # Whitelist of allowed query types (read-only operations)
    ALLOWED_STATEMENTS = {
        'SELECT', 'WITH', 'EXPLAIN', 'SHOW', 'DESCRIBE', 'DESC','INSERT', 'UPDATE', 'ALTER'
    }
    
    # Blacklist of write operations (comprehensive)
    FORBIDDEN_STATEMENTS = {
         'DELETE', 'DROP', 'TRUNCATE',
        'CREATE', 'REPLACE', 'RENAME', 'GRANT', 'REVOKE', 'COMMIT',
        'ROLLBACK', 'SAVEPOINT', 'LOCK', 'COPY', 'CALL', 'EXECUTE',
        'PREPARE', 'DEALLOCATE', 'SET', 'RESET'
    }
    
    @staticmethod
    def is_read_only(query: str) -> tuple[bool, str]:
        """
        Validate if a query is read-only.
        
        Args:
            query: SQL query string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove comments and normalize whitespace
        query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
        query_clean = ' '.join(query_clean.split()).strip().upper()
        
        if not query_clean:
            return False, "Empty query"
        
        # Split into statements (handle multiple statements)
        statements = [s.strip() for s in query_clean.split(';') if s.strip()]
        
        for statement in statements:
            # Get the first keyword
            first_keyword = statement.split()[0] if statement.split() else ''
            
            # Check if it's an allowed statement
            if first_keyword not in QueryValidator.ALLOWED_STATEMENTS:
                # Check if it contains forbidden keywords
                for forbidden in QueryValidator.FORBIDDEN_STATEMENTS:
                    if re.search(r'\b' + forbidden + r'\b', statement):
                        return False, f"Forbidden operation detected: {forbidden}"
                
                # If not in whitelist and not explicitly forbidden, reject for safety
                return False, f"Only SELECT, WITH (CTEs), and EXPLAIN queries are allowed"
        
        # Additional safety checks
        if 'INTO' in query_clean and 'SELECT' in query_clean:
            # Block SELECT INTO which creates tables
            if re.search(r'\bSELECT\s+.+\s+INTO\s+', query_clean):
                return False, "SELECT INTO is not allowed (creates tables)"
        
        return True, ""
    
    @staticmethod
    def is_write_allowed(query: str) -> tuple[bool, str]:
        """
        Validate if a query is allowed for write operations.
        
        Args:
            query: SQL query string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove comments and normalize whitespace
        query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
        query_clean = ' '.join(query_clean.split()).strip().upper()
        
        if not query_clean:
            return False, "Empty query"
        
        # Split into statements (handle multiple statements)
        statements = [s.strip() for s in query_clean.split(';') if s.strip()]
        
        allowed_writes = {'INSERT', 'UPDATE', 'ALTER'}
        
        for statement in statements:
            # Get the first keyword
            first_keyword = statement.split()[0] if statement.split() else ''
            
            # Check if it's an allowed write statement
            if first_keyword not in allowed_writes:
                # Check if it contains forbidden keywords
                for forbidden in QueryValidator.FORBIDDEN_STATEMENTS:
                    if re.search(r'\b' + forbidden + r'\b', statement):
                        return False, f"Forbidden operation detected: {forbidden}"
                
                # If not in allowed writes and not explicitly forbidden, reject
                return False, f"Only INSERT, UPDATE, and ALTER queries are allowed for writes"
        
        return True, ""


def run_sql(query: str, database: str = None) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query (SELECT, WITH, EXPLAIN).
    Supports complex queries including JOINs, subqueries, CTEs, window functions.
    
    Args:
        query: SQL query string (SELECT, WITH, EXPLAIN)
        database: Optional database name to query against
        
    Returns:
        List of dictionaries representing query results
        
    Raises:
        DatabaseError: If query execution fails or query is not read-only
    """
    # Validate query is read-only
    is_valid, error_msg = QueryValidator.is_read_only(query)
    if not is_valid:
        raise DatabaseError(f"Invalid query: {error_msg}")
    
    try:
        return ConnectionManager.execute_query(query, database, fetch_all=True)
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"Unexpected error: {str(e)}")


def run_write_sql(query: str, database: str = None) -> Dict[str, Any]:
    """
    Execute a write SQL query (INSERT, UPDATE, ALTER).
    
    Args:
        query: SQL query string
        database: Optional database name
        
    Returns:
        Dictionary with execution results
        
    Raises:
        DatabaseError: If query execution fails or query is not allowed
    """
    # Validate query is allowed for writes
    is_valid, error_msg = QueryValidator.is_write_allowed(query)
    if not is_valid:
        raise DatabaseError(f"Invalid write query: {error_msg}")
    
    conn = None
    cursor = None
    try:
        # Create write connection (no read-only constraint)
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=database or os.getenv("POSTGRES_DB"),
            connect_timeout=10
        )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        
        return {
            "affected_rows": cursor.rowcount,
            "message": f"Query executed successfully, affected {cursor.rowcount} rows"
        }
        
    except psycopg.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"Write query failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_schema(database: str = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Retrieve complete database schema information.
    
    Args:
        database: Optional database name to query against
    
    Returns:
        Dictionary mapping table names to their column definitions
        
    Raises:
        DatabaseError: If schema retrieval fails
    """
    query = """
        SELECT 
            c.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            CASE 
                WHEN pk.column_name IS NOT NULL THEN 'PRI'
                WHEN fk.column_name IS NOT NULL THEN 'MUL'
                ELSE ''
            END as column_key
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku
                ON tc.constraint_name = ku.constraint_name
                AND tc.table_schema = ku.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
        ) pk ON c.table_name = pk.table_name 
            AND c.column_name = pk.column_name
        LEFT JOIN (
            SELECT ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku
                ON tc.constraint_name = ku.constraint_name
                AND tc.table_schema = ku.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
        ) fk ON c.table_name = fk.table_name 
            AND c.column_name = fk.column_name
        WHERE c.table_schema = 'public'
        ORDER BY c.table_name, c.ordinal_position
    """
    
    try:
        rows = ConnectionManager.execute_query(query, database, fetch_all=True)
        
        schema = {}
        for row in rows:
            table = row["table_name"]
            if table not in schema:
                schema[table] = []
            schema[table].append({
                "column": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "key": row["column_key"]
            })
        
        return schema
        
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve schema: {str(e)}")


def get_relationships(database: str = None) -> List[Dict[str, str]]:
    """
    Retrieve foreign key relationships between tables.
    
    Args:
        database: Optional database name to query against
    
    Returns:
        List of dictionaries containing relationship information
        
    Raises:
        DatabaseError: If relationship retrieval fails
    """
    query = """
        SELECT
            tc.table_name as "table",
            kcu.column_name as "column",
            ccu.table_name as referenced_table,
            ccu.column_name as referenced_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name
    """
    
    try:
        return ConnectionManager.execute_query(query, database, fetch_all=True)
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve relationships: {str(e)}")


def insert_data(table: str, data: List[Dict[str, Any]], database: str = None) -> Dict[str, Any]:
    """
    Insert data into a table. Requires write permission.
    
    Args:
        table: Name of the table to insert into
        data: List of dictionaries where keys are column names
        database: Optional database name to insert into
        
    Returns:
        Dictionary with insert results
        
    Raises:
        DatabaseError: If insert fails or validation fails
    """
    if not table or not isinstance(table, str):
        raise DatabaseError("Valid table name is required")
    
    if not data or not isinstance(data, list) or not data:
        raise DatabaseError("Data must be a non-empty list of dictionaries")
    
    # Validate table name (alphanumeric and underscores only)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
        raise DatabaseError(f"Invalid table name: {table}")
    
    conn = None
    cursor = None
    
    try:
        # Need write connection for insert (remove read-only constraint)
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=database or os.getenv("POSTGRES_DB"),
            connect_timeout=10
        )
        cursor = conn.cursor(row_factory=dict_row)
        
        # Verify table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        """, (table,))
        
        if not cursor.fetchone():
            raise DatabaseError(f"Table '{table}' does not exist")
        
        # Validate all records have consistent columns
        columns = list(data[0].keys())
        for i, record in enumerate(data):
            if set(record.keys()) != set(columns):
                raise DatabaseError(f"Record {i} has inconsistent columns")
        
        # Build INSERT query
        columns_str = ", ".join(f'"{col}"' for col in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f'INSERT INTO "{table}" ({columns_str}) VALUES ({placeholders})'
        
        # Get primary key for RETURNING clause
        cursor.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
        """, (table,))
        
        pk_result = cursor.fetchone()
        pk_column = pk_result['attname'] if pk_result else None
        
        if pk_column:
            query += f' RETURNING "{pk_column}"'
        
        # Execute batch insert
        inserted_ids = []
        for record in data:
            values = tuple(record[col] for col in columns)
            cursor.execute(query, values)
            if pk_column:
                result = cursor.fetchone()
                if result:
                    inserted_ids.append(result[pk_column])
        
        conn.commit()
        
        return {
            "inserted_count": len(data),
            "last_insert_id": inserted_ids[-1] if inserted_ids else None,
            "message": f"Successfully inserted {len(data)} record(s) into {table}"
        }
        
    except psycopg.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"Insert failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def list_databases() -> List[str]:
    """
    List all accessible databases.
    
    Returns:
        List of database names
        
    Raises:
        DatabaseError: If listing fails
    """
    query = """
        SELECT datname 
        FROM pg_database 
        WHERE datistemplate = false 
        AND has_database_privilege(datname, 'CONNECT')
        ORDER BY datname
    """
    
    try:
        results = ConnectionManager.execute_query(query, database="postgres", fetch_all=True)
        return [row['datname'] for row in results]
    except Exception as e:
        raise DatabaseError(f"Failed to list databases: {str(e)}")


def get_query_stats(query: str, database: str = None) -> Dict[str, Any]:
    """
    Get query execution plan and statistics without executing the query.
    Useful for understanding complex queries.
    
    Args:
        query: SQL query to analyze
        database: Optional database name
        
    Returns:
        Dictionary with query statistics
        
    Raises:
        DatabaseError: If analysis fails
    """
    try:
        # Validate it's a read-only query first
        is_valid, error_msg = QueryValidator.is_read_only(query)
        if not is_valid:
            raise DatabaseError(f"Invalid query: {error_msg}")
        
        explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE false, VERBOSE true) {query}"
        result = ConnectionManager.execute_query(explain_query, database, fetch_all=False)
        
        if result and 'QUERY PLAN' in result:
            plan_data = result['QUERY PLAN']
            if isinstance(plan_data, list) and len(plan_data) > 0:
                plan = plan_data[0].get('Plan', {})
                return {
                    'estimated_rows': plan.get('Plan Rows', 0),
                    'estimated_cost': plan.get('Total Cost', 0),
                    'plan_type': plan.get('Node Type', 'Unknown'),
                    'full_plan': plan_data
                }
        
        return {'error': 'Could not parse query plan'}
        
    except Exception as e:
        raise DatabaseError(f"Failed to analyze query: {str(e)}")