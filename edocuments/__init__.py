
import sys
from ui.main import Ui_MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow


class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()
        ui = Ui_MainWindow()
        ui.setupUi(self)


def main():
    app = QApplication(sys.argv)
    mw = MainWindows()
    mw.show()
    app.exec()


if __name__ == "__main__":
    main()
