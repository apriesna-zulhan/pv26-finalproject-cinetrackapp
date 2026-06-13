from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

from ui.theme import BG_SURFACE, BORDER, WHITE, GRAY_300


class StatCard(QFrame):
    def __init__(self, label: str, value: str, subtitle: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self._color = color
        self.setFixedHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self._build(label, value, subtitle)

    def _build(self, label, value, subtitle):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(3)

        self._lbl_label = QLabel(label.upper())
        self._lbl_label.setStyleSheet(f"color: {GRAY_300}; font-size: 9px; font-weight: 700; letter-spacing: 1.5px; background: transparent !important; border: none !important;")

        self._lbl_val = QLabel(str(value))
        self._lbl_val.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._lbl_val.setStyleSheet(f"color: {WHITE}; background: transparent !important; border: none !important;")

        self._lbl_sub = QLabel(subtitle)
        self._lbl_sub.setStyleSheet(f"color: {GRAY_300}; font-size: 10px; background: transparent !important; border: none !important;")

        lay.addWidget(self._lbl_label)
        lay.addWidget(self._lbl_val)
        lay.addWidget(self._lbl_sub)

        self.setStyleSheet("""
            QFrame#stat_card {
                background: transparent;
            }
            QFrame#stat_card QLabel {
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }
        """)

    def set_value(self, v):
        self._lbl_val.setText(str(v))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.setBrush(QBrush(QColor(BG_SURFACE)))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawRoundedRect(r, 10, 10)
        
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, r.height() // 4, 3, r.height() // 2, 2, 2)
        
        glow = QLinearGradient(0, 0, r.width(), 0)
        c = QColor(self._color); c.setAlpha(25)
        glow.setColorAt(0, c); glow.setColorAt(0.6, QColor(0,0,0,0))
        p.setBrush(QBrush(glow))
        p.drawRoundedRect(r, 10, 10)
        
        p.end()