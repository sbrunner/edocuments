
from .ui.main import Ui_MainWindow
from PyQt5 import QMainWindow


class MainWindows(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


def main():
    mw = MainWindows()
    mw.show()


if __name__ == "__main__":
    main()
