"""
Nonlinear pendulum simulation widget for Tragictory Physics.

Upper plot: animated pendulum bob on a string.
Lower plot: kinetic and potential energy vs time.
Integration uses the exact nonlinear ODE via RK4.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


G: float = 9.81
DT: float = 0.02
TIMER_MS: int = 20
TRAIL_LEN: int = 300      # energy history points to keep


class PendulumWidget(QWidget):
    """Nonlinear pendulum with phase-space energy display.

    Top pane: animated pendulum (pivot + bob + string).
    Bottom pane: Eₖ(t) and Eₚ(t) curves with live marker.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise pendulum state and start timer."""
        super().__init__(parent)
        self._build_ui()
        self._reset()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Physics ───────────────────────────────────────────────────────────────

    def _reset(self) -> None:
        """Reinitialise state from current slider values."""
        self._L = self._sl_len.value() / 100.0          # cm → m (0.10–2.00 m)
        theta0 = math.radians(self._sl_angle.value())
        self._theta: float = theta0
        self._omega_dot: float = 0.0
        self._t: float = 0.0
        self._ek_hist: list[float] = []
        self._ep_hist: list[float] = []
        self._t_hist: list[float] = []
        m = 1.0
        self._E_total = m * G * self._L * (1.0 - math.cos(theta0))
        self._update_labels()

    def _deriv(self, theta: float, omega: float) -> tuple[float, float]:
        return omega, -(G / self._L) * math.sin(theta)

    def _rk4_step(self) -> None:
        """Advance state by DT using RK4."""
        th, om = self._theta, self._omega_dot
        k1_th, k1_om = self._deriv(th, om)
        k2_th, k2_om = self._deriv(th + 0.5*DT*k1_th, om + 0.5*DT*k1_om)
        k3_th, k3_om = self._deriv(th + 0.5*DT*k2_th, om + 0.5*DT*k2_om)
        k4_th, k4_om = self._deriv(th + DT*k3_th, om + DT*k3_om)
        self._theta += (DT/6) * (k1_th + 2*k2_th + 2*k3_th + k4_th)
        self._omega_dot += (DT/6) * (k1_om + 2*k2_om + 2*k3_om + k4_om)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Left: two stacked plots
        plot_layout = QVBoxLayout()
        plot_layout.setSpacing(4)

        # Upper: pendulum animation
        self._pw_pend = pg.PlotWidget()
        self._pw_pend.setBackground("#1e1e2e")
        self._pw_pend.setAspectLocked(True)
        self._pw_pend.setMouseEnabled(False, False)
        self._pw_pend.setXRange(-2.2, 2.2, padding=0)
        self._pw_pend.setYRange(-2.2, 0.3, padding=0)
        self._pw_pend.showGrid(x=False, y=False)
        self._pw_pend.getAxis("bottom").hide()
        self._pw_pend.getAxis("left").hide()

        # Pivot marker
        self._pw_pend.plot([0], [0], pen=None,
                           symbol="+", symbolSize=12,
                           symbolPen=pg.mkPen("#cdd6f4", width=2))
        # String line
        self._string_line = self._pw_pend.plot(
            pen=pg.mkPen("#cdd6f4", width=2))
        # Bob
        self._bob = self._pw_pend.plot(
            pen=None, symbol="o", symbolSize=18,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        # Bob trail
        self._bob_trail = self._pw_pend.plot(
            pen=pg.mkPen("#f38ba880", width=1))
        self._trail_x: list[float] = []
        self._trail_y: list[float] = []

        plot_layout.addWidget(self._pw_pend, stretch=2)

        # Lower: energy plot
        self._pw_energy = pg.PlotWidget()
        self._pw_energy.setBackground("#1e1e2e")
        self._pw_energy.setLabel("left", "E, Дж")
        self._pw_energy.setLabel("bottom", "t, с")
        self._pw_energy.showGrid(x=True, y=True, alpha=0.3)
        self._pw_energy.setYRange(-0.05, None, padding=0.1)
        self._pw_energy.addLegend()

        self._ek_curve = self._pw_energy.plot(
            pen=pg.mkPen("#a6e3a1", width=2), name="Eₖ")
        self._ep_curve = self._pw_energy.plot(
            pen=pg.mkPen("#fab387", width=2), name="Eₚ")

        plot_layout.addWidget(self._pw_energy, stretch=1)
        root.addLayout(plot_layout, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        # Length slider
        l_box = QGroupBox("Длина нити (м)")
        l_lay = QVBoxLayout(l_box)
        self._lbl_len = QLabel("L = 1.00 м")
        self._lbl_len.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_len = QSlider(Qt.Orientation.Horizontal)
        self._sl_len.setRange(10, 200)   # cm
        self._sl_len.setValue(100)
        self._sl_len.valueChanged.connect(self._on_change)
        l_lay.addWidget(self._lbl_len)
        l_lay.addWidget(self._sl_len)
        ctrl.addWidget(l_box)

        # Angle slider
        a_box = QGroupBox("Начальный угол (°)")
        a_lay = QVBoxLayout(a_box)
        self._lbl_angle = QLabel("θ₀ = 30°")
        self._lbl_angle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_angle = QSlider(Qt.Orientation.Horizontal)
        self._sl_angle.setRange(1, 179)
        self._sl_angle.setValue(30)
        self._sl_angle.valueChanged.connect(self._on_change)
        a_lay.addWidget(self._lbl_angle)
        a_lay.addWidget(self._sl_angle)
        ctrl.addWidget(a_box)

        # Readout
        info_box = QGroupBox("Параметры")
        info_lay = QVBoxLayout(info_box)
        self._lbl_period = QLabel()
        self._lbl_period.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_energy = QLabel()
        self._lbl_energy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_lay.addWidget(self._lbl_period)
        info_lay.addWidget(self._lbl_energy)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    def _update_labels(self) -> None:
        T_approx = 2 * math.pi * math.sqrt(self._L / G)
        self._lbl_len.setText(f"L = {self._L:.2f} м")
        self._lbl_angle.setText(f"θ₀ = {self._sl_angle.value()}°")
        self._lbl_period.setText(f"T ≈ {T_approx:.2f} с (малые углы)")
        self._lbl_energy.setText(f"E_total = {self._E_total:.3f} Дж")

    # ── Slots & animation ─────────────────────────────────────────────────────

    def _on_change(self) -> None:
        self._reset()

    def _step(self) -> None:
        self._rk4_step()
        self._t += DT

        L = self._L
        bx = L * math.sin(self._theta)
        by = -L * math.cos(self._theta)

        # Update pendulum
        self._string_line.setData([0.0, bx], [0.0, by])
        self._bob.setData([bx], [by])
        self._trail_x.append(bx)
        self._trail_y.append(by)
        if len(self._trail_x) > TRAIL_LEN:
            self._trail_x.pop(0)
            self._trail_y.pop(0)
        self._bob_trail.setData(self._trail_x, self._trail_y)

        # Energy
        m = 1.0
        ek = 0.5 * m * (L * self._omega_dot) ** 2
        ep = m * G * L * (1.0 - math.cos(self._theta))
        self._ek_hist.append(ek)
        self._ep_hist.append(ep)
        self._t_hist.append(self._t)
        if len(self._t_hist) > TRAIL_LEN * 5:
            self._ek_hist.pop(0)
            self._ep_hist.pop(0)
            self._t_hist.pop(0)
        self._ek_curve.setData(self._t_hist, self._ek_hist)
        self._ep_curve.setData(self._t_hist, self._ep_hist)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:  # type: ignore[override]
        self._timer.start()
        super().showEvent(event)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._timer.stop()
        super().closeEvent(event)

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Математический и пружинный маятники", PendulumWidget)
