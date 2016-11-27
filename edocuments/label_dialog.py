# -*- coding: utf-8 -*-

import os
import subprocess
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtGui import QPixmap
import edocuments
from edocuments.backend import Cmd, Merger
from edocuments.ui.label_dialog import Ui_Dialog


class Dialog(QDialog):

    def __init__(self, process):
        super().__init__()
        self.config = edocuments.config.get("scan_preview", {})
        self.process = process
        self.destinations = []
        self.postprocess = []
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.edit_button.clicked.connect(self.edit)
        self.ui.finish_button.clicked.connect(self.finish)
        self.ui.add_button.clicked.connect(self.add)

        cmds_config = edocuments.config.get("cmds", {})
        for cmd in self.config.get("commands", []):
            if isinstance(cmd, str):
                name = cmd
                cmd = cmds_config.get(name)
                cmd["name"] = name

            if cmd is not None:
                button = QPushButton(self)
                button.setText(cmd["display"])

                c = Cmd(self, cmd, self.process)

                button.clicked.connect(c.exec_)
                self.ui.button_container.addWidget(button)

    def finish(self):
        self.done(0)

    def _add(self):
        f = os.path.splitext(self.image)
        new_img = "{}_{}{}".format(
            f[0], len(self.destinations) + 1, f[1]
        )
        os.rename(self.image, new_img)
        self.image = new_img
        destination, _, _, _ = self.process.destination_filename(
            self.postprocess,
            new_img
        )
        self.destinations.append(destination)

    def add(self):
        self._add()
        self.done(1)

    def edit(self):
        subprocess.call([self.config.get("edit", "gimp"), self.image])
        self.set_image(self.image)

    def set_image(self, image_filename, postprocess=None):
        self.image = image_filename
        if postprocess is not None:
            self.postprocess = postprocess
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
