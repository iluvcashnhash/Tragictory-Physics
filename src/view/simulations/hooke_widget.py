"""
Hooke's law interactive widget for Tragictory Physics.

Draws an animated spring and hanging mass. Dragging the force slider
stretches the spring in real time; the graph shows F vs x (linear plot).
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


# Spring materials with different k values (N/m)
SPRINGS: dict[str, float] = {
    "Мягкая пружина   k = 10 Н/м":  10.0,
    "Средняя пружина  k = 30 Н/м":  30.0,
    "Жёсткая пружина  k = 80 Н/м":  80.0,
}
SPRING_NAMES = list(SPRINGS.keys())

F_MAX: float = 100.0    # N
X_MAX: float = 12.0     # m, for graph axis


class HookeWidget(QWidget):
    """Hooke's law visualiser: F = k·x.

    Left pane: animated spring & hanging weight.
    Right panel: F-x graph with current state dot and elastic limit marker.
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

        # Two side-by-side plots
        plots = QHBoxLayout()

        # Left: spring animation
        self._pw_spring = pg.PlotWidget()
        self._pw_spring.setBackground("#1e1e2e")
        self._pw_spring.setAspectLocked(False)
        self._pw_spring.setMouseEnabled(False, False)
        self._pw_spring.setXRange(-3, 3, padding=0)
        self._pw_spring.setYRange(-14, 1, padding=0)
        self._pw_spring.getAxis("bottom").hide()
        self._pw_spring.getAxis("left").hide()

        # Ceiling
        self._pw_spring.plot([-2, 2], [0, 0], pen=pg.mkPen("#cdd6f4", width=3))
        self._spring_line = self._pw_spring.plot(pen=pg.mkPen("#a6e3a1", width=2))
        self._mass_item = self._pw_spring.plot(
            pen=None, symbol="s", symbolSize=30,
            symbolBrush="#89b4fa", symbolPen=pg.mkPen(None))
        self._lbl_x_plot = pg.TextItem("", color="#fab387", anchor=(0, 0.5))
        self._pw_spring.addItem(self._lbl_x_plot)
        plots.addWidget(self._pw_spring, stretch=1)

        # Right: F-x graph
        self._pw_graph = pg.PlotWidget()
        self._pw_graph.setBackground("#1e1e2e")
        self._pw_graph.setLabel("bottom", "x, м")
        self._pw_graph.setLabel("left", "F, Н")
        self._pw_graph.showGrid(x=True, y=True, alpha=0.25)
        self._pw_graph.setXRange(0, X_MAX, padding=0.05)
        self._pw_graph.setYRange(0, F_MAX + 10, padding=0)

        self._hooke_line = self._pw_graph.plot(pen=pg.mkPen("#a6e3a1", width=2))
        self._elastic_limit = pg.InfiniteLine(
            pos=0, angle=90,
            pen=pg.mkPen("#f9e2af", width=1, style=Qt.PenStyle.DashLine),
            label="Предел упругости", labelOpts={"color": "#f9e2af", "position": 0.8})
        self._pw_graph.addItem(self._elastic_limit)
        self._dot = self._pw_graph.plot(
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

        # Spring selector
        sp_box = QGroupBox("Тип пружины")
        sp_lay = QVBoxLayout(sp_box)
        self._cb_spring = QComboBox()
        self._cb_spring.addItems(SPRING_NAMES)
        self._cb_spring.setCurrentIndex(1)
        self._cb_spring.currentIndexChanged.connect(self._update)
        sp_lay.addWidget(self._cb_spring)
        ctrl.addWidget(sp_box)

        # Force slider
        f_box = QGroupBox("Приложенная сила F (Н)")
        f_lay = QVBoxLayout(f_box)
        self._lbl_F = QLabel("F = 30 Н")
        self._lbl_F.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_F = QSlider(Qt.Orientation.Horizontal)
        self._sl_F.setRange(0, int(F_MAX))
        self._sl_F.setValue(30)
        self._sl_F.valueChanged.connect(self._update)
        f_lay.addWidget(self._lbl_F)
        f_lay.addWidget(self._sl_F)
        ctrl.addWidget(f_box)

        # Readout
        info_box = QGroupBox("Результат")
        info_lay = QVBoxLayout(info_box)
        self._lbl_k = QLabel()
        self._lbl_x = QLabel()
        self._lbl_regime = QLabel()
        self._lbl_regime.setStyleSheet("font-weight:bold;")
        for w in (self._lbl_k, self._lbl_x, self._lbl_regime):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        hint = QLabel("F = k · x")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#888; font-style:italic; font-size:16px;")
        ctrl.addWidget(hint)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self) -> None:
        k = SPRINGS[self._cb_spring.currentText()]
        F = float(self._sl_F.value())
        x = F / k   # extension in metres

        # Elastic limit: assume it's at 2/3 of X_MAX for this k
        x_limit = X_MAX * 0.6

        self._lbl_F.setText(f"F = {F:.0f} Н")
        self._lbl_k.setText(f"k = {k:.0f} Н/м")
        self._lbl_x.setText(f"x = F/k = {x:.2f} м")

        if x <= x_limit:
            self._lbl_regime.setText("🟢 Упругая деформация")
            self._lbl_regime.setStyleSheet("font-weight:bold; color:#a6e3a1;")
            dot_color = "#f38ba8"
        else:
            self._lbl_regime.setText("🔴 Пластическая деформация!")
            self._lbl_regime.setStyleSheet("font-weight:bold; color:#f38ba8;")
            dot_color = "#f9e2af"

        # Hooke line
        xs = np.linspace(0, X_MAX, 200)
        Fs = k * xs
        self._hooke_line.setData(xs, Fs)
        self._elastic_limit.setValue(x_limit)
        self._dot.setData([x], [F])
        self._dot.setSymbolBrush(pg.mkBrush(dot_color))

        # Spring animation: zigzag from y=0 to y=-x (scaled for display)
        display_len = min(x, 10.0)
        n_coils = 12
        zz_x = []
        zz_y = []
        for i in range(n_coils * 4 + 1):
            t = i / (n_coils * 4)
            zz_y.append(-t * display_len)
            phase = i % 4
            if phase == 0:
                zz_x.append(0.0)
            elif phase == 1:
                zz_x.append(1.2)
            elif phase == 2:
                zz_x.append(0.0)
            else:
                zz_x.append(-1.2)
        self._spring_line.setData(zz_x, zz_y)

        mass_y = -display_len - 1.5
        self._mass_item.setData([0], [mass_y])
        self._lbl_x_plot.setPos(1.5, -display_len / 2)
        self._lbl_x_plot.setText(f"x={x:.1f}м")

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Сила упругости и закон Гука", HookeWidget)
