"""
Ohm's law interactive circuit widget for Tragictory Physics.

Visualises a simple resistor circuit with real-time animated current
(moving charge dots), voltage and current readouts, and an I-V graph.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


TIMER_MS: int = 30
N_CHARGES: int = 20

# Resistor materials with resistivity proxy (Ω·unit)
RESISTORS: dict[str, float] = {
    "Нихром  ρ ↑↑":  100.0,
    "Сталь   ρ ↑":    30.0,
    "Медь    ρ ↓":     5.0,
    "Углерод ρ ↑↑↑": 200.0,
}
RES_NAMES = list(RESISTORS.keys())


class OhmWidget(QWidget):
    """Ohm's law U = I·R circuit visualiser.

    Animated moving charges show current flow.
    I-V characteristic updates in real time.
    Series and parallel resistance configurations available.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise charge positions and start animation."""
        super().__init__(parent)
        self._charge_pos = np.linspace(0, 1, N_CHARGES) % 1.0
        self._build_ui()
        self._update()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(4)

        # Circuit diagram (simple rectangle loop)
        self._pw_circ = pg.PlotWidget()
        self._pw_circ.setBackground("#1e1e2e")
        self._pw_circ.setAspectLocked(True)
        self._pw_circ.setMouseEnabled(False, False)
        self._pw_circ.setXRange(-5, 5, padding=0)
        self._pw_circ.setYRange(-3.5, 3.5, padding=0)
        self._pw_circ.getAxis("bottom").hide()
        self._pw_circ.getAxis("left").hide()

        # Circuit loop
        lx = [-4, 4, 4, -4, -4]
        ly = [-3, -3, 3, 3, -3]
        self._pw_circ.plot(lx, ly, pen=pg.mkPen("#585b70", width=3))

        # Battery symbol (left side)
        self._pw_circ.plot([-4, -4], [-0.5, 0.5],
                           pen=pg.mkPen("#f9e2af", width=4))
        self._pw_circ.plot([-4.3, -3.7], [0.2, 0.2],
                           pen=pg.mkPen("#f9e2af", width=2))
        lbl_batt = pg.TextItem("U", color="#f9e2af", anchor=(1.2, 0.5))
        lbl_batt.setPos(-4.5, 0)
        self._pw_circ.addItem(lbl_batt)

        # Resistor symbol (top)
        rx = np.linspace(-2, 2, 13)
        ry = 3.0 + 0.4 * np.array([0,1,-1,1,-1,1,-1,1,-1,1,-1,1,0])
        self._pw_circ.plot(rx.tolist(), ry.tolist(),
                           pen=pg.mkPen("#89b4fa", width=3))
        self._lbl_R_circ = pg.TextItem("R", color="#89b4fa", anchor=(0.5, 0))
        self._lbl_R_circ.setPos(0, 3.5)
        self._pw_circ.addItem(self._lbl_R_circ)

        # Charges (dots moving along the loop)
        self._charge_item = pg.ScatterPlotItem(
            size=8, pen=pg.mkPen(None), brush=pg.mkBrush("#f38ba8"))
        self._pw_circ.addItem(self._charge_item)

        # Ammeter symbol
        self._pw_circ.plot([3.5, 4.5], [-3, -3],
                           pen=pg.mkPen("#a6e3a1", width=3))
        lbl_A = pg.TextItem("A", color="#a6e3a1", anchor=(0.5, 1.3))
        lbl_A.setPos(4, -3)
        self._pw_circ.addItem(lbl_A)

        left.addWidget(self._pw_circ, stretch=2)

        # I-V graph
        self._pw_iv = pg.PlotWidget()
        self._pw_iv.setBackground("#1e1e2e")
        self._pw_iv.setLabel("bottom", "U, В")
        self._pw_iv.setLabel("left", "I, А")
        self._pw_iv.showGrid(x=True, y=True, alpha=0.25)
        self._iv_line = self._pw_iv.plot(pen=pg.mkPen("#89b4fa", width=2))
        self._iv_dot = self._pw_iv.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        left.addWidget(self._pw_iv, stretch=1)

        root.addLayout(left, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        res_box = QGroupBox("Материал резистора")
        res_lay = QVBoxLayout(res_box)
        self._cb_res = QComboBox()
        self._cb_res.addItems(RES_NAMES)
        self._cb_res.currentIndexChanged.connect(self._update)
        res_lay.addWidget(self._cb_res)
        ctrl.addWidget(res_box)

        U_box = QGroupBox("Напряжение U (В)")
        U_lay = QVBoxLayout(U_box)
        self._lbl_U = QLabel("U = 12 В")
        self._lbl_U.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_U = QSlider(Qt.Orientation.Horizontal)
        self._sl_U.setRange(1, 240)
        self._sl_U.setValue(12)
        self._sl_U.valueChanged.connect(self._update)
        U_lay.addWidget(self._lbl_U)
        U_lay.addWidget(self._sl_U)
        ctrl.addWidget(U_box)

        info_box = QGroupBox("Показания приборов")
        info_lay = QVBoxLayout(info_box)
        self._lbl_R = QLabel()
        self._lbl_I = QLabel()
        self._lbl_P = QLabel()
        self._lbl_I.setStyleSheet("font-weight:bold; font-size:14px; color:#a6e3a1;")
        for w in (self._lbl_R, self._lbl_I, self._lbl_P):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self) -> None:
        R = RESISTORS[self._cb_res.currentText()]
        U = self._sl_U.value()
        I = U / R
        P = U * I

        self._lbl_U.setText(f"U = {U} В")
        self._lbl_R.setText(f"R = {R:.0f} Ом")
        self._lbl_I.setText(f"I = {I:.3f} А")
        self._lbl_P.setText(f"P = {P:.2f} Вт")
        self._lbl_R_circ.setText(f"R={R:.0f}Ω")

        # I-V line
        Us = np.linspace(0, 240, 200)
        Is = Us / R
        self._iv_line.setData(Us.tolist(), Is.tolist())
        self._iv_dot.setData([U], [I])
        self._pw_iv.setXRange(0, 240, padding=0.05)
        self._pw_iv.setYRange(0, 240 / R * 1.1, padding=0)

        self._R = R
        self._U = U
        self._I = I

    # ── Animation ────────────────────────────────────────────────────────────

    # Map t ∈ [0,1) along circuit loop to (x,y)
    @staticmethod
    def _loop_pos(t: float) -> tuple[float, float]:
        # 4 segments: bottom (0-0.25), right (0.25-0.5), top (0.5-0.75), left (0.75-1.0)
        t = t % 1.0
        if t < 0.25:
            s = t / 0.25
            return -4 + 8 * s, -3.0
        elif t < 0.5:
            s = (t - 0.25) / 0.25
            return 4.0, -3 + 6 * s
        elif t < 0.75:
            s = (t - 0.5) / 0.25
            return 4 - 8 * s, 3.0
        else:
            s = (t - 0.75) / 0.25
            return -4.0, 3 - 6 * s

    def _step(self) -> None:
        speed = max(0.001, self._I / 50.0)
        self._charge_pos = (self._charge_pos + speed) % 1.0
        xs = []
        ys = []
        for p in self._charge_pos:
            x, y = self._loop_pos(float(p))
            xs.append(x)
            ys.append(y)
        self._charge_item.setData(x=xs, y=ys)

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
register_simulation("Закон Ома и сопротивление", OhmWidget)
