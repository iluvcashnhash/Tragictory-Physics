"""
Optics simulation widget for Tragictory Physics.

Visualises Snell's law of refraction in real time: incident, reflected, and
refracted rays at a planar interface between two media, including total internal
reflection.
"""

import math
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QComboBox,
    QGroupBox, QPushButton,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


# ── Layout constants (plot units) ──────────────────────────────────────────────
RAY_LEN: float = 80.0      # length of each ray segment in plot units
PLOT_RANGE: float = 100.0  # half-extent of the square viewport

# ── Media library ──────────────────────────────────────────────────────────────
MEDIA: dict[str, float] = {
    "Вакуум  (n = 1.000)": 1.000,
    "Воздух  (n = 1.003)": 1.0003,
    "Вода    (n = 1.330)": 1.33,
    "Стекло  (n = 1.500)": 1.50,
    "Алмаз   (n = 2.417)": 2.417,
}
MEDIA_NAMES: list[str] = list(MEDIA.keys())


class OpticsWidget(QWidget):
    """Interactive Snell's-law refraction simulation.

    Displays incident, reflected, and refracted rays at a horizontal interface.
    Handles total internal reflection by hiding the refracted ray.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise widget and draw the initial ray configuration."""
        super().__init__(parent)
        self._build_ui()
        self._update()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build two-pane layout: plot left, controls right."""
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # ── Plot ──────────────────────────────────────────────────────────────
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setAspectLocked(True)
        self._pw.setMouseEnabled(False, False)
        self._pw.showGrid(x=False, y=False)
        self._pw.getAxis("bottom").hide()
        self._pw.getAxis("left").hide()
        self._pw.setXRange(-PLOT_RANGE, PLOT_RANGE, padding=0)
        self._pw.setYRange(-PLOT_RANGE, PLOT_RANGE, padding=0)

        # Medium background rectangles
        upper_bg = pg.LinearRegionItem(
            values=(-PLOT_RANGE, PLOT_RANGE),
            orientation="horizontal",
            movable=False,
            brush=pg.mkBrush(80, 80, 90, 60),
            pen=pg.mkPen(None),
        )
        upper_bg.setRegion((0, PLOT_RANGE))
        self._pw.addItem(upper_bg)

        lower_bg = pg.LinearRegionItem(
            values=(-PLOT_RANGE, 0),
            orientation="horizontal",
            movable=False,
            brush=pg.mkBrush(60, 100, 140, 60),
            pen=pg.mkPen(None),
        )
        lower_bg.setRegion((-PLOT_RANGE, 0))
        self._pw.addItem(lower_bg)

        # Interface line (y = 0)
        self._pw.addItem(pg.InfiniteLine(
            pos=0, angle=0,
            pen=pg.mkPen("#cdd6f4", width=2),
        ))

        # Normal (dashed vertical)
        self._pw.addItem(pg.InfiniteLine(
            pos=0, angle=90,
            pen=pg.mkPen("#585b70", width=1, style=Qt.PenStyle.DashLine),
        ))

        # Media labels
        self._lbl_n1_plot = pg.TextItem("Среда 1", color="#cdd6f4", anchor=(0, 1))
        self._lbl_n1_plot.setPos(-PLOT_RANGE + 4, PLOT_RANGE - 4)
        self._pw.addItem(self._lbl_n1_plot)

        self._lbl_n2_plot = pg.TextItem("Среда 2", color="#89dceb", anchor=(0, 0))
        self._lbl_n2_plot.setPos(-PLOT_RANGE + 4, -PLOT_RANGE + 4)
        self._pw.addItem(self._lbl_n2_plot)

        # Angle arc label
        self._lbl_alpha = pg.TextItem("α", color="#fab387", anchor=(0.5, 0.5))
        self._pw.addItem(self._lbl_alpha)
        self._lbl_gamma = pg.TextItem("γ", color="#89b4fa", anchor=(0.5, 0.5))
        self._pw.addItem(self._lbl_gamma)

        # Rays as PlotDataItems
        self._incident_line = self._pw.plot(
            pen=pg.mkPen("#f38ba8", width=3),
        )
        self._reflected_line = self._pw.plot(
            pen=pg.mkPen("#fab387", width=2, style=Qt.PenStyle.DashLine),
        )
        self._refracted_line = self._pw.plot(
            pen=pg.mkPen("#89b4fa", width=3),
        )

        root.addWidget(self._pw, stretch=3)

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        # Angle of incidence slider
        a_box = QGroupBox("Угол падения (α)")
        a_lay = QVBoxLayout(a_box)
        self._lbl_angle = QLabel("α = 45°")
        self._lbl_angle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_angle = QSlider(Qt.Orientation.Horizontal)
        self._sl_angle.setRange(1, 89)
        self._sl_angle.setValue(45)
        self._sl_angle.valueChanged.connect(self._update)
        a_lay.addWidget(self._lbl_angle)
        a_lay.addWidget(self._sl_angle)
        ctrl.addWidget(a_box)

        # Medium 1 combo
        m1_box = QGroupBox("Среда 1 (над границей)")
        m1_lay = QVBoxLayout(m1_box)
        self._cb_n1 = QComboBox()
        self._cb_n1.addItems(MEDIA_NAMES)
        self._cb_n1.setCurrentIndex(1)   # Воздух by default
        self._cb_n1.currentIndexChanged.connect(self._update)
        m1_lay.addWidget(self._cb_n1)
        ctrl.addWidget(m1_box)

        # Medium 2 combo
        m2_box = QGroupBox("Среда 2 (под границей)")
        m2_lay = QVBoxLayout(m2_box)
        self._cb_n2 = QComboBox()
        self._cb_n2.addItems(MEDIA_NAMES)
        self._cb_n2.setCurrentIndex(3)   # Стекло by default
        self._cb_n2.currentIndexChanged.connect(self._update)
        m2_lay.addWidget(self._cb_n2)
        ctrl.addWidget(m2_box)

        # Readout panel
        info_box = QGroupBox("Результат")
        info_lay = QVBoxLayout(info_box)
        self._lbl_n1 = QLabel()
        self._lbl_n2 = QLabel()
        self._lbl_gamma = QLabel()
        self._lbl_tir = QLabel()
        self._lbl_tir.setStyleSheet("color: #f38ba8; font-weight: bold;")
        for w in (self._lbl_n1, self._lbl_n2, self._lbl_gamma, self._lbl_tir):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        # Snell reminder
        snell_lbl = QLabel("n₁·sin α = n₂·sin γ")
        snell_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        snell_lbl.setStyleSheet("color: #888; font-style: italic;")
        ctrl.addWidget(snell_lbl)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update logic ───────────────────────────────────────────────────────────

    def _update(self) -> None:
        """Recalculate ray angles via Snell's law and redraw all lines."""
        alpha_deg: int = self._sl_angle.value()
        alpha_rad: float = math.radians(alpha_deg)

        n1: float = MEDIA[self._cb_n1.currentText()]
        n2: float = MEDIA[self._cb_n2.currentText()]

        self._lbl_angle.setText(f"α = {alpha_deg}°")
        self._lbl_n1.setText(f"n₁ = {n1:.4f}")
        self._lbl_n2.setText(f"n₂ = {n2:.4f}")

        # ── Incident ray: from upper-left to origin ────────────────────────────
        # alpha is measured from normal (vertical), so:
        #   x offset = sin(alpha), y offset = cos(alpha)  (downward toward origin)
        ix = -RAY_LEN * math.sin(alpha_rad)
        iy = RAY_LEN * math.cos(alpha_rad)
        self._incident_line.setData([ix, 0.0], [iy, 0.0])

        # ── Reflected ray: mirror of incident about normal ─────────────────────
        rx = RAY_LEN * math.sin(alpha_rad)
        ry = RAY_LEN * math.cos(alpha_rad)
        self._reflected_line.setData([0.0, rx], [0.0, ry])

        # ── Refracted ray via Snell's law ──────────────────────────────────────
        sin_gamma: float = (n1 / n2) * math.sin(alpha_rad)

        if sin_gamma > 1.0:
            # Total internal reflection — hide refracted ray
            self._refracted_line.setData([], [])
            self._lbl_gamma.setText("Полное внутреннее отражение!")
            self._lbl_tir.setText("⚠ Преломлённый луч отсутствует")
            self._lbl_alpha.setPos(
                12 * math.sin(alpha_rad / 2),
                12 * math.cos(alpha_rad / 2),
            )
            self._lbl_gamma.setPos(0, 0)
        else:
            gamma_rad: float = math.asin(sin_gamma)
            gamma_deg: float = math.degrees(gamma_rad)
            gx = RAY_LEN * math.sin(gamma_rad)
            gy = -RAY_LEN * math.cos(gamma_rad)
            self._refracted_line.setData([0.0, gx], [0.0, gy])
            self._lbl_gamma.setText(f"γ = {gamma_deg:.1f}°")
            self._lbl_tir.setText("")

            # Angle labels on canvas
            self._lbl_alpha.setPos(
                14 * math.sin(alpha_rad / 2),
                14 * math.cos(alpha_rad / 2),
            )
            self._lbl_gamma.setPos(
                14 * math.sin(gamma_rad / 2),
                -14 * math.cos(gamma_rad / 2),
            )

        # Update media label text
        self._lbl_n1_plot.setText(f"Среда 1  n={n1:.3f}")
        self._lbl_n2_plot.setText(f"Среда 2  n={n2:.3f}")

    # ── Public accessors ───────────────────────────────────────────────────────

    def get_back_button(self) -> QPushButton:
        """Return the back button for controller connection.

        Returns:
            QPushButton: The navigation back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Преломление света и линзы", OpticsWidget)
