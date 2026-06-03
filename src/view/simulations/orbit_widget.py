"""
Gravitational orbit simulation widget for Tragictory Physics.

Simulates a planet orbiting a fixed star at (0,0) using Newton's law of
gravitation, integrated with RK4. The orbital trail reveals ellipse,
parabola, or hyperbola depending on initial velocity.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


# ── Simulation constants (AU / yr units for nice numbers) ─────────────────────
GM: float = 4 * math.pi ** 2   # G*M in AU³/yr²  (→ Earth v_circ ≈ 2π AU/yr)
DT: float = 0.0005              # years per step
TIMER_MS: int = 20
STEPS_PER_FRAME: int = 10       # physics steps between redraws
TRAIL_MAX: int = 2000           # max trail points kept
ESCAPE_R: float = 30.0          # AU — reset if planet escapes this far

# Initial position: planet starts at (1, 0) AU
X0: float = 1.0
Y0: float = 0.0

# v_circular = 2π AU/yr ≈ 6.283
V_CIRC: float = 2.0 * math.pi
V_MIN_SLIDER: int = 10          # slider units (tenths of V_CIRC/10)
V_MAX_SLIDER: int = 150
V_DEFAULT_SLIDER: int = 100     # → v = V_CIRC (circular orbit)


class OrbitWidget(QWidget):
    """Planetary orbit simulator using gravitational attraction to a fixed star.

    Trail colour indicates orbit type:
      green  — ellipse (v < v_escape)
      yellow — near-parabolic
      red    — hyperbolic (v ≥ v_escape)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise orbital state and start animation timer."""
        super().__init__(parent)
        self._build_ui()
        self._reset()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._frame)
        self._timer.start()

    # ── Physics ───────────────────────────────────────────────────────────────

    def _v0(self) -> float:
        """Return initial velocity (AU/yr) from slider."""
        return (self._sl_v.value() / 100.0) * V_CIRC

    def _reset(self) -> None:
        """Set planet to starting position with current v₀."""
        self._px = X0
        self._py = Y0
        self._vx = 0.0
        self._vy = self._v0()
        self._trail_x: list[float] = []
        self._trail_y: list[float] = []
        self._update_labels()

    def _accel(self, x: float, y: float) -> tuple[float, float]:
        r2 = x*x + y*y
        r = math.sqrt(r2)
        if r < 1e-6:
            return 0.0, 0.0
        factor = -GM / (r2 * r)
        return factor * x, factor * y

    def _rk4(self) -> None:
        """One RK4 step for (px, py, vx, vy)."""
        px, py, vx, vy = self._px, self._py, self._vx, self._vy

        ax1, ay1 = self._accel(px, py)
        k1 = (vx, vy, ax1, ay1)

        px2 = px + 0.5*DT*k1[0]; py2 = py + 0.5*DT*k1[1]
        vx2 = vx + 0.5*DT*k1[2]; vy2 = vy + 0.5*DT*k1[3]
        ax2, ay2 = self._accel(px2, py2)
        k2 = (vx2, vy2, ax2, ay2)

        px3 = px + 0.5*DT*k2[0]; py3 = py + 0.5*DT*k2[1]
        vx3 = vx + 0.5*DT*k2[2]; vy3 = vy + 0.5*DT*k2[3]
        ax3, ay3 = self._accel(px3, py3)
        k3 = (vx3, vy3, ax3, ay3)

        px4 = px + DT*k3[0]; py4 = py + DT*k3[1]
        vx4 = vx + DT*k3[2]; vy4 = vy + DT*k3[3]
        ax4, ay4 = self._accel(px4, py4)
        k4 = (vx4, vy4, ax4, ay4)

        self._px += (DT/6)*(k1[0]+2*k2[0]+2*k3[0]+k4[0])
        self._py += (DT/6)*(k1[1]+2*k2[1]+2*k3[1]+k4[1])
        self._vx += (DT/6)*(k1[2]+2*k2[2]+2*k3[2]+k4[2])
        self._vy += (DT/6)*(k1[3]+2*k2[3]+2*k3[3]+k4[3])

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setAspectLocked(True)
        self._pw.setMouseEnabled(False, False)
        self._pw.setXRange(-4, 4, padding=0)
        self._pw.setYRange(-4, 4, padding=0)
        self._pw.showGrid(x=True, y=True, alpha=0.15)
        self._pw.getAxis("bottom").hide()
        self._pw.getAxis("left").hide()

        # Star at origin
        self._pw.plot([0], [0], pen=None,
                      symbol="star", symbolSize=20,
                      symbolBrush="#f9e2af", symbolPen=pg.mkPen(None))

        self._trail_item = self._pw.plot(pen=pg.mkPen("#a6e3a1", width=2))
        self._planet_item = self._pw.plot(
            pen=None, symbol="o", symbolSize=12,
            symbolBrush="#89b4fa", symbolPen=pg.mkPen(None))

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        v_box = QGroupBox("Начальная скорость v₀")
        v_lay = QVBoxLayout(v_box)
        self._lbl_v = QLabel()
        self._lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_v = QSlider(Qt.Orientation.Horizontal)
        self._sl_v.setRange(V_MIN_SLIDER, V_MAX_SLIDER)
        self._sl_v.setValue(V_DEFAULT_SLIDER)
        self._sl_v.valueChanged.connect(self._on_change)
        v_lay.addWidget(self._lbl_v)
        v_lay.addWidget(self._sl_v)
        ctrl.addWidget(v_box)

        info_box = QGroupBox("Состояние орбиты")
        info_lay = QVBoxLayout(info_box)
        self._lbl_type = QLabel()
        self._lbl_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_type.setStyleSheet("font-weight:bold; font-size:14px;")
        self._lbl_ratio = QLabel()
        self._lbl_ratio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_ratio.setStyleSheet("color:#888; font-style:italic;")
        info_lay.addWidget(self._lbl_type)
        info_lay.addWidget(self._lbl_ratio)
        ctrl.addWidget(info_box)

        reset_btn = QPushButton("↺ Перезапустить")
        reset_btn.clicked.connect(self._reset)
        ctrl.addWidget(reset_btn)

        hint = QLabel("v_кр = √2 · v_цирк")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#888; font-style:italic;")
        ctrl.addWidget(hint)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    def _update_labels(self) -> None:
        v0 = self._v0()
        v_esc = math.sqrt(2) * V_CIRC
        ratio = v0 / V_CIRC
        self._lbl_v.setText(f"v₀ = {v0:.2f} а.е./г\n({ratio:.2f} · v_цирк)")
        if v0 < 0.99 * v_esc:
            orbit_type = "🟢 Эллипс"
            trail_color = "#a6e3a1"
        elif v0 < 1.01 * v_esc:
            orbit_type = "🟡 Парабола"
            trail_color = "#f9e2af"
        else:
            orbit_type = "🔴 Гипербола"
            trail_color = "#f38ba8"
        self._lbl_type.setText(orbit_type)
        self._lbl_ratio.setText(f"v_esc ≈ {v_esc:.2f} а.е./г")
        self._trail_item.setPen(pg.mkPen(trail_color, width=2))

    # ── Slots & animation ─────────────────────────────────────────────────────

    def _on_change(self) -> None:
        self._reset()

    def _frame(self) -> None:
        for _ in range(STEPS_PER_FRAME):
            self._rk4()
        r = math.sqrt(self._px**2 + self._py**2)
        if r > ESCAPE_R or r < 0.02:
            self._reset()
            return
        self._trail_x.append(self._px)
        self._trail_y.append(self._py)
        if len(self._trail_x) > TRAIL_MAX:
            self._trail_x.pop(0)
            self._trail_y.pop(0)
        self._trail_item.setData(self._trail_x, self._trail_y)
        self._planet_item.setData([self._px], [self._py])

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
register_simulation("Закон всемирного тяготения", OrbitWidget)
