"""
Photoelectric effect simulation widget for Tragictory Physics.

Plots Eₖ vs ν (frequency) using Einstein's equation:
  Eₖ = h·ν − A_out   (Eₖ = 0 if below threshold)
A red dot marks the current wavelength; a warning appears below threshold.
"""

import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox, QFormLayout,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


H: float = 6.626e-34    # J·s
C: float = 3.0e8        # m/s
EV: float = 1.602e-19   # J per eV

# Work functions in eV
METALS: dict[str, float] = {
    "Цезий (Cs)  A = 2.0 эВ":   2.0,
    "Цинк (Zn)   A = 4.3 эВ":   4.3,
    "Платина (Pt) A = 5.7 эВ":  5.7,
}
METAL_NAMES = list(METALS.keys())

LAM_MIN_NM = 100   # nm
LAM_MAX_NM = 800   # nm

# Frequency axis for the graph (Hz)
NU_MIN: float = C / (LAM_MAX_NM * 1e-9)
NU_MAX: float = C / (LAM_MIN_NM * 1e-9)


def _Ek_eV(nu: float, A_eV: float) -> float:
    """Return kinetic energy in eV; 0 if below threshold."""
    return max(0.0, H * nu / EV - A_eV)


class PhotoelectricWidget(QWidget):
    """Einstein photoelectric-effect visualiser.

    Graph: Eₖ (eV) vs ν (×10¹⁴ Hz). Red dot = current wavelength.
    Below the threshold frequency the dot sits on the x-axis and a
    warning is shown.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise and draw the initial state."""
        super().__init__(parent)
        self._build_ui()
        self._update()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Plot
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setLabel("bottom", "ν, ×10¹⁴ Гц")
        self._pw.setLabel("left", "Eₖ, эВ")
        self._pw.showGrid(x=True, y=True, alpha=0.25)

        # x-axis in units of 10¹⁴ Hz
        nu_scale = 1e14
        self._nu_arr = np.linspace(NU_MIN, NU_MAX, 400)
        self._nu_scaled = self._nu_arr / nu_scale

        # Threshold line (will update)
        self._threshold_line = pg.InfiniteLine(
            pos=0, angle=90,
            pen=pg.mkPen("#f9e2af", width=1, style=Qt.PenStyle.DashLine))
        self._pw.addItem(self._threshold_line)

        # Zero baseline
        self._pw.addItem(pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen("#585b70", width=1)))

        self._curve = self._pw.plot(pen=pg.mkPen("#89b4fa", width=2))
        self._dot = self._pw.plot(
            pen=None, symbol="o", symbolSize=12,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        self._tir_text = pg.TextItem(
            "", color="#f38ba8", anchor=(0.5, 0))
        self._pw.addItem(self._tir_text)

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        # Metal selector
        metal_box = QGroupBox("Металл")
        metal_lay = QVBoxLayout(metal_box)
        self._cb_metal = QComboBox()
        self._cb_metal.addItems(METAL_NAMES)
        self._cb_metal.currentIndexChanged.connect(self._update)
        metal_lay.addWidget(self._cb_metal)
        ctrl.addWidget(metal_box)

        # Wavelength slider
        wave_box = QGroupBox("Длина волны λ (нм)")
        form = QFormLayout(wave_box)
        self._lbl_lam = QLabel("400 нм")
        self._lbl_lam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sl_lam = QSlider(Qt.Orientation.Horizontal)
        self._sl_lam.setRange(LAM_MIN_NM, LAM_MAX_NM)
        self._sl_lam.setValue(400)
        self._sl_lam.valueChanged.connect(self._update)
        form.addRow("λ =", self._lbl_lam)
        form.addRow("", self._sl_lam)
        ctrl.addWidget(wave_box)

        # Readout
        info_box = QGroupBox("Результат")
        info_lay = QVBoxLayout(info_box)
        self._lbl_nu = QLabel()
        self._lbl_E_photon = QLabel()
        self._lbl_A = QLabel()
        self._lbl_Ek = QLabel()
        self._lbl_Ek.setStyleSheet("font-weight:bold; font-size:14px;")
        for w in (self._lbl_nu, self._lbl_E_photon, self._lbl_A, self._lbl_Ek):
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_lay.addWidget(w)
        ctrl.addWidget(info_box)

        hint = QLabel("Eₖ = hν − A_вых")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#888; font-style:italic;")
        ctrl.addWidget(hint)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self) -> None:
        lam_nm = self._sl_lam.value()
        lam_m = lam_nm * 1e-9
        nu = C / lam_m
        nu_scale = 1e14

        A_eV = METALS[self._cb_metal.currentText()]
        nu_threshold = A_eV * EV / H
        Ek = _Ek_eV(nu, A_eV)

        self._lbl_lam.setText(f"{lam_nm} нм")
        self._lbl_nu.setText(f"ν = {nu/nu_scale:.2f} ×10¹⁴ Гц")
        self._lbl_E_photon.setText(f"E_фотона = {H*nu/EV:.2f} эВ")
        self._lbl_A.setText(f"A_вых = {A_eV:.1f} эВ")
        self._lbl_Ek.setText(f"Eₖ = {Ek:.2f} эВ")

        # Build curve: Eₖ(ν) — zero below threshold, linear above
        Ek_arr = np.array([_Ek_eV(n, A_eV) for n in self._nu_arr])
        self._curve.setData(self._nu_scaled, Ek_arr)

        # Threshold line
        self._threshold_line.setValue(nu_threshold / nu_scale)

        # Dot
        self._dot.setData([nu / nu_scale], [Ek])

        # Auto-range y
        y_max = max(float(np.max(Ek_arr)), 0.5)
        self._pw.setXRange(NU_MIN / nu_scale, NU_MAX / nu_scale, padding=0.02)
        self._pw.setYRange(-0.1, y_max * 1.1, padding=0)

        # Warning text
        if nu < nu_threshold:
            self._tir_text.setText("⛔ Фотоэффекта нет!")
            self._tir_text.setPos(nu / nu_scale, 0.05)
        else:
            self._tir_text.setText("")

    # ── Public ────────────────────────────────────────────────────────────────

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Фотоэффект и уравнение Эйнштейна", PhotoelectricWidget)
