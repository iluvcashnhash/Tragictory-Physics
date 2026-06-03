"""
MKT (Molecular Kinetic Theory) simulation widget for Tragictory Physics.

Simulates ideal gas molecules as elastic point particles inside a resizable
box, with temperature controlling RMS speed and a computed pressure readout.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


# ── Constants ──────────────────────────────────────────────────────────────────
N_MOLECULES: int = 100
T_MIN: int = 100        # Kelvin
T_MAX: int = 1000       # Kelvin
T_DEFAULT: int = 300    # Kelvin
V_MIN: int = 20         # box half-side in plot units
V_MAX: int = 90         # box half-side in plot units
V_DEFAULT: int = 60     # box half-side in plot units
TIMER_INTERVAL_MS: int = 25
# Base RMS speed (plot units/step) at 300 K
BASE_SPEED: float = 0.8


class MKTWidget(QWidget):
    """Interactive ideal-gas simulation using elastic point-particle collisions.

    Displays N_MOLECULES dots bouncing inside an adjustable square box.
    Speed magnitudes scale as √T; pressure is estimated as P ~ N·T / V².
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the widget, particles, and animation timer."""
        super().__init__(parent)
        self._temperature: float = float(T_DEFAULT)
        self._box: float = float(V_DEFAULT)

        self._init_particles()
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Particle initialisation ────────────────────────────────────────────────

    def _init_particles(self) -> None:
        """Randomly place N_MOLECULES particles with speed ∝ √T."""
        rng = np.random.default_rng(42)
        b = self._box * 0.9
        self._pos = rng.uniform(-b, b, (N_MOLECULES, 2))
        angles = rng.uniform(0, 2 * math.pi, N_MOLECULES)
        speed = self._rms_speed()
        self._vel = np.column_stack([
            speed * np.cos(angles),
            speed * np.sin(angles),
        ])

    def _rms_speed(self) -> float:
        """Return the per-particle speed (plot units/step) for current T."""
        return BASE_SPEED * math.sqrt(self._temperature / T_DEFAULT)

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build the two-pane layout: plot on the left, controls on the right."""
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # ── Plot pane ──────────────────────────────────────────────────────────
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("#1e1e2e")
        self._plot_widget.setAspectLocked(True)
        self._plot_widget.setMouseEnabled(False, False)
        self._plot_widget.showGrid(x=False, y=False)
        self._plot_widget.getAxis("bottom").hide()
        self._plot_widget.getAxis("left").hide()

        ax = self._plot_widget.getPlotItem()
        ax.setXRange(-V_MAX - 5, V_MAX + 5, padding=0)
        ax.setYRange(-V_MAX - 5, V_MAX + 5, padding=0)

        # Box outline
        self._box_rect = pg.PlotDataItem(pen=pg.mkPen("#89b4fa", width=2))
        self._plot_widget.addItem(self._box_rect)
        self._update_box_rect()

        # Molecule scatter
        self._scatter = pg.ScatterPlotItem(
            size=5,
            pen=pg.mkPen(None),
            brush=pg.mkBrush("#a6e3a1"),
        )
        self._plot_widget.addItem(self._scatter)
        self._scatter.setData(
            x=self._pos[:, 0].tolist(),
            y=self._pos[:, 1].tolist(),
        )

        root.addWidget(self._plot_widget, stretch=3)

        # ── Control pane ───────────────────────────────────────────────────────
        ctrl = QVBoxLayout()
        ctrl.setSpacing(16)

        # Back button
        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        # Temperature slider
        t_box = QGroupBox("Температура")
        t_layout = QVBoxLayout(t_box)
        self._lbl_temp = QLabel(f"T = {T_DEFAULT} K")
        self._lbl_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_temp = QSlider(Qt.Orientation.Horizontal)
        self._sl_temp.setRange(T_MIN, T_MAX)
        self._sl_temp.setValue(T_DEFAULT)
        self._sl_temp.valueChanged.connect(self._on_temp_changed)
        t_layout.addWidget(self._lbl_temp)
        t_layout.addWidget(self._sl_temp)
        ctrl.addWidget(t_box)

        # Volume slider
        v_box = QGroupBox("Объём сосуда")
        v_layout = QVBoxLayout(v_box)
        self._lbl_vol = QLabel(f"V ~ {V_DEFAULT}²")
        self._lbl_vol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_vol = QSlider(Qt.Orientation.Horizontal)
        self._sl_vol.setRange(V_MIN, V_MAX)
        self._sl_vol.setValue(V_DEFAULT)
        self._sl_vol.valueChanged.connect(self._on_vol_changed)
        v_layout.addWidget(self._lbl_vol)
        v_layout.addWidget(self._sl_vol)
        ctrl.addWidget(v_box)

        # Pressure readout
        p_box = QGroupBox("Давление")
        p_layout = QVBoxLayout(p_box)
        self._lbl_pressure = QLabel()
        self._lbl_pressure.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_pressure.setStyleSheet("font-size: 16px; font-weight: bold;")
        p_layout.addWidget(self._lbl_pressure)
        ctrl.addWidget(p_box)

        # Formula reminder
        formula_lbl = QLabel("P ~ N·T / V²")
        formula_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formula_lbl.setStyleSheet("color: #888; font-style: italic;")
        ctrl.addWidget(formula_lbl)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

        self._update_pressure_label()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _update_box_rect(self) -> None:
        """Redraw the square vessel boundary."""
        b = self._box
        xs = [-b, b, b, -b, -b]
        ys = [-b, -b, b, b, -b]
        self._box_rect.setData(x=xs, y=ys)

    def _update_pressure_label(self) -> None:
        """Recompute and display P ~ N·T / V²."""
        p = N_MOLECULES * self._temperature / (self._box ** 2)
        self._lbl_pressure.setText(f"P ≈ {p:.1f} у.е.")

    # ── Slot handlers ──────────────────────────────────────────────────────────

    def _on_temp_changed(self, value: int) -> None:
        """Scale all velocity magnitudes to match new temperature."""
        old_speed = self._rms_speed()
        self._temperature = float(value)
        new_speed = self._rms_speed()
        if old_speed > 0:
            self._vel *= new_speed / old_speed
        self._lbl_temp.setText(f"T = {value} K")
        self._update_pressure_label()

    def _on_vol_changed(self, value: int) -> None:
        """Resize the box; clamp any particles that are now outside."""
        self._box = float(value)
        self._lbl_vol.setText(f"V ~ {value}²")
        # Clamp positions to new box and invert velocity if needed
        b = self._box
        for i in range(N_MOLECULES):
            if self._pos[i, 0] > b:
                self._pos[i, 0] = b
                self._vel[i, 0] = -abs(self._vel[i, 0])
            elif self._pos[i, 0] < -b:
                self._pos[i, 0] = -b
                self._vel[i, 0] = abs(self._vel[i, 0])
            if self._pos[i, 1] > b:
                self._pos[i, 1] = b
                self._vel[i, 1] = -abs(self._vel[i, 1])
            elif self._pos[i, 1] < -b:
                self._pos[i, 1] = -b
                self._vel[i, 1] = abs(self._vel[i, 1])
        self._update_box_rect()
        self._plot_widget.getPlotItem().setXRange(-V_MAX - 5, V_MAX + 5, padding=0)
        self._plot_widget.getPlotItem().setYRange(-V_MAX - 5, V_MAX + 5, padding=0)
        self._update_pressure_label()

    # ── Animation step ─────────────────────────────────────────────────────────

    def _step(self) -> None:
        """Advance particle positions by one time step, handle wall collisions."""
        self._pos += self._vel
        b = self._box

        # Elastic wall collisions: reflect velocity component and clamp position
        hit_right = self._pos[:, 0] > b
        hit_left = self._pos[:, 0] < -b
        hit_top = self._pos[:, 1] > b
        hit_bottom = self._pos[:, 1] < -b

        self._vel[hit_right, 0] = -np.abs(self._vel[hit_right, 0])
        self._vel[hit_left, 0] = np.abs(self._vel[hit_left, 0])
        self._vel[hit_top, 1] = -np.abs(self._vel[hit_top, 1])
        self._vel[hit_bottom, 1] = np.abs(self._vel[hit_bottom, 1])

        np.clip(self._pos[:, 0], -b, b, out=self._pos[:, 0])
        np.clip(self._pos[:, 1], -b, b, out=self._pos[:, 1])

        self._scatter.setData(
            x=self._pos[:, 0].tolist(),
            y=self._pos[:, 1].tolist(),
        )

    # ── Public accessors ───────────────────────────────────────────────────────

    def get_back_button(self) -> QPushButton:
        """Return the back button for external signal connection.

        Returns:
            QPushButton: The back navigation button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Идеальный газ и основное уравнение МКТ", MKTWidget)
