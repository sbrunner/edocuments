# -*- coding: utf-8 -*-

import re
import pathlib
from os import path
from threading import Thread
from subprocess import call
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QMainWindow, QFileDialog, \
    QErrorMessage, QMessageBox, QProgressDialog
import edocuments
from edocuments.process import process, destination_filename
from edocuments.ui.main import Ui_MainWindow
from edocuments.label_dialog import Dialog


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
        self.ui.scan_to.returnPressed.connect(self.scan_start)
        self.ui.scan_to.editingFinished.connect(self.scan_start)
        self.ui.scan_start.clicked.connect(self.scan_start)

        self.image_dialog = Dialog()

    def scan_browse(self, event):
        filename = QFileDialog.getSaveFileName(
            self, "Scan to", directory=self.filename()
        )[0]
        filename = re.sub(r"\.[a-z0-9A-Z]{2,5}$", "", filename)

        if filename[:len(edocuments.root_folder)] == edocuments.root_folder:
            filename = filename[len(edocuments.root_folder):]
        self.ui.scan_to.setText(filename)

    def filename(self):
        filename = self.ui.scan_to.text()
        if len(filename) == 0 or filename[0] != '/':
            filename = path.join(edocuments.root_folder, filename)
        return filename

    def scan_start(self, event):
        if pathlib.Path(self.filename()).is_dir():
            err = QErrorMessage(self)
            err.setWindowTitle("eDocuments - Error")
            err.showMessage("The destination is a directory!")
            return

        destination = destination_filename(
            self.ui.scan_type.currentData().get("cmds"),
            self.filename()
        )

        if pathlib.Path(destination).is_file():
            msg = QMessageBox(self)
            msg.setWindowTitle("Scanning...")
            msg.setText("The destination file already exists")
            msg.setInformativeText("Do you want to overwrite it?")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel | QMessageBox.Open)
            ret = msg.exec()
            if ret == QMessageBox.Ok:
                self._scan()
            elif ret == QMessageBox.Open:
                cmd = edocuments.config.get('open_cmd').split(' ')
                cmd.append(destination)
                call(cmd)
        else:
            self._scan()

    def _scan(self):
        cmds = self.ui.scan_type.currentData().get("cmds")

        self.progress = QProgressDialog("Scanning...", "Cancel", 0, len(cmds), self)
        self.progress.setWindowTitle("Scanning...")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

        t = Thread(target=self._do_scan)
        t.start()

    def _do_scan(self):
        cmds = self.ui.scan_type.currentData().get("cmds")
        filename = process(
            cmds, destination_filename=self.filename(),
            progress=self.progress, progress_text='{display}'
        )
        self.progress.hide()

        self.image_dialog.set_image(filename)
        self.image_dialog.exec()
