from pathlib import Path

from PyQt5.QtWidgets import QApplication

from gui import MainWindow

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyleSheet(Path('./themes/light.qss').read_text())
    mainWin = MainWindow()
    mainWin.show()

    sys.exit(app.exec_())
