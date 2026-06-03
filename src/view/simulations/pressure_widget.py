"""
Pascal's law and pressure in liquids widget for Tragictory Physics.

Shows pressure as a function of depth using p = p0 + ρgh.
Animates a U-tube manometer and a pressure vs depth graph.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


G: float = 9.81
P0: float = 101325.0   # Pa, atmospheric

LIQUIDS: dict[str, float] = {
    "Вода          ρ = 1000 кг/м³": 1000.0,
    "Морская вода  ρ = 1025 кг/м³": 1025.0,
    "Ртуть         ρ = 13600 кг/м³": 13600.0,
    "Масло         ρ =  900 кг/м³":  900.0,
}
LIQUID_NAMES = list(LIQUIDS.keys())
MAX_DEPTH: float = 20.0   # metres


class PressureWidget(QWidget):
    """Pascal's law: pressure vs depth p = p₀ + ρgh.

    Left pane: tank with colour-coded pressure gradient.
    Right pane: p(h) graph with probe point.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise and draw initial state."""
        super().__init__(parent)
        self._build_ui()
        self._update()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        plots = QHBoxLayout()

        # Left: tank visualisation
        self._pw_tank = pg.PlotWidget()
        self._pw_tank.setBackground("#1e1e2e")
        self._pw_tank.setMouseEnabled(False, False)
        self._pw_tank.setAspectLocked(False)
        self._pw_tank.setXRange(-3, 3, padding=0)
        self._pw_tank.setYRange(-MAX_DEPTH - 1, 2, padding=0)
        self._pw_tank.getAxis("bottom").hide()
        self._pw_tank.getAxis("left").hide()

        # Tank walls
        self._pw_tank.plot([-2, -2, 2, 2], [1, -MAX_DEPTH, -MAX_DEPTH, 1],
                           pen=pg.mkPen("#585b70", width=2))
        # Surface
        self._pw_tank.addItem(pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen("#89b4fa", width=2)))

        # Pressure gradient image
        self._img_tank = pg.ImageItem()
        self._pw_tank.addItem(self._img_tank)
        self._img_tank.setPos(-2, -MAX_DEPTH)

        # Probe dot
        self._probe_dot = self._pw_tank.plot(
            pen=None, symbol="o", symbolSize=14,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen("#ffffff", width=1))
        self._probe_label = pg.TextItem("", color="#f38ba8", anchor=(0, 0.5))
        self._pw_tank.addItem(self._probe_label)

        plots.addWidget(self._pw_tank, stretch=1)

        # Right: p(h) graph
        self._pw_graph = pg.PlotWidget()
        self._pw_graph.setBackground("#1e1e2e")
        self._pw_graph.setLabel("left", "Глубина h, м")
        self._pw_graph.setLabel("bottom", "p, кПа")
        self._pw_graph.showGrid(x=True, y=True, alpha=0.25)
        self._curve_p = self._pw_graph.plot(pen=pg.mkPen("#89b4fa", width=2))
        self._dot_p = self._pw_graph.plot(
            pen=None, symbol="o", symbolSize=12,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        plots.addWidget(self._pw_graph, stretch=2)

        root.addLayout(plots, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        liq_box = QGroupBox("Жидкость")
        liq_lay = QVBoxLayout(liq_box)
        self._cb_liq = QComboBox()
        self._cb_liq.addItems(LIQUID_NAMES)
        self._cb_liq.currentIndexChanged.connect(self._update)
        liq_lay.addWidget(self._cb_liq)
        ctrl.addWidget(liq_box)

        depth_box = QGroupBox("Глубина зонда h (м)")
        depth_lay = QVBoxLayout(depth_box)
        self._lbl_depth = QLabel("h = 5.0 м")
        self._lbl_depth.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_depth = QSlider(Qt.Orientation.Horizontal)
        self._sl_depth.setRange(0, int(MAX_DEPTH * 10))
        self._sl_depth.setValue(50)
        self._sl_depth.valueChanged.connect(self._update)
        depth_lay.addWidget(self._lbl_depth)
        depth_lay.addWidget(self._sl_depth)
        ctrl.addWidget(depth_box)

        info_box = QGroupBox("Давление на зонде")
        info_lay = QVBoxLayout(info_box)
        self._lbl_p_atm = QLabel(f"p₀ = {P0/1000:.1f} кПа")
        self._lbl_p_atm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_p_rho = QLabel()
        self._lbl_p_rho.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_p_total = QLabel()
        self._lbl_p_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_p_total.setStyleSheet("font-weight:bold; font-size:14px; color:#89b4fa;")
        for w in (self._lbl_p_atm, self._lbl_p_rho, self._lbl_p_total):
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        hint = QLabel("p = p₀ + ρgh")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#888; font-style:italic; font-size:16px;")
        ctrl.addWidget(hint)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self) -> None:
        rho = LIQUIDS[self._cb_liq.currentText()]
        h_probe = self._sl_depth.value() / 10.0
        p_probe = P0 + rho * G * h_probe

        self._lbl_depth.setText(f"h = {h_probe:.1f} м")
        self._lbl_p_rho.setText(f"ρgh = {rho*G*h_probe/1000:.1f} кПа")
        self._lbl_p_total.setText(f"p = {p_probe/1000:.1f} кПа")

        # Pressure gradient image (width=4 px, height=MAX_DEPTH in 100 rows)
        N = 100
        depths = np.linspace(0, MAX_DEPTH, N)
        pressures = P0 + rho * G * depths
        p_norm = (pressures - P0) / (rho * G * MAX_DEPTH)   # 0 … 1

        # Build 4×N image: columns are depth rows, gradient blue→red
        img = np.zeros((4, N, 3), dtype=np.uint8)
        img[:, :, 0] = (p_norm * 200).astype(np.uint8)          # R
        img[:, :, 1] = 60
        img[:, :, 2] = (255 - p_norm * 200).astype(np.uint8)    # B

        self._img_tank.setImage(img.transpose(1, 0, 2))
        self._img_tank.setRect(-2, -MAX_DEPTH, 4, MAX_DEPTH)

        # Probe
        self._probe_dot.setData([0], [-h_probe])
        self._probe_label.setText(f"{p_probe/1000:.0f} кПа")
        self._probe_label.setPos(0.3, -h_probe)

        # p(h) graph
        p_kpa = (P0 + rho * G * depths) / 1000.0
        self._curve_p.setData(p_kpa, depths)
        self._dot_p.setData([p_probe / 1000], [h_probe])
        self._pw_graph.setYRange(0, MAX_DEPTH, padding=0.05)
        self._pw_graph.invertY(True)

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Давление в жидкостях и газах. Закон Паскаля", PressureWidget)
