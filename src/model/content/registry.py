"""
Content registry for Tragictory Physics database seeding.

This module provides a registry system for managing educational content
that will be loaded into the database during the seeding process.
"""

CONTENT_REGISTRY = []

def register_content(grade: int, grade_desc: str, title: str, has_simulation: bool, theory_html: str, formulas: list, questions: list = None):
    """Register educational content for database seeding.
    
    Args:
        grade: Grade number (e.g., 10 for 10th grade)
        grade_desc: Description of the grade
        title: Topic title
        has_simulation: Whether the topic has simulation available
        theory_html: HTML content for the theory
        formulas: List of formula dictionaries with 'formula_latex' and 'description' keys
    """
    CONTENT_REGISTRY.append({
        "grade": grade,
        "grade_desc": grade_desc,
        "title": title,
        "has_simulation": has_simulation,
        "theory": theory_html,
        "formulas": formulas,
        "questions": questions or []
    })
