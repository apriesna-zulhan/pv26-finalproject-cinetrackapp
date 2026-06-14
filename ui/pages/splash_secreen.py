from PySide6.QtWidgets import QSplashScreen, QApplication
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtGui     import QPainter, QColor, QFont, QFontMetrics


class SplashScreen(QSplashScreen):

    TITLE      = "CineTrack"
    TAGLINE    = "Katalog Film Pribadimu"

    BG_COLOR   = QColor("#141414")
    RED_COLOR  = QColor("#E50914")
    WHITE      = QColor("#FFFFFF")
    GRAY       = QColor("#B3B3B3")

    CHAR_INTERVAL   = 110
    TAGLINE_DELAY   = 3400
    FADEOUT_DELAY   = 4200

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint  |
            Qt.SplashScreen
        )

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self._visible_chars  = 0
        self._tagline_alpha  = 0
        self._global_alpha   = 255

        self._char_timer = QTimer(self)
        self._char_timer.setInterval(self.CHAR_INTERVAL)
        self._char_timer.timeout.connect(self._show_next_char)

        self._tagline_timer = QTimer(self)
        self._tagline_timer.setSingleShot(True)
        self._tagline_timer.timeout.connect(self._start_tagline_fade)

        self._fadeout_timer = QTimer(self)
        self._fadeout_timer.setSingleShot(True)
        self._fadeout_timer.timeout.connect(self._start_fadeout)

        self._tagline_fade_timer = QTimer(self)
        self._tagline_fade_timer.setInterval(16)
        self._tagline_fade_timer.timeout.connect(self._tick_tagline_fade)

        self._fadeout_tick_timer = QTimer(self)
        self._fadeout_tick_timer.setInterval(16)
        self._fadeout_tick_timer.timeout.connect(self._tick_fadeout)

    def start(self):
        self.showFullScreen()
        QTimer.singleShot(300, self._char_timer.start)
        self._tagline_timer.start(self.TAGLINE_DELAY)
        self._fadeout_timer.start(self.FADEOUT_DELAY)

    def _show_next_char(self):
        if self._visible_chars < len(self.TITLE):
            self._visible_chars += 1
            self.repaint()
        else:
            self._char_timer.stop()

    def _start_tagline_fade(self):
        self._tagline_alpha = 0
        self._tagline_fade_timer.start()

    def _tick_tagline_fade(self):
        self._tagline_alpha = min(255, self._tagline_alpha + 8)
        self.repaint()
        if self._tagline_alpha >= 255:
            self._tagline_fade_timer.stop()

    def _start_fadeout(self):
        self._fadeout_tick_timer.start()

    def _tick_fadeout(self):
        self._global_alpha = max(0, self._global_alpha - 10)
        self.repaint()
        if self._global_alpha <= 0:
            self._fadeout_tick_timer.stop()

    def drawContents(self, painter: QPainter):
        w = self.width()
        h = self.height()

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._global_alpha / 255.0)

        painter.fillRect(self.rect(), self.BG_COLOR)

        visible = self.TITLE[:self._visible_chars]
        full    = self.TITLE

        font_title = QFont("Segoe UI", 80, QFont.Bold)
        painter.setFont(font_title)

        fm     = QFontMetrics(font_title)
        full_w = fm.horizontalAdvance(full)
        text_x = (w - full_w) // 2
        text_y = h // 2 - 30

        painter.setPen(self.WHITE)
        painter.drawText(text_x, text_y, visible)

        if self._visible_chars > 0:
            bar_w = fm.horizontalAdvance(visible)
            bar_x = text_x
            bar_y = text_y + 14
            painter.fillRect(bar_x, bar_y, bar_w, 5, self.RED_COLOR)

        if self._tagline_alpha > 0:
            font_tag = QFont("Segoe UI", 18)
            font_tag.setLetterSpacing(QFont.AbsoluteSpacing, 4)
            painter.setFont(font_tag)

            color = QColor(self.GRAY)
            color.setAlpha(self._tagline_alpha)
            painter.setPen(color)

            fm_tag = QFontMetrics(font_tag)
            tag_w  = fm_tag.horizontalAdvance(self.TAGLINE)
            painter.drawText((w - tag_w) // 2, text_y + 55, self.TAGLINE)

        font_ver = QFont("Segoe UI", 11)
        painter.setFont(font_ver)
        ver_color = QColor(self.GRAY)
        ver_color.setAlpha(min(self._tagline_alpha, 180))
        painter.setPen(ver_color)