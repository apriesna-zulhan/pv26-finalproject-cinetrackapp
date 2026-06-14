import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen
from ui.theme import load_qss

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("CineTrack")
    app.setOrganizationName("CineTrack Dev")

    app.setFont(QFont("Segoe UI", 10))

    qss = load_qss()
    if qss:
        app.setStyleSheet(qss)

    window = MainWindow()

    splash = SplashScreen()
    splash.start()

    def show_main():
        window.showMaximized()
        splash.finish(window)
        window.raise_()
        window.activateWindow()

    QTimer.singleShot(5000, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()