"""
Archimedes' principle simulation widget for Tragictory Physics.

Animates a block being lowered into a liquid. Shows buoyancy, weight,
and net force as vector arrows. The block sinks, floats, or hovers
depending on density ratio.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


G: float = 9.81

LIQUIDS: dict[str, float] = {
    "Вода          ρ = 1000 кг/м³": 1000.0,
    "Морская вода  ρ = 1025 кг/м³": 1025.0,
    "Масло         ρ =  900 кг/м³":  900.0,
    "Ртуть         ρ = 13600 кг/м³": 13600.0,
}
LIQUID_NAMES = list(LIQUIDS.keys())

# Display geometry (plot units)
TANK_X0, TANK_X1 = -4.0, 4.0
LIQUID_Y_TOP = 0.0
LIQUID_Y_BOT = -8.0
BLOCK_W = 3.0
BLOCK_H = 2.0


class ArchimedesWidget(QWidget):
    """Archimedes buoyancy visualiser.

    Shows the block position, weight arrow (down), buoyancy arrow (up),
    and net force, plus a status label (тонет / плавает / всплывает).
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

        # Plot
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setAspectLocked(False)
        self._pw.setMouseEnabled(False, False)
        self._pw.setXRange(-5, 5, padding=0)
        self._pw.setYRange(-9, 5, padding=0)
        self._pw.getAxis("bottom").hide()
        self._pw.getAxis("left").hide()

        # Tank walls
        self._pw.plot(
            [TANK_X0, TANK_X0, TANK_X1, TANK_X1],
            [3, LIQUID_Y_BOT, LIQUID_Y_BOT, 3],
            pen=pg.mkPen("#585b70", width=2))

        # Liquid fill (LinearRegionItem)
        self._liquid_region = pg.LinearRegionItem(
            values=(LIQUID_Y_BOT, LIQUID_Y_TOP),
            orientation="horizontal",
            movable=False,
            brush=pg.mkBrush(60, 130, 200, 80),
            pen=pg.mkPen(None),
        )
        self._pw.addItem(self._liquid_region)

        # Surface line
        self._pw.addItem(pg.InfiniteLine(
            pos=LIQUID_Y_TOP, angle=0,
            pen=pg.mkPen("#89b4fa", width=2)))

        # Block (filled rectangle via PlotDataItem filled curve)
        self._block_item = pg.PlotDataItem(
            fillLevel=None,
            pen=pg.mkPen("#f9e2af", width=2),
            brush=pg.mkBrush(249, 226, 175, 180),
        )
        self._pw.addItem(self._block_item)

        # Force arrows as thick lines + arrowheads
        self._arrow_W = pg.PlotDataItem(pen=pg.mkPen("#f38ba8", width=4))   # weight ↓
        self._arrow_F = pg.PlotDataItem(pen=pg.mkPen("#a6e3a1", width=4))   # buoy  ↑
        self._arrow_N = pg.PlotDataItem(pen=pg.mkPen("#cba6f7", width=3))   # net
        self._pw.addItem(self._arrow_W)
        self._pw.addItem(self._arrow_F)
        self._pw.addItem(self._arrow_N)

        # Labels
        self._lbl_W_plot = pg.TextItem("", color="#f38ba8", anchor=(0, 0.5))
        self._lbl_F_plot = pg.TextItem("", color="#a6e3a1", anchor=(0, 0.5))
        self._lbl_status = pg.TextItem("", color="#f9e2af", anchor=(0.5, 0))
        self._pw.addItem(self._lbl_W_plot)
        self._pw.addItem(self._lbl_F_plot)
        self._pw.addItem(self._lbl_status)

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        # Liquid selector
        liq_box = QGroupBox("Жидкость")
        liq_lay = QVBoxLayout(liq_box)
        self._cb_liquid = QComboBox()
        self._cb_liquid.addItems(LIQUID_NAMES)
        self._cb_liquid.currentIndexChanged.connect(self._update)
        liq_lay.addWidget(self._cb_liquid)
        ctrl.addWidget(liq_box)

        # Block density slider
        rho_box = QGroupBox("Плотность тела ρ_тела (кг/м³)")
        rho_lay = QVBoxLayout(rho_box)
        self._lbl_rho = QLabel("ρ = 800 кг/м³")
        self._lbl_rho.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_rho = QSlider(Qt.Orientation.Horizontal)
        self._sl_rho.setRange(100, 20000)
        self._sl_rho.setValue(800)
        self._sl_rho.valueChanged.connect(self._update)
        rho_lay.addWidget(self._lbl_rho)
        rho_lay.addWidget(self._sl_rho)
        ctrl.addWidget(rho_box)

        # Volume slider
        v_box = QGroupBox("Объём тела V (дм³)")
        v_lay = QVBoxLayout(v_box)
        self._lbl_vol = QLabel("V = 1.0 дм³")
        self._lbl_vol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_vol = QSlider(Qt.Orientation.Horizontal)
        self._sl_vol.setRange(1, 20)
        self._sl_vol.setValue(10)
        self._sl_vol.valueChanged.connect(self._update)
        v_lay.addWidget(self._lbl_vol)
        v_lay.addWidget(self._sl_vol)
        ctrl.addWidget(v_box)

        # Readout
        info_box = QGroupBox("Силы")
        info_lay = QVBoxLayout(info_box)
        self._lbl_weight = QLabel()
        self._lbl_buoy = QLabel()
        self._lbl_net = QLabel()
        self._lbl_state = QLabel()
        self._lbl_state.setStyleSheet("font-weight:bold; font-size:14px;")
        for w in (self._lbl_weight, self._lbl_buoy, self._lbl_net, self._lbl_state):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self) -> None:
        rho_body = self._sl_rho.value()          # kg/m³
        V_dm3 = self._sl_vol.value() / 10.0      # dm³ → 0.1 … 2.0 dm³
        V_m3 = V_dm3 * 1e-3                      # m³
        rho_liq = LIQUIDS[self._cb_liquid.currentText()]

        mass = rho_body * V_m3
        W = mass * G
        F_b = rho_liq * V_m3 * G
        F_net = W - F_b   # positive = sinks

        self._lbl_rho.setText(f"ρ = {rho_body} кг/м³")
        self._lbl_vol.setText(f"V = {V_dm3:.1f} дм³")
        self._lbl_weight.setText(f"Сила тяжести W = {W:.2f} Н ↓")
        self._lbl_buoy.setText(f"Сила Архимеда F = {F_b:.2f} Н ↑")
        self._lbl_net.setText(f"Равнодействующая = {F_net:.2f} Н")

        # Determine block y position
        if rho_body < rho_liq:
            # floats: fraction submerged = rho_body/rho_liq
            frac = rho_body / rho_liq
            block_top = BLOCK_H * (1 - frac)
            state = "🟢 Плавает"
            state_color = "#a6e3a1"
        elif rho_body == rho_liq:
            block_top = 0.0
            state = "🟡 Взвешено"
            state_color = "#f9e2af"
        else:
            # sinks to bottom
            block_top = LIQUID_Y_BOT + BLOCK_H
            state = "🔴 Тонет"
            state_color = "#f38ba8"

        self._lbl_state.setText(state)
        self._lbl_state.setStyleSheet(f"font-weight:bold; font-size:14px; color:{state_color};")

        bx0 = -BLOCK_W / 2
        bx1 = BLOCK_W / 2
        by0 = block_top - BLOCK_H
        by1 = block_top
        self._block_item.setData(
            [bx0, bx1, bx1, bx0, bx0],
            [by0, by0, by1, by1, by0],
        )
        self._block_item.setFillLevel(by0)

        # Arrows (scaled)
        scale = 0.015
        cx = 0.0
        cy_centre = (by0 + by1) / 2
        # Weight arrow: down from centre
        W_len = W * scale
        self._arrow_W.setData([cx, cx], [cy_centre, cy_centre - W_len])
        self._lbl_W_plot.setText(f"W={W:.1f}Н")
        self._lbl_W_plot.setPos(cx + 0.2, cy_centre - W_len / 2)
        # Buoyancy: up
        F_len = F_b * scale
        self._arrow_F.setData([cx, cx], [cy_centre, cy_centre + F_len])
        self._lbl_F_plot.setText(f"F={F_b:.1f}Н")
        self._lbl_F_plot.setPos(cx + 0.2, cy_centre + F_len / 2)
        # Net (offset slightly)
        N_len = F_net * scale
        self._arrow_N.setData([cx - 0.3, cx - 0.3], [cy_centre, cy_centre - N_len])

        self._lbl_status.setText(state)
        self._lbl_status.setPos(0, LIQUID_Y_BOT - 0.5)

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Закон Архимеда и плавание тел", ArchimedesWidget)
