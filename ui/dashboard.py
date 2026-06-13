import sys
import math
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGridLayout, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath, QFontDatabase
)
import pyqtgraph as pg

try:
    from ui.animations import UIAnimator
except ModuleNotFoundError:
    from animations import UIAnimator


# ── Palette ────────────────────────────────────────────────────────────────────
CYAN        = QColor(0,   240, 255)
CYAN_DIM    = QColor(0,   180, 200, 80)
CYAN_GHOST  = QColor(0,   240, 255, 25)
CYAN_MID    = QColor(0,   200, 220, 140)
BLUE_DARK   = QColor(4,   14,  30)
BLUE_PANEL  = QColor(8,   20,  42, 210)
BLUE_BORDER = QColor(0,   140, 200, 180)
WHITE_SOFT  = QColor(200, 240, 255)
ACCENT_WARN = QColor(255, 200, 50)
GRID_LINE   = QColor(0,   80,  120, 40)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _mono(size: int, bold: bool = False) -> QFont:
    f = QFont("Courier New", size)
    f.setBold(bold)
    return f


def _label(text: str, size: int = 11, bold: bool = False,
           color: str = "#00f0ff") -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(_mono(size, bold))
    lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return lbl


# ── Stat Card ──────────────────────────────────────────────────────────────────
class StatCard(QWidget):
    def __init__(self, title: str, value: str, unit: str = "",
                 color: QColor = CYAN, parent=None):
        super().__init__(parent)
        self._color = color
        self._pulse = 0.0
        self._dp    = +0.04
        self.setFixedHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        self._title_lbl = _label(title.upper(), 9,  color="#8ab8cc")
        self._value_lbl = _label(value,         22, bold=True, color=color.name())
        self._unit_lbl  = _label(unit,           9,  color="#5a8a9a")

        lay.addWidget(self._title_lbl)
        lay.addWidget(self._value_lbl)
        lay.addWidget(self._unit_lbl)

    def tick(self):
        self._pulse += self._dp
        if self._pulse >= 1.0 or self._pulse <= 0.0:
            self._dp = -self._dp
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)

        bg = QLinearGradient(0, 0, 0, self.height())
        bg.setColorAt(0, QColor(0, 30, 55, 180))
        bg.setColorAt(1, QColor(0, 15, 30, 160))
        p.setBrush(QBrush(bg))

        pen_col = QColor(self._color)
        pen_col.setAlpha(int(80 + 100 * self._pulse))
        p.setPen(QPen(pen_col, 1.2))
        p.drawRoundedRect(r, 8, 8)

        dot_col = QColor(self._color)
        dot_col.setAlpha(int(160 + 95 * self._pulse))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(dot_col))
        p.drawEllipse(QRectF(self.width() - 18, 10, 7, 7))
        p.end()


# ── Spark Line ─────────────────────────────────────────────────────────────────
class SparkLine(QWidget):
    def __init__(self, data: list, color: QColor = CYAN, parent=None):
        super().__init__(parent)
        self._data  = data
        self._color = color
        self.setFixedHeight(36)

    def paintEvent(self, _):
        if len(self._data) < 2:
            return
        p   = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mn, mx = min(self._data), max(self._data)
        rng = mx - mn or 1

        def pt(i):
            x = i / (len(self._data) - 1) * w
            y = h - (self._data[i] - mn) / rng * (h - 4) - 2
            return QPointF(x, y)

        path = QPainterPath()
        path.moveTo(QPointF(0, h))
        for i in range(len(self._data)):
            path.lineTo(pt(i))
        path.lineTo(QPointF(w, h))
        path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        c0 = QColor(self._color); c0.setAlpha(60)
        c1 = QColor(self._color); c1.setAlpha(0)
        grad.setColorAt(0, c0)
        grad.setColorAt(1, c1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        line_col = QColor(self._color)
        line_col.setAlpha(220)
        p.setPen(QPen(line_col, 1.8))
        for i in range(len(self._data) - 1):
            p.drawLine(pt(i), pt(i + 1))
        p.end()


# ── Arc Core Widget ─────────────────────────────────────────────────────────────
class ArcCoreWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle  = 0
        self.pulse  = 0.0
        self.setMinimumWidth(320)

    def tick(self, angle: int, pulse: float):
        self.angle = angle
        self.pulse = pulse
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width()  // 2
        cy = self.height() // 2

        # ── Outer ghost rings ──────────────────────────────────────────────────
        for r, a in [(148, 18), (138, 28), (128, 40)]:
            col = QColor(CYAN_DIM)
            col.setAlpha(a)
            p.setPen(QPen(col, 1, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # ── Rotating arcs ──────────────────────────────────────────────────────
        arc_configs = [
            (125, 200, 3,   0,  100),
            (110, 140, 2,  45,   80),
            ( 95,  90, 2,  90,   60),
        ]
        for radius, alpha, width, offset, span in arc_configs:
            col = QColor(CYAN)
            col.setAlpha(alpha)
            p.setPen(QPen(col, width, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
            x, y = cx - radius, cy - radius
            d = radius * 2
            p.drawArc(x, y, d, d, (self.angle + offset) * 16, span * 16)
            p.drawArc(x, y, d, d, (self.angle + offset + 180) * 16, span * 16)

        # ── Radial tick marks ──────────────────────────────────────────────────
        tick_col = QColor(CYAN)
        tick_col.setAlpha(70)
        p.setPen(QPen(tick_col, 1))
        for deg in range(0, 360, 30):
            rad    = math.radians(deg)
            inner  = 130
            outer  = 145
            x1 = cx + inner * math.cos(rad)
            y1 = cy + inner * math.sin(rad)
            x2 = cx + outer * math.cos(rad)
            y2 = cy + outer * math.sin(rad)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ── Cardinal crosshairs ────────────────────────────────────────────────
        dim = QColor(CYAN)
        dim.setAlpha(55)
        p.setPen(QPen(dim, 1))
        crosshairs = [
            (cx - 165, cy,       cx - 148, cy),
            (cx + 148, cy,       cx + 165, cy),
            (cx,       cy - 165, cx,       cy - 148),
            (cx,       cy + 148, cx,       cy + 165),
        ]
        for x1, y1, x2, y2 in crosshairs:
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ── Reactor glow ───────────────────────────────────────────────────────
        pulse_val = 0.5 + 0.5 * math.sin(self.pulse)
        glow = QRadialGradient(cx, cy, 50)
        glow.setColorAt(0, QColor(0, 240, 255, int(80 + 60 * pulse_val)))
        glow.setColorAt(1, QColor(0, 100, 180, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(cx - 50, cy - 50, 100, 100)

        # ── Hard center dot ────────────────────────────────────────────────────
        center_col = QColor(0, 255, 255, int(200 + 55 * pulse_val))
        p.setBrush(QBrush(center_col))
        p.drawEllipse(cx - 6, cy - 6, 12, 12)

        # ── Status label ───────────────────────────────────────────────────────
        label_col = QColor(CYAN)
        label_col.setAlpha(160)
        p.setPen(QPen(label_col, 1))
        p.setFont(_mono(7))
        p.drawText(
            QRectF(cx - 125, cy + 130, 250, 20),
            Qt.AlignmentFlag.AlignCenter,
            "◈  REACTOR NOMINAL  ◈"
        )
        p.end()


# ── Main HUD ────────────────────────────────────────────────────────────────────
class JarvisAnalyticsHUD(QWidget):
    sig_show    = pyqtSignal(str)
    sig_hide    = pyqtSignal()
    sig_status  = pyqtSignal(str)

    _WINDOW = 20

    def __init__(self):
        super().__init__()
        self._angle       = 0
        self._pulse_t     = 0.0
        self._session_buf = list(np.linspace(4200, 11200, self._WINDOW))
        self._lead_buf    = list(np.linspace(45, 124, self._WINDOW))
        self._lat_buf     = [round(38 + 8 * math.sin(i * 0.4), 1)
                             for i in range(self._WINDOW)]
        self._init_ui()
        self._connect_signals()
        self.hide()

    # ── UI Construction ─────────────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(1200, 660)
        self._center_on_screen()

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)
        root.addWidget(self._build_left_panel(),  stretch=5)
        root.addWidget(self._build_right_panel(), stretch=7)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(_label("JARVIS  //  CORE TELEMETRY", 13, bold=True))
        lay.addWidget(_label("techfintrail.com  ·  live feed", 9, color="#3a8a9a"))

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #004466; border: 1px solid #004466;")
        lay.addWidget(sep)

        self._arc = ArcCoreWidget()
        lay.addWidget(self._arc, stretch=1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #004466; border: 1px solid #004466;")
        lay.addWidget(sep2)

        self._log_lbl = _label(">> INITIALIZING TELEMETRY LINK_", 9, color="#00c8d8")
        self._log_lbl.setWordWrap(True)
        lay.addWidget(self._log_lbl)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(
            "background-color: rgba(8,20,42,210);"
            "border: 1.5px solid rgba(0,140,200,160);"
            "border-radius: 16px;"
        )
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        # Title row
        title_row = QHBoxLayout()
        title = _label("PERFORMANCE OVERVIEW", 12, bold=True)
        live  = _label("LIVE  ●", 9, color="#00ff88")
        live.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(title)
        title_row.addWidget(live)
        lay.addLayout(title_row)

        # KPI cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self._kpi_sessions = StatCard("Sessions / mo", "11,200", "↑ +33%",  CYAN)
        self._kpi_leads    = StatCard("Leads / wk",    "124",    "↑ +39%",  QColor(80, 255, 160))
        self._kpi_latency  = StatCard("Avg Latency",   "38 ms",  "↓ optimal", ACCENT_WARN)
        self._kpi_uptime   = StatCard("Uptime",        "99.97%", "30-day",  QColor(180, 100, 255))
        for card in (self._kpi_sessions, self._kpi_leads,
                     self._kpi_latency,  self._kpi_uptime):
            kpi_row.addWidget(card)
        lay.addLayout(kpi_row)

        # Charts grid
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(self._make_chart_block("Monthly User Sessions", "sessions", CYAN),               0, 0)
        grid.addWidget(self._make_chart_block("Weekly Lead Captures",  "leads",    QColor(80,255,160)), 0, 1)
        grid.addWidget(self._make_chart_block("Response Latency (ms)", "latency",  ACCENT_WARN),        1, 0)
        grid.addWidget(self._build_status_table(),                                                       1, 1)
        lay.addLayout(grid, stretch=1)

        return panel

    def _make_chart_block(self, title: str, key: str, color: QColor) -> QWidget:
        block = QWidget()
        block.setStyleSheet(
            "background: rgba(0,20,40,140);"
            "border: 1px solid rgba(0,100,160,80);"
            "border-radius: 10px;"
        )
        lay = QVBoxLayout(block)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        lay.addWidget(_label(title, 9, bold=True, color=color.name()))

        data_map = {
            "sessions": self._session_buf,
            "leads":    self._lead_buf,
            "latency":  self._lat_buf,
        }
        spark = SparkLine(data_map[key], color)
        plot  = self._build_plot(key, color)

        lay.addWidget(spark)
        lay.addWidget(plot, stretch=1)

        setattr(self, f"_spark_{key}", spark)
        setattr(self, f"_plot_{key}",  plot)
        return block

    def _build_plot(self, key: str, color: QColor) -> pg.PlotWidget:
        pw = pg.PlotWidget()
        pw.setBackground("transparent")
        pw.setMinimumHeight(110)
        for ax in ("bottom", "left"):
            pw.getAxis(ax).setPen(pg.mkPen(GRID_LINE))
            pw.getAxis(ax).setTextPen(pg.mkPen(QColor(80, 160, 180)))
        pw.showGrid(x=True, y=True, alpha=0.08)

        pen = pg.mkPen(color, width=2)
        data_map = {
            "sessions": ([1, 2, 3, 4, 5],       [4200, 5100, 6800, 8400, 11200]),
            "leads":    ([1, 2, 3, 4],           [45,   62,   89,   124]),
            "latency":  ([1, 2, 3, 4, 5, 6, 7, 8], [42, 39, 41, 38, 40, 37, 39, 38]),
        }
        xs, ys = data_map[key]

        if key == "leads":
            bars = pg.BarGraphItem(
                x=xs, height=ys, width=0.5,
                brush=pg.mkBrush(QColor(color.red(), color.green(), color.blue(), 140)),
                pen=pg.mkPen(color)
            )
            pw.addItem(bars)
        else:
            pw.plot(xs, ys, pen=pen, symbol='o',
                    symbolSize=5, symbolBrush=pg.mkBrush(255, 255, 255, 180))
        return pw

    def _build_status_table(self) -> QWidget:
        block = QWidget()
        block.setStyleSheet(
            "background: rgba(0,20,40,140);"
            "border: 1px solid rgba(0,100,160,80);"
            "border-radius: 10px;"
        )
        lay = QVBoxLayout(block)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)
        lay.addWidget(_label("SYSTEM STATUS", 9, bold=True))

        rows = [
            ("API Gateway",   "OPERATIONAL", "#00ff88"),
            ("CDN Edge",      "OPERATIONAL", "#00ff88"),
            ("Auth Service",  "DEGRADED",    "#ffcc00"),
            ("DB Primary",    "OPERATIONAL", "#00ff88"),
            ("Analytics ETL", "OPERATIONAL", "#00ff88"),
        ]
        for name, status, col in rows:
            row_w = QWidget()
            row_w.setStyleSheet(
                "background: rgba(0,30,50,100); border: none;"
                "border-radius: 4px; margin: 1px 0;"
            )
            row_lay = QHBoxLayout(row_w)
            row_lay.setSpacing(0)
            n = _label(f"  {name}", 9, color="#7ab8cc")
            s = _label(status,      9, color=col)
            s.setAlignment(Qt.AlignmentFlag.AlignRight)
            row_lay.addWidget(n, stretch=3)
            row_lay.addWidget(s, stretch=2)
            lay.addWidget(row_w)

        lay.addStretch()
        return block

    # ── Signals ────────────────────────────────────────────────────────────────
    def _connect_signals(self):
        self.sig_show.connect(self._on_show)
        self.sig_hide.connect(self._on_hide)
        self.sig_status.connect(self.update_status)

    def _on_show(self, text: str):
        self.update_status(text)
        UIAnimator.fade_in(self)

    def _on_hide(self):
        UIAnimator.fade_out(self, on_finished=self.hide)

    # ── Animation tick ─────────────────────────────────────────────────────────
    def _tick(self):
        self._angle   = (self._angle + 2) % 360
        self._pulse_t += 0.05
        self._arc.tick(self._angle, self._pulse_t)

        for card in (self._kpi_sessions, self._kpi_leads,
                     self._kpi_latency,  self._kpi_uptime):
            card.tick()

        self._session_buf.append(self._session_buf[-1] + np.random.randint(-80, 150))
        self._session_buf = self._session_buf[-self._WINDOW:]

        self._lead_buf.append(max(0, self._lead_buf[-1] + np.random.randint(-3, 6)))
        self._lead_buf = self._lead_buf[-self._WINDOW:]

        self._lat_buf.append(round(38 + 8 * math.sin(self._pulse_t * 0.7), 1))
        self._lat_buf = self._lat_buf[-self._WINDOW:]

        self._spark_sessions._data = self._session_buf; self._spark_sessions.update()
        self._spark_leads._data    = self._lead_buf;    self._spark_leads.update()
        self._spark_latency._data  = self._lat_buf;     self._spark_latency.update()

    # ── Utility ────────────────────────────────────────────────────────────────
    def _center_on_screen(self):
        geo = QApplication.primaryScreen().geometry()
        self.move(
            (geo.width()  - self.width())  // 2,
            (geo.height() - self.height()) // 2,
        )

    def update_status(self, text: str):
        self._log_lbl.setText(f">> {text.upper()}_")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QLinearGradient(0, 0, self.width(), self.height())
        bg.setColorAt(0, QColor(4,  14, 30, 230))
        bg.setColorAt(1, QColor(2,   8, 20, 245))
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 18, 18)

        border_col = QColor(0, 140, 200, 90)
        p.setPen(QPen(border_col, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 18, 18)
        p.end()