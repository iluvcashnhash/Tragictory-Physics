"""
Magnetic field visualisation widget for Tragictory Physics.

Shows the magnetic field lines of a straight current-carrying wire
and of two parallel wires (attraction/repulsion) using a vector field
rendered with pg.ImageItem arrows.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


GRID_N: int = 30
HALF: float = 5.0


class MagneticFieldWidget(QWidget):
    """Magnetic field B of one or two current-carrying wires.

    Renders field vectors as a quiver-style scatter with arrow colour
    encoding magnitude; wire positions shown as coloured dots.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._update()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setAspectLocked(True)
        self._pw.setMouseEnabled(False, False)
        self._pw.setXRange(-HALF, HALF, padding=0)
        self._pw.setYRange(-HALF, HALF, padding=0)
        self._pw.getAxis("bottom").hide()
        self._pw.getAxis("left").hide()

        # Field vectors as scatter (colour-coded by magnitude)
        self._arrows = pg.ScatterPlotItem(pen=pg.mkPen(None))
        self._pw.addItem(self._arrows)

        # Field lines (stream-line style circles for single wire)
        self._field_lines: list[pg.PlotDataItem] = []
        for r in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]:
            theta = np.linspace(0, 2 * math.pi, 80)
            item = self._pw.plot(
                (r * np.cos(theta)).tolist(),
                (r * np.sin(theta)).tolist(),
                pen=pg.mkPen("#89b4fa40", width=1))
            self._field_lines.append(item)

        # Wire markers
        self._wire1 = self._pw.plot(
            pen=None, symbol="o", symbolSize=14,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen("#ffffff", width=1))
        self._wire2 = self._pw.plot(
            pen=None, symbol="o", symbolSize=14,
            symbolBrush="#a6e3a1", symbolPen=pg.mkPen("#ffffff", width=1))

        # Force arrow between wires
        self._force_arrow = self._pw.plot(pen=pg.mkPen("#f9e2af", width=3))
        self._force_label = pg.TextItem("", color="#f9e2af", anchor=(0.5, 1))
        self._pw.addItem(self._force_label)

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        mode_box = QGroupBox("Конфигурация")
        mode_lay = QVBoxLayout(mode_box)
        self._cb_mode = QComboBox()
        self._cb_mode.addItems(["Один провод", "Два провода (параллельные токи)",
                                 "Два провода (антипараллельные токи)"])
        self._cb_mode.currentIndexChanged.connect(self._update)
        mode_lay.addWidget(self._cb_mode)
        ctrl.addWidget(mode_box)

        I1_box = QGroupBox("Ток I₁ (А)")
        I1_lay = QVBoxLayout(I1_box)
        self._lbl_I1 = QLabel("I₁ = 5 А")
        self._lbl_I1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_I1 = QSlider(Qt.Orientation.Horizontal)
        self._sl_I1.setRange(1, 20)
        self._sl_I1.setValue(5)
        self._sl_I1.valueChanged.connect(self._update)
        I1_lay.addWidget(self._lbl_I1)
        I1_lay.addWidget(self._sl_I1)
        ctrl.addWidget(I1_box)

        I2_box = QGroupBox("Ток I₂ (А)")
        I2_lay = QVBoxLayout(I2_box)
        self._lbl_I2 = QLabel("I₂ = 5 А")
        self._lbl_I2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_I2 = QSlider(Qt.Orientation.Horizontal)
        self._sl_I2.setRange(1, 20)
        self._sl_I2.setValue(5)
        self._sl_I2.valueChanged.connect(self._update)
        I2_lay.addWidget(self._lbl_I2)
        I2_lay.addWidget(self._sl_I2)
        ctrl.addWidget(I2_box)

        info_box = QGroupBox("Поле")
        info_lay = QVBoxLayout(info_box)
        self._lbl_info = QLabel()
        self._lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_info.setStyleSheet("color:#cba6f7; font-style:italic;")
        info_lay.addWidget(self._lbl_info)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Field computation ─────────────────────────────────────────────────────

    def _B_wire(self, gx: np.ndarray, gy: np.ndarray,
                wx: float, wy: float, I: float) -> tuple[np.ndarray, np.ndarray]:
        """Return (Bx, By) from a wire at (wx,wy) with current I (out of page)."""
        dx = gx - wx
        dy = gy - wy
        r2 = dx**2 + dy**2 + 1e-4
        # B = μ₀I/(2πr) in direction (-dy, dx)/r
        factor = I / r2
        return -dy * factor, dx * factor

    def _update(self) -> None:
        I1 = self._sl_I1.value()
        I2 = self._sl_I2.value()
        mode = self._cb_mode.currentIndex()

        self._lbl_I1.setText(f"I₁ = {I1} А")
        self._lbl_I2.setText(f"I₂ = {I2} А")

        lin = np.linspace(-HALF * 0.9, HALF * 0.9, GRID_N)
        GX, GY = np.meshgrid(lin, lin)
        gx = GX.ravel()
        gy = GY.ravel()

        if mode == 0:
            Bx, By = self._B_wire(gx, gy, 0.0, 0.0, I1)
            self._wire1.setData([0], [0])
            self._wire2.setData([], [])
            self._force_arrow.setData([], [])
            self._force_label.setText("")
            for line in self._field_lines:
                line.setVisible(True)
            self._lbl_info.setText("B = μ₀I / (2πr)\nКонцентрические окружности")
        else:
            sep = 2.0
            I2_sign = I2 if mode == 1 else -I2
            Bx1, By1 = self._B_wire(gx, gy, -sep, 0.0, I1)
            Bx2, By2 = self._B_wire(gx, gy,  sep, 0.0, I2_sign)
            Bx = Bx1 + Bx2
            By = By1 + By2
            self._wire1.setData([-sep], [0])
            self._wire2.setData([ sep], [0])
            for line in self._field_lines:
                line.setVisible(False)
            # Force direction
            if mode == 1:
                fx = [sep * 0.6, sep * 0.3]
                fy = [0, 0]
                self._force_label.setText("← Притяжение →")
                self._lbl_info.setText("Параллельные токи\nПРИТЯГИВАЮТСЯ")
            else:
                fx = [sep * 0.3, sep * 0.8]
                fy = [0, 0]
                self._force_label.setText("→ Отталкивание ←")
                self._lbl_info.setText("Антипараллельные токи\nОТТАЛКИВАЮТСЯ")
            self._force_arrow.setData(fx, fy)
            self._force_label.setPos(0, 0.5)

        # Normalise for display
        B_mag = np.sqrt(Bx**2 + By**2)
        B_max = np.percentile(B_mag, 95)
        if B_max < 1e-9:
            return
        scale = 0.3 * HALF * 2 / GRID_N / B_max
        Bx_n = np.clip(Bx * scale, -0.8, 0.8)
        By_n = np.clip(By * scale, -0.8, 0.8)

        # Colour by magnitude (clipped)
        mag_norm = np.clip(B_mag / B_max, 0, 1)
        brushes = [pg.mkBrush(
            int(50 + 150 * m), int(130 + 80 * (1 - m)), int(200 * (1 - m) + 50), 180)
            for m in mag_norm]

        spots = [{"pos": (float(gx[i] + Bx_n[i] * 0.5),
                          float(gy[i] + By_n[i] * 0.5)),
                  "brush": brushes[i], "size": 4}
                 for i in range(len(gx))]
        self._arrows.setData(spots)

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Магнитное поле и опыт Эрстеда", MagneticFieldWidget)
