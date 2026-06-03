"""
Friction simulation widget for Tragictory Physics.

Animates a block sliding across a surface. Shows applied force,
friction force, and resulting motion. F-t and v-t plots update in real time.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg


G: float = 9.81
TIMER_MS: int = 30
DT: float = TIMER_MS / 1000.0
TRAIL_MAX: int = 200

SURFACES: dict[str, tuple[float, float]] = {
    "Лёд       μ = 0.03":      (0.03, 0.02),
    "Дерево    μ = 0.30":      (0.30, 0.25),
    "Резина    μ = 0.70":      (0.70, 0.60),
    "Бетон     μ = 0.55":      (0.55, 0.45),
}
SURFACE_NAMES = list(SURFACES.keys())


class FrictionWidget(QWidget):
    """Block sliding simulation with static and kinetic friction.

    Animated scene on the left; F-t and v-t graphs on the right.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise simulation state and start timer."""
        super().__init__(parent)
        self._t: float = 0.0
        self._v: float = 0.0
        self._x: float = 0.0
        self._t_hist: list[float] = []
        self._v_hist: list[float] = []
        self._build_ui()

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

        # Scene
        self._pw_scene = pg.PlotWidget()
        self._pw_scene.setBackground("#1e1e2e")
        self._pw_scene.setMouseEnabled(False, False)
        self._pw_scene.setXRange(-10, 10, padding=0)
        self._pw_scene.setYRange(-1.5, 3.5, padding=0)
        self._pw_scene.getAxis("bottom").hide()
        self._pw_scene.getAxis("left").hide()
        # Ground
        self._pw_scene.plot([-10, 10], [0, 0], pen=pg.mkPen("#585b70", width=3))
        # Block
        self._block = pg.PlotDataItem(
            pen=pg.mkPen("#89b4fa", width=2),
            brush=pg.mkBrush(137, 180, 250, 180),
            fillLevel=0,
        )
        self._pw_scene.addItem(self._block)
        # Applied force arrow
        self._arrow_F = self._pw_scene.plot(pen=pg.mkPen("#f38ba8", width=3))
        # Friction arrow
        self._arrow_f = self._pw_scene.plot(pen=pg.mkPen("#a6e3a1", width=3))
        # Labels
        self._lbl_F_scene = pg.TextItem("F", color="#f38ba8", anchor=(0, 1))
        self._lbl_f_scene = pg.TextItem("f", color="#a6e3a1", anchor=(1, 1))
        self._pw_scene.addItem(self._lbl_F_scene)
        self._pw_scene.addItem(self._lbl_f_scene)

        left.addWidget(self._pw_scene, stretch=1)

        # v-t graph
        self._pw_v = pg.PlotWidget()
        self._pw_v.setBackground("#1e1e2e")
        self._pw_v.setLabel("left", "v, м/с")
        self._pw_v.setLabel("bottom", "t, с")
        self._pw_v.showGrid(x=True, y=True, alpha=0.25)
        self._pw_v.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen("#585b70")))
        self._curve_v = self._pw_v.plot(pen=pg.mkPen("#89b4fa", width=2))
        left.addWidget(self._pw_v, stretch=1)

        root.addLayout(left, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        surf_box = QGroupBox("Поверхность")
        surf_lay = QVBoxLayout(surf_box)
        self._cb_surf = QComboBox()
        self._cb_surf.addItems(SURFACE_NAMES)
        self._cb_surf.setCurrentIndex(1)
        self._cb_surf.currentIndexChanged.connect(self._reset)
        surf_lay.addWidget(self._cb_surf)
        ctrl.addWidget(surf_box)

        mass_box = QGroupBox("Масса тела (кг)")
        mass_lay = QVBoxLayout(mass_box)
        self._lbl_mass = QLabel("m = 5 кг")
        self._lbl_mass.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_mass = QSlider(Qt.Orientation.Horizontal)
        self._sl_mass.setRange(1, 50)
        self._sl_mass.setValue(5)
        self._sl_mass.valueChanged.connect(self._reset)
        mass_lay.addWidget(self._lbl_mass)
        mass_lay.addWidget(self._sl_mass)
        ctrl.addWidget(mass_box)

        F_box = QGroupBox("Сила тяги F (Н)")
        F_lay = QVBoxLayout(F_box)
        self._lbl_Fapp = QLabel("F = 20 Н")
        self._lbl_Fapp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_Fapp = QSlider(Qt.Orientation.Horizontal)
        self._sl_Fapp.setRange(0, 200)
        self._sl_Fapp.setValue(20)
        self._sl_Fapp.valueChanged.connect(self._reset)
        F_lay.addWidget(self._lbl_Fapp)
        F_lay.addWidget(self._sl_Fapp)
        ctrl.addWidget(F_box)

        info_box = QGroupBox("Силы")
        info_lay = QVBoxLayout(info_box)
        self._lbl_fric = QLabel()
        self._lbl_net = QLabel()
        self._lbl_acc = QLabel()
        self._lbl_motion = QLabel()
        self._lbl_motion.setStyleSheet("font-weight:bold;")
        for w in (self._lbl_fric, self._lbl_net, self._lbl_acc, self._lbl_motion):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    def _reset(self) -> None:
        self._t = 0.0
        self._v = 0.0
        self._x = 0.0
        self._t_hist.clear()
        self._v_hist.clear()

    # ── Step ─────────────────────────────────────────────────────────────────

    def _step(self) -> None:
        m = self._sl_mass.value()
        F_app = float(self._sl_Fapp.value())
        mu_s, mu_k = SURFACES[self._cb_surf.currentText()]
        N = m * G
        f_static_max = mu_s * N
        f_kinetic = mu_k * N

        self._lbl_mass.setText(f"m = {m} кг")
        self._lbl_Fapp.setText(f"F = {F_app:.0f} Н")

        # Determine friction and acceleration
        if self._v == 0.0:
            if F_app <= f_static_max:
                f = F_app   # static friction exactly balances
                a = 0.0
                motion = "⛔ Покой (статическое трение)"
                motion_color = "#f9e2af"
            else:
                f = f_kinetic
                a = (F_app - f) / m
                motion = "▶ Движение"
                motion_color = "#a6e3a1"
        else:
            f = f_kinetic
            a = (F_app - f) / m
            if a < 0 and self._v + a * DT < 0:
                a = -self._v / DT   # stop without reversing
            motion = "▶ Движение" if self._v > 0 else "⛔ Остановка"
            motion_color = "#a6e3a1" if self._v > 0 else "#f9e2af"

        self._lbl_fric.setText(f"f_тр = {f:.1f} Н")
        self._lbl_net.setText(f"F_рез = {F_app - f:.1f} Н")
        self._lbl_acc.setText(f"a = {a:.2f} м/с²")
        self._lbl_motion.setText(motion)
        self._lbl_motion.setStyleSheet(f"font-weight:bold; color:{motion_color};")

        self._v = max(0.0, self._v + a * DT)
        self._x += self._v * DT
        self._t += DT

        # Wrap block position
        bx = (self._x % 20.0) - 10.0
        self._block.setData(
            [bx - 1, bx + 1, bx + 1, bx - 1, bx - 1],
            [0, 0, 2, 2, 0])

        scale = 0.05
        F_len = F_app * scale
        f_len = f * scale
        self._arrow_F.setData([bx + 1, bx + 1 + F_len], [1, 1])
        self._arrow_f.setData([bx - 1, bx - 1 - f_len], [1, 1])
        self._lbl_F_scene.setPos(bx + 1 + F_len, 1)
        self._lbl_f_scene.setPos(bx - 1 - f_len, 1)

        self._t_hist.append(self._t)
        self._v_hist.append(self._v)
        if len(self._t_hist) > TRAIL_MAX:
            self._t_hist.pop(0)
            self._v_hist.pop(0)
        self._curve_v.setData(self._t_hist, self._v_hist)

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
register_simulation("Сила трения", FrictionWidget)
