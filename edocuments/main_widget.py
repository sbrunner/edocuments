# -*- coding: utf-8 -*-

import re
import pathlib
from subprocess import call
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QErrorMessage, QMessageBox
import edocuments
from edocuments.process import process, destination_filename
from edocuments.ui.main import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.scan_comments.setText(edocuments.config.get("scan_comments"))

        default_index = 0
        for s in edocuments.config.get("scans", []):
            if s.get("default") is True:
                default_index = self.ui.scan_type.count()
            self.ui.scan_type.addItem(s.get("name"), s)
        self.ui.scan_type.setCurrentIndex(default_index)

        self.ui.scan_browse.clicked.connect(self.scan_browse)
        self.ui.scan_start.clicked.connect(self.scan_start)

    def scan_browse(self, event):
        filename = QFileDialog.getOpenFileName(
            self, directory=edocuments.root_folder
        )[0]
        filename = re.sub(r"\.[a-z0-9A-Z]{2,5}$", "", filename)

        if filename[:len(edocuments.root_folder)] == edocuments.root_folder:
            filename = filename[len(edocuments.root_folder):]
        self.ui.scan_to.setText(filename)

    def scan_start(self, event):
        filename = self.ui.scan_to.text()
        if filename[0] != '/':
            filename = edocuments.root_folder + filename

        destination = destination_filename(
            self.ui.scan_type.currentData().get("cmds"),
            destination_filename=filename
        )

        path = pathlib.Path(destination)
        if path.is_dir():
            QErrorMessage.showMessage("The destination is a directory!")
            return

        if path.is_file():
            msg = QMessageBox()
            msg.setText("The destination file already exists")
            msg.setInformativeText("Do you want to overwrite it?")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel | QMessageBox.Open)
            ret = msg.exec()
            if ret == QMessageBox.Ok:
                process(
                    self.ui.scan_type.currentData().get("cmds"),
                    destination_filename=filename
                )
            elif ret == QMessageBox.Open:
                cmd = edocuments.config.get('open_cmd').split(' ')
                cmd.append(destination)
                call(cmd)
