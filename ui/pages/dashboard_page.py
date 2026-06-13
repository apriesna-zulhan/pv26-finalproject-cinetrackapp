from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QCursor
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet,
    QValueAxis, QBarCategoryAxis
)
from PySide6.QtGui import QPainter, QPen

from ui.components.stat_card import StatCard
from ui.theme import (BG_BASE, BG_SURFACE, BG_CARD, WHITE, GRAY_100,
                       GRAY_300, GRAY_400, RED, GOLD,
                       GREEN_ACT, BLUE_ACT, BORDER)
from database.db_manager import DatabaseManager


class RecentFavRow(QFrame):
    klik_detail = Signal(dict)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(52)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {BORDER};
                border-radius: 0;
            }}
            QFrame:hover {{
                background: {BG_CARD};
            }}
        """)
        self._build(data)

    def _build(self, d):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 8, 8, 8)
        lay.setSpacing(12)

        lbl_j = QLabel(d.get("judul", "?"))
        lbl_j.setStyleSheet(
            f"color: {WHITE}; font-weight: 600; font-size: 12px; background: transparent;"
        )
        lbl_j.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        genre = d.get("genre", "")
        lbl_g = QLabel(genre)
        lbl_g.setStyleSheet(
            f"color: {GRAY_300}; font-size: 11px; background: transparent;"
        )
        lbl_g.setFixedWidth(80)

        rating = float(d.get("rating", 0))
        rc = (GREEN_ACT if rating >= 8 else
              GOLD if rating >= 6.5 else
              "#ff6b35" if rating >= 5 else GRAY_300)
        lbl_r = QLabel(f"⭐ {rating:.1f}")
        lbl_r.setStyleSheet(
            f"color: {rc}; font-size: 11px; font-weight: 600; background: transparent;"
        )
        lbl_r.setFixedWidth(55)

        lbl_d = QLabel(d.get("tanggal_tambah", ""))
        lbl_d.setStyleSheet(
            f"color: {GRAY_400}; font-size: 10px; background: transparent;"
        )
        lbl_d.setFixedWidth(85)

        lbl_hint = QLabel("›")
        lbl_hint.setStyleSheet(
            f"color: {GRAY_400}; font-size: 16px; background: transparent;"
        )

        lay.addWidget(lbl_j)
        lay.addWidget(lbl_g)
        lay.addWidget(lbl_r)
        lay.addWidget(lbl_d)
        lay.addWidget(lbl_hint)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.klik_detail.emit(self.data)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db            = DatabaseManager()
        self._film_populer: list[dict] = []
        self._api_req      = 0
        self._client       = None  
        self._build()

    def set_client(self, client):
        self._client = client

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        page = QWidget()
        page.setStyleSheet(f"background: {BG_BASE};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 32, 40, 40)
        lay.setSpacing(28)

        lbl_title = QLabel("Dashboard")
        lbl_title.setObjectName("page_title")
        lay.addWidget(lbl_title)

        lay.addLayout(self._build_stats())

        lay.addWidget(self._build_chart())

        lay.addWidget(self._build_recent_fav())

        lay.addStretch()
        scroll.setWidget(page)
        root.addWidget(scroll)

    def _build_stats(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        items = [
            ("Film Populer TMDb", "–",  "Dimuat dari API",     RED),
            ("Film Favorit",      "0",  "Tersimpan di SQLite", "#7C3AED"),
            ("Rating Rata-rata",  "–",  "Dari daftar favorit", GOLD),
            ("Request API",       "0",  "Sesi ini",            BLUE_ACT),
        ]
        self._stats: list[StatCard] = []
        for lbl, val, sub, clr in items:
            c = StatCard(lbl, val, sub, clr)
            self._stats.append(c)
            row.addWidget(c)
        return row

    def _build_chart(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("chart_frame")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(8)

        lbl = QLabel("📊  Top 10 Film Paling Populer")
        lbl.setObjectName("section_title")
        sub = QLabel("Skor popularitas real-time dari TMDb API")
        sub.setObjectName("muted")
        lay.addWidget(lbl)
        lay.addWidget(sub)

        self._chart = QChart()
        self._chart.setBackgroundBrush(QColor(BG_SURFACE))
        self._chart.setPlotAreaBackgroundBrush(QColor(BG_SURFACE))
        self._chart.setPlotAreaBackgroundVisible(True)
        self._chart.legend().hide()
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        from PySide6.QtCore import QMargins
        self._chart.setMargins(QMargins(0, 0, 0, 0))

        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.Antialiasing)
        self._chart_view.setStyleSheet("background: transparent; border: none;")
        self._chart_view.setFixedHeight(240)
        lay.addWidget(self._chart_view)
        return frame

    def _build_recent_fav(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("chart_frame")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(0)

        hdr = QHBoxLayout()
        lbl = QLabel("❤️  Favorit Terbaru")
        lbl.setObjectName("section_title")
        self._lbl_hint_fav = QLabel("Klik baris untuk melihat detail & sinopsis")
        self._lbl_hint_fav.setStyleSheet(
            f"color: {GRAY_400}; font-size: 10px;"
        )
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(self._lbl_hint_fav)
        lay.addLayout(hdr)
        lay.addSpacing(14)

        col_hdr = QFrame()
        col_hdr.setFixedHeight(28)
        col_hdr.setStyleSheet(
            f"background: {BG_CARD}; border-radius: 4px;"
        )
        ch = QHBoxLayout(col_hdr)
        ch.setContentsMargins(0, 0, 8, 0)
        ch.setSpacing(12)
        for txt, w in [("JUDUL", 0), ("GENRE", 80), ("RATING", 55), ("TANGGAL", 85), ("", 16)]:
            l = QLabel(txt)
            l.setStyleSheet(
                f"color: {GRAY_100}; font-size: 9px; "
                f"font-weight: 700; letter-spacing: 1px;"
            )
            if w:
                l.setFixedWidth(w)
            else:
                l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            ch.addWidget(l)
        lay.addWidget(col_hdr)
        lay.addSpacing(4)

        self._fav_container = QVBoxLayout()
        self._fav_container.setSpacing(0)
        lay.addLayout(self._fav_container)

        self._lbl_no_fav = QLabel(
            "Belum ada film favorit. Tambahkan dari halaman Film Populer!"
        )
        self._lbl_no_fav.setAlignment(Qt.AlignCenter)
        self._lbl_no_fav.setStyleSheet(
            f"color: {GRAY_400}; padding: 24px; font-size: 12px;"
        )
        lay.addWidget(self._lbl_no_fav)
        return frame

    def refresh(self, film_list: list[dict] = None, api_req: int = 0):
        if film_list is not None:
            self._film_populer = film_list
        self._api_req = api_req
        self._update_stats()
        self._update_chart()
        self._update_recent_fav()

    def _update_stats(self):
        n   = self.db.count()
        avg = self.db.avg_rating()
        self._stats[0].set_value(
            str(len(self._film_populer)) if self._film_populer else "–"
        )
        self._stats[1].set_value(n)
        self._stats[2].set_value(f"{avg:.1f}" if avg else "–")
        self._stats[3].set_value(self._api_req)

    def _update_chart(self):
        self._chart.removeAllSeries()
        for ax in self._chart.axes():
            self._chart.removeAxis(ax)

        if not self._film_populer:
            return

        top10 = self._film_populer[:10]
        bs    = QBarSet("Popularitas")
        bs.setColor(QColor(RED))
        bs.setBorderColor(QColor(RED))
        cats  = []
        for f in top10:
            bs.append(round(f.get("popularity", 0), 1))
            t = f.get("title", "?")
            cats.append(t[:11] + "…" if len(t) > 11 else t)

        series = QBarSeries()
        series.append(bs)
        self._chart.addSeries(series)

        ax_x = QBarCategoryAxis()
        ax_x.append(cats)
        ax_x.setLabelsColor(QColor(GRAY_300))
        ax_x.setLabelsFont(QFont("Segoe UI", 7))
        ax_x.setGridLineVisible(False)
        ax_x.setLinePen(QPen(QColor(BORDER)))
        self._chart.addAxis(ax_x, Qt.AlignBottom)
        series.attachAxis(ax_x)

        ax_y = QValueAxis()
        ax_y.setLabelsColor(QColor(GRAY_300))
        ax_y.setLabelsFont(QFont("Segoe UI", 8))
        ax_y.setGridLineColor(QColor(BORDER))
        ax_y.setLinePen(QPen(QColor(BORDER)))
        self._chart.addAxis(ax_y, Qt.AlignLeft)
        series.attachAxis(ax_y)

    def _update_recent_fav(self):
        while self._fav_container.count():
            item = self._fav_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        favs = self.db.semua()[:8]  
        if not favs:
            self._lbl_no_fav.show()
            self._lbl_hint_fav.hide()
            return

        self._lbl_no_fav.hide()
        self._lbl_hint_fav.show()

        for f in favs:
            row = RecentFavRow(f)
            row.klik_detail.connect(self._on_klik_fav)
            self._fav_container.addWidget(row)

    def _on_klik_fav(self, data: dict):
        from ui.pages.favorites_page import FavDetailDialog
        dlg = FavDetailDialog(data, self.db, self._client, self)
        dlg.data_changed.connect(self._update_recent_fav)
        dlg.exec()
