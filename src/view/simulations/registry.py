"""
Simulation registry for Tragictory Physics.

Provides a factory pattern for dynamically creating simulation widgets
by topic name, allowing new simulations to be added without modifying
the main controller.
"""

from typing import Dict, Optional, Type
from PyQt6.QtWidgets import QWidget


SIMULATION_REGISTRY: Dict[str, Type[QWidget]] = {}


def register_simulation(topic_name: str, widget_class: Type[QWidget]) -> None:
    """Register a simulation widget class for a given topic name.

    Args:
        topic_name: The exact topic title string used in the database.
        widget_class: The QWidget subclass to instantiate for this topic.
    """
    SIMULATION_REGISTRY[topic_name] = widget_class


def get_simulation_widget(topic_name: str) -> Optional[QWidget]:
    """Create and return a simulation widget instance for the given topic.

    Args:
        topic_name: The exact topic title string used in the database.

    Returns:
        Optional[QWidget]: A fresh widget instance, or None if not registered.
    """
    widget_class = SIMULATION_REGISTRY.get(topic_name)
    if widget_class:
        return widget_class()
    return None
