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
from ..view.welcome_widget import WelcomeWidget
from ..view.quiz_widget import QuizWidget
from ..view.simulations.registry import get_simulation_widget
from ..view.simulations import simulation_widget as _sim_reg  # noqa: F401 — triggers registration
from ..view.simulations import dynamics_widget as _dyn_reg    # noqa: F401 — triggers registration
from ..view.simulations import mkt_widget as _mkt_reg         # noqa: F401 — triggers registration
from ..view.simulations import optics_widget as _opt_reg      # noqa: F401 — triggers registration
from ..view.simulations import spring_widget as _spr_reg      # noqa: F401 — triggers registration
from ..view.simulations import pendulum_widget as _pen_reg    # noqa: F401 — triggers registration
from ..view.simulations import orbit_widget as _orb_reg       # noqa: F401 — triggers registration
from ..view.simulations import wave_widget as _wav_reg        # noqa: F401 — triggers registration


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
        
        # Track currently selected topic title for simulation routing
        self._current_topic_title: str = ""
        self._current_questions: list = []

        # Initialize persistent widgets
        self.welcome_widget = WelcomeWidget()
        self.theory_widget = TheoryWidget()
        self.quiz_widget = QuizWidget()

        # simulation_stack is managed dynamically; keep a reference
        self._sim_stack = self.main_window.get_simulation_stack()

        # Add widgets to outer content_stack in correct order
        stack = self.main_window.get_content_stack()
        stack.addWidget(self.welcome_widget)    # Index 0: Welcome
        stack.addWidget(self.theory_widget)     # Index 1: Theory
        stack.addWidget(self._sim_stack)        # Index 2: Simulations
        stack.addWidget(self.quiz_widget)       # Index 3: Quiz

        # Set welcome widget as default
        stack.setCurrentIndex(0)
        
        # Setup UI connections
        self._setup_connections()
        
        # Load initial data
        self.load_navigation_tree()
    
    def _setup_connections(self) -> None:
        """Setup signal-slot connections for UI interactions."""
        navigation_tree = self.main_window.get_navigation_tree()
        navigation_tree.itemClicked.connect(self._on_tree_item_clicked)
        
        # Connect simulation button
        self.theory_widget.get_simulation_button().clicked.connect(
            self._on_simulation_button_clicked
        )

        # Connect back button for quiz
        self.quiz_widget.get_back_button().clicked.connect(self._on_back_button_clicked)

        # Connect quiz button in theory widget
        self.theory_widget.get_quiz_button().clicked.connect(self._on_quiz_button_clicked)

        # Connect search input to navigation filter
        self.main_window.search_input.textChanged.connect(self._filter_navigation_tree)
    
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
        self._current_topic_title = topic_title

        # Update theory widget with data
        self.theory_widget.set_title(topic_title)
        
        # Set theory content
        theory_html = theory_data.get('content_html', '<p>Содержимое теории отсутствует.</p>')
        self.theory_widget.set_theory(theory_html)
        
        # Set formulas
        self.theory_widget.set_formulas(formulas_data)
        
        # Switch to theory view (index 1)
        self.main_window.get_content_stack().setCurrentIndex(1)
        
        # Show/hide simulation button based on topic data
        if self._topic_has_simulation(topic_id):
            self.theory_widget.show_simulation_button()
        else:
            self.theory_widget.hide_simulation_button()

        # Load questions and show/hide quiz button
        self._current_questions = self.db_manager.get_questions_for_topic(topic_id)
        if self._current_questions:
            self.quiz_widget.load_question(self._current_questions[0])
            self.theory_widget.show_quiz_button()
        else:
            self._current_questions = []
            self.theory_widget.hide_quiz_button()
    
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
        """Handle simulation button click — create widget via factory and display it."""
        widget = get_simulation_widget(self._current_topic_title)
        if widget is None:
            return

        # Clear any previously loaded simulation widget from the stack
        while self._sim_stack.count() > 0:
            old = self._sim_stack.widget(0)
            self._sim_stack.removeWidget(old)
            old.deleteLater()

        # Add fresh widget and show it
        self._sim_stack.addWidget(widget)
        self._sim_stack.setCurrentIndex(0)

        # Wire up back button on the new widget
        if hasattr(widget, 'get_back_button'):
            widget.get_back_button().clicked.connect(self._on_back_button_clicked)

        # Wire kinematics-specific controls if this is the ballistics widget
        if hasattr(widget, 'velocity_spinbox'):
            widget.velocity_spinbox.valueChanged.connect(
                lambda: self._update_ballistics_simulation(widget)
            )
            widget.velocity_slider.valueChanged.connect(
                lambda: self._update_ballistics_simulation(widget)
            )
            widget.angle_slider.valueChanged.connect(
                lambda: self._update_ballistics_simulation(widget)
            )
            widget.planet_combo.currentTextChanged.connect(
                lambda: self._update_ballistics_simulation(widget)
            )
            self._update_ballistics_simulation(widget)

        # Show the simulation container (index 2 of outer stack)
        self.main_window.get_content_stack().setCurrentIndex(2)
    
    def show(self) -> None:
        """Show the main window."""
        self.main_window.show()
    
    def get_main_window(self) -> MainWindow:
        """Get the main window instance.
        
        Returns:
            MainWindow: The main window instance.
        """
        return self.main_window
    
    def _update_ballistics_simulation(self, widget: 'QWidget') -> None:
        """Update the ballistics simulation plot with current widget parameters.

        Args:
            widget: The SimulationWidget instance to read values from and update.
        """
        try:
            velocity = widget.get_velocity()
            angle = widget.get_angle()
            gravity = widget.get_gravity()
            x_coords, y_coords = ProjectileModel.calculate_trajectory(
                velocity, angle, gravity
            )
            widget.update_plot(x_coords, y_coords)
        except Exception as e:
            print(f"Error updating simulation: {e}")
    
    def _filter_navigation_tree(self, text: str) -> None:
        """Filter navigation tree items based on search text.

        Shows only topic items whose text contains *text* (case-insensitive).
        A grade (parent) node is hidden when none of its topics match.

        Args:
            text: The search string typed by the user.
        """
        query = text.strip().lower()
        tree = self.main_window.get_navigation_tree()

        for grade_idx in range(tree.topLevelItemCount()):
            grade_item = tree.topLevelItem(grade_idx)
            any_visible = False

            for topic_idx in range(grade_item.childCount()):
                topic_item = grade_item.child(topic_idx)
                match = query == "" or query in topic_item.text(0).lower()
                topic_item.setHidden(not match)
                if match:
                    any_visible = True

            grade_item.setHidden(not any_visible)

    def _on_quiz_button_clicked(self) -> None:
        """Handle quiz button click — switch to quiz view (index 3)."""
        self.main_window.get_content_stack().setCurrentIndex(3)

    def _on_back_button_clicked(self) -> None:
        """Handle back button click event to return to theory view."""
        self.main_window.get_content_stack().setCurrentIndex(1)
