# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication

from edocuments.main_widget import MainWindow


def gui_main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    app.exec()
