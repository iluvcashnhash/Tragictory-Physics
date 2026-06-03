"""
Main controller module for Tragictory Physics.

This module contains the MainController class that coordinates between
the database manager and the main window, handling navigation and content display.
"""

from typing import Optional
from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtCore import Qt

from ..model.db_manager import DatabaseManager
from ..model.kinematics import ProjectileModel
from ..view.main_window import MainWindow
from ..view.theory_widget import TheoryWidget
from ..view.simulation_widget import SimulationWidget


class MainController:
    """Main controller for the physics education application.
    
    Coordinates between the database model and UI views, handling navigation
    tree population and topic selection events.
    """
    
    def __init__(self) -> None:
        """Initialize the controller with database manager and main window."""
        # Initialize components
        self.db_manager = DatabaseManager()
        self.main_window = MainWindow()
        
        # Create and setup theory widget
        self.theory_widget = TheoryWidget()
        self.main_window.get_content_stack().addWidget(self.theory_widget)
        
        # Create and setup simulation widget
        self.simulation_widget = SimulationWidget()
        self.main_window.get_content_stack().addWidget(self.simulation_widget)
        
        # Set welcome widget as default (index 0)
        self.main_window.get_content_stack().setCurrentIndex(0)
        
        # Setup UI connections
        self._setup_connections()
        
        # Load initial data
        self.load_navigation_tree()
    
    def _setup_connections(self) -> None:
        """Setup signal-slot connections for UI interactions."""
        navigation_tree = self.main_window.get_navigation_tree()
        navigation_tree.itemClicked.connect(self._on_tree_item_clicked)
        
        # Connect simulation button if needed
        self.theory_widget.get_simulation_button().clicked.connect(
            self._on_simulation_button_clicked
        )
        
        # Connect simulation widget signals to update simulation
        self.simulation_widget.velocity_spinbox.valueChanged.connect(self.update_simulation)
        self.simulation_widget.velocity_slider.valueChanged.connect(self.update_simulation)
        self.simulation_widget.angle_slider.valueChanged.connect(self.update_simulation)
        self.simulation_widget.planet_combo.currentTextChanged.connect(self.update_simulation)
        
        # Connect back button to return to theory view
        self.simulation_widget.get_back_button().clicked.connect(self._on_back_button_clicked)
    
    def load_navigation_tree(self) -> None:
        """Load navigation tree with grades and topics from database."""
        navigation_tree = self.main_window.get_navigation_tree()
        navigation_tree.clear()
        
        # Get grades from database
        grades = self.db_manager.get_grades()
        
        for grade in grades:
            # Create grade item
            grade_item = QTreeWidgetItem(navigation_tree)
            grade_item.setText(0, f"{grade['number']} класс")
            grade_item.setData(0, Qt.ItemDataRole.UserRole, grade['id'])
            # Make grade items non-selectable but keep them expandable
            grade_item.setFlags(grade_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            
            # Get topics for this grade
            topics = self.db_manager.get_topics_by_grade(grade['id'])
            
            for topic in topics:
                # Create topic item
                topic_item = QTreeWidgetItem(grade_item)
                topic_item.setText(0, topic['title'])
                topic_item.setData(0, Qt.ItemDataRole.UserRole, topic['id'])
                
                # Store simulation availability flag
                topic_item.setData(1, Qt.ItemDataRole.UserRole, topic['is_simulation_available'])
        
        # Expand all grade items
        navigation_tree.expandAll()
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle tree item click events.
        
        Args:
            item: The clicked tree item.
            column: The column that was clicked.
        """
        # Check if this is a topic item (has a parent)
        if item.parent() is not None:
            topic_id = item.data(0, Qt.ItemDataRole.UserRole)
            if topic_id is not None:
                self.on_topic_selected(topic_id)
    
    def on_topic_selected(self, topic_id: int) -> None:
        """Handle topic selection by loading and displaying theory content.
        
        Args:
            topic_id: The ID of the selected topic.
        """
        # Get theory data from database
        theory_data = self.db_manager.get_theory_for_topic(topic_id)
        formulas_data = self.db_manager.get_formulas_for_topic(topic_id)
        
        # Get topic title from tree (or could fetch from database)
        topic_title = self._get_topic_title_by_id(topic_id)
        
        # Update theory widget with data
        self.theory_widget.set_title(topic_title)
        
        # Set theory content
        theory_html = theory_data.get('content_html', '<p>Содержимое теории отсутствует.</p>')
        self.theory_widget.set_theory(theory_html)
        
        # Set formulas
        self.theory_widget.set_formulas(formulas_data)
        
        # Switch to theory view (index 1)
        content_stack = self.main_window.get_content_stack()
        content_stack.setCurrentIndex(1)
        
        # Show/hide simulation button based on topic data
        if self._topic_has_simulation(topic_id):
            self.theory_widget.show_simulation_button()
        else:
            self.theory_widget.hide_simulation_button()
    
    def _get_topic_title_by_id(self, topic_id: int) -> str:
        """Get topic title by ID from navigation tree.
        
        Args:
            topic_id: The ID of the topic.
            
        Returns:
            str: The topic title, or empty string if not found.
        """
        navigation_tree = self.main_window.get_navigation_tree()
        
        # Iterate through all items to find the topic
        iterator = navigation_tree.topLevelItemCount()
        for grade_idx in range(iterator):
            grade_item = navigation_tree.topLevelItem(grade_idx)
            
            for topic_idx in range(grade_item.childCount()):
                topic_item = grade_item.child(topic_idx)
                item_topic_id = topic_item.data(0, Qt.ItemDataRole.UserRole)
                
                if item_topic_id == topic_id:
                    return topic_item.text(0)
        
        return "Неизвестная тема"
    
    def _topic_has_simulation(self, topic_id: int) -> bool:
        """Check if topic has available simulation.
        
        Args:
            topic_id: The ID of the topic.
            
        Returns:
            bool: True if simulation is available, False otherwise.
        """
        navigation_tree = self.main_window.get_navigation_tree()
        
        # Iterate through all items to find the topic
        for grade_idx in range(navigation_tree.topLevelItemCount()):
            grade_item = navigation_tree.topLevelItem(grade_idx)
            
            for topic_idx in range(grade_item.childCount()):
                topic_item = grade_item.child(topic_idx)
                item_topic_id = topic_item.data(0, Qt.ItemDataRole.UserRole)
                
                if item_topic_id == topic_id:
                    return bool(topic_item.data(1, Qt.ItemDataRole.UserRole))
        
        return False
    
    def _on_simulation_button_clicked(self) -> None:
        """Handle simulation button click event."""
        # Switch to simulation view (index 2)
        content_stack = self.main_window.get_content_stack()
        content_stack.setCurrentIndex(2)
        
        # Update simulation with current parameters
        self.update_simulation()
    
    def show(self) -> None:
        """Show the main window."""
        self.main_window.show()
    
    def get_main_window(self) -> MainWindow:
        """Get the main window instance.
        
        Returns:
            MainWindow: The main window instance.
        """
        return self.main_window
    
    def update_simulation(self) -> None:
        """Update the simulation plot with current parameters."""
        try:
            # Get current values from simulation widget
            velocity = self.simulation_widget.get_velocity()
            angle = self.simulation_widget.get_angle()
            gravity = self.simulation_widget.get_gravity()
            
            # Calculate trajectory
            x_coords, y_coords = ProjectileModel.calculate_trajectory(
                velocity, angle, gravity
            )
            
            # Update plot
            self.simulation_widget.update_plot(x_coords, y_coords)
            
        except Exception as e:
            print(f"Error updating simulation: {e}")
    
    def _on_back_button_clicked(self) -> None:
        """Handle back button click event to return to theory view."""
        content_stack = self.main_window.get_content_stack()
        content_stack.setCurrentIndex(1)
