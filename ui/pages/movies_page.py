import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QMessageBox,
    QProgressBar, QDialog, QFormLayout, QTextEdit, QDoubleSpinBox,
    QComboBox, QDialogButtonBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap

from ui.components.movie_card import MovieCard
from ui.components.hero_banner import HeroBanner
from ui.components.image_cache import get_cached, store
from ui.theme import (BG_BASE, BG_SURFACE, WHITE, GRAY_200, GRAY_300,
                       GRAY_400, RED, GOLD, GREEN_ACT, BORDER, GENRE_NAMES)
from api.workers import MovieFetchWorker, ImageWorker
from database.db_manager import DatabaseManager
from config import TMDB_API_KEY, POSTER_FETCH_PAGES

GENRES_FILTER = [
    ("Semua", None), ("Aksi", 28), ("Drama", 18), ("Komedi", 35),
    ("Horor", 27), ("Sci-Fi", 878), ("Animasi", 16),
    ("Romantis", 10749), ("Thriller", 53), ("Petualangan", 12),
    ("Fantasi", 14), ("Keluarga", 10751),
]
GENRE_LIST_EDIT = [
    "Film","Aksi","Drama","Komedi","Horor","Sci-Fi",
    "Animasi","Romantis","Thriller","Petualangan","Fantasi","Lainnya"
]


def _spin_row(spin: QDoubleSpinBox) -> QHBoxLayout:
    spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
    spin.setFixedWidth(80)
    row = QHBoxLayout()
    row.setSpacing(6)
    btn_m = QPushButton("−")
    btn_m.setObjectName("btn_ghost")
    btn_m.setFixedSize(32, 32)
    btn_m.clicked.connect(
        lambda: spin.setValue(round(max(0.0, spin.value() - 0.1), 1))
    )
    btn_p = QPushButton("+")
    btn_p.setObjectName("btn_ghost")
    btn_p.setFixedSize(32, 32)
    btn_p.clicked.connect(
        lambda: spin.setValue(round(min(10.0, spin.value() + 0.1), 1))
    )
    row.addWidget(btn_m)
    row.addWidget(spin)
    row.addWidget(btn_p)
    row.addStretch()
    return row


class CatatanDialog(QDialog):
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝  Catatan Film")
        self.setMinimumWidth(440)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel(f"📝  {data.get('judul','Film')}")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet(f"color: {WHITE};")
        lay.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border: none; border-top: 1px solid {BORDER};")
        lay.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo = QComboBox()
        self.combo.addItems(GENRE_LIST_EDIT)
        idx = self.combo.findText(data.get("genre", "Film"))
        self.combo.setCurrentIndex(max(idx, 0))
        form.addRow("Genre", self.combo)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0, 10)
        self.spin.setSingleStep(0.1)
        self.spin.setDecimals(1)
        self.spin.setValue(float(data.get("rating", 0)))
        form.addRow("Rating Pribadi (0–10)", _spin_row(self.spin))

        self.txt = QTextEdit()
        self.txt.setPlainText(data.get("catatan", ""))
        self.txt.setFixedHeight(100)
        self.txt.setPlaceholderText(
            "Tulis kesan atau catatan pribadi tentang film ini..."
        )
        form.addRow("Catatan", self.txt)

        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self) -> dict:
        return {
            "genre":   self.combo.currentText(),
            "rating":  self.spin.value(),
            "catatan": self.txt.toPlainText().strip(),
        }


class DetailDialog(QDialog):
    favorite_changed = Signal(str)

    def __init__(self, film: dict, db: DatabaseManager, client, parent=None):
        super().__init__(parent)
        self.film        = film
        self.db          = db
        self.client      = client
        self._fav        = db.by_tmdb(film.get("id"))
        self._img_worker = None
        self.setWindowTitle(film.get("title", "Detail Film"))
        self.setMinimumSize(720, 480)
        self.setModal(True)
        self._build()
        self._load_poster()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._poster_lbl = QLabel("⏳")
        self._poster_lbl.setFixedSize(240, 360)
        self._poster_lbl.setAlignment(Qt.AlignCenter)
        self._poster_lbl.setFont(QFont("Segoe UI Emoji", 28))
        self._poster_lbl.setStyleSheet(f"background: {BG_SURFACE};")
        root.addWidget(self._poster_lbl)

        right = QWidget()
        right.setStyleSheet(f"background: {BG_SURFACE};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(28, 28, 28, 28)
        rl.setSpacing(10)

        judul = self.film.get("title", "?")
        lbl_j = QLabel(judul)
        lbl_j.setFont(QFont("Segoe UI", 17, QFont.Black))
        lbl_j.setStyleSheet(f"color: {WHITE}; background: transparent;")
        lbl_j.setWordWrap(True)
        rl.addWidget(lbl_j)

        tahun  = str(self.film.get("release_date", ""))[:4] or "–"
        rating = self.film.get("vote_average", 0)
        gids   = self.film.get("genre_ids", [])
        genres = ", ".join(
            GENRE_NAMES.get(g, "") for g in gids[:4] if g in GENRE_NAMES
        )
        lbl_m = QLabel(f"⭐ {rating:.1f}  ·  {tahun}  ·  {genres}")
        lbl_m.setStyleSheet(
            f"color: {GRAY_200}; font-size: 12px; background: transparent;"
        )
        rl.addWidget(lbl_m)

        desc = self.film.get("overview", "").strip() or "Sinopsis tidak tersedia."
        lbl_d = QLabel(desc)
        lbl_d.setStyleSheet(
            f"color: {GRAY_200}; font-size: 12px; background: transparent;"
        )
        lbl_d.setWordWrap(True)
        rl.addWidget(lbl_d)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border: none; border-top: 1px solid {BORDER};")
        rl.addWidget(sep)

        lbl_c = QLabel("CATATAN PRIBADI")
        lbl_c.setObjectName("form_label")
        rl.addWidget(lbl_c)

        self._txt = QTextEdit()
        self._txt.setFixedHeight(75)
        self._txt.setPlaceholderText("Tulis catatan pribadi...")
        if self._fav:
            self._txt.setPlainText(self._fav.get("catatan", ""))
        rl.addWidget(self._txt)

        lbl_r = QLabel("RATING PRIBADI")
        lbl_r.setObjectName("form_label")
        rl.addWidget(lbl_r)

        self._spin = QDoubleSpinBox()
        self._spin.setRange(0, 10)
        self._spin.setSingleStep(0.1)
        self._spin.setDecimals(1)
        self._spin.setValue(
            float(self._fav.get("rating", 0)) if self._fav else rating
        )
        rl.addLayout(_spin_row(self._spin))

        rl.addStretch()

        row_btn = QHBoxLayout()
        row_btn.setSpacing(10)

        is_fav = self._fav is not None
        self._btn_fav = QPushButton(
            "♥  Hapus dari Favorit" if is_fav else "♥  Tambah ke Favorit"
        )
        self._btn_fav.setObjectName("btn_danger" if is_fav else "btn_primary")
        self._btn_fav.setFixedHeight(40)
        self._btn_fav.clicked.connect(self._toggle_fav)

        btn_save = QPushButton("💾  Simpan Catatan")
        btn_save.setObjectName("btn_secondary")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self._save_catatan)

        btn_close = QPushButton("Tutup")
        btn_close.setObjectName("btn_ghost")
        btn_close.setFixedHeight(40)
        btn_close.clicked.connect(self.accept)

        row_btn.addWidget(self._btn_fav)
        row_btn.addWidget(btn_save)
        row_btn.addStretch()
        row_btn.addWidget(btn_close)
        rl.addLayout(row_btn)

        root.addWidget(right, stretch=1)

    def _load_poster(self):
        path = self.film.get("poster_path")
        if not path:
            return
        url = self.client.poster_url(path, "w500")
        if not url:
            return
        px = get_cached(url)
        if px:
            self._set_poster(px)
            return
        self._img_worker = ImageWorker(self.client, url)
        self._img_worker.finished.connect(
            lambda u, d: self._set_poster(store(u, d))
        )
        self._img_worker.start()

    def _set_poster(self, px: QPixmap):
        if px and not px.isNull():
            scaled = px.scaled(
                240, 360, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (scaled.width() - 240) // 2
            y = (scaled.height() - 360) // 2
            self._poster_lbl.setPixmap(scaled.copy(x, y, 240, 360))
            self._poster_lbl.setText("")

    def _toggle_fav(self):
        if self._fav:
            self.db.hapus(self._fav["id"])
            self._fav = None
            self._btn_fav.setText("♥  Tambah ke Favorit")
            self._btn_fav.setObjectName("btn_primary")
            self._btn_fav.style().unpolish(self._btn_fav)
            self._btn_fav.style().polish(self._btn_fav)
            self.favorite_changed.emit(
                f'"{self.film.get("title")}" dihapus dari favorit'
            )
        else:
            gids  = self.film.get("genre_ids", [])
            genre = GENRE_NAMES.get(gids[0] if gids else 0, "Film")
            fid   = self.db.tambah(
                tmdb_id       = self.film.get("id"),
                judul         = self.film.get("title", "?"),
                genre         = genre,
                rating        = self._spin.value(),
                catatan       = self._txt.toPlainText().strip(),
                poster_path   = self.film.get("poster_path", ""),
                backdrop_path = self.film.get("backdrop_path", ""),
                overview      = self.film.get("overview", ""),
                release_year  = str(self.film.get("release_date", ""))[:4],
            )
            self._fav = self.db.by_id(fid)
            self._btn_fav.setText("♥  Hapus dari Favorit")
            self._btn_fav.setObjectName("btn_danger")
            self._btn_fav.style().unpolish(self._btn_fav)
            self._btn_fav.style().polish(self._btn_fav)
            self.favorite_changed.emit(
                f'"{self.film.get("title")}" ditambahkan ke favorit ❤️'
            )

    def _save_catatan(self):
        if self._fav:
            self.db.update(
                self._fav["id"],
                self._fav.get("judul", ""),
                self._fav.get("genre", ""),
                self._spin.value(),
                self._txt.toPlainText().strip(),
            )
            self.favorite_changed.emit("Catatan berhasil disimpan 💾")
        else:
            QMessageBox.information(
                self, "Info",
                "Tambahkan film ke favorit terlebih dahulu."
            )

    def closeEvent(self, e):
        if self._img_worker and self._img_worker.isRunning():
            self._img_worker.stop()
        super().closeEvent(e)


class MoviesPage(QWidget):
    favorite_changed = Signal(str)

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client         = client
        self.db             = DatabaseManager()
        self._films: list[dict] = []
        self._cards: list[MovieCard] = []
        self._img_workers: list[ImageWorker] = []
        self._backdrop_worker: ImageWorker | None = None  
        self._fetch_worker  = None
        self._pages_loaded  = 0
        self._genre_id      = None
        self._api_req       = 0
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(3)
        self._progress.hide()
        root.addWidget(self._progress)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        page = QWidget()
        page.setStyleSheet(f"background: {BG_BASE};")
        self._lay = QVBoxLayout(page)
        self._lay.setContentsMargins(0, 0, 0, 48)
        self._lay.setSpacing(0)

        self._hero = HeroBanner()
        self._hero.klik_favorit.connect(self._toggle_fav)
        self._hero.klik_detail.connect(self._show_detail)
        self._lay.addWidget(self._hero)

        konten = QWidget()
        konten.setStyleSheet(f"background: {BG_BASE};")
        kl = QVBoxLayout(konten)
        kl.setContentsMargins(40, 28, 40, 0)
        kl.setSpacing(20)

        kl.addLayout(self._build_searchbar())
        kl.addLayout(self._build_chips())

        row_sec = QHBoxLayout()
        self._lbl_section = QLabel("Film Populer Saat Ini")
        self._lbl_section.setObjectName("section_title")
        self._lbl_count = QLabel("")
        self._lbl_count.setObjectName("muted")
        row_sec.addWidget(self._lbl_section)
        row_sec.addStretch()
        row_sec.addWidget(self._lbl_count)
        kl.addLayout(row_sec)

        self._grid_frame = QFrame()
        self._grid_frame.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._grid_frame)
        self._grid.setSpacing(16)
        self._grid.setContentsMargins(0, 0, 0, 0)
        kl.addWidget(self._grid_frame)

        self._lbl_info = QLabel("⏳  Memuat film dari TMDb API...")
        self._lbl_info.setAlignment(Qt.AlignCenter)
        self._lbl_info.setStyleSheet(
            f"color: {GRAY_300}; font-size: 14px; padding: 60px;"
        )
        kl.addWidget(self._lbl_info)

        self._btn_more = QPushButton("MUAT LEBIH BANYAK")
        self._btn_more.setObjectName("load_more_btn")
        self._btn_more.setFixedHeight(42)
        self._btn_more.hide()
        self._btn_more.clicked.connect(self._load_more)
        kl.addSpacing(16)
        kl.addWidget(self._btn_more, 0, Qt.AlignCenter)
        kl.addStretch()

        self._lay.addWidget(konten)
        scroll.setWidget(page)
        root.addWidget(scroll)

        QTimer.singleShot(300, self._initial_load)

    def _build_searchbar(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._search = QLineEdit()
        self._search.setObjectName("search_input")
        self._search.setPlaceholderText("🔍  Cari judul film...")
        self._search.setFixedWidth(300)
        self._search.setFixedHeight(38)
        self._search.textChanged.connect(self._render_grid)

        self._lbl_api = QLabel("● Menghubungkan...")
        self._lbl_api.setStyleSheet(
            f"color: {GOLD}; font-size: 11px; font-weight: 600;"
        )

        btn_ref = QPushButton("🔄  Refresh")
        btn_ref.setObjectName("btn_ghost")
        btn_ref.setFixedHeight(38)
        btn_ref.clicked.connect(self._initial_load)

        row.addWidget(self._search)
        row.addStretch()
        row.addWidget(self._lbl_api)
        row.addSpacing(16)
        row.addWidget(btn_ref)
        return row

    def _build_chips(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        self._chips: list[QPushButton] = []
        for nama, gid in GENRES_FILTER:
            btn = QPushButton(nama)
            btn.setObjectName("genre_chip")
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("active", gid is None)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.clicked.connect(
                lambda _, g=gid, b=btn: self._set_genre(g, b)
            )
            self._chips.append(btn)
            row.addWidget(btn)
        row.addStretch()
        return row

    def _initial_load(self):
        self._films.clear()
        self._pages_loaded = 0
        self._stop_fetch()
        self._fetch(POSTER_FETCH_PAGES)

    def _load_more(self):
        self._stop_fetch()
        self._fetch(self._pages_loaded + 2)

    def _fetch(self, up_to_page: int):
        self._progress.show()
        self._lbl_info.setText("⏳  Memuat film...")
        self._lbl_info.show()
        self._set_api_status("connecting")

        self._fetch_worker = MovieFetchWorker(self.client, pages=up_to_page)
        self._fetch_worker.finished.connect(self._on_films)
        self._fetch_worker.error.connect(self._on_error)
        self._fetch_worker.progress.connect(
            lambda d, t: self._lbl_info.setText(f"⏳  Memuat halaman {d}/{t}...")
        )
        self._fetch_worker.start()
        self._api_req += 1
        self._pages_loaded = up_to_page

    def _stop_fetch(self):
        if self._fetch_worker and self._fetch_worker.isRunning():
            self._fetch_worker.stop()
            self._fetch_worker = None

    def _stop_img_workers(self):
        for w in self._img_workers:
            if w.isRunning():
                w.stop()
        self._img_workers.clear()

    def _on_films(self, films: list):
        self._progress.hide()
        self._films = films
        self._set_api_status("online")

        if films:
            hero = random.choice(films[:10])
            self._hero.set_film(hero)
            self._load_backdrop(hero)

        self._render_grid()
        total = len(films)
        self._btn_more.setText(f"MUAT LEBIH BANYAK  ({total} film dimuat)")
        self._btn_more.show()
        self.favorite_changed.emit(f"✅  {total} film dimuat dari TMDb API")

    def _on_error(self, msg: str):
        self._progress.hide()
        self._lbl_info.setText("⚠️  Gagal memuat. Klik Refresh untuk coba lagi.")
        self._set_api_status("offline")
        box = QMessageBox(self)
        box.setWindowTitle("⚠️  Koneksi API Bermasalah")
        box.setIcon(QMessageBox.Warning)
        box.setText("<b>Tidak dapat terhubung ke TMDb API</b>")
        box.setInformativeText(
            f"{msg}\n\n"
            "• Cek koneksi internet Anda\n"
            "• Pastikan API key benar di config.py\n"
            "• Klik Retry untuk coba lagi"
        )
        box.setStandardButtons(QMessageBox.Retry | QMessageBox.Ok)
        if box.exec() == QMessageBox.Retry:
            QTimer.singleShot(500, self._initial_load)

    def _render_grid(self):
        self._stop_img_workers()

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        fav_ids = self.db.tmdb_ids()

        tampil = self._films
        if self._genre_id:
            tampil = [
                f for f in tampil
                if self._genre_id in f.get("genre_ids", [])
            ]

        q = self._search.text().strip().lower()
        if q:
            tampil = [
                f for f in tampil
                if q in f.get("title", "").lower()
            ]

        if not tampil:
            self._lbl_info.setText("🔍  Tidak ada film yang cocok.")
            self._lbl_info.show()
            self._lbl_count.setText("")
            return

        self._lbl_info.hide()
        self._lbl_count.setText(f"{len(tampil)} film")

        COLS = 6
        for i, film in enumerate(tampil):
            card = MovieCard(film, film.get("id") in fav_ids)
            card.klik_detail.connect(self._show_detail)
            card.klik_simpan.connect(self._toggle_fav)
            r, c = divmod(i, COLS)
            self._grid.addWidget(card, r, c)
            self._cards.append(card)
            self._lazy_load_poster(card, film)

    def _lazy_load_poster(self, card: MovieCard, film: dict):
        path = film.get("poster_path")
        if not path:
            return
        url = self.client.poster_url(path, "w500")
        if not url:
            return
        px = get_cached(url)
        if px:
            card.set_poster(px)
            return
        w = ImageWorker(self.client, url)
        w.finished.connect(
            lambda u, data, c=card: c.set_poster(store(u, data))
        )
        w.start()
        self._img_workers.append(w)

    def _load_backdrop(self, film: dict):
        if self._backdrop_worker and self._backdrop_worker.isRunning():
            self._backdrop_worker.stop()
            self._backdrop_worker = None

        path = film.get("backdrop_path")
        if not path:
            return
        url = self.client.backdrop_url(path)
        if not url:
            return
        px = get_cached(url)
        if px:
            self._hero.set_backdrop(px)
            return
        self._backdrop_worker = ImageWorker(self.client, url)
        self._backdrop_worker.finished.connect(
            lambda u, data: self._hero.set_backdrop(store(u, data))
        )
        self._backdrop_worker.start()

    def _toggle_fav(self, film: dict):
        tmdb_id  = film.get("id")
        judul    = film.get("title", "Film")
        existing = self.db.by_tmdb(tmdb_id)

        if existing:
            self.db.hapus(existing["id"])
            self.favorite_changed.emit(f'"{judul}" dihapus dari favorit')
        else:
            gids  = film.get("genre_ids", [])
            genre = GENRE_NAMES.get(gids[0] if gids else 0, "Film")
            dlg   = CatatanDialog(
                {"judul": judul, "genre": genre,
                 "rating": film.get("vote_average", 0), "catatan": ""},
                self
            )
            if dlg.exec() == QDialog.Accepted:
                d = dlg.get_data()
                self.db.tambah(
                    tmdb_id       = tmdb_id,
                    judul         = judul,
                    genre         = d["genre"],
                    rating        = d["rating"],
                    catatan       = d["catatan"],
                    poster_path   = film.get("poster_path", ""),
                    backdrop_path = film.get("backdrop_path", ""),
                    overview      = film.get("overview", ""),
                    release_year  = str(film.get("release_date", ""))[:4],
                )
                self.favorite_changed.emit(
                    f'"{judul}" ditambahkan ke favorit ❤️'
                )
            else:
                return

        fav_ids = self.db.tmdb_ids()
        for c in self._cards:
            c.set_tersimpan(c.data.get("id") in fav_ids)

    def _show_detail(self, film: dict):
        dlg = DetailDialog(film, self.db, self.client, self)
        dlg.favorite_changed.connect(self.favorite_changed)
        dlg.exec()
        fav_ids = self.db.tmdb_ids()
        for c in self._cards:
            c.set_tersimpan(c.data.get("id") in fav_ids)

    def _set_genre(self, gid, btn: QPushButton):
        self._genre_id = gid
        for c in self._chips:
            c.setProperty("active", c is btn)
            c.style().unpolish(c)
            c.style().polish(c)
        self._render_grid()

    def _set_api_status(self, status: str):
        mapping = {
            "online":     ("● TMDb API  Online ✓", GREEN_ACT),
            "offline":    ("● TMDb API  Offline",  RED),
            "connecting": ("● Menghubungkan...",   GOLD),
        }
        txt, clr = mapping.get(status, ("●", GRAY_300))
        self._lbl_api.setText(txt)
        self._lbl_api.setStyleSheet(
            f"color: {clr}; font-size: 11px; font-weight: 600;"
        )

    def refresh_card_states(self):
        fav_ids = self.db.tmdb_ids()
        for c in self._cards:
            c.set_tersimpan(c.data.get("id") in fav_ids)

    @property
    def api_req(self):
        return self._api_req

    def closeEvent(self, e):
        self._cleanup()
        super().closeEvent(e)

    def hideEvent(self, e):
        super().hideEvent(e)

    def _cleanup(self):
        self._stop_fetch()
        self._stop_img_workers()
        if self._backdrop_worker and self._backdrop_worker.isRunning():
            self._backdrop_worker.stop()
            self._backdrop_worker = None

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            pass