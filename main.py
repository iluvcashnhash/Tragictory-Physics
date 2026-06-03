"""
Main entry point for Tragictory Physics application.

This module initializes the PyQt6 application, sets up the database,
and launches the main controller for the physics education software.
"""

import sys
from PyQt6.QtWidgets import QApplication

from src.model import db_setup
from src.controller.main_controller import MainController


def main() -> None:
    """Main application entry point."""
    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setApplicationName("Tragictory Physics")
    
    # Apply dark theme style sheet
    try:
        with open("assets/style.qss", "r", encoding="utf-8") as style_file:
            app.setStyleSheet(style_file.read())
    except FileNotFoundError:
        print("Style file not found, using default theme")
    except Exception as e:
        print(f"Error loading style sheet: {e}")
    
    # Initialize database
    db_setup.initialize_db()
    
    # Create and show main controller
    controller = MainController()
    controller.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()