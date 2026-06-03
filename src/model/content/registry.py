"""
Content registry for Tragictory Physics database seeding.

This module provides a registry system for managing educational content
that will be loaded into the database during the seeding process.

Content modules are discovered automatically via load_all_content().
Each content module at any depth under src/model/content/ that does not
start with '__' or equal 'registry' is imported, which triggers their
register_content() call and populates CONTENT_REGISTRY.
"""

import importlib
import pkgutil
import sys
from pathlib import Path

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


def load_all_content() -> None:
    """Dynamically import all content modules to populate CONTENT_REGISTRY.

    Walks every Python module found recursively inside the
    ``src.model.content`` package, skipping:
    - Files/packages whose name starts with ``__`` (e.g. ``__init__``).
    - The ``registry`` module itself.

    Importing each module executes its top-level ``register_content()``
    call, which appends an entry to CONTENT_REGISTRY.
    """
    package_name = __name__.rsplit('.', 1)[0]  # 'src.model.content'
    package_path = str(Path(__file__).parent)

    for finder, module_name, is_pkg in pkgutil.walk_packages(
        path=[package_path],
        prefix=package_name + '.',
        onerror=lambda name: None,
    ):
        # Extract the leaf name (after the last dot)
        leaf = module_name.rsplit('.', 1)[-1]

        if leaf.startswith('__') or leaf == 'registry':
            continue

        if module_name not in sys.modules:
            importlib.import_module(module_name)
