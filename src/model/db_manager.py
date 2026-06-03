"""
Database manager module for Tragictory Physics.

This module provides a singleton DatabaseManager class for handling all database
operations with proper connection management and data access methods.
"""

import sqlite3
from typing import List, Dict, Optional
from .db_setup import get_connection


class DatabaseManager:
    """Singleton database manager for physics education application.
    
    Provides centralized access to database operations with connection pooling
    and data retrieval methods returning dictionaries with column names as keys.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls) -> 'DatabaseManager':
        """Create or return the singleton instance.
        
        Returns:
            DatabaseManager: The singleton instance of DatabaseManager.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the database manager with connection."""
        if self._connection is None:
            self._connection = get_connection()
            self._connection.row_factory = sqlite3.Row
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert sqlite3.Row to dictionary.
        
        Args:
            row: SQLite row object.
            
        Returns:
            Dict: Dictionary with column names as keys.
        """
        return dict(row)
    
    def get_grades(self) -> List[Dict]:
        """Get all grades from the database.
        
        Returns:
            List[Dict]: List of grade dictionaries with keys: id, number, description.
        """
        cursor = self._connection.cursor()
        cursor.execute("SELECT id, number, description FROM grades ORDER BY number")
        rows = cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]
    
    def get_topics_by_grade(self, grade_id: int) -> List[Dict]:
        """Get topics for a specific grade.
        
        Args:
            grade_id: The ID of the grade.
            
        Returns:
            List[Dict]: List of topic dictionaries with keys: id, grade_id, title, 
                       is_simulation_available.
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT id, grade_id, title, is_simulation_available FROM topics "
            "WHERE grade_id = ? ORDER BY title",
            (grade_id,)
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]
    
    def get_theory_for_topic(self, topic_id: int) -> Dict:
        """Get theory content for a specific topic.
        
        Args:
            topic_id: The ID of the topic.
            
        Returns:
            Dict: Theory block dictionary with keys: id, topic_id, content_html.
                  Returns empty dict if no theory found.
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT id, topic_id, content_html FROM theory_blocks "
            "WHERE topic_id = ? LIMIT 1",
            (topic_id,)
        )
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else {}
    
    def get_formulas_for_topic(self, topic_id: int) -> List[Dict]:
        """Get formulas for a specific topic.
        
        Args:
            topic_id: The ID of the topic.
            
        Returns:
            List[Dict]: List of formula dictionaries with keys: id, topic_id, 
                       formula_latex, description.
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT id, topic_id, formula_latex, description FROM formulas "
            "WHERE topic_id = ? ORDER BY id",
            (topic_id,)
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]
    
    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        self.close()


# Global instance for easy access
db_manager = DatabaseManager()
