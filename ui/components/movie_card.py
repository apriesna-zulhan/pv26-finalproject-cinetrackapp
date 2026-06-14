from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (QPixmap, QPainter, QColor, QLinearGradient, QBrush,
                            QPen, QFont, QPainterPath)

from ui.theme import (BG_CARD, WHITE, GRAY_200,
                       GENRE_COLORS, GENRE_NAMES)

CARD_W = 175
CARD_H = 262


class MovieCard(QFrame):
    klik_simpan = Signal(dict)
    klik_detail = Signal(dict)

    def __init__(self, data: dict, tersimpan: bool = False, parent=None):
        super().__init__(parent)
        self.data      = data
        self.tersimpan = tersimpan
        self._hovered  = False
        self._pixmap   = None

        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._build_overlay()

    def _build_overlay(self):
        self._overlay = QFrame(self)
        self._overlay.setGeometry(0, CARD_H - 110, CARD_W, 110)
        self._overlay.setStyleSheet("background: transparent;")
        self._overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        lay = QVBoxLayout(self._overlay)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(4)
        lay.addStretch()

        judul = self.data.get("title", "?")
        self._lbl_title = QLabel(judul)
        self._lbl_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._lbl_title.setStyleSheet(f"color: {WHITE}; background: transparent;")
        self._lbl_title.setWordWrap(True)

        gids   = self.data.get("genre_ids", [])
        gname  = GENRE_NAMES.get(gids[0], "Film") if gids else "Film"
        rating = self.data.get("vote_average", 0)
        tahun  = str(self.data.get("release_date", ""))[:4] or "–"

        self._lbl_meta = QLabel(f"{gname}  ·  ⭐ {rating:.1f}  ·  {tahun}")
        self._lbl_meta.setFont(QFont("Segoe UI", 8))
        self._lbl_meta.setStyleSheet(f"color: {GRAY_200}; background: transparent;")

        lay.addWidget(self._lbl_title)
        lay.addWidget(self._lbl_meta)

    def set_poster(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def set_tersimpan(self, v: bool):
        self.tersimpan = v
        self.update()

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.klik_detail.emit(self.data)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = self.rect()

        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 8, 8)
        p.setClipPath(path)

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(r.size(), Qt.KeepAspectRatioByExpanding,
                                          Qt.SmoothTransformation)
            x = (scaled.width() - r.width()) // 2
            y = (scaled.height() - r.height()) // 2
            p.drawPixmap(-x, -y, scaled)
        else:
            gids  = self.data.get("genre_ids", [])
            color = GENRE_COLORS.get(gids[0] if gids else 0, "#E50914")
            grad  = QLinearGradient(0, 0, 0, r.height())
            c1 = QColor(color); c1.setAlpha(200)
            c2 = QColor(color); c2.setAlpha(60)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            p.fillRect(r, QColor(BG_CARD))
            p.fillRect(r, QBrush(grad))
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(255, 255, 255, 80))
            p.drawText(r, Qt.AlignCenter, "⏳")

        fade = QLinearGradient(0, r.height() - 130, 0, r.height())
        fade.setColorAt(0, QColor(0, 0, 0, 0))
        fade.setColorAt(0.4, QColor(0, 0, 0, 120))
        fade.setColorAt(1, QColor(0, 0, 0, 240))
        p.fillRect(r, QBrush(fade))

        if self._hovered:
            p.fillRect(r, QColor(0, 0, 0, 50))

        p.setClipping(False)

        border_color = QColor(RED) if self._hovered else QColor(180, 180, 180)
        pen = QPen(border_color, 2 if self._hovered else 1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 7, 7)

        if self.tersimpan:
            font = QFont("Segoe UI Emoji", 15)
            p.setFont(font)
            rect_badge = QRect(r.width()-32, 4, 28, 28)
            p.setPen(QColor(0, 0, 0, 120))
            p.drawText(rect_badge.adjusted(1, 1, 1, 1), Qt.AlignCenter, "⭐")
            p.setPen(QColor("#F5C518"))
            p.drawText(rect_badge, Qt.AlignCenter, "⭐")
