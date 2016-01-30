# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QPixmap
from edocuments.ui.label_dialog import Ui_Dialog


class Dialog(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def set_image(self, image_filename):
        size = 800
        pixmap = QPixmap(image_filename)
        if pixmap.width() > pixmap.height():
            if pixmap.width() > size:
                pixmap = pixmap.scaledToWidth(size)
        else:
            if pixmap.height() > size:
                pixmap = pixmap.scaledToHeight(size)
        self.ui.label.setPixmap(pixmap)
        self.ui.label.setMask(pixmap.mask())
        self.ui.label.show()
