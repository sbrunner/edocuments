# -*- coding: utf-8 -*-

import sys
import re
import pathlib
import traceback
from os import path
from threading import Thread
from subprocess import call
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.Qt import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QFileDialog, \
    QErrorMessage, QMessageBox, QProgressDialog, QListWidgetItem
import edocuments
from edocuments.process import process, destination_filename
from edocuments.index import index
from edocuments.ui.main import Ui_MainWindow
from edocuments.label_dialog import Dialog


class MainWindow(QMainWindow):
    scan_end = pyqtSignal(str)
    scan_error = pyqtSignal(str)

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
        self.ui.scan_start.clicked.connect(self.scan_start)

        self.image_dialog = Dialog()

        self.scan_end.connect(self.end_scan)
        self.scan_error.connect(self.on_scan_error)

        self.ui.search_text.textChanged.connect(self.search_change)
        self.ui.search_btn.clicked.connect(self.search)

        self.ui.library_update.triggered.connect(self.update_library)

    def search_change(self, text):
        pass

    def search(self):
        for result in index.search(self.ui.search_text.text()):
            QListWidgetItem(result, self.ui.search_result_list)
            # self.ui.search_result_list.insertItem

    def scan_browse(self, event):
        filename = QFileDialog.getSaveFileName(
            self, "Scan to", directory=self.filename()
        )[0]
        filename = re.sub(r"\.[a-z0-9A-Z]{2,5}$", "", filename)

        if filename[:len(edocuments.root_folder)] == edocuments.root_folder:
            filename = filename[len(edocuments.root_folder):]
        self.ui.scan_to.setText(filename)

    def update_library(self):
        t = Thread(target=self._do_update_library)
        t.start()

    def _do_update_library(self):
        progress = QProgressDialog(
            "Scanning...", None, 0, 1000, self)
        progress.setWindowTitle('Updating the library...')
        progress.setLabelText('Browsing the files...')
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        todo = []
        for conv in edocuments.config.get('to_txt'):
            cmds = conv.get("cmds")
            for filename in Path(edocuments.root_folder).rglob(
                    "*." + conv.get('extension')):
                todo.append((str(filename), cmds))

        nb = len(todo)

        results = edocuments.pool.imap_unordered(_to_txt, todo)

        progress.setLabelText('Parsing the files...')

        interval = timedelta(
            seconds=edocuments.config.get('save_interval', 60))
        last_save = datetime.now()

        nb_error = 0
        nb_empty = 0
        no = 0
        for filename, text in results:
            no += 1
            print("%i / %i" % (no, nb))
            progress.setValue(no * 1000 / nb)

            if text is False:
                nb_error += 1
            elif text is None:
                nb_empty += 1
            else:
                index.add(filename, text)

            if datetime.now() - last_save > interval:
                index.save()
                last_save = datetime.now()

        index.save()

        if nb_error != 0:
            self.scan_error.emit("Finished with %i errors" % nb_error)
        if nb_empty != 0:
            self.scan_error.emit("Finished with %i without text" % nb_empty)

    def filename(self):
        filename = self.ui.scan_to.text()
        if len(filename) == 0 or filename[0] != '/':
            filename = path.join(edocuments.root_folder, filename)
        return filename

    def scan_start(self, event=None):
        if pathlib.Path(self.filename()).is_dir():
            err = QErrorMessage(self)
            err.setWindowTitle("eDocuments - Error")
            err.showMessage("The destination is a directory!")
            return

        destination, extension = destination_filename(
            self.ui.scan_type.currentData().get("cmds"),
            self.filename()
        )

        if pathlib.Path(destination).is_file():
            msg = QMessageBox(self)
            msg.setWindowTitle("Scanning...")
            msg.setText("The destination file already exists")
            msg.setInformativeText("Do you want to overwrite it?")
            msg.setStandardButtons(
                QMessageBox.Ok | QMessageBox.Cancel | QMessageBox.Open)
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

        self.progress = QProgressDialog(
            "Scanning...", "Cancel", 0, len(cmds), self)
        self.progress.setWindowTitle("Scanning...")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

        t = Thread(target=self._do_scan)
        t.start()

    def _do_scan(self):
        cmds = self.ui.scan_type.currentData().get("cmds")
        try:
            filename, extension = process(
                cmds, destination_filename=self.filename(),
                progress=self.progress, progress_text='{display}',
                main_window=self, status_text='{cmd}',
            )
        except:
            self.scan_error.emit(sys.exc_info()[0])

        self.scan_end.emit(filename)

        cmds = self.ui.scan_type.currentData().get("postprocess", [])
        try:
            filename, extension = process(
                cmds, destination_filename=self.filename(),
                in_extention=extension,
                main_window=self, status_text='{cmd}',
            )
            conv = [
                c for c in self.config.get('to_txt')
                if c['extension'] == extension
            ]
            if len(conv) >= 1:
                conv = conv[0]
                cmds = conv.get("cmds")
                try:
                    text, extension = process(
                        cmds, filename=filename, get_content=True,
                        main_window=self, status_text='{cmd}',
                    )
                    index.add(filename, text)
                except:
                    self.scan_error.emit(sys.exc_info()[0])
        except:
            self.scan_error.emit(sys.exc_info()[0])

    def end_scan(self, filename):
        self.progress.hide()

        self.image_dialog.set_image(filename)
        self.image_dialog.exec()

        self.ui.scan_to.setText(re.sub(
            ' ([0-9]{1,3})$',
            lambda m: ' ' + str(int(m.group(1)) + 1),
            self.ui.scan_to.text()
        ))

    def on_scan_error(self, error):
        err = QErrorMessage(self)
        err.setWindowTitle("eDocuments - scan error")
        err.showMessage(error)


def _to_txt(job):
    filename, cmds = job
    try:
        if len(index.get(str(filename))) == 0:
            text, extension = process(
                cmds, filename=str(filename), get_content=True,
            )
            return filename, text
        return filename, False
    except:
        traceback.print_exc()
        return filename, False
