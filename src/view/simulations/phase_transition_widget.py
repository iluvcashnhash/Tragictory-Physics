"""
Phase transition simulation widget for Tragictory Physics.

Simulates the heating curve of a substance: T(Q) with flat plateaux
at melting and boiling points. Animated particles change appearance
to visualise solid → liquid → gas transitions.
"""

import math
import random
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


TIMER_MS: int = 30

# Substance data: (T_melt K, T_boil K, L_melt J/g, L_boil J/g, c_s, c_l, c_g J/gK)
SUBSTANCES: dict[str, tuple] = {
    "Вода    (0°C / 100°C)":  (273, 373, 334,  2260, 2.09, 4.18, 2.01),
    "Лёд/Спирт (−114°C / 78°C)": (159, 351, 108,   855, 1.80, 2.44, 1.50),
    "Свинец  (327°C / 1749°C)": (600, 2022,  24,   872, 0.13, 0.16, 0.10),
}
SUB_NAMES = list(SUBSTANCES.keys())

N_PART = 60    # number of animated particles
BOX = 40.0


class PhaseTransitionWidget(QWidget):
    """Heating curve T(Q) + animated particle phase visualiser."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise and start animation."""
        super().__init__(parent)
        self._Q: float = 0.0
        self._build_ui()
        self._reset_particles()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Particles ────────────────────────────────────────────────────────────

    def _reset_particles(self) -> None:
        rng = np.random.default_rng(7)
        self._px = rng.uniform(-BOX * 0.7, BOX * 0.7, N_PART)
        self._py = rng.uniform(-BOX * 0.7, BOX * 0.7, N_PART)
        self._pvx = rng.uniform(-0.3, 0.3, N_PART)
        self._pvy = rng.uniform(-0.3, 0.3, N_PART)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(4)

        # Particle animation
        self._pw_anim = pg.PlotWidget()
        self._pw_anim.setBackground("#1e1e2e")
        self._pw_anim.setAspectLocked(True)
        self._pw_anim.setMouseEnabled(False, False)
        self._pw_anim.setXRange(-BOX, BOX, padding=0)
        self._pw_anim.setYRange(-BOX, BOX, padding=0)
        self._pw_anim.getAxis("bottom").hide()
        self._pw_anim.getAxis("left").hide()
        b = BOX
        self._pw_anim.plot([-b, b, b, -b, -b], [-b, -b, b, b, -b],
                           pen=pg.mkPen("#585b70", width=1))
        self._part_item = pg.ScatterPlotItem(
            size=7, pen=pg.mkPen(None), brush=pg.mkBrush("#89b4fa"))
        self._pw_anim.addItem(self._part_item)
        self._phase_label = pg.TextItem("", color="#f9e2af", anchor=(0.5, 0))
        self._phase_label.setPos(0, -BOX + 3)
        self._pw_anim.addItem(self._phase_label)
        left.addWidget(self._pw_anim, stretch=2)

        # Heating curve
        self._pw_curve = pg.PlotWidget()
        self._pw_curve.setBackground("#1e1e2e")
        self._pw_curve.setLabel("bottom", "Q, кДж/г")
        self._pw_curve.setLabel("left", "T, K")
        self._pw_curve.showGrid(x=True, y=True, alpha=0.25)
        self._static_curve = self._pw_curve.plot(
            pen=pg.mkPen("#a6e3a1", width=2))
        self._dot_curve = self._pw_curve.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        left.addWidget(self._pw_curve, stretch=2)

        root.addLayout(left, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        sub_box = QGroupBox("Вещество")
        sub_lay = QVBoxLayout(sub_box)
        self._cb_sub = QComboBox()
        self._cb_sub.addItems(SUB_NAMES)
        self._cb_sub.currentIndexChanged.connect(self._on_sub_change)
        sub_lay.addWidget(self._cb_sub)
        ctrl.addWidget(sub_box)

        rate_box = QGroupBox("Скорость нагрева")
        rate_lay = QVBoxLayout(rate_box)
        self._lbl_rate = QLabel("×1")
        self._lbl_rate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_rate = QSlider(Qt.Orientation.Horizontal)
        self._sl_rate.setRange(1, 20)
        self._sl_rate.setValue(5)
        self._sl_rate.valueChanged.connect(lambda v: self._lbl_rate.setText(f"×{v}"))
        rate_lay.addWidget(self._lbl_rate)
        rate_lay.addWidget(self._sl_rate)
        ctrl.addWidget(rate_box)

        info_box = QGroupBox("Состояние")
        info_lay = QVBoxLayout(info_box)
        self._lbl_T = QLabel()
        self._lbl_phase = QLabel()
        self._lbl_phase.setStyleSheet("font-weight:bold; font-size:14px;")
        for w in (self._lbl_T, self._lbl_phase):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        reset_btn = QPushButton("↺ Сбросить")
        reset_btn.clicked.connect(self._full_reset)
        ctrl.addWidget(reset_btn)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

        self._on_sub_change(0)

    def _on_sub_change(self, _: int = 0) -> None:
        self._full_reset()
        self._draw_static_curve()

    def _full_reset(self) -> None:
        self._Q = 0.0
        self._reset_particles()

    def _draw_static_curve(self) -> None:
        T_m, T_b, Lm, Lb, cs, cl, cg = SUBSTANCES[self._cb_sub.currentText()]
        T0 = T_m - 80
        qs = []
        Ts = []
        q = 0.0
        # Solid heating
        q_end_solid = cs * (T_m - T0)
        for t in np.linspace(T0, T_m, 30):
            qs.append(cs * (t - T0))
            Ts.append(t)
        # Melting plateau
        for frac in np.linspace(0, 1, 20):
            qs.append(q_end_solid + Lm * frac)
            Ts.append(T_m)
        q_after_melt = q_end_solid + Lm
        # Liquid heating
        q_end_liquid = q_after_melt + cl * (T_b - T_m)
        for t in np.linspace(T_m, T_b, 40):
            qs.append(q_after_melt + cl * (t - T_m))
            Ts.append(t)
        # Boiling plateau
        for frac in np.linspace(0, 1, 20):
            qs.append(q_end_liquid + Lb * frac)
            Ts.append(T_b)
        q_after_boil = q_end_liquid + Lb
        # Gas heating
        for t in np.linspace(T_b, T_b + 200, 20):
            qs.append(q_after_boil + cg * (t - T_b))
            Ts.append(t)
        self._qs_arr = np.array(qs) / 1000.0   # J/g → kJ/g
        self._Ts_arr = np.array(Ts)
        self._Q_max = float(self._qs_arr[-1])
        self._static_curve.setData(self._qs_arr, self._Ts_arr)
        self._pw_curve.setXRange(0, self._Q_max, padding=0.05)
        self._pw_curve.setYRange(float(self._Ts_arr[0]) - 20,
                                  float(self._Ts_arr[-1]) + 20, padding=0)

    # ── Step ─────────────────────────────────────────────────────────────────

    def _step(self) -> None:
        rate = self._sl_rate.value()
        dQ = 0.5 * rate / 1000.0   # kJ/g per step
        self._Q = min(self._Q + dQ, self._Q_max)

        # Interpolate T from curve
        T_now = float(np.interp(self._Q, self._qs_arr, self._Ts_arr))
        self._dot_curve.setData([self._Q], [T_now])

        T_m, T_b, *_ = SUBSTANCES[self._cb_sub.currentText()]
        if T_now < T_m - 0.5:
            phase = "🧊 Твёрдое"
            speed = 0.1
            size = 8
            color = "#89b4fa"
        elif T_now < T_b - 0.5:
            phase = "💧 Жидкость"
            speed = 0.5 + (T_now - T_m) / (T_b - T_m) * 1.5
            size = 6
            color = "#74c7ec"
        else:
            phase = "💨 Газ"
            speed = 3.0 + (T_now - T_b) / 100.0
            size = 4
            color = "#cba6f7"

        self._lbl_T.setText(f"T = {T_now:.1f} K  ({T_now - 273:.1f} °C)")
        self._lbl_phase.setText(phase)
        self._phase_label.setText(phase)

        # Animate particles
        if T_now < T_m - 0.5:
            # Solid: vibrate in place
            self._px += np.random.uniform(-speed, speed, N_PART)
            self._py += np.random.uniform(-speed, speed, N_PART)
            np.clip(self._px, -BOX * 0.8, BOX * 0.8, out=self._px)
            np.clip(self._py, -BOX * 0.8, BOX * 0.8, out=self._py)
        else:
            # Liquid / gas: move freely
            self._pvx = np.clip(self._pvx * 0.98 + np.random.uniform(-0.2, 0.2, N_PART), -speed, speed)
            self._pvy = np.clip(self._pvy * 0.98 + np.random.uniform(-0.2, 0.2, N_PART), -speed, speed)
            self._px += self._pvx
            self._py += self._pvy
            wall = BOX * 0.9
            self._pvx[self._px > wall] *= -1;  self._px[self._px > wall] = wall
            self._pvx[self._px < -wall] *= -1; self._px[self._px < -wall] = -wall
            self._pvy[self._py > wall] *= -1;  self._py[self._py > wall] = wall
            self._pvy[self._py < -wall] *= -1; self._py[self._py < -wall] = -wall

        self._part_item.setData(
            x=self._px.tolist(), y=self._py.tolist(),
            size=size, brush=pg.mkBrush(color))

        if self._Q >= self._Q_max:
            self._Q = 0.0
            self._reset_particles()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self._timer.stop(); super().hideEvent(event)

    def showEvent(self, event) -> None:  # type: ignore[override]
        self._timer.start(); super().showEvent(event)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._timer.stop(); super().closeEvent(event)

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Плавление и кристаллизация", PhaseTransitionWidget)
