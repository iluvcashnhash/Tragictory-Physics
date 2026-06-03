"""
Simulation widget module for Tragictory Physics.

This module contains the SimulationWidget class that provides interactive
physics simulations with real-time trajectory visualization using pyqtgraph.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QSlider, QSpinBox, QComboBox, QLabel, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from typing import Tuple


class SimulationWidget(QWidget):
    """Widget for interactive physics simulations.
    
    Provides a plot widget for trajectory visualization and control panel
    with sliders and inputs for adjusting simulation parameters.
    """
    
    # Planet gravity values (m/s²)
    PLANET_GRAVITY = {
        "Земля": 9.81,
        "Луна": 1.62,
        "Марс": 3.72,
        "Юпитер": 24.79,
        "Венера": 8.87
    }
    
    def __init__(self) -> None:
        """Initialize the simulation widget with plot and controls."""
        super().__init__()
        
        # Setup main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Initialize UI components
        self._setup_plot_widget()
        self._setup_control_panel()
        
        # Setup initial plot
        self._setup_plot_appearance()
    
    def _setup_plot_widget(self) -> None:
        """Setup the pyqtgraph plot widget for trajectory visualization."""
        # Create plot widget
        self.plot_widget = pg.PlotWidget(title="Траектория движения тела")
        
        # Configure plot appearance
        self.plot_widget.setLabel('left', 'Высота', units='м', color='#d4d4d4')
        self.plot_widget.setLabel('bottom', 'Дальность', units='м', color='#d4d4d4')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setBackground('#1e1e1e')
        
        # Set axis text color
        self.plot_widget.getAxis('left').setPen('#d4d4d4')
        self.plot_widget.getAxis('bottom').setPen('#d4d4d4')
        self.plot_widget.getAxis('left').setTextPen('#d4d4d4')
        self.plot_widget.getAxis('bottom').setTextPen('#d4d4d4')
        
        # Create plot item for trajectory
        self.trajectory_plot = self.plot_widget.plot(
            pen=pg.mkPen('#ff9d00', width=3), 
            name='Траектория'
        )
        
        # Add to main layout (left side)
        self.main_layout.addWidget(self.plot_widget, stretch=3)
    
    def _setup_control_panel(self) -> None:
        """Setup the control panel with parameter inputs."""
        # Create control panel group
        control_group = QGroupBox("Параметры симуляции")
        control_layout = QVBoxLayout(control_group)
        
        # Add back button at the top
        self.back_button = QPushButton("Вернуться к теории")
        control_layout.addWidget(self.back_button)
        
        # Create form layout for controls
        self.form_layout = QFormLayout()
        
        # Velocity control (SpinBox + Slider combination)
        velocity_widget = QWidget()
        velocity_layout = QHBoxLayout(velocity_widget)
        velocity_layout.setContentsMargins(0, 0, 0, 0)
        
        self.velocity_spinbox = QSpinBox()
        self.velocity_spinbox.setRange(1, 100)
        self.velocity_spinbox.setValue(20)
        self.velocity_spinbox.setSuffix(" м/с")
        self.velocity_spinbox.setMinimumWidth(80)
        
        self.velocity_slider = QSlider(Qt.Orientation.Horizontal)
        self.velocity_slider.setRange(1, 100)
        self.velocity_slider.setValue(20)
        
        # Connect velocity controls
        self.velocity_spinbox.valueChanged.connect(self.velocity_slider.setValue)
        self.velocity_slider.valueChanged.connect(self.velocity_spinbox.setValue)
        
        velocity_layout.addWidget(self.velocity_spinbox)
        velocity_layout.addWidget(self.velocity_slider)
        
        # Angle control
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(0, 90)
        self.angle_slider.setValue(45)
        
        self.angle_label = QLabel("45°")
        self.angle_label.setMinimumWidth(40)
        
        # Connect angle slider to label
        self.angle_slider.valueChanged.connect(
            lambda value: self.angle_label.setText(f"{value}°")
        )
        
        # Angle widget with label
        angle_widget = QWidget()
        angle_layout = QHBoxLayout(angle_widget)
        angle_layout.setContentsMargins(0, 0, 0, 0)
        angle_layout.addWidget(self.angle_label)
        angle_layout.addWidget(self.angle_slider)
        
        # Planet selection
        self.planet_combo = QComboBox()
        self.planet_combo.addItems(list(self.PLANET_GRAVITY.keys()))
        self.planet_combo.setCurrentText("Земля")
        
        # Add controls to form layout
        self.form_layout.addRow("Скорость (v₀):", velocity_widget)
        self.form_layout.addRow("Угол запуска:", angle_widget)
        self.form_layout.addRow("Планета:", self.planet_combo)
        
        # Add form layout to control layout
        control_layout.addLayout(self.form_layout)
        control_layout.addStretch()
        
        # Add control panel to main layout (right side)
        self.main_layout.addWidget(control_group, stretch=1)
    
    def _setup_plot_appearance(self) -> None:
        """Setup initial plot appearance and empty trajectory."""
        # Set initial axis ranges
        self.plot_widget.setXRange(0, 100)
        self.plot_widget.setYRange(0, 50)
        
        # Add ground line with dark theme color
        ground_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('#d4d4d4', width=1, style=Qt.PenStyle.DashLine, alpha=0.5))
        self.plot_widget.addItem(ground_line)
    
    def get_velocity(self) -> int:
        """Get current velocity value.
        
        Returns:
            int: Current velocity in m/s.
        """
        return self.velocity_spinbox.value()
    
    def get_angle(self) -> int:
        """Get current angle value.
        
        Returns:
            int: Current angle in degrees.
        """
        return self.angle_slider.value()
    
    def get_gravity(self) -> float:
        """Get current gravity value based on selected planet.
        
        Returns:
            float: Current gravity in m/s².
        """
        planet = self.planet_combo.currentText()
        return self.PLANET_GRAVITY[planet]
    
    def update_plot(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Update the trajectory plot with new data.
        
        Args:
            x_data: Array of x coordinates.
            y_data: Array of y coordinates.
        """
        # Update trajectory plot
        self.trajectory_plot.setData(x_data, y_data)
        
        # Auto-scale plot to fit trajectory
        if len(x_data) > 0 and len(y_data) > 0:
            x_max = np.max(x_data) * 1.1  # Add 10% margin
            y_max = np.max(y_data) * 1.2  # Add 20% margin
            
            self.plot_widget.setXRange(0, max(x_max, 10))  # Minimum range of 10
            self.plot_widget.setYRange(0, max(y_max, 10))  # Minimum range of 10
    
    def clear_plot(self) -> None:
        """Clear the trajectory plot."""
        empty_x = np.array([0])
        empty_y = np.array([0])
        self.trajectory_plot.setData(empty_x, empty_y)
    
    def get_plot_widget(self) -> pg.PlotWidget:
        """Get the plot widget instance.
        
        Returns:
            pg.PlotWidget: The plot widget.
        """
        return self.plot_widget
    
    def get_back_button(self) -> QPushButton:
        """Get the back button widget.
        
        Returns:
            QPushButton: The back button for returning to theory view.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Баллистическое движение", SimulationWidget)
