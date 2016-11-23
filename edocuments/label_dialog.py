# -*- coding: utf-8 -*-

import subprocess
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtGui import QPixmap
import edocuments
from edocuments.ui.label_dialog import Ui_Dialog


class Dialog(QDialog):

    def __init__(self, process):
        super().__init__()
        self.config = edocuments.config.get("scan_preview", {})
        self.process = process
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.edit_button.clicked.connect(self.edit)

        cmds_config = edocuments.config.get("cmds", {})
        for cmd in self.config.get("commands", []):
            if isinstance(cmd, str):
                cmd = cmds_config.get(cmd)

            if cmd is not None:
                button = QPushButton(self)
                button.setText(cmd["display"])

                def action():
                    filename, extension = self.process.process(
                        [cmd], filenames=[self.image],
                    )
                    self.set_image(filename)

                button.clicked.connect(action)
                self.ui.button_container.addWidget(button)

    def edit(self):
        subprocess.call([self.config.get("edit", "gimp"), self.image])
        self.set_image(self.image)

    def set_image(self, image_filename):
        self.image = image_filename
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
