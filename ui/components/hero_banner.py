from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (QPixmap, QPainter, QColor, QLinearGradient,
                            QBrush, QFont)

from ui.theme import (BG_BASE, WHITE, GRAY_200,
                      GENRE_NAMES, GENRE_COLORS)


class HeroBanner(QWidget):
    klik_favorit = Signal(dict)
    klik_detail  = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._film   = {}
        self._pixmap = None

        self.setFixedHeight(420)

        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self._build()

    def _build(self):
        self._content = QWidget(self)

        self._content.setAttribute(Qt.WA_NoSystemBackground, True)
        self._content.setAttribute(Qt.WA_TranslucentBackground, True)
        self._content.setStyleSheet("background: transparent;")

        cl = QVBoxLayout(self._content)
        cl.setContentsMargins(56, 0, 56, 48)
        cl.setSpacing(0)
        cl.addStretch()

        self._lbl_badge = QLabel("▶  POPULER MINGGU INI")
        self._lbl_badge.setStyleSheet(f"""
            color: {WHITE}; font-size: 10px; font-weight: 700;
            letter-spacing: 2px; background: transparent;
            padding: 4px 0;
        """)

        self._lbl_title = QLabel("–")
        self._lbl_title.setFont(QFont("Segoe UI", 40, QFont.Black))
        self._lbl_title.setStyleSheet(f"color: {WHITE}; background: transparent;")
        self._lbl_title.setWordWrap(True)
        self._lbl_title.setMaximumWidth(620)

        self._lbl_meta = QLabel("")
        self._lbl_meta.setStyleSheet(
            f"color: {GRAY_200}; font-size: 13px; background: transparent; padding: 6px 0;"
        )

        self._lbl_desc = QLabel("")
        self._lbl_desc.setStyleSheet(
            f"color: {GRAY_200}; font-size: 13px; line-height: 1.6; background: transparent;"
        )
        self._lbl_desc.setWordWrap(True)
        self._lbl_desc.setMaximumWidth(580)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(0, 18, 0, 0)

        self._btn_fav = QPushButton("▶  Tambah Favorit")
        self._btn_fav.setObjectName("btn_primary")
        self._btn_fav.setFixedHeight(44)
        self._btn_fav.setMinimumWidth(180)
        self._btn_fav.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._btn_fav.clicked.connect(lambda: self.klik_favorit.emit(self._film))

        self._btn_info = QPushButton("ⓘ  Info Film")
        self._btn_info.setObjectName("btn_secondary")
        self._btn_info.setFixedHeight(44)
        self._btn_info.setMinimumWidth(140)
        self._btn_info.setFont(QFont("Segoe UI", 13))
        self._btn_info.clicked.connect(lambda: self.klik_detail.emit(self._film))

        row.addWidget(self._btn_fav)
        row.addWidget(self._btn_info)
        row.addStretch()

        cl.addWidget(self._lbl_badge)
        cl.addSpacing(4)
        cl.addWidget(self._lbl_title)
        cl.addWidget(self._lbl_meta)
        cl.addWidget(self._lbl_desc)
        cl.addLayout(row)

    def set_film(self, data: dict):
        self._film = data
        judul  = data.get("title", "–")
        tahun  = str(data.get("release_date", ""))[:4] or "–"
        rating = data.get("vote_average", 0)
        gids   = data.get("genre_ids", [])
        genres = ", ".join(GENRE_NAMES.get(g, "") for g in gids[:3] if g in GENRE_NAMES)
        desc   = data.get("overview", "").strip() or "Sinopsis tidak tersedia untuk film ini."
        if len(desc) > 200:
            desc = desc[:200] + "…"

        self._lbl_title.setText(judul)
        self._lbl_meta.setText(f"⭐ {rating:.1f}  ·  {genres}  ·  {tahun}")
        self._lbl_desc.setText(desc)
        self.update()

    def set_backdrop(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self._pixmap = pixmap
            self.update()

    def resizeEvent(self, e):
        self._content.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(e)

    def showEvent(self, e):
        self._content.setGeometry(0, 0, self.width(), self.height())
        super().showEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = self.rect()

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                r.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (scaled.width()  - r.width())  // 2
            y = (scaled.height() - r.height()) // 2
            p.drawPixmap(-x, -y, scaled)
        else:
            gids  = self._film.get("genre_ids", [])
            color = GENRE_COLORS.get(gids[0] if gids else 0, "#E50914")
            grad  = QLinearGradient(0, 0, r.width(), r.height())
            c     = QColor(color)
            c.setAlpha(140)
            grad.setColorAt(0, c)
            grad.setColorAt(1, QColor(BG_BASE))
            p.fillRect(r, QBrush(grad))

        fade_lr = QLinearGradient(0, 0, r.width(), 0)
        fade_lr.setColorAt(0.00, QColor(20, 20, 20, 210))
        fade_lr.setColorAt(0.40, QColor(20, 20, 20, 90))
        fade_lr.setColorAt(0.75, QColor(20, 20, 20, 20))
        fade_lr.setColorAt(1.00, QColor(20, 20, 20, 0))
        p.fillRect(r, QBrush(fade_lr))

        fade_tb = QLinearGradient(0, r.height() * 0.15, 0, r.height())
        fade_tb.setColorAt(0.0, QColor(20, 20, 20, 0))
        fade_tb.setColorAt(0.5, QColor(20, 20, 20, 50))
        fade_tb.setColorAt(1.0, QColor(20, 20, 20, 230))
        p.fillRect(r, QBrush(fade_tb))
