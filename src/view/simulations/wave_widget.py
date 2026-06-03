"""
Travelling wave simulation widget for Tragictory Physics.

Renders y(x, t) = A·sin(k·x − ω·t) scrolling in real time.
A red marker shows that medium particles oscillate only vertically
while the wave travels horizontally.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


TIMER_MS: int = 25
X_MIN: float = 0.0
X_MAX: float = 10.0        # metres
N_POINTS: int = 500
MARKER_X: float = 5.0      # fixed x position of the particle marker


class WaveWidget(QWidget):
    """Travelling transverse wave y(x,t) = A·sin(k·x − ω·t).

    Controls: amplitude A, frequency ν, wavelength λ.
    A red dot at fixed x shows vertical oscillation of a medium particle.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise wave parameters and start animation timer."""
        super().__init__(parent)
        self._t: float = 0.0
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Wave parameters ───────────────────────────────────────────────────────

    def _A(self) -> float:
        return self._sl_amp.value() / 100.0        # 0.05 – 2.00 m

    def _nu(self) -> float:
        return self._sl_freq.value() / 10.0        # 0.1 – 5.0 Hz

    def _lam(self) -> float:
        return self._sl_wave.value() / 10.0        # 0.5 – 5.0 m

    def _omega(self) -> float:
        return 2.0 * math.pi * self._nu()

    def _k(self) -> float:
        return 2.0 * math.pi / self._lam()

    def _speed(self) -> float:
        return self._nu() * self._lam()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Plot
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setLabel("bottom", "x, м")
        self._pw.setLabel("left", "y, м")
        self._pw.setXRange(X_MIN, X_MAX, padding=0)
        self._pw.setYRange(-2.2, 2.2, padding=0)
        self._pw.showGrid(x=True, y=True, alpha=0.25)

        # Equilibrium line
        self._pw.addItem(pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen("#585b70", width=1)))
        # Marker vertical dashed line
        self._marker_line = pg.InfiniteLine(
            pos=MARKER_X, angle=90,
            pen=pg.mkPen("#f38ba880", width=1, style=Qt.PenStyle.DashLine))
        self._pw.addItem(self._marker_line)

        # Wave curve
        self._curve = self._pw.plot(pen=pg.mkPen("#89b4fa", width=2))

        # Particle marker
        self._marker = self._pw.plot(
            pen=None, symbol="o", symbolSize=14,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))

        # Direction arrow label
        arrow_lbl = pg.TextItem("→ волна", color="#a6e3a1", anchor=(0, 1))
        arrow_lbl.setPos(X_MIN + 0.3, -1.8)
        self._pw.addItem(arrow_lbl)
        osc_lbl = pg.TextItem("↕ частица", color="#f38ba8", anchor=(0, 0))
        osc_lbl.setPos(MARKER_X + 0.2, 1.8)
        self._pw.addItem(osc_lbl)

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        def _make_slider(title: str, lo: int, hi: int, val: int,
                         fmt_fn) -> tuple[QGroupBox, QSlider, QLabel]:
            box = QGroupBox(title)
            lay = QVBoxLayout(box)
            lbl = QLabel(fmt_fn(val))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo, hi)
            sl.setValue(val)
            sl.valueChanged.connect(lambda _: self._on_change())
            lay.addWidget(lbl)
            lay.addWidget(sl)
            return box, sl, lbl

        self._box_amp, self._sl_amp, self._lbl_amp = _make_slider(
            "Амплитуда A (м)", 5, 200, 100,
            lambda v: f"A = {v/100:.2f} м")
        self._box_freq, self._sl_freq, self._lbl_freq = _make_slider(
            "Частота ν (Гц)", 1, 50, 10,
            lambda v: f"ν = {v/10:.1f} Гц")
        self._box_wave, self._sl_wave, self._lbl_wave = _make_slider(
            "Длина волны λ (м)", 5, 50, 20,
            lambda v: f"λ = {v/10:.1f} м")

        for box in (self._box_amp, self._box_freq, self._box_wave):
            ctrl.addWidget(box)

        # Derived readout
        info_box = QGroupBox("Производные величины")
        info_lay = QVBoxLayout(info_box)
        self._lbl_speed = QLabel()
        self._lbl_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_omega_lbl = QLabel()
        self._lbl_omega_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_omega_lbl.setStyleSheet("color:#cba6f7; font-style:italic;")
        info_lay.addWidget(self._lbl_speed)
        info_lay.addWidget(self._lbl_omega_lbl)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)
        self._on_change()

    # ── Slots & animation ─────────────────────────────────────────────────────

    def _on_change(self) -> None:
        self._lbl_amp.setText(f"A = {self._A():.2f} м")
        self._lbl_freq.setText(f"ν = {self._nu():.1f} Гц")
        self._lbl_wave.setText(f"λ = {self._lam():.1f} м")
        v = self._speed()
        self._lbl_speed.setText(f"v = λ·ν = {v:.2f} м/с")
        self._lbl_omega_lbl.setText(
            f"ω = {self._omega():.2f} рад/с   k = {self._k():.2f} рад/м")

    def _step(self) -> None:
        dt_s = TIMER_MS / 1000.0
        self._t += dt_s

        xs = np.linspace(X_MIN, X_MAX, N_POINTS)
        ys = self._A() * np.sin(self._k() * xs - self._omega() * self._t)
        self._curve.setData(xs, ys)

        # Marker: same formula at fixed x
        y_marker = self._A() * math.sin(
            self._k() * MARKER_X - self._omega() * self._t)
        self._marker.setData([MARKER_X], [y_marker])

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
register_simulation("Распространение механических волн. Продольные и поперечные волны", WaveWidget)
