"""
Welcome widget module for Tragictory Physics.

This module contains the WelcomeWidget class that displays a welcome screen
with illustration and instructions when the application starts.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont


class WelcomeWidget(QWidget):
    """Widget for displaying welcome screen with illustration and instructions.
    
    Shows a welcome message and illustration when the application starts,
    before any topic is selected from the navigation tree.
    """
    
    def __init__(self) -> None:
        """Initialize the welcome widget with centered layout."""
        super().__init__()
        
        # Create main layout with center alignment
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(20)
        
        # Initialize UI components
        self._setup_welcome_image()
        self._setup_welcome_text()
    
    def _setup_welcome_image(self) -> None:
        """Setup the welcome illustration image."""
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load and scale image
        try:
            pixmap = QPixmap("assets/welcome_bg.png")
            if not pixmap.isNull():
                # Scale to 400px width while keeping aspect ratio
                scaled_pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
            else:
                # If image not found, create a placeholder
                self.image_label.setText("📚")
                self.image_label.setStyleSheet("font-size: 120px; color: #d4d4d4;")
        except Exception:
            # If image loading fails, create a placeholder
            self.image_label.setText("📚")
            self.image_label.setStyleSheet("font-size: 120px; color: #d4d4d4;")
        
        self.layout.addWidget(self.image_label)
    
    def _setup_welcome_text(self) -> None:
        """Setup the welcome message text."""
        self.welcome_label = QLabel(
            "Добро пожаловать в Tragictory Physics\n"
            "Выберите класс и тему в меню слева"
        )
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            QLabel {
                color: #d4d4d4;
                font-size: 16px;
                font-weight: 500;
                line-height: 1.5;
            }
        """)
        self.welcome_label.setWordWrap(True)
        
        self.layout.addWidget(self.welcome_label)
