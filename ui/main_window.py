from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QStatusBar,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QAction

from config import APP_NAME, APP_VERSION, WINDOW_W, WINDOW_H, TMDB_API_KEY
from api.tmdb_client import TMDbClient
from ui.pages.dashboard_page import DashboardPage
from ui.pages.movies_page import MoviesPage
from ui.pages.favorites_page import FavoritesPage
from ui.theme import (BG_BASE, WHITE,
                       GRAY_400, RED, GOLD, GREEN_ACT, BORDER)

ANGGOTA = [
    ("Apriesna Zulhan", "F1D02310100"),
    ("Cindy Natasya Aulia Putri", "F1D02310109"),
    ("Wahyu Indra Purnama", "F1D02410099"),
]

class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self.setObjectName("nav_btn")
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self.set_active(False)

    def set_active(self, v: bool):
        self.setProperty("active", v)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setText(f"   {self._icon}   {self._label}")


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(250)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        logo_f = QFrame()
        logo_f.setFixedHeight(72)
        logo_f.setStyleSheet(
            f"background: #0D0D0D; border-bottom: 1px solid {BORDER};"
        )
        ll = QHBoxLayout(logo_f)
        ll.setContentsMargins(20, 0, 20, 0)

        icon_box = QFrame()
        icon_box.setFixedSize(32, 32)
        icon_box.setStyleSheet(f"background: {RED}; border-radius: 6px;")
        ib_lay = QHBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib = QLabel("▶")
        ib.setAlignment(Qt.AlignCenter)
        ib.setStyleSheet("color: white; font-size: 12px; background: transparent;")
        ib_lay.addWidget(ib)

        lbl_logo = QLabel(APP_NAME.upper())
        lbl_logo.setObjectName("logo_text")
        lbl_logo.setFont(QFont("Segoe UI", 14, QFont.Black))

        ll.addWidget(icon_box)
        ll.addSpacing(10)
        ll.addWidget(lbl_logo)
        ll.addStretch()
        lay.addWidget(logo_f)
        lay.addSpacing(16)

        def section(t):
            l = QLabel(t)
            l.setObjectName("nav_section")
            l.setFixedHeight(28)
            l.setFont(QFont("Segoe UI", 8, QFont.Bold))
            lay.addWidget(l)

        section("MENU UTAMA")
        self.btn_dashboard = NavButton("⊞", "Dashboard")
        self.btn_movies    = NavButton("🎬", "Film Populer")
        lay.addWidget(self.btn_dashboard)
        lay.addWidget(self.btn_movies)

        lay.addSpacing(8)
        section("KOLEKSI")
        self.btn_favorites = NavButton("❤️", "Favorit Saya")
        lay.addWidget(self.btn_favorites)
        lay.addStretch()

        info = QFrame()
        info.setStyleSheet(
            f"background: #0D0D0D; border-top: 1px solid {BORDER};"
        )
        il = QVBoxLayout(info)
        il.setContentsMargins(20, 12, 20, 16)
        il.setSpacing(6)

        self.lbl_api = QLabel("● TMDb API · Menghubungkan...")
        self.lbl_api.setStyleSheet(f"color: {GOLD}; font-size: 10px;")
        self.lbl_db  = QLabel("● SQLite · cinetrack.db")
        self.lbl_db.setStyleSheet(f"color: #4DA3FF; font-size: 10px;")
        lbl_ver = QLabel(f"{APP_NAME} v{APP_VERSION}  ·  PySide6")
        lbl_ver.setStyleSheet(f"color: {GRAY_400}; font-size: 9px;")

        il.addWidget(self.lbl_api)
        il.addWidget(self.lbl_db)
        il.addWidget(lbl_ver)
        lay.addWidget(info)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0D0D0D"))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class Topbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setFixedHeight(56)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(32, 0, 32, 0)

        self.lbl_page = QLabel("Film Populer")
        self.lbl_page.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.lbl_page.setStyleSheet(f"color: {WHITE};")

        self.lbl_date = QLabel()
        self.lbl_date.setStyleSheet(f"color: {GRAY_400}; font-size: 11px;")

        lay.addWidget(self.lbl_page)
        lay.addStretch()
        lay.addWidget(self.lbl_date)

        self._update_date()
        t = QTimer(self)
        t.timeout.connect(self._update_date)
        t.start(60_000)

    def _update_date(self):
        self.lbl_date.setText(
            QDateTime.currentDateTime().toString("dddd, d MMMM yyyy  ·  HH:mm")
        )

    def set_page(self, name: str):
        self.lbl_page.setText(name)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Katalog Film Desktop")
        self.setMinimumSize(WINDOW_W, WINDOW_H)
        self._client  = TMDbClient(TMDB_API_KEY)
        self._api_req = 0
        self._build_menubar()
        self._build()
        self._navigate(0)

    def _build_menubar(self):
        mb = self.menuBar()

        menu_file = mb.addMenu("&File")

        act_dashboard = QAction("⊞  Dashboard", self)
        act_dashboard.setShortcut("Ctrl+1")
        act_dashboard.triggered.connect(lambda: self._navigate(0))

        act_movies = QAction("🎬  Film Populer", self)
        act_movies.setShortcut("Ctrl+2")
        act_movies.triggered.connect(lambda: self._navigate(1))

        act_fav = QAction("❤️  Favorit Saya", self)
        act_fav.setShortcut("Ctrl+3")
        act_fav.triggered.connect(lambda: self._navigate(2))

        act_exit = QAction("🚪  Keluar", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)

        menu_file.addAction(act_dashboard)
        menu_file.addAction(act_movies)
        menu_file.addAction(act_fav)
        menu_file.addSeparator()
        menu_file.addAction(act_exit)

        # ── Export ──
        menu_export = mb.addMenu("&Export")

        act_csv = QAction("📄  Export CSV", self)
        act_csv.setShortcut("Ctrl+E")
        act_csv.triggered.connect(self._export_csv)

        act_pdf = QAction("📑  Export PDF", self)
        act_pdf.setShortcut("Ctrl+Shift+E")
        act_pdf.triggered.connect(self._export_pdf)

        menu_export.addAction(act_csv)
        menu_export.addAction(act_pdf)

        menu_help = mb.addMenu("&Help")

        act_about = QAction("ℹ️  Tentang CineTrack", self)
        act_about.triggered.connect(self._show_about)

        act_anggota = QAction("👥  Anggota Kelompok", self)
        act_anggota.triggered.connect(self._show_anggota)

        menu_help.addAction(act_about)
        menu_help.addAction(act_anggota)

    def _export_csv(self):
        self._navigate(2)
        self._pg_fav.do_export_csv()

    def _export_pdf(self):
        self._navigate(2)
        self._pg_fav.do_export_pdf()

    def _show_about(self):
        QMessageBox.information(
            self, f"Tentang {APP_NAME}",
            f"<b>{APP_NAME} v{APP_VERSION}</b><br><br>"
            "Aplikasi katalog film desktop berbasis PySide6.<br>"
            "Data film dari <b>TMDb API v3</b>, disimpan lokal dengan <b>SQLite</b>.<br><br>"
            "Fitur: Dashboard · Film Populer · Favorit · Export CSV/PDF<br>"
            "Chart: QtCharts · Thread: QThread · Theme: Netflix Dark"
        )

    def _show_anggota(self):
        lines = "<br>".join(
            f"&nbsp;&nbsp;• <b>{n}</b> &nbsp;—&nbsp; NIM {nim}"
            for n, nim in ANGGOTA
        )
        QMessageBox.information(
            self, "👥  Anggota Kelompok",
            f"<b>Kelompok CineTrack</b><br><br>{lines}"
        )

    def _build(self):
        central = QWidget()
        central.setObjectName("root_widget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.btn_dashboard.clicked.connect(lambda: self._navigate(0))
        self._sidebar.btn_movies.clicked.connect(lambda: self._navigate(1))
        self._sidebar.btn_favorites.clicked.connect(lambda: self._navigate(2))
        root.addWidget(self._sidebar)

        right = QWidget()
        right.setStyleSheet(f"background: {BG_BASE};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self._topbar = Topbar()
        rl.addWidget(self._topbar)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {BG_BASE};")

        self._pg_dash   = DashboardPage()
        self._pg_dash.set_client(self._client)
        self._pg_movies = MoviesPage(self._client)
        self._pg_movies.favorite_changed.connect(self._on_fav_changed)
        self._pg_fav    = FavoritesPage(self._client)

        self._stack.addWidget(self._pg_dash)    
        self._stack.addWidget(self._pg_movies)  
        self._stack.addWidget(self._pg_fav)     

        rl.addWidget(self._stack)
        root.addWidget(right, stretch=1)

        self._sb = QStatusBar()
        self._sb.setSizeGripEnabled(False)
        self.setStatusBar(self._sb)

        nim_text = "  👥  " + "   |   ".join(
            f"{n}  ({nim})" for n, nim in ANGGOTA
        )
        lbl_nim = QLabel(nim_text)
        lbl_nim.setStyleSheet("color: #4DA3FF; font-size: 10px;")
        self._sb.addPermanentWidget(lbl_nim)

        self._lbl_time = QLabel()
        self._lbl_time.setStyleSheet("color: #4A4A4A; font-size: 10px;")
        self._sb.addWidget(self._lbl_time)

        self._update_status()
        t = QTimer(self)
        t.timeout.connect(self._update_status)
        t.start(60_000)

    def _navigate(self, idx: int):
        self._stack.setCurrentIndex(idx)
        pages = ["Dashboard", "Film Populer", "Favorit Saya"]
        self._topbar.set_page(pages[idx])
        self._sidebar.btn_dashboard.set_active(idx == 0)
        self._sidebar.btn_movies.set_active(idx == 1)
        self._sidebar.btn_favorites.set_active(idx == 2)

        if idx == 0:
            self._pg_dash.refresh(self._pg_movies._films, self._api_req)
        elif idx == 2:
            self._pg_fav.load_favorites()
            self._pg_movies.refresh_card_states()
        self._update_status()

    def _on_fav_changed(self, msg: str):
        self._sb.showMessage(f"  {msg}", 5000)
        self._api_req = self._pg_movies.api_req
        from database.db_manager import DatabaseManager
        n = DatabaseManager().count()
        self._sidebar.lbl_db.setText(f"● SQLite · {n} film favorit")
        self._sidebar.lbl_api.setText("● TMDb API · Online ✓")
        self._sidebar.lbl_api.setStyleSheet(
            f"color: {GREEN_ACT}; font-size: 10px;"
        )
        if self._stack.currentIndex() == 0:
            self._pg_dash.refresh(self._pg_movies._films, self._api_req)

    def _update_status(self):
        now = QDateTime.currentDateTime().toString("ddd, d MMM yyyy · HH:mm")
        self._lbl_time.setText(f"  📅 {now}   ·   TMDb API v3   ·   PySide6 6.x  ")

    def closeEvent(self, e):
        self._pg_movies._cleanup()
        super().closeEvent(e)
