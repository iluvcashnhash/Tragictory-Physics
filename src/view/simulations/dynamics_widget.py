"""
Dynamics widget module for Tragictory Physics.

This module contains the DynamicsWidget class that visualizes the
inclined plane simulation using pyqtgraph.
"""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QSlider, QLabel, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt

from ...model.dynamics import InclinedPlaneModel


# Scale factor: 1 Newton = this many plot units for arrow length
FORCE_SCALE: float = 0.015


class DynamicsWidget(QWidget):
    """Widget for visualizing a block on an inclined plane with force vectors.

    Provides interactive sliders for angle, mass, and friction coefficient.
    Renders the inclined plane, block, and force vectors using pyqtgraph.
    """

    def __init__(self) -> None:
        """Initialize the dynamics widget."""
        super().__init__()

        self._angle_deg: float = 30.0
        self._mass: float = 10.0
        self._friction_coeff: float = 0.3

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(16)

        self._setup_plot(main_layout)
        self._setup_control_panel(main_layout)

        self.update_plot()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _setup_plot(self, parent_layout: QHBoxLayout) -> None:
        """Create and configure the pyqtgraph PlotWidget."""
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1e1e1e")
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.hideAxis("left")
        self.plot_widget.setXRange(-0.2, 1.8)
        self.plot_widget.setYRange(-0.5, 1.5)

        parent_layout.addWidget(self.plot_widget, stretch=3)

    def _setup_control_panel(self, parent_layout: QHBoxLayout) -> None:
        """Create sliders and result labels for the control panel."""
        panel = QGroupBox("Параметры")
        panel.setMinimumWidth(220)
        panel.setMaximumWidth(260)

        form = QFormLayout(panel)
        form.setSpacing(12)

        # --- Angle slider (0–89°) ---
        self._angle_label = QLabel("30°")
        self._angle_slider = QSlider(Qt.Orientation.Horizontal)
        self._angle_slider.setRange(0, 89)
        self._angle_slider.setValue(30)
        self._angle_slider.valueChanged.connect(self._on_angle_changed)
        form.addRow("Угол наклона:", self._angle_label)
        form.addRow(self._angle_slider)

        # --- Mass slider (1–50 kg) ---
        self._mass_label = QLabel("10 кг")
        self._mass_slider = QSlider(Qt.Orientation.Horizontal)
        self._mass_slider.setRange(1, 50)
        self._mass_slider.setValue(10)
        self._mass_slider.valueChanged.connect(self._on_mass_changed)
        form.addRow("Масса:", self._mass_label)
        form.addRow(self._mass_slider)

        # --- Friction slider (0.0–1.0, step 0.1 → stored as 0–10) ---
        self._friction_label = QLabel("μ = 0.30")
        self._friction_slider = QSlider(Qt.Orientation.Horizontal)
        self._friction_slider.setRange(0, 10)
        self._friction_slider.setValue(3)
        self._friction_slider.valueChanged.connect(self._on_friction_changed)
        form.addRow("Коэф. трения:", self._friction_label)
        form.addRow(self._friction_slider)

        # --- Results display ---
        results_box = QGroupBox("Результаты")
        results_layout = QVBoxLayout(results_box)
        results_layout.setSpacing(6)

        self._lbl_fg   = QLabel()
        self._lbl_fp   = QLabel()
        self._lbl_fn   = QLabel()
        self._lbl_ff   = QLabel()
        self._lbl_fnet = QLabel()
        self._lbl_acc  = QLabel()

        for lbl in (self._lbl_fg, self._lbl_fp, self._lbl_fn,
                    self._lbl_ff, self._lbl_fnet, self._lbl_acc):
            lbl.setStyleSheet("color: #d4d4d4; font-size: 12px;")
            results_layout.addWidget(lbl)

        # Wrap everything in a vertical layout
        # Back button
        self._back_button = QPushButton("← Назад к теории")
        self._back_button.setMinimumHeight(36)

        outer = QVBoxLayout()
        outer.addWidget(panel)
        outer.addWidget(results_box)
        outer.addStretch()
        outer.addWidget(self._back_button)
        parent_layout.addLayout(outer, stretch=1)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_angle_changed(self, value: int) -> None:
        """Handle angle slider change."""
        self._angle_deg = float(value)
        self._angle_label.setText(f"{value}°")
        self.update_plot()

    def _on_mass_changed(self, value: int) -> None:
        """Handle mass slider change."""
        self._mass = float(value)
        self._mass_label.setText(f"{value} кг")
        self.update_plot()

    def _on_friction_changed(self, value: int) -> None:
        """Handle friction slider change."""
        self._friction_coeff = value / 10.0
        self._friction_label.setText(f"μ = {self._friction_coeff:.2f}")
        self.update_plot()

    # ------------------------------------------------------------------
    # Main drawing method
    # ------------------------------------------------------------------

    def update_plot(self) -> None:
        """Recalculate forces and redraw the scene."""
        self.plot_widget.clear()

        forces = InclinedPlaneModel.calculate_forces(
            mass=self._mass,
            angle_deg=self._angle_deg,
            friction_coeff=self._friction_coeff,
        )

        self._update_result_labels(forces)
        self._draw_inclined_plane()
        self._draw_block_and_arrows(forces)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_inclined_plane(self) -> None:
        """Draw the inclined plane as a filled polygon."""
        angle_rad = np.deg2rad(self._angle_deg)
        length = 1.5

        # Top-right corner of the slope
        top_x = length * np.cos(angle_rad)
        top_y = length * np.sin(angle_rad)

        # Filled triangle: origin, top of slope, foot of slope
        xs = np.array([0.0, top_x, top_x, 0.0])
        ys = np.array([0.0, top_y, 0.0,   0.0])

        fill = pg.PlotDataItem(
            xs, ys,
            fillLevel=None,
            pen=pg.mkPen(color="#4a90d9", width=2),
            fillBrush=pg.mkBrush("#1a3a5c"),
        )
        fill.setFillLevel(0)
        fill.setFillBrush(pg.mkBrush("#1a3a5c"))
        self.plot_widget.addItem(fill)

        # Slope surface line
        slope_line = pg.PlotDataItem(
            [0.0, top_x], [0.0, top_y],
            pen=pg.mkPen(color="#4a90d9", width=3),
        )
        self.plot_widget.addItem(slope_line)

        # Ground line
        ground = pg.PlotDataItem(
            [0.0, top_x], [0.0, 0.0],
            pen=pg.mkPen(color="#555555", width=2, style=Qt.PenStyle.DashLine),
        )
        self.plot_widget.addItem(ground)

    def _draw_block_and_arrows(self, forces: dict) -> None:
        """Draw the block as a square and force vectors as arrows."""
        angle_rad = np.deg2rad(self._angle_deg)

        # Block position: placed at 50% along the slope
        t = 0.75  # distance along slope
        block_size = 0.10

        # Center of the block (sitting on the slope surface)
        cx = t * np.cos(angle_rad) - (block_size / 2) * np.sin(angle_rad)
        cy = t * np.sin(angle_rad) + (block_size / 2) * np.cos(angle_rad)

        # Draw block as a filled rectangle rotated with the slope
        # Build corners in local frame then rotate
        half = block_size / 2
        corners_local = np.array([
            [-half, -half],
            [ half, -half],
            [ half,  half],
            [-half,  half],
            [-half, -half],
        ])
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
        corners_world = corners_local @ rot.T

        # Block center on slope surface
        bx = t * np.cos(angle_rad)
        by = t * np.sin(angle_rad) + half * np.cos(angle_rad)

        block_xs = corners_world[:, 0] + bx
        block_ys = corners_world[:, 1] + by

        block_item = pg.PlotDataItem(
            block_xs, block_ys,
            pen=pg.mkPen(color="#e8c07a", width=2),
            fillLevel=None,
            fillBrush=pg.mkBrush("#c8963a"),
        )
        block_item.setFillLevel(0)
        block_item.setFillBrush(pg.mkBrush("#c8963a80"))
        self.plot_widget.addItem(block_item)

        # Arrow origin: center of block face
        origin_x = bx
        origin_y = by

        # --- F_gravity: straight down ---
        self._add_arrow(
            origin_x, origin_y,
            dx=0.0, dy=-forces['F_gravity'] * FORCE_SCALE,
            color="#e05555",
            label="Fg",
        )

        # --- F_normal: perpendicular to slope (rotated 90° from slope dir) ---
        nx = -np.sin(angle_rad)
        ny =  np.cos(angle_rad)
        fn_len = forces['F_normal'] * FORCE_SCALE
        self._add_arrow(
            origin_x, origin_y,
            dx=nx * fn_len, dy=ny * fn_len,
            color="#55c555",
            label="Fn",
        )

        # --- F_friction: along slope upward (opposing downslope motion) ---
        ff_len = forces['F_friction_max'] * FORCE_SCALE
        fx =  np.cos(angle_rad) * ff_len   # up the slope
        fy =  np.sin(angle_rad) * ff_len
        self._add_arrow(
            origin_x, origin_y,
            dx=-fx, dy=-fy,   # friction opposes motion (up the slope)
            color="#e8c84a",
            label="Ff",
        )

    def _add_arrow(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        color: str,
        label: str,
    ) -> None:
        """Add an arrow and a small label to the plot.

        Args:
            x: Arrow tail x coordinate.
            y: Arrow tail y coordinate.
            dx: Horizontal component of the arrow vector.
            dy: Vertical component of the arrow vector.
            color: Hex color string for the arrow.
            label: Short text label shown at the arrow tip.
        """
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return

        tip_x = x + dx
        tip_y = y + dy

        # Shaft line
        line = pg.PlotDataItem(
            [x, tip_x], [y, tip_y],
            pen=pg.mkPen(color=color, width=2),
        )
        self.plot_widget.addItem(line)

        # Arrowhead at the tip, pointing in (dx, dy) direction
        angle_deg = float(np.degrees(np.arctan2(dy, dx)))
        arrow = pg.ArrowItem(
            pos=(tip_x, tip_y),
            angle=angle_deg - 180,   # ArrowItem angle is the direction of the tail
            headLen=14,
            headWidth=8,
            tailLen=None,
            pen=pg.mkPen(color),
            brush=pg.mkBrush(color),
        )
        self.plot_widget.addItem(arrow)

        # Label at tip
        text = pg.TextItem(label, color=color, anchor=(0.5, 0.5))
        offset = 0.07
        text.setPos(tip_x + offset * np.sign(dx or 1),
                    tip_y + offset * np.sign(dy or 1))
        self.plot_widget.addItem(text)

    # ------------------------------------------------------------------
    # Results labels
    # ------------------------------------------------------------------

    def get_back_button(self) -> QPushButton:
        """Return the back button widget.

        Returns:
            QPushButton: The back-to-theory button.
        """
        return self._back_button

    def _update_result_labels(self, forces: dict) -> None:
        """Update the numeric results in the right-side panel."""
        self._lbl_fg.setText(f"F_gravity  = {forces['F_gravity']:.1f} Н")
        self._lbl_fp.setText(f"F_parallel = {forces['F_parallel']:.1f} Н")
        self._lbl_fn.setText(f"F_normal   = {forces['F_normal']:.1f} Н")
        self._lbl_ff.setText(f"F_friction = {forces['F_friction_max']:.1f} Н")
        self._lbl_fnet.setText(f"F_net      = {forces['F_net']:.1f} Н")
        state = "движется" if forces['F_net'] > 0 else "покоится"
        self._lbl_acc.setText(
            f"a = {forces['acceleration']:.2f} м/с²  ({state})"
        )


from .registry import register_simulation
register_simulation("Законы Ньютона", DynamicsWidget)
