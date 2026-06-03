"""
Reflection and mirrors simulation widget for Tragictory Physics.

Shows a ray reflecting off a flat, concave, or convex mirror.
Draws the incident ray, normal, reflected ray, and focal/centre markers.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


RAY_LEN: float = 8.0
MIRROR_H: float = 4.0     # half-height of curved mirror arc


class MirrorWidget(QWidget):
    """Flat / concave / convex mirror ray tracer.

    Controls: mirror type, angle of incidence, object distance.
    Shows: incident ray, normal, reflected ray, focal point (curved mirrors),
    and image position label.
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
        self._pw.setXRange(-10, 2, padding=0)
        self._pw.setYRange(-6, 6, padding=0)
        self._pw.getAxis("bottom").hide()
        self._pw.getAxis("left").hide()

        # Optical axis
        self._pw.addItem(pg.InfiniteLine(
            pos=0, angle=0,
            pen=pg.mkPen("#585b70", width=1, style=Qt.PenStyle.DashLine)))

        # Mirror surface
        self._mirror_item = self._pw.plot(pen=pg.mkPen("#cdd6f4", width=3))

        # Normal at hit point
        self._normal_item = self._pw.plot(
            pen=pg.mkPen("#585b70", width=1, style=Qt.PenStyle.DashLine))

        # Rays
        self._incident = self._pw.plot(pen=pg.mkPen("#f38ba8", width=2))
        self._reflected = self._pw.plot(pen=pg.mkPen("#a6e3a1", width=2))
        self._virtual = self._pw.plot(
            pen=pg.mkPen("#a6e3a160", width=1, style=Qt.PenStyle.DashLine))

        # Object arrow
        self._object_item = self._pw.plot(pen=pg.mkPen("#f9e2af", width=3))

        # Focal point
        self._focal_dot = self._pw.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush="#cba6f7", symbolPen=pg.mkPen(None))
        self._focal_label = pg.TextItem("F", color="#cba6f7", anchor=(0.5, 1.2))
        self._pw.addItem(self._focal_label)

        # Image label
        self._image_label = pg.TextItem("", color="#fab387", anchor=(0.5, 0))
        self._pw.addItem(self._image_label)

        # Angle arc label
        self._alpha_label = pg.TextItem("α", color="#f38ba8", anchor=(0, 0.5))
        self._pw.addItem(self._alpha_label)

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(14)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        mirror_box = QGroupBox("Тип зеркала")
        mirror_lay = QVBoxLayout(mirror_box)
        self._cb_mirror = QComboBox()
        self._cb_mirror.addItems(["Плоское", "Вогнутое (сферическое)", "Выпуклое (сферическое)"])
        self._cb_mirror.currentIndexChanged.connect(self._update)
        mirror_lay.addWidget(self._cb_mirror)
        ctrl.addWidget(mirror_box)

        angle_box = QGroupBox("Угол падения α (°)")
        angle_lay = QVBoxLayout(angle_box)
        self._lbl_angle = QLabel("α = 30°")
        self._lbl_angle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_angle = QSlider(Qt.Orientation.Horizontal)
        self._sl_angle.setRange(1, 89)
        self._sl_angle.setValue(30)
        self._sl_angle.valueChanged.connect(self._update)
        angle_lay.addWidget(self._lbl_angle)
        angle_lay.addWidget(self._sl_angle)
        ctrl.addWidget(angle_box)

        dist_box = QGroupBox("Расстояние до объекта (у.е.)")
        dist_lay = QVBoxLayout(dist_box)
        self._lbl_dist = QLabel("d = 6")
        self._lbl_dist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_dist = QSlider(Qt.Orientation.Horizontal)
        self._sl_dist.setRange(1, 18)
        self._sl_dist.setValue(6)
        self._sl_dist.valueChanged.connect(self._update)
        dist_lay.addWidget(self._lbl_dist)
        dist_lay.addWidget(self._sl_dist)
        ctrl.addWidget(dist_box)

        info_box = QGroupBox("Закон отражения")
        info_lay = QVBoxLayout(info_box)
        self._lbl_law = QLabel("α_пад = α_отр")
        self._lbl_law.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_law.setStyleSheet("font-style:italic; color:#a6e3a1;")
        self._lbl_image = QLabel()
        self._lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_lay.addWidget(self._lbl_law)
        info_lay.addWidget(self._lbl_image)
        ctrl.addWidget(info_box)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self) -> None:
        mode = self._cb_mirror.currentIndex()
        alpha_deg = self._sl_angle.value()
        alpha_rad = math.radians(alpha_deg)
        d_obj = self._sl_dist.value()

        self._lbl_angle.setText(f"α = {alpha_deg}°")
        self._lbl_dist.setText(f"d = {d_obj}")

        # Hit point on mirror (x=0)
        hit_y = math.tan(alpha_rad) * d_obj * 0.3 - 1.0
        hit_y = max(-MIRROR_H + 0.5, min(MIRROR_H - 0.5, hit_y))

        # ── Mirror surface ──────────────────────────────────────────────────
        F = 3.0   # focal length for curved mirrors
        R = 2 * F

        if mode == 0:  # flat
            self._mirror_item.setData([0, 0], [-MIRROR_H, MIRROR_H])
            nx, ny = 1.0, 0.0   # normal points right
            self._focal_dot.setData([], [])
            self._focal_label.setText("")
        elif mode == 1:  # concave (opens right)
            theta = np.linspace(-math.asin(MIRROR_H / R),
                                 math.asin(MIRROR_H / R), 60)
            mx = R * (1 - np.cos(theta))
            my = R * np.sin(theta)
            self._mirror_item.setData(mx.tolist(), my.tolist())
            # Normal at hit_y: tangent of circle → normal points toward centre (R, 0)
            theta_h = math.asin(max(-1, min(1, hit_y / R)))
            nx = -math.cos(theta_h)  # inward normal
            ny = -math.sin(theta_h)
            # hit point on concave surface
            hx = R * (1 - math.cos(theta_h))
            hit_y_adj = R * math.sin(theta_h)
            self._focal_dot.setData([-F], [0])
            self._focal_label.setPos(-F, 0)
            self._focal_label.setText("F")
        else:  # convex (opens left)
            theta = np.linspace(-math.asin(MIRROR_H / R),
                                 math.asin(MIRROR_H / R), 60)
            mx = -R * (1 - np.cos(theta))
            my = R * np.sin(theta)
            self._mirror_item.setData(mx.tolist(), my.tolist())
            theta_h = math.asin(max(-1, min(1, hit_y / R)))
            nx = math.cos(theta_h)   # outward normal
            ny = math.sin(theta_h)
            self._focal_dot.setData([F], [0])
            self._focal_label.setPos(F, 0)
            self._focal_label.setText("F (мнимый)")

        if mode == 0:
            hx, hy = 0.0, hit_y
        else:
            hy = hit_y

        # For flat mirror, fix hit coords
        if mode == 0:
            hx, hy = 0.0, hit_y
        elif mode == 1:
            theta_h = math.asin(max(-1, min(1, hit_y / R)))
            hx = R * (1 - math.cos(theta_h))
            hy = R * math.sin(theta_h)
            nx = -math.cos(theta_h)
            ny = -math.sin(theta_h)
            mag = math.sqrt(nx*nx + ny*ny)
            nx /= mag; ny /= mag
        else:
            theta_h = math.asin(max(-1, min(1, hit_y / R)))
            hx = -R * (1 - math.cos(theta_h))
            hy = R * math.sin(theta_h)
            nx = math.cos(theta_h)
            ny = math.sin(theta_h)
            mag = math.sqrt(nx*nx + ny*ny)
            nx /= mag; ny /= mag

        # Incident ray: comes from (-d_obj, hy + d_obj * tan(alpha))
        src_x = -d_obj
        src_y = hy + d_obj * math.tan(alpha_rad)
        self._incident.setData([src_x, hx], [src_y, hy])

        # Incident direction (unit vector toward hit)
        idx = hx - src_x; idy = hy - src_y
        i_len = math.sqrt(idx**2 + idy**2)
        idx /= i_len; idy /= i_len

        # Reflect: r = d - 2(d·n)n
        dot = idx * nx + idy * ny
        rx = idx - 2 * dot * nx
        ry = idy - 2 * dot * ny

        self._reflected.setData(
            [hx, hx + rx * RAY_LEN],
            [hy, hy + ry * RAY_LEN])

        # Virtual extension
        self._virtual.setData(
            [hx, hx - rx * RAY_LEN * 0.5],
            [hy, hy - ry * RAY_LEN * 0.5])

        # Normal line
        self._normal_item.setData(
            [hx - nx * 2, hx + nx * 2],
            [hy - ny * 2, hy + ny * 2])

        self._alpha_label.setPos(hx + 0.4, hy + 0.4)

        # Image info
        if mode == 0:
            self._lbl_image.setText("Мнимое, прямое, равное")
            self._image_label.setText("")
        elif mode == 1:
            if d_obj > F:
                img_type = "Действительное, перевёрнутое"
            else:
                img_type = "Мнимое, прямое, увеличенное"
            self._lbl_image.setText(img_type)
        else:
            self._lbl_image.setText("Мнимое, прямое, уменьшенное")

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Отражение света и плоские зеркала", MirrorWidget)
