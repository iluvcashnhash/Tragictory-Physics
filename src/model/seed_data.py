"""
Database seeding module for Tragictory Physics.

This module populates the database with initial educational content
using the CONTENT_REGISTRY system for scalable content management.
"""

import json
import sqlite3
from .db_setup import get_connection


def seed_database() -> None:
    """Populate the database with initial content from CONTENT_REGISTRY.
    
    This function clears all existing data and populates the database
    with educational content registered in CONTENT_REGISTRY.
    """
    # Import CONTENT_REGISTRY to ensure all content modules are loaded
    from .content import CONTENT_REGISTRY
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear all existing data
        cursor.execute("DELETE FROM questions")
        cursor.execute("DELETE FROM formulas")
        cursor.execute("DELETE FROM theory_blocks")
        cursor.execute("DELETE FROM topics")
        cursor.execute("DELETE FROM grades")
        
        # Track created grades to avoid duplicates
        grade_ids = {}
        
        # Process all registered content
        for content in CONTENT_REGISTRY:
            grade = content["grade"]
            grade_desc = content["grade_desc"]
            title = content["title"]
            has_simulation = content["has_simulation"]
            theory_html = content["theory"]
            formulas = content["formulas"]
            questions = content.get("questions", [])
            
            # Create or get grade
            if grade not in grade_ids:
                cursor.execute(
                    "INSERT INTO grades (number, description) VALUES (?, ?)",
                    (grade, grade_desc)
                )
                grade_ids[grade] = cursor.lastrowid
                print(f"Added grade: {grade} - {grade_desc}")
            
            grade_id = grade_ids[grade]
            
            # Create topic
            cursor.execute(
                """INSERT INTO topics (grade_id, title, is_simulation_available) 
                   VALUES (?, ?, ?)""",
                (grade_id, title, has_simulation)
            )
            topic_id = cursor.lastrowid
            print(f"Added topic: {title}")
            
            # Create theory block
            cursor.execute(
                """INSERT INTO theory_blocks (topic_id, content_html) 
                   VALUES (?, ?)""",
                (topic_id, theory_html)
            )
            
            # Create formulas
            for formula in formulas:
                formula_latex = formula.get("formula_latex", "")
                description = formula.get("description", "")
                
                cursor.execute(
                    """INSERT INTO formulas (topic_id, formula_latex, description) 
                       VALUES (?, ?, ?)""",
                    (topic_id, formula_latex, description)
                )
            
            print(f"Added {len(formulas)} formulas")

            # Create questions
            for question in questions:
                cursor.execute(
                    """INSERT INTO questions (topic_id, question_text, options_json, correct_index)
                       VALUES (?, ?, ?, ?)""",
                    (
                        topic_id,
                        question.get("text", ""),
                        json.dumps(question.get("options", []), ensure_ascii=False),
                        question.get("correct_index", 0)
                    )
                )

            if questions:
                print(f"Added {len(questions)} questions")
        
        # Commit all changes
        conn.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
