from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QDoubleSpinBox, QComboBox, QDialogButtonBox,
    QSizePolicy, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QColor, QCursor
import os

from database.db_manager import DatabaseManager
from ui.components.image_cache import get_cached, store
from ui.theme import (BG_BASE, BG_SURFACE, BG_CARD, WHITE,
                       GRAY_200, GRAY_300, GRAY_400, RED, GOLD, GREEN_ACT,
                       BORDER)

GENRE_LIST = ["Film","Aksi","Drama","Komedi","Horor","Sci-Fi",
              "Animasi","Romantis","Thriller","Petualangan","Fantasi","Lainnya"]

SORT_OPTIONS = [
    ("Terbaru Ditambahkan", "id_desc"),
    ("Terlama Ditambahkan", "id_asc"),
    ("Rating Tertinggi",    "rating_desc"),
    ("Rating Terendah",     "rating_asc"),
    ("Judul A–Z",           "judul_asc"),
    ("Judul Z–A",           "judul_desc"),
]

TABLE_COLS = ["#", "Judul", "Genre", "Rating", "Tahun", "Catatan", "Ditambahkan"]


def _preview_pixmap(path: str, w: int, h: int):
    if path and os.path.isfile(path):
        px = QPixmap(path)
        if not px.isNull():
            return px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None


def _make_img_panel(preview_lbl: QLabel, pilih_fn, hapus_fn) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setSpacing(8)
    lay.setAlignment(Qt.AlignTop)
    lbl = QLabel("Poster")
    lbl.setStyleSheet(f"color:{GRAY_300}; font-size:11px; font-weight:600;")
    btn_p = QPushButton("📁  Pilih Gambar")
    btn_p.setObjectName("btn_ghost")
    btn_p.setFixedWidth(120)
    btn_p.clicked.connect(pilih_fn)
    btn_h = QPushButton("✕  Hapus")
    btn_h.setObjectName("btn_ghost")
    btn_h.setFixedWidth(120)
    btn_h.clicked.connect(hapus_fn)
    lay.addWidget(lbl)
    lay.addWidget(preview_lbl)
    lay.addWidget(btn_p)
    lay.addWidget(btn_h)
    return lay


def _make_preview_lbl() -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(120, 180)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setText("🎬")
    lbl.setFont(QFont("Segoe UI Emoji", 28))
    lbl.setStyleSheet(f"background:{BG_CARD}; border:1px dashed {GRAY_400}; border-radius:6px; color:{GRAY_300};")
    return lbl


def _spin_row(spin: QDoubleSpinBox) -> QHBoxLayout:
    spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
    spin.setFixedWidth(80)
    row = QHBoxLayout()
    row.setSpacing(6)
    btn_m = QPushButton("−")
    btn_m.setObjectName("btn_ghost")
    btn_m.setFixedSize(32, 32)
    btn_m.clicked.connect(lambda: spin.setValue(round(max(0.0, spin.value() - 0.1), 1)))
    btn_p = QPushButton("+")
    btn_p.setObjectName("btn_ghost")
    btn_p.setFixedSize(32, 32)
    btn_p.clicked.connect(lambda: spin.setValue(round(min(10.0, spin.value() + 0.1), 1)))
    row.addWidget(btn_m)
    row.addWidget(spin)
    row.addWidget(btn_p)
    row.addStretch()
    return row


class EditDialog(QDialog):
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️  Edit Film Favorit")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._poster_path = data.get("poster_path", "") or ""

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel(f"✏️  {data.get('judul','?')}")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet(f"color:{WHITE};")
        lay.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border:none;border-top:1px solid {BORDER};")
        lay.addWidget(sep)

        body = QHBoxLayout()
        body.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.judul_edit = QLineEdit()
        self.judul_edit.setMaxLength(100)
        self.judul_edit.setText(data.get("judul", ""))
        form.addRow("Judul *", self.judul_edit)

        self.combo = QComboBox()
        self.combo.addItems(GENRE_LIST)
        idx = self.combo.findText(data.get("genre", "Film"))
        self.combo.setCurrentIndex(max(idx, 0))
        form.addRow("Genre", self.combo)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0, 10)
        self.spin.setSingleStep(0.1)
        self.spin.setDecimals(1)
        self.spin.setValue(float(data.get("rating", 0)))
        form.addRow("Rating (0–10)", _spin_row(self.spin))

        self.tahun_edit = QLineEdit()
        self.tahun_edit.setMaxLength(4)
        self.tahun_edit.setPlaceholderText("contoh: 2023")
        self.tahun_edit.setText(data.get("release_year", "") or "")
        form.addRow("Tahun Rilis", self.tahun_edit)

        self.txt = QTextEdit()
        self.txt.setPlainText(data.get("catatan", ""))
        self.txt.setFixedHeight(80)
        self.txt.setPlaceholderText("Tulis catatan pribadi...")
        form.addRow("Catatan", self.txt)

        body.addLayout(form, stretch=1)

        self._img_preview = _make_preview_lbl()
        px = _preview_pixmap(self._poster_path, 120, 180)
        if px:
            self._img_preview.setPixmap(px)
            self._img_preview.setText("")

        body.addLayout(_make_img_panel(self._img_preview, self._pilih_gambar, self._hapus_gambar))
        lay.addLayout(body)

        lbl_req = QLabel("* Wajib diisi  ·  Format gambar: JPG, PNG, BMP, WEBP")
        lbl_req.setStyleSheet(f"color:{GRAY_400}; font-size:10px;")
        lay.addWidget(lbl_req)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _pilih_gambar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Gambar Poster", "",
            "Gambar (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        if not path:
            return
        self._poster_path = path
        px = _preview_pixmap(path, 120, 180)
        if px:
            self._img_preview.setPixmap(px)
            self._img_preview.setText("")

    def _hapus_gambar(self):
        self._poster_path = ""
        self._img_preview.clear()
        self._img_preview.setText("🎬")

    def _validate_and_accept(self):
        judul = self.judul_edit.text().strip()
        if not judul:
            QMessageBox.warning(self, "Validasi", "Judul film tidak boleh kosong.")
            self.judul_edit.setFocus()
            return
        if len(judul) < 2:
            QMessageBox.warning(self, "Validasi", "Judul film minimal 2 karakter.")
            return
        tahun = self.tahun_edit.text().strip()
        if tahun and (not tahun.isdigit() or not (1888 <= int(tahun) <= 2100)):
            QMessageBox.warning(self, "Validasi", "Tahun rilis tidak valid (1888–2100).")
            return
        if not (0 <= self.spin.value() <= 10):
            QMessageBox.warning(self, "Validasi", "Rating harus antara 0 hingga 10.")
            return
        if len(self.txt.toPlainText().strip()) > 500:
            QMessageBox.warning(self, "Validasi", "Catatan maksimal 500 karakter.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "judul":        self.judul_edit.text().strip(),
            "genre":        self.combo.currentText(),
            "rating":       self.spin.value(),
            "release_year": self.tahun_edit.text().strip(),
            "catatan":      self.txt.toPlainText().strip(),
            "poster_path":  self._poster_path,
        }


class TambahManualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕  Tambah Film Favorite")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._poster_path = ""

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel("➕  Tambah Film ke Favorit")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet(f"color:{WHITE};")
        lay.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border:none;border-top:1px solid {BORDER};")
        lay.addWidget(sep)

        body = QHBoxLayout()
        body.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.judul_edit = QLineEdit()
        self.judul_edit.setPlaceholderText("Masukkan judul film...")
        self.judul_edit.setMaxLength(100)
        form.addRow("Judul *", self.judul_edit)

        self.combo = QComboBox()
        self.combo.addItems(GENRE_LIST)
        form.addRow("Genre", self.combo)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0, 10)
        self.spin.setSingleStep(0.1)
        self.spin.setDecimals(1)
        self.spin.setValue(0.0)
        form.addRow("Rating (0–10)", _spin_row(self.spin))

        self.tahun_edit = QLineEdit()
        self.tahun_edit.setPlaceholderText("contoh: 2023")
        self.tahun_edit.setMaxLength(4)
        form.addRow("Tahun Rilis", self.tahun_edit)

        self.txt = QTextEdit()
        self.txt.setFixedHeight(80)
        self.txt.setPlaceholderText("Tulis catatan pribadi (opsional)...")
        form.addRow("Catatan", self.txt)

        body.addLayout(form, stretch=1)

        self._img_preview = _make_preview_lbl()
        body.addLayout(_make_img_panel(self._img_preview, self._pilih_gambar, self._hapus_gambar))
        lay.addLayout(body)

        lbl_req = QLabel("* Wajib diisi  ·  Format gambar: JPG, PNG, BMP, WEBP")
        lbl_req.setStyleSheet(f"color:{GRAY_400}; font-size:10px;")
        lay.addWidget(lbl_req)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _pilih_gambar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Gambar Poster", "",
            "Gambar (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        if not path:
            return
        self._poster_path = path
        px = _preview_pixmap(path, 120, 180)
        if px:
            self._img_preview.setPixmap(px)
            self._img_preview.setText("")

    def _hapus_gambar(self):
        self._poster_path = ""
        self._img_preview.clear()
        self._img_preview.setText("🎬")

    def _validate_and_accept(self):
        judul = self.judul_edit.text().strip()
        if not judul:
            QMessageBox.warning(self, "Validasi", "Judul film tidak boleh kosong.")
            self.judul_edit.setFocus()
            return
        if len(judul) < 2:
            QMessageBox.warning(self, "Validasi", "Judul film minimal 2 karakter.")
            return
        tahun = self.tahun_edit.text().strip()
        if tahun and (not tahun.isdigit() or not (1888 <= int(tahun) <= 2100)):
            QMessageBox.warning(self, "Validasi", "Tahun rilis tidak valid (1888–2100).")
            return
        if len(self.txt.toPlainText().strip()) > 500:
            QMessageBox.warning(self, "Validasi", "Catatan maksimal 500 karakter.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "judul":        self.judul_edit.text().strip(),
            "genre":        self.combo.currentText(),
            "rating":       self.spin.value(),
            "release_year": self.tahun_edit.text().strip(),
            "catatan":      self.txt.toPlainText().strip(),
            "poster_path":  self._poster_path,
        }


class FavDetailDialog(QDialog):
    data_changed = Signal()

    def __init__(self, data: dict, db: DatabaseManager, client=None, parent=None):
        super().__init__(parent)
        self._data       = data
        self._db         = db
        self._client     = client
        self._img_worker = None
        self.setWindowTitle(data.get("judul", "Detail Film"))
        self.setMinimumSize(720, 460)
        self.setModal(True)
        self._build()
        self._load_poster()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._poster_lbl = QLabel("🎬")
        self._poster_lbl.setFixedSize(220, 330)
        self._poster_lbl.setAlignment(Qt.AlignCenter)
        self._poster_lbl.setFont(QFont("Segoe UI Emoji", 36))
        self._poster_lbl.setStyleSheet(f"background:{BG_CARD}; border-radius:0;")
        root.addWidget(self._poster_lbl)

        right = QFrame()
        right.setStyleSheet(f"background:{BG_SURFACE};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(28, 28, 28, 28)
        rl.setSpacing(10)

        lbl_j = QLabel(self._data.get("judul", "?"))
        lbl_j.setFont(QFont("Segoe UI", 17, QFont.Black))
        lbl_j.setStyleSheet(f"color:{WHITE}; background:transparent;")
        lbl_j.setWordWrap(True)
        rl.addWidget(lbl_j)

        rating = float(self._data.get("rating", 0))
        genre  = self._data.get("genre", "–")
        tahun  = self._data.get("release_year", "–") or "–"
        tgl    = self._data.get("tanggal_tambah", "–")
        lbl_m  = QLabel(f"⭐ {rating:.1f}  ·  {genre}  ·  {tahun}  ·  Ditambahkan: {tgl}")
        lbl_m.setStyleSheet(f"color:{GRAY_200}; font-size:12px; background:transparent;")
        rl.addWidget(lbl_m)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border:none; border-top:1px solid {BORDER};")
        rl.addWidget(sep)

        lbl_syn = QLabel("SINOPSIS")
        lbl_syn.setObjectName("form_label")
        rl.addWidget(lbl_syn)

        overview = self._data.get("overview", "").strip() or "Sinopsis tidak tersedia."
        lbl_ov = QLabel(overview)
        lbl_ov.setStyleSheet(f"color:{GRAY_200}; font-size:12px; background:transparent;")
        lbl_ov.setWordWrap(True)
        rl.addWidget(lbl_ov)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"border:none; border-top:1px solid {BORDER};")
        rl.addWidget(sep2)

        lbl_cat = QLabel("CATATAN PRIBADI")
        lbl_cat.setObjectName("form_label")
        rl.addWidget(lbl_cat)

        self._txt = QTextEdit()
        self._txt.setFixedHeight(70)
        self._txt.setPlainText(self._data.get("catatan", "").strip())
        self._txt.setPlaceholderText("Tulis catatan atau kesan pribadi...")
        rl.addWidget(self._txt)
        rl.addStretch()

        row_btn = QHBoxLayout()
        row_btn.setSpacing(10)

        btn_save = QPushButton("💾  Simpan Catatan")
        btn_save.setObjectName("btn_primary")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)

        btn_edit = QPushButton("✏️  Edit Detail")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.setFixedHeight(38)
        btn_edit.clicked.connect(self._edit)

        btn_hapus = QPushButton("🗑️  Hapus")
        btn_hapus.setObjectName("btn_danger")
        btn_hapus.setFixedHeight(38)
        btn_hapus.clicked.connect(self._hapus)

        btn_close = QPushButton("Tutup")
        btn_close.setObjectName("btn_ghost")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.accept)

        row_btn.addWidget(btn_save)
        row_btn.addWidget(btn_edit)
        row_btn.addWidget(btn_hapus)
        row_btn.addStretch()
        row_btn.addWidget(btn_close)
        rl.addLayout(row_btn)

        root.addWidget(right, stretch=1)

    def _load_poster(self):
        path = self._data.get("poster_path", "") or ""
        if os.path.isfile(path):
            px = QPixmap(path)
            if not px.isNull():
                self._set_poster(px)
            return
        if not self._client or not path:
            return
        url = self._client.poster_url(path, "w500")
        if not url:
            return
        px = get_cached(url)
        if px:
            self._set_poster(px)
            return
        from api.workers import ImageWorker
        self._img_worker = ImageWorker(self._client, url)
        self._img_worker.finished.connect(lambda u, d: self._set_poster(store(u, d)))
        self._img_worker.start()

    def _set_poster(self, px: QPixmap):
        if px and not px.isNull():
            scaled = px.scaled(220, 330, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width()  - 220) // 2
            y = (scaled.height() - 330) // 2
            self._poster_lbl.setPixmap(scaled.copy(x, y, 220, 330))
            self._poster_lbl.setText("")

    def _save(self):
        catatan = self._txt.toPlainText().strip()
        if len(catatan) > 500:
            QMessageBox.warning(self, "Validasi", "Catatan maksimal 500 karakter.")
            return
        self._db.update(
            self._data["id"],
            self._data.get("judul", ""),
            self._data.get("genre", ""),
            float(self._data.get("rating", 0)),
            catatan,
            release_year=self._data.get("release_year", "") or "",
        )
        QMessageBox.information(self, "Tersimpan", "Catatan berhasil disimpan! 💾")
        self.data_changed.emit()

    def _edit(self):
        dlg = EditDialog(self._data, self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            self._db.update(
                self._data["id"],
                d["judul"], d["genre"], d["rating"], d["catatan"],
                release_year=d["release_year"],
                poster_path=d["poster_path"],
            )
            self.data_changed.emit()
            self.accept()

    def _hapus(self):
        box = QMessageBox(self)
        box.setWindowTitle("🗑️  Hapus Favorit?")
        box.setIcon(QMessageBox.Question)
        box.setText(f"Hapus <b>{self._data.get('judul','film ini')}</b> dari daftar favorit?")
        box.setInformativeText("Tindakan ini tidak dapat dibatalkan.")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        if box.exec() == QMessageBox.Yes:
            self._db.hapus(self._data["id"])
            self.data_changed.emit()
            self.accept()

    def closeEvent(self, e):
        if self._img_worker and self._img_worker.isRunning():
            self._img_worker.stop()
        super().closeEvent(e)


class FavCard(QFrame):
    klik_card  = Signal(dict)
    klik_edit  = Signal(int)
    klik_hapus = Signal(int)

    def __init__(self, data: dict, client=None, parent=None):
        super().__init__(parent)
        self.fav_id = data["id"]
        self.data   = data
        self.client = client
        self.setObjectName("fav_card")
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._build(data)
        self._load_poster(data)

    def _build(self, d):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 16, 0)
        lay.setSpacing(0)

        self._poster = QLabel()
        self._poster.setFixedSize(80, 120)
        self._poster.setAlignment(Qt.AlignCenter)
        self._poster.setStyleSheet(f"background:{BG_CARD}; border-radius:10px 0 0 10px;")
        self._poster.setText("🎬")
        self._poster.setFont(QFont("Segoe UI Emoji", 22))
        lay.addWidget(self._poster)

        info = QVBoxLayout()
        info.setContentsMargins(18, 14, 14, 14)
        info.setSpacing(5)

        lbl_j = QLabel(d.get("judul", "?"))
        lbl_j.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_j.setStyleSheet(f"color:{WHITE}; background:transparent;")

        genre = d.get("genre", "Film")
        row1  = QHBoxLayout()
        row1.setSpacing(8)
        lbl_g = QLabel(genre)
        lbl_g.setStyleSheet(f"""
            color:{RED}; font-size:10px; font-weight:700;
            background:rgba(229,9,20,0.12);
            border:1px solid rgba(229,9,20,0.3);
            border-radius:4px; padding:1px 8px;
        """)
        lbl_yr = QLabel(d.get("release_year", "") or "")
        lbl_yr.setStyleSheet(f"color:{GRAY_400}; font-size:10px; background:transparent;")
        lbl_dt = QLabel(f"📅 {d.get('tanggal_tambah','')}")
        lbl_dt.setStyleSheet(f"color:{GRAY_400}; font-size:10px; background:transparent;")
        row1.addWidget(lbl_g)
        row1.addWidget(lbl_yr)
        row1.addStretch()
        row1.addWidget(lbl_dt)

        overview = d.get("overview", "").strip() or "Klik untuk melihat detail film."
        preview  = overview[:80] + "…" if len(overview) > 80 else overview
        lbl_ov   = QLabel(preview)
        lbl_ov.setStyleSheet(f"color:{GRAY_300}; font-size:11px; font-style:italic; background:transparent;")

        info.addWidget(lbl_j)
        info.addLayout(row1)
        info.addWidget(lbl_ov)
        info.addStretch()
        lay.addLayout(info, stretch=1)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.setContentsMargins(0, 14, 0, 14)
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        rating = float(d.get("rating", 0))
        rc = (GREEN_ACT if rating >= 8 else GOLD if rating >= 6.5 else
              "#ff6b35" if rating >= 5 else GRAY_300)
        lbl_r = QLabel(f"⭐ {rating:.1f}")
        lbl_r.setFont(QFont("Consolas", 15, QFont.Bold))
        lbl_r.setStyleSheet(f"color:{rc}; background:transparent;")
        lbl_r.setAlignment(Qt.AlignRight)

        btn_e = QPushButton("✏️  Edit")
        btn_e.setObjectName("btn_edit")
        btn_e.setFixedSize(88, 30)
        btn_e.setCursor(QCursor(Qt.PointingHandCursor))
        btn_e.clicked.connect(lambda: self.klik_edit.emit(self.fav_id))

        btn_h = QPushButton("🗑️  Hapus")
        btn_h.setObjectName("btn_danger")
        btn_h.setFixedSize(88, 30)
        btn_h.setCursor(QCursor(Qt.PointingHandCursor))
        btn_h.clicked.connect(lambda: self.klik_hapus.emit(self.fav_id))

        right.addWidget(lbl_r)
        right.addStretch()
        right.addWidget(btn_e)
        right.addWidget(btn_h)
        lay.addLayout(right)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.klik_card.emit(self.data)

    def _load_poster(self, d: dict):
        path = d.get("poster_path", "") or ""
        if os.path.isfile(path):
            px = QPixmap(path)
            if not px.isNull():
                self._set_poster(px)
            return
        if not self.client or not path:
            return
        url = self.client.poster_url(path, "w500")
        if not url:
            return
        cached = get_cached(url)
        if cached:
            self._set_poster(cached)
            return
        from api.workers import ImageWorker
        w = ImageWorker(self.client, url)
        w.finished.connect(lambda u, data: self._set_poster(store(u, data)))
        w.start()
        self._img_w = w

    def _set_poster(self, px: QPixmap):
        if px and not px.isNull():
            scaled = px.scaled(80, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width()  - 80)  // 2
            y = (scaled.height() - 120) // 2
            self._poster.setPixmap(scaled.copy(x, y, 80, 120))
            self._poster.setText("")


class FavoritesPage(QWidget):
    def __init__(self, client=None, parent=None):
        super().__init__(parent)
        self.db         = DatabaseManager()
        self.client     = client
        self._all_data: list[dict] = []
        self._view_mode = "card"
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QFrame()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"background:{BG_BASE}; border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(40, 0, 40, 0)

        lbl_t = QLabel("Favorit Saya")
        lbl_t.setObjectName("page_title")
        self._lbl_count = QLabel("")
        self._lbl_count.setObjectName("muted")

        btn_add = QPushButton("➕  Tambah Film Favorite")
        btn_add.setObjectName("btn_ghost")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._tambah_manual)

        hl.addWidget(lbl_t)
        hl.addSpacing(12)
        hl.addWidget(self._lbl_count)
        hl.addStretch()
        hl.addWidget(btn_add)
        root.addWidget(hdr)

        root.addWidget(self._build_statbar())
        root.addWidget(self._build_toolbar())

        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet(f"background:{BG_BASE};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._list_w = QFrame()
        self._list_w.setStyleSheet(f"background:{BG_BASE};")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(40, 20, 40, 40)
        self._list_lay.setSpacing(10)
        self._list_lay.addStretch()
        scroll.setWidget(self._list_w)
        self._content_stack.addWidget(scroll)

        self._table = QTableWidget()
        self._table.setColumnCount(len(TABLE_COLS))
        self._table.setHorizontalHeaderLabels(TABLE_COLS)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.setShowGrid(True)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._table_double_click)
        self._content_stack.addWidget(self._table)

        root.addWidget(self._content_stack)

    def _build_statbar(self) -> QFrame:
        f = QFrame()
        f.setFixedHeight(44)
        f.setStyleSheet(f"background:{BG_SURFACE}; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(f)
        lay.setContentsMargins(40, 0, 40, 0)
        lay.setSpacing(32)

        self._lbl_total = QLabel("Total: 0 film")
        self._lbl_avg   = QLabel("Rating rata-rata: –")
        self._lbl_db    = QLabel("📂  cinetrack.db · SQLite Lokal")
        for l in [self._lbl_total, self._lbl_avg, self._lbl_db]:
            l.setStyleSheet(f"color:{GRAY_400}; font-size:11px;")
            lay.addWidget(l)
        lay.addStretch()

        btn_csv = QPushButton("📄 CSV")
        btn_csv.setObjectName("btn_ghost")
        btn_csv.setFixedHeight(30)
        btn_csv.clicked.connect(self.do_export_csv)

        btn_pdf = QPushButton("📑 PDF")
        btn_pdf.setObjectName("btn_ghost")
        btn_pdf.setFixedHeight(30)
        btn_pdf.clicked.connect(self.do_export_pdf)

        lay.addWidget(btn_csv)
        lay.addWidget(btn_pdf)
        return f

    def _build_toolbar(self) -> QFrame:
        f = QFrame()
        f.setFixedHeight(52)
        f.setStyleSheet(f"background:{BG_BASE}; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(f)
        lay.setContentsMargins(40, 0, 40, 0)
        lay.setSpacing(12)

        self._search = QLineEdit()
        self._search.setObjectName("search_input")
        self._search.setPlaceholderText("🔍  Cari judul film favorit...")
        self._search.setFixedWidth(260)
        self._search.setFixedHeight(34)
        self._search.textChanged.connect(self._apply_filter)

        lbl_sort = QLabel("Urutkan:")
        lbl_sort.setStyleSheet(f"color:{GRAY_300}; font-size:12px;")

        self._combo_sort = QComboBox()
        self._combo_sort.setFixedHeight(34)
        self._combo_sort.setFixedWidth(190)
        for label, _ in SORT_OPTIONS:
            self._combo_sort.addItem(label)
        self._combo_sort.currentIndexChanged.connect(self._apply_filter)

        self._btn_card = QPushButton("▦  Kartu")
        self._btn_card.setObjectName("btn_primary")
        self._btn_card.setFixedHeight(34)
        self._btn_card.setFixedWidth(90)
        self._btn_card.clicked.connect(lambda: self._set_view("card"))

        self._btn_table = QPushButton("☰  Tabel")
        self._btn_table.setObjectName("btn_ghost")
        self._btn_table.setFixedHeight(34)
        self._btn_table.setFixedWidth(90)
        self._btn_table.clicked.connect(lambda: self._set_view("table"))

        lay.addWidget(self._search)
        lay.addStretch()
        lay.addWidget(lbl_sort)
        lay.addWidget(self._combo_sort)
        lay.addSpacing(16)
        lay.addWidget(self._btn_card)
        lay.addWidget(self._btn_table)
        return f

    def _set_view(self, mode: str):
        self._view_mode = mode
        if mode == "card":
            self._content_stack.setCurrentIndex(0)
            self._btn_card.setObjectName("btn_primary")
            self._btn_table.setObjectName("btn_ghost")
        else:
            self._content_stack.setCurrentIndex(1)
            self._btn_card.setObjectName("btn_ghost")
            self._btn_table.setObjectName("btn_primary")
        for btn in [self._btn_card, self._btn_table]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def load_favorites(self):
        self._all_data = self.db.semua()
        self._apply_filter()
        n   = len(self._all_data)
        avg = self.db.avg_rating()
        self._lbl_count.setText(f"{n} film")
        self._lbl_total.setText(f"Total: {n} film")
        self._lbl_avg.setText(f"Rating rata-rata: {'–' if not avg else f'{avg:.1f} ⭐'}")

    def _apply_filter(self):
        q    = self._search.text().strip().lower()
        data = self._all_data
        if q:
            data = [d for d in data if q in d.get("judul", "").lower()]
        sort_key = SORT_OPTIONS[self._combo_sort.currentIndex()][1]
        if sort_key == "id_desc":
            data = sorted(data, key=lambda x: x["id"], reverse=True)
        elif sort_key == "id_asc":
            data = sorted(data, key=lambda x: x["id"])
        elif sort_key == "rating_desc":
            data = sorted(data, key=lambda x: float(x.get("rating", 0)), reverse=True)
        elif sort_key == "rating_asc":
            data = sorted(data, key=lambda x: float(x.get("rating", 0)))
        elif sort_key == "judul_asc":
            data = sorted(data, key=lambda x: x.get("judul", "").lower())
        elif sort_key == "judul_desc":
            data = sorted(data, key=lambda x: x.get("judul", "").lower(), reverse=True)
        self._render_cards(data)
        self._render_table(data)

    def _render_cards(self, data: list[dict]):
        while self._list_lay.count() > 1:
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not data:
            q   = self._search.text().strip()
            msg = (f"🔍  Tidak ada film yang cocok dengan \"{q}\"."
                   if q else
                   "🎬  Belum ada film favorit.\nTambahkan dari halaman Film Populer!")
            lbl = QLabel(msg)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color:{GRAY_400}; font-size:14px; padding:80px;")
            self._list_lay.insertWidget(0, lbl)
        else:
            for d in data:
                card = FavCard(d, self.client)
                card.klik_card.connect(self._show_detail)
                card.klik_edit.connect(self._edit)
                card.klik_hapus.connect(self._hapus)
                self._list_lay.insertWidget(self._list_lay.count() - 1, card)

    def _render_table(self, data: list[dict]):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(data))
        for row, d in enumerate(data):
            rating = float(d.get("rating", 0))
            rc = (GREEN_ACT if rating >= 8 else GOLD if rating >= 6.5 else
                  "#ff6b35" if rating >= 5 else GRAY_300)
            values = [
                str(row + 1),
                d.get("judul", ""),
                d.get("genre", "–"),
                f"{rating:.1f}",
                d.get("release_year", "–") or "–",
                (d.get("catatan", "") or "")[:50],
                d.get("tanggal_tambah", "–"),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 3:
                    item.setForeground(QColor(rc))
                    item.setFont(QFont("Consolas", 11, QFont.Bold))
                item.setData(Qt.UserRole, d.get("id"))
                self._table.setItem(row, col, item)
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 70)
        self._table.setColumnWidth(4, 60)
        self._table.setColumnWidth(6, 110)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self._table.setSortingEnabled(True)

    def _table_double_click(self, index):
        fid = self._table.item(index.row(), 0).data(Qt.UserRole)
        if fid is None:
            return
        data = self.db.by_id(fid)
        if data:
            self._show_detail(data)

    def _show_detail(self, data: dict):
        dlg = FavDetailDialog(data, self.db, self.client, self)
        dlg.data_changed.connect(self.load_favorites)
        dlg.exec()

    def _tambah_manual(self):
        dlg = TambahManualDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.tambah(
                tmdb_id=None,
                judul=d["judul"],
                genre=d["genre"],
                rating=d["rating"],
                catatan=d["catatan"],
                release_year=d["release_year"],
                poster_path=d["poster_path"],
            )
            self.load_favorites()

    def _edit(self, fid: int):
        data = self.db.by_id(fid)
        if not data:
            return
        dlg = EditDialog(data, self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.update(
                fid,
                d["judul"], d["genre"], d["rating"], d["catatan"],
                release_year=d["release_year"],
                poster_path=d["poster_path"],
            )
            self.load_favorites()

    def _hapus(self, fid: int):
        d = self.db.by_id(fid)
        j = d.get("judul", "film ini") if d else "film ini"
        box = QMessageBox(self)
        box.setWindowTitle("🗑️  Hapus Favorit?")
        box.setIcon(QMessageBox.Question)
        box.setText(f"Hapus <b>{j}</b> dari daftar favorit?")
        box.setInformativeText("Tindakan ini tidak dapat dibatalkan.")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        if box.exec() == QMessageBox.Yes:
            self.db.hapus(fid)
            self.load_favorites()

    def do_export_csv(self):
        if not self._all_data:
            QMessageBox.information(self, "Export CSV", "Tidak ada data untuk diekspor.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "favorit_cinetrack.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        from utils.export import export_csv
        if export_csv(self._all_data, path):
            QMessageBox.information(self, "Export Berhasil", f"✅  Data berhasil diekspor ke:\n{path}")
        else:
            QMessageBox.critical(self, "Export Gagal", "Gagal menyimpan file CSV.")

    def do_export_pdf(self):
        if not self._all_data:
            QMessageBox.information(self, "Export PDF", "Tidak ada data untuk diekspor.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "favorit_cinetrack.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        from utils.export import export_pdf
        import os as _os
        if export_pdf(self._all_data, path, "Daftar Film Favorit — CineTrack"):
            actual = path if _os.path.exists(path) else path.replace(".pdf", ".html")
            QMessageBox.information(self, "Export Berhasil", f"✅  Data berhasil diekspor ke:\n{actual}")
        else:
            QMessageBox.critical(self, "Export Gagal", "Gagal menyimpan file PDF.")

    def showEvent(self, e):
        super().showEvent(e)
        self.load_favorites()