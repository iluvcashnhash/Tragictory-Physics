"""
Main window module for Tragictory Physics.

This module contains the MainWindow class that provides the main UI layout
with navigation tree and content area using PyQt6.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QWidget, QVBoxLayout, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    """Main application window for Tragictory Physics.
    
    Provides a split interface with navigation tree on the left and
    content area on the right using QStackedWidget for different views.
    """
    
    def __init__(self) -> None:
        """Initialize the main window with UI components."""
        super().__init__()
        
        # Window properties
        self.setWindowTitle("Tragictory Physics")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for navigation and content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Initialize UI components
        self._setup_navigation_panel()
        self._setup_content_panel()
        
        # Set initial splitter sizes (30% navigation, 70% content)
        self.splitter.setSizes([300, 700])
    
    def _setup_navigation_panel(self) -> None:
        """Setup the left navigation panel with search input and tree widget."""
        # Container widget so search + tree share one splitter slot
        nav_container = QWidget()
        nav_container.setMaximumWidth(400)
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по темам...")
        self.search_input.setClearButtonEnabled(True)
        nav_layout.addWidget(self.search_input)

        # Navigation tree
        self.navigation_tree = QTreeWidget()
        self.navigation_tree.setHeaderLabel("Навигация")
        nav_layout.addWidget(self.navigation_tree)

        # Add sample grade items (will be populated from database later)
        grades = ["7 класс", "8 класс", "9 класс", "10 класс", "11 класс"]

        for grade_text in grades:
            grade_item = QTreeWidgetItem(self.navigation_tree)
            grade_item.setText(0, grade_text)
            grade_item.setData(0, Qt.ItemDataRole.UserRole, None)

            sample_topics = ["Тема 1", "Тема 2", "Тема 3"]
            for topic_text in sample_topics:
                topic_item = QTreeWidgetItem(grade_item)
                topic_item.setText(0, topic_text)
                topic_item.setData(0, Qt.ItemDataRole.UserRole, None)

        # Expand all grade items by default
        self.navigation_tree.expandAll()

        # Add container to splitter (left side)
        self.splitter.addWidget(nav_container)
    
    def _setup_content_panel(self) -> None:
        """Setup the right content panel with stacked widget."""
        # Outer stack: welcome (0), theory (1), simulation (2)
        self.content_stack = QStackedWidget()
        
        # Inner stack for simulations (index 2 of content_stack)
        self.simulation_stack = QStackedWidget()
        
        # Add content stack to splitter (right side)
        self.splitter.addWidget(self.content_stack)
    
    def get_navigation_tree(self) -> QTreeWidget:
        """Get the navigation tree widget.
        
        Returns:
            QTreeWidget: The navigation tree widget.
        """
        return self.navigation_tree
    
    def get_content_stack(self) -> QStackedWidget:
        """Get the content stacked widget.
        
        Returns:
            QStackedWidget: The content stacked widget.
        """
        return self.content_stack

    def get_simulation_stack(self) -> QStackedWidget:
        """Get the simulation stacked widget.

        Returns:
            QStackedWidget: The inner stack that holds all simulation widgets.
        """
        return self.simulation_stack
