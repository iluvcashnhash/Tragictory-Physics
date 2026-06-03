"""
Ideal gas isoprocess simulation widget for Tragictory Physics.

Plots the p-V diagram for isothermal, isobaric, or isochoric processes
described by the Mendeleev-Clapeyron equation pV = νRT.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QGroupBox, QPushButton, QComboBox, QFormLayout,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg


NU: float = 1.0          # moles
R: float = 8.314         # J/(mol·K)

# Slider ranges
T_MIN, T_MAX, T_DEF = 100, 1000, 300       # K
V_MIN, V_MAX, V_DEF = 1,   100,  20        # dm³ → ×10⁻³ m³
P_MIN, P_MAX, P_DEF = 1,   500,  100       # kPa

PROCESS_NAMES = ["Изотерма (T = const)", "Изобара (p = const)", "Изохора (V = const)"]


def _p_from_TV(T: float, V: float) -> float:
    """Return pressure in kPa given T (K) and V (dm³)."""
    return NU * R * T / (V * 1e-3) / 1e3


def _V_from_TP(T: float, p: float) -> float:
    """Return volume in dm³ given T (K) and p (kPa)."""
    return NU * R * T / (p * 1e3) * 1e3


def _T_from_pV(p: float, V: float) -> float:
    """Return temperature in K given p (kPa) and V (dm³)."""
    return p * 1e3 * V * 1e-3 / (NU * R)


class ThermoWidget(QWidget):
    """p-V diagram for ideal gas isoprocesses.

    One parameter is locked per the selected process; the other two
    are linked via pV = νRT.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the widget and draw the initial curve."""
        super().__init__(parent)
        self._blocked = False
        self._build_ui()
        self._redraw()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        # Plot
        self._pw = pg.PlotWidget()
        self._pw.setBackground("#1e1e2e")
        self._pw.setLabel("bottom", "V, дм³")
        self._pw.setLabel("left", "p, кПа")
        self._pw.showGrid(x=True, y=True, alpha=0.25)
        self._pw.setXRange(0, V_MAX + 5, padding=0)
        self._pw.setYRange(0, P_MAX + 20, padding=0)

        self._curve = self._pw.plot(pen=pg.mkPen("#89b4fa", width=2))
        self._dot = self._pw.plot(
            pen=None, symbol="o", symbolSize=12,
            symbolBrush="#f38ba8", symbolPen=pg.mkPen(None))
        self._process_label = pg.TextItem("", color="#cba6f7", anchor=(0, 1))
        self._pw.addItem(self._process_label)

        root.addWidget(self._pw, stretch=3)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)

        self.back_button = QPushButton("← Назад к теории")
        self.back_button.setFixedHeight(36)
        ctrl.addWidget(self.back_button)

        # Process selector
        proc_box = QGroupBox("Процесс")
        proc_lay = QVBoxLayout(proc_box)
        self._cb_process = QComboBox()
        self._cb_process.addItems(PROCESS_NAMES)
        self._cb_process.currentIndexChanged.connect(self._on_process_change)
        proc_lay.addWidget(self._cb_process)
        ctrl.addWidget(proc_box)

        # Sliders via QFormLayout
        sliders_box = QGroupBox("Параметры газа")
        form = QFormLayout(sliders_box)

        self._sl_T, self._lbl_T = self._make_slider(T_MIN, T_MAX, T_DEF)
        self._sl_V, self._lbl_V = self._make_slider(V_MIN, V_MAX, V_DEF)
        self._sl_p, self._lbl_p = self._make_slider(P_MIN, P_MAX, P_DEF)

        form.addRow("T (K):", self._lbl_T)
        form.addRow("", self._sl_T)
        form.addRow("V (дм³):", self._lbl_V)
        form.addRow("", self._sl_V)
        form.addRow("p (кПа):", self._lbl_p)
        form.addRow("", self._sl_p)

        self._sl_T.valueChanged.connect(self._on_T_changed)
        self._sl_V.valueChanged.connect(self._on_V_changed)
        self._sl_p.valueChanged.connect(self._on_p_changed)

        ctrl.addWidget(sliders_box)

        # Readout
        self._lbl_state = QLabel()
        self._lbl_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_state.setStyleSheet("color:#a6e3a1; font-style:italic;")
        ctrl.addWidget(self._lbl_state)

        ctrl.addStretch()
        root.addLayout(ctrl, stretch=1)
        self._on_process_change(0)

    @staticmethod
    def _make_slider(lo: int, hi: int, val: int) -> tuple[QSlider, QLabel]:
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        lbl = QLabel(str(val))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sl, lbl

    # ── Process switching ─────────────────────────────────────────────────────

    def _on_process_change(self, idx: int) -> None:
        """Lock/unlock sliders according to selected process."""
        # 0=isothermal(T locked), 1=isobaric(p locked), 2=isochoric(V locked)
        self._sl_T.setEnabled(idx != 0)
        self._sl_V.setEnabled(idx != 2)
        self._sl_p.setEnabled(idx != 1)
        self._redraw()

    # ── Slider handlers ───────────────────────────────────────────────────────

    def _on_T_changed(self, val: int) -> None:
        if self._blocked:
            return
        self._lbl_T.setText(str(val))
        proc = self._cb_process.currentIndex()
        self._blocked = True
        if proc == 1:   # isobaric: T changes → V changes
            p = self._sl_p.value()
            V_new = max(V_MIN, min(V_MAX, int(_V_from_TP(val, p))))
            self._sl_V.setValue(V_new)
        elif proc == 2: # isochoric: T changes → p changes
            V = self._sl_V.value()
            p_new = max(P_MIN, min(P_MAX, int(_p_from_TV(val, V))))
            self._sl_p.setValue(p_new)
        self._blocked = False
        self._redraw()

    def _on_V_changed(self, val: int) -> None:
        if self._blocked:
            return
        self._lbl_V.setText(str(val))
        proc = self._cb_process.currentIndex()
        self._blocked = True
        if proc == 0:   # isothermal: V changes → p changes
            T = self._sl_T.value()
            p_new = max(P_MIN, min(P_MAX, int(_p_from_TV(T, val))))
            self._sl_p.setValue(p_new)
        elif proc == 1: # isobaric: V changes → T changes
            p = self._sl_p.value()
            T_new = max(T_MIN, min(T_MAX, int(_T_from_pV(p, val))))
            self._sl_T.setValue(T_new)
        self._blocked = False
        self._redraw()

    def _on_p_changed(self, val: int) -> None:
        if self._blocked:
            return
        self._lbl_p.setText(str(val))
        proc = self._cb_process.currentIndex()
        self._blocked = True
        if proc == 0:   # isothermal: p changes → V changes
            T = self._sl_T.value()
            V_new = max(V_MIN, min(V_MAX, int(_V_from_TP(T, val))))
            self._sl_V.setValue(V_new)
        elif proc == 2: # isochoric: p changes → T changes
            V = self._sl_V.value()
            T_new = max(T_MIN, min(T_MAX, int(_T_from_pV(val, V))))
            self._sl_T.setValue(T_new)
        self._blocked = False
        self._redraw()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _redraw(self) -> None:
        proc = self._cb_process.currentIndex()
        T = self._sl_T.value()
        V = self._sl_V.value()
        p = self._sl_p.value()

        self._lbl_T.setText(str(T))
        self._lbl_V.setText(str(V))
        self._lbl_p.setText(str(p))
        self._lbl_state.setText(f"pV = νRT → {p}·{V} = {int(p*V)}\nνRT = {int(NU*R*T)}")

        if proc == 0:   # isothermal: hyperbola p = νRT/V
            Vs = np.linspace(V_MIN, V_MAX, 300)
            ps = _p_from_TV(T, Vs)
            label = f"Изотерма  T = {T} K"
        elif proc == 1: # isobaric: horizontal line
            Vs = np.array([V_MIN, V_MAX], dtype=float)
            ps = np.full_like(Vs, float(p))
            label = f"Изобара  p = {p} кПа"
        else:           # isochoric: vertical line
            ps = np.array([P_MIN, P_MAX], dtype=float)
            Vs = np.full_like(ps, float(V))
            label = f"Изохора  V = {V} дм³"

        self._curve.setData(Vs, ps)
        self._dot.setData([V], [p])
        self._process_label.setText(label)
        self._process_label.setPos(2, P_MAX + 15)

    # ── Public ────────────────────────────────────────────────────────────────

    def get_back_button(self) -> QPushButton:
        """Return the back navigation button.

        Returns:
            QPushButton: Back button.
        """
        return self.back_button


from .registry import register_simulation
register_simulation("Идеальный газ и основное уравнение МКТ", ThermoWidget)
