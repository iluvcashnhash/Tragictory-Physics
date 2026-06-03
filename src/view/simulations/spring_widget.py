"""
Spring (damped harmonic oscillator) simulation widget for Tragictory Physics.

Plots x(t) = A * exp(-β*t) * cos(ω*t) in real time; the curve rebuilds
immediately on any slider change.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


T_WINDOW: float = 20.0      # seconds of history shown
DT: float = 0.02            # simulation time step (s)
TIMER_MS: int = 20
A0: float = 1.0             # initial amplitude (plot units)


class SpringWidget(QWidget):
    """Damped harmonic oscillator: x(t) = A·exp(-β·t)·cos(ω·t).

    Sliders control mass m, stiffness k, and damping β.
    The curve is redrawn from t=0 each time a slider moves.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise oscillator state and start animation timer."""
        super().__init__(parent)
        self._t: float = 0.0
        self._build_ui()
        self._rebuild_curve()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Physics helpers ────────────────────────────────────────────────────────

    def _params(self) -> tuple[float, float, float]:
        """Return (m, k, β) from current slider values."""
        m = self._sl_mass.value() / 10.0        # 0.1 – 5.0 kg
        k = self._sl_stiff.value() / 10.0       # 0.1 – 20.0 N/m
        beta = self._sl_damp.value() / 100.0    # 0.00 – 2.00 s⁻¹
        return m, k, beta

    def _omega(self, m: float, k: float, beta: float) -> float:
        """Return angular frequency ω = sqrt(k/m - β²); 0 if overdamped."""
        discriminant = k / m - beta ** 2
        return math.sqrt(max(discriminant, 0.0))

    def _x(self, t: float) -> float:
        """Return displacement at time t."""
        m, k, beta = self._params()
        omega = self._omega(m, k, beta)
        return A0 * math.exp(-beta * t) * math.cos(omega * t)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Plot
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setLabel("left", "Смещение x, м")
        self._pw.setLabel("bottom", "Время t, с")
        self._pw.setYRange(-1.2, 1.2, padding=0)
        self._pw.setXRange(0, T_WINDOW, padding=0)
        self._pw.showGrid(x=True, y=True, alpha=0.3)
        self._pw.addItem(pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen("#585b70", width=1)))

        self._curve = self._pw.plot(pen=pg.mkPen("#a6e3a1", width=2))
        self._marker = self._pw.plot(
            pen=None,
            symbol="o", symbolSize=10,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None),
        )
        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        def _slider_group(title: str, lo: int, hi: int, val: int,
                          fmt_fn, slot) -> tuple[QGroupBox, QSlider, QLabel]:
            box = QGroupBox(title)
            lay = QVBoxLayout(box)
            lbl = QLabel(fmt_fn(val))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo, hi)
            sl.setValue(val)
            sl.valueChanged.connect(slot)
            lay.addWidget(lbl)
            lay.addWidget(sl)
            return box, sl, lbl

        self._box_mass, self._sl_mass, self._lbl_mass = _slider_group(
            "Масса m (кг)", 1, 50, 10,
            lambda v: f"m = {v/10:.1f} кг", self._on_change)
        self._box_stiff, self._sl_stiff, self._lbl_stiff = _slider_group(
            "Жёсткость k (Н/м)", 1, 200, 40,
            lambda v: f"k = {v/10:.1f} Н/м", self._on_change)
        self._box_damp, self._sl_damp, self._lbl_damp = _slider_group(
            "Затухание β (с⁻¹)", 0, 200, 10,
            lambda v: f"β = {v/100:.2f} с⁻¹", self._on_change)

        for box in (self._box_mass, self._box_stiff, self._box_damp):
            ctrl.addWidget(box)

        self._lbl_omega = QLabel()
        self._lbl_omega.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_omega.setStyleSheet("color:#cba6f7; font-style:italic;")
        ctrl.addWidget(self._lbl_omega)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Slots & animation ─────────────────────────────────────────────────────

    def _on_change(self) -> None:
        m, k, beta = self._params()
        self._lbl_mass.setText(f"m = {m:.1f} кг")
        self._lbl_stiff.setText(f"k = {k:.1f} Н/м")
        self._lbl_damp.setText(f"β = {beta:.2f} с⁻¹")
        omega = self._omega(m, k, beta)
        self._lbl_omega.setText(f"ω = {omega:.2f} рад/с")
        self._t = 0.0
        self._rebuild_curve()

    def _rebuild_curve(self) -> None:
        """Precompute and draw the full damped cosine from t=0 to T_WINDOW."""
        ts = np.arange(0.0, T_WINDOW, DT)
        m, k, beta = self._params()
        omega = self._omega(m, k, beta)
        xs = A0 * np.exp(-beta * ts) * np.cos(omega * ts)
        self._curve.setData(ts, xs)
        m_val, k_val, beta_val = self._params()
        omega_val = self._omega(m_val, k_val, beta_val)
        self._lbl_omega.setText(f"ω = {omega_val:.2f} рад/с")

    def _step(self) -> None:
        self._t += DT
        if self._t > T_WINDOW:
            self._t = 0.0
        x_now = self._x(self._t)
        self._marker.setData([self._t], [x_now])

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
register_simulation("Механические колебания и волны", SpringWidget)
