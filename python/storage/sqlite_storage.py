"""
SQLite storage module for the Trading Information Scraper application.

This module provides functionality for storing financial data in a SQLite database.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """
    Storage class for SQLite database.
    
    This class provides methods for storing financial data in a SQLite database.
    """
    
    def __init__(self, db_path: str = "./data/trading.db"):
        """
        Initialize the SQLite storage.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory_exists()
        self._initialize_database()
    
    def store(self, data: Union[Dict, pd.DataFrame], table_name: str) -> bool:
        """
        Store data in a SQLite table.
        
        Args:
            data: Data to store
            table_name: Name of the table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert data to DataFrame if it's not already
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = self._convert_to_dataframe(data)
                
            # Connect to the database
            conn = self._get_connection()
            
            # Store DataFrame in the table
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            conn.close()
            logger.info(f"Data stored in table {table_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error storing data in table {table_name}: {e}")
            return False
    
    def append(self, data: Union[Dict, pd.DataFrame], table_name: str) -> bool:
        """
        Append data to an existing SQLite table.
        
        Args:
            data: Data to append
            table_name: Name of the table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert data to DataFrame if it's not already
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = self._convert_to_dataframe(data)
                
            # Connect to the database
            conn = self._get_connection()
            
            # Check if the table exists
            if self._table_exists(conn, table_name):
                # Append DataFrame to the table
                df.to_sql(table_name, conn, if_exists='append', index=False)
                logger.info(f"Data appended to table {table_name}")
            else:
                # Table doesn't exist, create it
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                logger.info(f"Table {table_name} created with data")
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error appending data to table {table_name}: {e}")
            return False
    
    def load(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Load data from a SQLite table.
        
        Args:
            table_name: Name of the table
            conditions: Dictionary of column-value pairs for filtering
            
        Returns:
            DataFrame with the loaded data
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            
            # Build the query
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if conditions:
                where_clauses = []
                for column, value in conditions.items():
                    where_clauses.append(f"{column} = ?")
                    params.append(value)
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute the query
            df = pd.read_sql_query(query, conn, params=params)
            
            conn.close()
            logger.info(f"Data loaded from table {table_name}")
            
            return df
        except Exception as e:
            logger.error(f"Error loading data from table {table_name}: {e}")
            return pd.DataFrame()
    
    def execute_query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """
        Execute a custom SQL query.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            DataFrame with the query results
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            
            # Execute the query
            df = pd.read_sql_query(query, conn, params=params)
            
            conn.close()
            logger.info(f"Query executed: {query}")
            
            return df
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def execute_update(self, query: str, params: Optional[List] = None) -> bool:
        """
        Execute a custom SQL update query.
        
        Args:
            query: SQL query to execute (INSERT, UPDATE, DELETE)
            params: Parameters for the query
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute the query
            cursor.execute(query, params or [])
            conn.commit()
            
            affected_rows = cursor.rowcount
            conn.close()
            
            logger.info(f"Update query executed: {query} (affected {affected_rows} rows)")
            return True
        except Exception as e:
            logger.error(f"Error executing update query: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Query for table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> List[Tuple[str, str]]:
        """
        Get the schema of a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of (column_name, column_type) tuples
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Query for table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = [(row[1], row[2]) for row in cursor.fetchall()]  # (name, type)
            
            conn.close()
            return schema
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
            return []
    
    def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """
        Create a new table.
        
        Args:
            table_name: Name of the table
            schema: Dictionary mapping column names to their types
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build the CREATE TABLE query
            columns = [f"{name} {type_}" for name, type_ in schema.items()]
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            
            # Execute the query
            cursor.execute(query)
            conn.commit()
            conn.close()
            
            logger.info(f"Table {table_name} created")
            return True
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
    
    def drop_table(self, table_name: str) -> bool:
        """
        Drop a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to the database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute the DROP TABLE query
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()
            conn.close()
            
            logger.info(f"Table {table_name} dropped")
            return True
        except Exception as e:
            logger.error(f"Error dropping table {table_name}: {e}")
            return False
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        return conn
    
    def _ensure_directory_exists(self):
        """Ensure the directory for the database file exists."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            logger.debug(f"Database directory {os.path.dirname(self.db_path)} ensured")
        except Exception as e:
            logger.error(f"Error ensuring database directory: {e}")
            raise
    
    def _initialize_database(self):
        """Initialize the database with necessary tables."""
        try:
            # Connect to the database
            conn = self._get_connection()
            
            # Create metadata table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            
            # Insert or update initialization record
            conn.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """, ('initialized', 'true', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.debug("Database initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            conn: SQLite connection
            table_name: Name of the table
            
        Returns:
            True if the table exists, False otherwise
        """
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None
    
    def _convert_to_dataframe(self, data: Any) -> pd.DataFrame:
        """
        Convert data to a pandas DataFrame.
        
        Args:
            data: Data to convert
            
        Returns:
            DataFrame with the data
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            # Check if it's a dictionary of records
            if all(isinstance(v, dict) for v in data.values()):
                # Convert to list of dictionaries
                records = [{"id": k, **v} for k, v in data.items()]
                return pd.DataFrame(records)
            else:
                # Simple dictionary
                return pd.DataFrame([data])
        elif isinstance(data, list):
            # List of dictionaries
            if all(isinstance(item, dict) for item in data):
                return pd.DataFrame(data)
            else:
                # List of values
                return pd.DataFrame({"value": data})
        else:
            # Single value
            return pd.DataFrame({"value": [data]})