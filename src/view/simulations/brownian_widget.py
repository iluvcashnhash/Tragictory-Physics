"""
Brownian motion simulation widget for Tragictory Physics.

A large 'pollen' particle is bombarded by tiny invisible molecules,
each collision nudging it in a random direction. The trail of the
pollen particle is drawn, illustrating the random walk.
"""

import math
import random
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


TIMER_MS: int = 30
N_SMALL: int = 60          # number of small molecules shown
BOX: float = 50.0          # half-extent of the arena
TRAIL_MAX: int = 800       # pollen trail length


class BrownianWidget(QWidget):
    """Brownian motion: large pollen particle buffeted by tiny molecules.

    The pollen's trail is drawn; temperature controls molecule speed.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise particle positions and start animation."""
        super().__init__(parent)
        self._build_ui()
        self._reset()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Init ─────────────────────────────────────────────────────────────────

    def _reset(self) -> None:
        # Small molecules: random positions & velocities
        self._sx = np.random.uniform(-BOX, BOX, N_SMALL)
        self._sy = np.random.uniform(-BOX, BOX, N_SMALL)
        speed = self._molecule_speed()
        angles = np.random.uniform(0, 2 * math.pi, N_SMALL)
        self._svx = speed * np.cos(angles)
        self._svy = speed * np.sin(angles)
        # Pollen starts at centre
        self._px: float = 0.0
        self._py: float = 0.0
        self._pvx: float = 0.0
        self._pvy: float = 0.0
        self._trail_x: list[float] = [0.0]
        self._trail_y: list[float] = [0.0]

    def _molecule_speed(self) -> float:
        T = self._sl_temp.value()
        return 0.5 + T / 50.0

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setAspectLocked(True)
        self._pw.setMouseEnabled(False, False)
        self._pw.setXRange(-BOX, BOX, padding=0)
        self._pw.setYRange(-BOX, BOX, padding=0)
        self._pw.getAxis("bottom").hide()
        self._pw.getAxis("left").hide()

        # Box boundary
        b = BOX
        self._pw.plot([-b, b, b, -b, -b], [-b, -b, b, b, -b],
                      pen=pg.mkPen("#585b70", width=1))

        self._trail_item = self._pw.plot(pen=pg.mkPen("#f38ba860", width=1))
        self._pollen_item = self._pw.plot(
            pen=None, symbol="o", symbolSize=18,
            symbolBrush="#f9e2af", symbolPen=pg.mkPen("#f9e2af", width=2))
        self._mol_item = pg.ScatterPlotItem(
            size=4, pen=pg.mkPen(None), brush=pg.mkBrush("#89b4fa80"))
        self._pw.addItem(self._mol_item)

        root.addWidget(self._pw, stretch=3)

        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        t_box = QGroupBox("Температура")
        t_lay = QVBoxLayout(t_box)
        self._lbl_temp = QLabel("T = 300 K")
        self._lbl_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_temp = QSlider(Qt.Orientation.Horizontal)
        self._sl_temp.setRange(50, 1000)
        self._sl_temp.setValue(300)
        self._sl_temp.valueChanged.connect(self._on_temp)
        t_lay.addWidget(self._lbl_temp)
        t_lay.addWidget(self._sl_temp)
        ctrl.addWidget(t_box)

        reset_btn = QPushButton("↺ Сбросить след")
        reset_btn.clicked.connect(self._reset)
        ctrl.addWidget(reset_btn)

        hint = QLabel("Жёлтая точка — пыльца\nСиние — молекулы воды")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#888; font-style:italic;")
        ctrl.addWidget(hint)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    def _on_temp(self, val: int) -> None:
        self._lbl_temp.setText(f"T = {val} K")
        speed = self._molecule_speed()
        norms = np.sqrt(self._svx**2 + self._svy**2)
        norms = np.where(norms < 1e-9, 1.0, norms)
        self._svx = self._svx / norms * speed
        self._svy = self._svy / norms * speed

    # ── Animation ────────────────────────────────────────────────────────────

    def _step(self) -> None:
        # Move small molecules & bounce off walls
        self._sx += self._svx
        self._sy += self._svy
        self._svx[self._sx > BOX] *= -1;  self._sx[self._sx > BOX] = BOX
        self._svx[self._sx < -BOX] *= -1; self._sx[self._sx < -BOX] = -BOX
        self._svy[self._sy > BOX] *= -1;  self._sy[self._sy > BOX] = BOX
        self._svy[self._sy < -BOX] *= -1; self._sy[self._sy < -BOX] = -BOX

        # Collision detection with pollen (radius 3 units)
        POLLEN_R = 3.0
        dx = self._sx - self._px
        dy = self._sy - self._py
        dist = np.sqrt(dx**2 + dy**2)
        hits = dist < POLLEN_R + 1.5

        if np.any(hits):
            impulse_x = float(np.sum(-self._svx[hits])) * 0.04
            impulse_y = float(np.sum(-self._svy[hits])) * 0.04
            self._pvx += impulse_x
            self._pvy += impulse_y
            # Reverse hit molecules
            self._svx[hits] *= -1
            self._svy[hits] *= -1

        # Drag on pollen
        self._pvx *= 0.92
        self._pvy *= 0.92

        self._px += self._pvx
        self._py += self._pvy

        # Clamp pollen
        self._px = max(-BOX + 3, min(BOX - 3, self._px))
        self._py = max(-BOX + 3, min(BOX - 3, self._py))

        self._trail_x.append(self._px)
        self._trail_y.append(self._py)
        if len(self._trail_x) > TRAIL_MAX:
            self._trail_x.pop(0)
            self._trail_y.pop(0)

        self._trail_item.setData(self._trail_x, self._trail_y)
        self._pollen_item.setData([self._px], [self._py])
        self._mol_item.setData(x=self._sx.tolist(), y=self._sy.tolist())

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
register_simulation("Броуновское движение и строение вещества", BrownianWidget)
