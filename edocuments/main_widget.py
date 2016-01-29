# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QMainWindow
from edocuments.ui.main import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui = Ui_MainWindow()
        ui.setupUi(self)
