# Database utilities and connection management

import sqlite3
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Context manager for database connections with proper error handling"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self, row_factory=None):
        """
        Get a database connection with automatic cleanup.
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            if row_factory:
                conn.row_factory = row_factory
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, row_factory=None):
        """
        Execute a query and optionally fetch results.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch_one: Return single result
            fetch_all: Return all results
            row_factory: Optional row factory for results
        
        Returns:
            Query results or None
        """
        with self.get_connection(row_factory=row_factory) as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return None
    
    def insert(self, table, data):
        """
        Insert a row into a table.
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs
        
        Returns:
            Last row ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            return cursor.lastrowid


class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass


def get_db_manager(db_path):
    """Factory function to create a DatabaseManager instance"""
    return DatabaseManager(db_path)
