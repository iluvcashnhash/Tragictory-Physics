"""
Heat transfer simulation widget for Tragictory Physics.

Simulates a 1-D temperature distribution for conduction, convection, and
radiation modes. The colour bar shows the temperature gradient in real time.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


TIMER_MS: int = 30
N: int = 100           # grid cells
L: float = 1.0         # rod length, metres
DX: float = L / N
DT_SIM: float = 0.001  # simulation seconds per real step


MODES = ["Теплопроводность", "Конвекция (жидкость)", "Излучение (Стефан–Больцман)"]

# Thermal diffusivity α = k/(ρc) for conduction modes
MATERIALS: dict[str, float] = {
    "Медь    α = 1.17·10⁻⁴":   1.17e-4,
    "Сталь   α = 1.20·10⁻⁵":   1.20e-5,
    "Стекло  α = 3.40·10⁻⁷":   3.40e-7,
}
MAT_NAMES = list(MATERIALS.keys())
SIGMA: float = 5.67e-8   # Stefan-Boltzmann constant


class HeatTransferWidget(QWidget):
    """1-D heat equation visualiser for three transfer modes.

    Conduction: ∂T/∂t = α·∂²T/∂x²
    Convection: ∂T/∂t = −v·∂T/∂x  (advection)
    Radiation:  dT/dt = −ε·σ·T⁴/ρc (simplified)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise temperature profile and start animation."""
        super().__init__(parent)
        self._build_ui()
        self._reset()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    # ── Init ─────────────────────────────────────────────────────────────────

    def _reset(self) -> None:
        """Set initial temperature profile: hot left wall, cool right wall."""
        T_hot = float(self._sl_Thot.value())
        T_cold = float(self._sl_Tcold.value())
        self._T = np.linspace(T_hot, T_cold, N)
        self._t_sim: float = 0.0

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        plots = QVBoxLayout()
        plots.setSpacing(4)

        # Temperature profile plot
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setLabel("bottom", "x, м")
        self._pw.setLabel("left", "T, K")
        self._pw.showGrid(x=True, y=True, alpha=0.25)
        self._curve = self._pw.plot(pen=pg.mkPen("#f38ba8", width=2))
        plots.addWidget(self._pw, stretch=2)

        # Heatmap strip
        self._pw_map = pg.PlotWidget()
        self._pw_map.setBackground("#1e1e2e")
        self._pw_map.setMouseEnabled(False, False)
        self._pw_map.setFixedHeight(60)
        self._pw_map.getAxis("left").hide()
        self._pw_map.getAxis("bottom").hide()
        self._img = pg.ImageItem()
        self._pw_map.addItem(self._img)
        cmap = pg.colormap.get("plasma", source="matplotlib", skipCache=True)
        self._img.setColorMap(cmap)
        plots.addWidget(self._pw_map, stretch=1)

        root.addLayout(plots, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        mode_box = QGroupBox("Режим")
        mode_lay = QVBoxLayout(mode_box)
        self._cb_mode = QComboBox()
        self._cb_mode.addItems(MODES)
        self._cb_mode.currentIndexChanged.connect(self._on_mode)
        mode_lay.addWidget(self._cb_mode)
        ctrl.addWidget(mode_box)

        self._mat_box = QGroupBox("Материал (теплопроводность)")
        mat_lay = QVBoxLayout(self._mat_box)
        self._cb_mat = QComboBox()
        self._cb_mat.addItems(MAT_NAMES)
        mat_lay.addWidget(self._cb_mat)
        ctrl.addWidget(self._mat_box)

        Th_box = QGroupBox("T горячей стороны (K)")
        Th_lay = QVBoxLayout(Th_box)
        self._lbl_Thot = QLabel("T = 600 K")
        self._lbl_Thot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_Thot = QSlider(Qt.Orientation.Horizontal)
        self._sl_Thot.setRange(300, 1500)
        self._sl_Thot.setValue(600)
        self._sl_Thot.valueChanged.connect(self._on_change)
        Th_lay.addWidget(self._lbl_Thot)
        Th_lay.addWidget(self._sl_Thot)
        ctrl.addWidget(Th_box)

        Tc_box = QGroupBox("T холодной стороны (K)")
        Tc_lay = QVBoxLayout(Tc_box)
        self._lbl_Tcold = QLabel("T = 300 K")
        self._lbl_Tcold.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_Tcold = QSlider(Qt.Orientation.Horizontal)
        self._sl_Tcold.setRange(100, 600)
        self._sl_Tcold.setValue(300)
        self._sl_Tcold.valueChanged.connect(self._on_change)
        Tc_lay.addWidget(self._lbl_Tcold)
        Tc_lay.addWidget(self._sl_Tcold)
        ctrl.addWidget(Tc_box)

        reset_btn = QPushButton("↺ Сбросить")
        reset_btn.clicked.connect(self._reset)
        ctrl.addWidget(reset_btn)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    def _on_mode(self, idx: int) -> None:
        self._mat_box.setVisible(idx == 0)
        self._reset()

    def _on_change(self) -> None:
        self._lbl_Thot.setText(f"T = {self._sl_Thot.value()} K")
        self._lbl_Tcold.setText(f"T = {self._sl_Tcold.value()} K")
        self._reset()

    # ── Step ─────────────────────────────────────────────────────────────────

    def _step(self) -> None:
        mode = self._cb_mode.currentIndex()
        T_hot = float(self._sl_Thot.value())
        T_cold = float(self._sl_Tcold.value())

        if mode == 0:   # Conduction
            alpha = MATERIALS[self._cb_mat.currentText()]
            r = alpha * DT_SIM / DX**2
            r = min(r, 0.4)   # stability
            new_T = self._T.copy()
            new_T[1:-1] += r * (self._T[2:] - 2*self._T[1:-1] + self._T[:-2])
            new_T[0] = T_hot
            new_T[-1] = T_cold
            self._T = new_T

        elif mode == 1: # Convection (advection)
            v = 0.1
            new_T = self._T.copy()
            new_T[1:] -= v * DT_SIM / DX * (self._T[1:] - self._T[:-1])
            new_T[0] = T_hot
            self._T = new_T

        else:           # Radiation
            eps = 0.9
            rho_c = 1e6
            dT = -eps * SIGMA * self._T**4 / rho_c * DT_SIM * 500
            self._T = np.clip(self._T + dT, 100.0, 2000.0)
            self._T[0] = T_hot

        xs = np.linspace(0, L, N)
        self._curve.setData(xs, self._T)
        self._pw.setYRange(min(T_cold - 50, 50), T_hot + 50, padding=0)

        # Heatmap
        T_norm = (self._T - 100) / 1400.0
        T_norm = np.clip(T_norm, 0, 1)
        img_row = (T_norm * 255).astype(np.uint8)
        img_2d = np.tile(img_row, (20, 1))
        self._img.setImage(img_2d.T)
        self._img.setRect(0, 0, N, 20)

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
register_simulation("Виды теплопередачи", HeatTransferWidget)
