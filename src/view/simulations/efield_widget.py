"""
Electric potential field visualisation widget for Tragictory Physics.

Renders the scalar potential φ = k·q₁/r₁ + k·q₂/r₂ as a heatmap using
pg.ImageItem with a diverging colormap, with charge positions overlaid.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QFormLayout,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


K_E: float = 8.99e9     # N·m²/C²  (not used numerically — normalised)
GRID_N: int = 120       # grid resolution
HALF: float = 5.0       # half-extent of the domain (arbitrary units)
CLIP_VAL: float = 15.0  # clip potential to ±this for colormap


class EFieldWidget(QWidget):
    """Electric potential heatmap for two point charges.

    The colormap uses red for high potential (positive) and blue for low
    (negative). Charge positions are shown as overlaid scatter points.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the widget and render the initial field."""
        super().__init__(parent)
        self._build_ui()
        self._update()

    # ── Grid ─────────────────────────────────────────────────────────────────

    def _make_grid(self) -> tuple[np.ndarray, np.ndarray]:
        lin = np.linspace(-HALF, HALF, GRID_N)
        return np.meshgrid(lin, lin)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Plot
        self._vb = pg.PlotWidget()
        self._vb.setBackground("#1e1e2e")
        self._vb.setAspectLocked(True)
        self._vb.setMouseEnabled(False, False)
        self._vb.getAxis("bottom").hide()
        self._vb.getAxis("left").hide()
        self._vb.setXRange(0, GRID_N, padding=0)
        self._vb.setYRange(0, GRID_N, padding=0)

        # ImageItem for heatmap
        self._img = pg.ImageItem()
        self._vb.addItem(self._img)

        # Colormap: blue → black → red
        cmap = pg.colormap.get("RdBu", source="matplotlib", skipCache=True)
        self._img.setColorMap(cmap)

        # Colorbar
        cb = pg.ColorBarItem(
            values=(-CLIP_VAL, CLIP_VAL),
            colorMap=cmap,
            label="φ (у.е.)",
        )
        cb.setImageItem(self._img)

        # Charge markers
        self._scatter = pg.ScatterPlotItem(size=18, pen=pg.mkPen("#ffffff", width=2))
        self._vb.addItem(self._scatter)

        # Labels q1, q2
        self._lbl_q1_plot = pg.TextItem("q₁", color="#ffffff", anchor=(0.5, 1.5))
        self._lbl_q2_plot = pg.TextItem("q₂", color="#ffffff", anchor=(0.5, 1.5))
        self._vb.addItem(self._lbl_q1_plot)
        self._vb.addItem(self._lbl_q2_plot)

        root.addWidget(self._vb, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        charges_box = QGroupBox("Заряды")
        form = QFormLayout(charges_box)

        self._sl_q1, self._lbl_q1 = self._make_slider(-10, 10, 5)
        self._sl_q2, self._lbl_q2 = self._make_slider(-10, 10, -5)
        self._sl_d, self._lbl_d = self._make_slider(10, 80, 40)

        form.addRow("q₁ (у.е.):", self._lbl_q1)
        form.addRow("", self._sl_q1)
        form.addRow("q₂ (у.е.):", self._lbl_q2)
        form.addRow("", self._sl_q2)
        form.addRow("Расстояние:", self._lbl_d)
        form.addRow("", self._sl_d)

        self._sl_q1.valueChanged.connect(self._update)
        self._sl_q2.valueChanged.connect(self._update)
        self._sl_d.valueChanged.connect(self._update)

        ctrl.addWidget(charges_box)

        # Info
        info_box = QGroupBox("Состояние")
        info_lay = QVBoxLayout(info_box)
        self._lbl_info = QLabel()
        self._lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_info.setStyleSheet("color:#a6e3a1; font-style:italic;")
        info_lay.addWidget(self._lbl_info)
        ctrl.addWidget(info_box)

        hint = QLabel("φ = k·q₁/r₁ + k·q₂/r₂")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#888; font-style:italic;")
        ctrl.addWidget(hint)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    @staticmethod
    def _make_slider(lo: int, hi: int, val: int) -> tuple[QSlider, QLabel]:
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        lbl = QLabel(str(val))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sl, lbl

    # ── Field computation & redraw ────────────────────────────────────────────

    def _update(self) -> None:
        q1 = self._sl_q1.value()
        q2 = self._sl_q2.value()
        d_frac = self._sl_d.value() / 100.0   # fraction of domain width

        self._lbl_q1.setText(f"{q1:+d}")
        self._lbl_q2.setText(f"{q2:+d}")
        self._lbl_d.setText(str(self._sl_d.value()))

        # Charge positions in grid coordinates
        cx = GRID_N / 2
        cy = GRID_N / 2
        sep = d_frac * GRID_N / 2.0
        x1g, y1g = cx - sep, cy
        x2g, y2g = cx + sep, cy

        # Grid in normalised units
        xs = np.linspace(0, GRID_N, GRID_N)
        ys = np.linspace(0, GRID_N, GRID_N)
        XX, YY = np.meshgrid(xs, ys)

        eps = 1.5   # softening to avoid singularity
        r1 = np.sqrt((XX - x1g)**2 + (YY - y1g)**2) + eps
        r2 = np.sqrt((XX - x2g)**2 + (YY - y2g)**2) + eps

        phi = q1 / r1 + q2 / r2
        phi = np.clip(phi, -CLIP_VAL, CLIP_VAL)

        # ImageItem expects (x, y) indexing → transpose
        self._img.setImage(phi.T, levels=(-CLIP_VAL, CLIP_VAL))

        # Charge markers
        brushes = []
        for q in (q1, q2):
            if q > 0:
                brushes.append(pg.mkBrush("#f38ba8"))
            elif q < 0:
                brushes.append(pg.mkBrush("#89b4fa"))
            else:
                brushes.append(pg.mkBrush("#6c7086"))

        self._scatter.setData(
            x=[x1g, x2g], y=[y1g, y2g],
            brush=brushes,
        )
        self._lbl_q1_plot.setPos(x1g, y1g)
        self._lbl_q2_plot.setPos(x2g, y2g)

        config = "одноимённые" if q1 * q2 > 0 else ("разноимённые" if q1 * q2 < 0 else "нейтральные")
        self._lbl_info.setText(f"Заряды: {config}\nq₁={q1:+d}, q₂={q2:+d}")

    # ── Public ────────────────────────────────────────────────────────────────

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Теорема Гаусса в электростатике", EFieldWidget)
