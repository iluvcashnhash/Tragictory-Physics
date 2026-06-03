"""
RLC oscillatory circuit simulation widget for Tragictory Physics.

Plots charge q(t) and current I(t) for damped electromagnetic oscillations:
  q(t) = q₀ · exp(−R·t / 2L) · cos(ω·t)
  I(t) = dq/dt
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QFormLayout,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


T_WINDOW: float = 0.05      # seconds of history shown
DT: float = 1e-5            # integration step
N_POINTS: int = 2000        # samples to display
TIMER_MS: int = 25
Q0: float = 1.0             # initial charge (normalised)


class RLCWidget(QWidget):
    """Damped LC circuit: q(t) = q₀·e^(−Rt/2L)·cos(ω·t), I = dq/dt.

    Sliders control L (μH), C (μF), and R (Ω). The time-axis autoscales
    to show ~3 full oscillations or the decay window, whichever is shorter.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the widget and start animation timer."""
        super().__init__(parent)
        self._t_offset: float = 0.0
        self._build_ui()
        self._rebuild()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Physics ───────────────────────────────────────────────────────────────

    def _get_params(self) -> tuple[float, float, float]:
        L = self._sl_L.value() * 1e-3     # mH → H
        C = self._sl_C.value() * 1e-6     # μF → F
        R = self._sl_R.value() * 0.1      # tenths of Ω
        return L, C, R

    def _omega(self, L: float, C: float, R: float) -> float:
        discriminant = 1.0 / (L * C) - (R / (2 * L)) ** 2
        return math.sqrt(max(discriminant, 0.0))

    def _q(self, t: float, L: float, C: float, R: float) -> float:
        alpha = R / (2 * L)
        omega = self._omega(L, C, R)
        return Q0 * math.exp(-alpha * t) * math.cos(omega * t)

    def _I(self, t: float, L: float, C: float, R: float) -> float:
        """dq/dt computed analytically."""
        alpha = R / (2 * L)
        omega = self._omega(L, C, R)
        return Q0 * math.exp(-alpha * t) * (
            -alpha * math.cos(omega * t) - omega * math.sin(omega * t)
        )

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Two vertically stacked plots
        plot_col = QVBoxLayout()
        plot_col.setSpacing(4)

        self._pw_q = pg.PlotWidget()
        self._pw_q.setBackground("#1e1e2e")
        self._pw_q.setLabel("left", "q (Кл)")
        self._pw_q.showGrid(x=True, y=True, alpha=0.25)
        self._pw_q.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen("#585b70")))
        self._curve_q = self._pw_q.plot(pen=pg.mkPen("#89b4fa", width=2), name="q(t)")
        self._dot_q = self._pw_q.plot(
            pen=None, symbol="o", symbolSize=9,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        plot_col.addWidget(self._pw_q, stretch=1)

        self._pw_I = pg.PlotWidget()
        self._pw_I.setBackground("#1e1e2e")
        self._pw_I.setLabel("left", "I (А)")
        self._pw_I.setLabel("bottom", "t (мс)")
        self._pw_I.showGrid(x=True, y=True, alpha=0.25)
        self._pw_I.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen("#585b70")))
        self._curve_I = self._pw_I.plot(pen=pg.mkPen("#a6e3a1", width=2), name="I(t)")
        self._dot_I = self._pw_I.plot(
            pen=None, symbol="o", symbolSize=9,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        plot_col.addWidget(self._pw_I, stretch=1)

        root.addLayout(plot_col, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        params_box = QGroupBox("Параметры контура")
        form = QFormLayout(params_box)

        self._sl_L, self._lbl_L = self._make_slider(1, 100, 10)
        self._sl_C, self._lbl_C = self._make_slider(1, 100, 10)
        self._sl_R, self._lbl_R = self._make_slider(0, 200, 10)

        form.addRow("L (мГн):", self._lbl_L)
        form.addRow("", self._sl_L)
        form.addRow("C (мкФ):", self._lbl_C)
        form.addRow("", self._sl_C)
        form.addRow("R (Ом):", self._lbl_R)
        form.addRow("", self._sl_R)

        self._sl_L.valueChanged.connect(self._on_change)
        self._sl_C.valueChanged.connect(self._on_change)
        self._sl_R.valueChanged.connect(self._on_change)

        ctrl.addWidget(params_box)

        info_box = QGroupBox("Производные")
        info_lay = QVBoxLayout(info_box)
        self._lbl_omega = QLabel()
        self._lbl_omega.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_T0 = QLabel()
        self._lbl_T0.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_regime = QLabel()
        self._lbl_regime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_regime.setStyleSheet("font-weight:bold;")
        for w in (self._lbl_omega, self._lbl_T0, self._lbl_regime):
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    @staticmethod
    def _make_slider(lo: int, hi: int, val: int) -> tuple[QSlider, QLabel]:
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        lbl = QLabel(str(val))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sl, lbl

    # ── Rebuild & animate ─────────────────────────────────────────────────────

    def _on_change(self) -> None:
        L, C, R = self._get_params()
        self._lbl_L.setText(f"{self._sl_L.value()} мГн")
        self._lbl_C.setText(f"{self._sl_C.value()} мкФ")
        self._lbl_R.setText(f"{self._sl_R.value() * 0.1:.1f} Ом")
        self._t_offset = 0.0
        self._rebuild()

    def _rebuild(self) -> None:
        L, C, R = self._get_params()
        omega = self._omega(L, C, R)

        self._lbl_L.setText(f"{self._sl_L.value()} мГн")
        self._lbl_C.setText(f"{self._sl_C.value()} мкФ")
        self._lbl_R.setText(f"{self._sl_R.value() * 0.1:.1f} Ом")

        if omega < 1.0:
            self._lbl_omega.setText("ω → 0 (критич.)")
            self._lbl_T0.setText("")
            self._lbl_regime.setText("🔴 Апериодический режим")
            self._lbl_regime.setStyleSheet("font-weight:bold; color:#f38ba8;")
        else:
            T0 = 2 * math.pi / omega
            self._lbl_omega.setText(f"ω = {omega:.1f} рад/с")
            self._lbl_T0.setText(f"T₀ = {T0*1e3:.3f} мс")
            self._lbl_regime.setText("🟢 Колебательный режим")
            self._lbl_regime.setStyleSheet("font-weight:bold; color:#a6e3a1;")

        # Build display array
        t_arr = np.linspace(0, T_WINDOW, N_POINTS)
        q_arr = np.array([self._q(t, L, C, R) for t in t_arr])
        I_arr = np.array([self._I(t, L, C, R) for t in t_arr])

        self._t_arr = t_arr
        self._q_arr = q_arr
        self._I_arr = I_arr

        t_ms = t_arr * 1e3
        self._curve_q.setData(t_ms, q_arr)
        self._curve_I.setData(t_ms, I_arr)
        self._pw_q.setXRange(0, T_WINDOW * 1e3, padding=0)
        self._pw_I.setXRange(0, T_WINDOW * 1e3, padding=0)

    def _step(self) -> None:
        self._t_offset += TIMER_MS / 1000.0
        if self._t_offset > T_WINDOW:
            self._t_offset = 0.0
        L, C, R = self._get_params()
        t_now = self._t_offset
        q_now = self._q(t_now, L, C, R)
        I_now = self._I(t_now, L, C, R)
        self._dot_q.setData([t_now * 1e3], [q_now])
        self._dot_I.setData([t_now * 1e3], [I_now])

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
register_simulation("Электромагнитные волны и уравнения Максвелла", RLCWidget)
