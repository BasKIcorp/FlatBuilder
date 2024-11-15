from pathlib import Path

from PyQt5.QtWidgets import QApplication

from GUI.MainWindow import MainWindow


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyleSheet(Path('Themes/light.qss').read_text())
    mainWin = MainWindow()
    mainWin.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
