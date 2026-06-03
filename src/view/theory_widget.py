"""
Theory widget module for Tragictory Physics.

This module contains the TheoryWidget class that displays theory content,
formulas, and provides access to simulations for selected topics.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser, 
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
)
from PyQt6.QtGui import QFont
from typing import List, Dict


class TheoryWidget(QWidget):
    """Widget for displaying theory content and formulas.
    
    Provides a structured view for educational content including topic title,
    theory text in HTML format, formulas table, and simulation launch button.
    """
    
    def __init__(self) -> None:
        """Initialize the theory widget with UI components."""
        super().__init__()
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Initialize UI components
        self._setup_title_label()
        self._setup_theory_browser()
        self._setup_formulas_table()
        self._setup_simulation_button()
    
    def _setup_title_label(self) -> None:
        """Setup the topic title label with large bold font."""
        self.title_label = QLabel()
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)
    
    def _setup_theory_browser(self) -> None:
        """Setup the text browser for HTML theory content."""
        self.theory_browser = QTextBrowser()
        self.theory_browser.setOpenExternalLinks(False)
        self.theory_browser.setMinimumHeight(300)
        self.layout.addWidget(self.theory_browser)
    
    def _setup_formulas_table(self) -> None:
        """Setup the table widget for displaying formulas."""
        self.formulas_table = QTableWidget()
        self.formulas_table.setColumnCount(2)
        self.formulas_table.setHorizontalHeaderLabels(["Формула", "Описание"])
        
        # Enable word wrap for cells
        self.formulas_table.setWordWrap(True)
        
        # Configure column resize modes
        header = self.formulas_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Formula column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description column
        
        # Configure automatic row height
        self.formulas_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self.formulas_table.setAlternatingRowColors(True)
        self.formulas_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.layout.addWidget(self.formulas_table)
    
    def _setup_simulation_button(self) -> None:
        """Setup the simulation launch button (hidden by default)."""
        self.simulation_button = QPushButton("Запустить симуляцию")
        self.simulation_button.hide()  # Hidden initially
        self.layout.addWidget(self.simulation_button)
    
    def set_title(self, text: str) -> None:
        """Set the topic title.
        
        Args:
            text: The title text to display.
        """
        self.title_label.setText(text)
    
    def set_theory(self, html: str) -> None:
        """Set the theory content in HTML format.
        
        Args:
            html: The HTML content to display in the theory browser.
        """
        self.theory_browser.setHtml(html)
    
    def set_formulas(self, data_list: List[Dict]) -> None:
        """Set the formulas data in the table.
        
        Args:
            data_list: List of dictionaries with 'formula_latex' and 'description' keys.
        """
        if not data_list:
            self.formulas_table.setRowCount(0)
            return
        
        self.formulas_table.setRowCount(len(data_list))
        
        for row, formula_data in enumerate(data_list):
            # Formula column
            formula_item = QTableWidgetItem(formula_data.get('formula_latex', ''))
            self.formulas_table.setItem(row, 0, formula_item)
            
            # Description column
            description_item = QTableWidgetItem(formula_data.get('description', ''))
            self.formulas_table.setItem(row, 1, description_item)
    
    def show_simulation_button(self) -> None:
        """Show the simulation launch button."""
        self.simulation_button.show()
    
    def hide_simulation_button(self) -> None:
        """Hide the simulation launch button."""
        self.simulation_button.hide()
    
    def get_simulation_button(self) -> QPushButton:
        """Get the simulation button widget.
        
        Returns:
            QPushButton: The simulation launch button.
        """
        return self.simulation_button
