"""
Database setup module for Tragictory Physics.

This module handles the initialization of the SQLite database with all required
tables for the physics education application.
"""

import sqlite3
from pathlib import Path
from typing import Optional


def get_db_path() -> Path:
    """Get the path to the database file.
    
    Returns:
        Path: The path to the SQLite database file.
    """
    return Path(__file__).parent.parent.parent / "data" / "physics_data.sqlite"


def initialize_db() -> None:
    """Initialize the database with all required tables.
    
    Creates the database file and all tables if they don't exist.
    Enables foreign key constraints.
    """
    db_path = get_db_path()
    
    # Ensure the data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create grades table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER NOT NULL UNIQUE,
                description TEXT
            )
        """)
        
        # Create topics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                is_simulation_available BOOLEAN DEFAULT 0,
                FOREIGN KEY (grade_id) REFERENCES grades (id) ON DELETE CASCADE
            )
        """)
        
        # Create theory_blocks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS theory_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                content_html TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
            )
        """)
        
        # Create formulas table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS formulas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                formula_latex TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_connection() -> sqlite3.Connection:
    """Get a database connection with foreign keys enabled.
    
    Returns:
        sqlite3.Connection: Database connection with foreign keys enabled.
    """
    db_path = get_db_path()
    
    if not db_path.exists():
        initialize_db()
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


if __name__ == "__main__":
    # Initialize database when run directly
    initialize_db()
    print(f"Database initialized at: {get_db_path()}")
