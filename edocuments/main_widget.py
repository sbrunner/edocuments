# -*- coding: utf-8 -*-

import os
import sys
import re
import pathlib
import traceback
from threading import Thread
from subprocess import call
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.Qt import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QFileDialog, \
    QErrorMessage, QMessageBox, QProgressDialog, QListWidgetItem
import edocuments
from edocuments.process import Process
from edocuments.index import index
from edocuments.ui.main import Ui_MainWindow
from edocuments.label_dialog import Dialog


class MainWindow(QMainWindow):
    scan_end = pyqtSignal(str)
    scan_error = pyqtSignal(str)
    update_update_library_progress = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.process = Process()

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
        self.ui.open.clicked.connect(self.open_selected)
        self.ui.open_folder.clicked.connect(self.open_folder)

        self.image_dialog = Dialog()

        self.scan_end.connect(self.end_scan)
        self.scan_error.connect(self.on_scan_error)
        self.update_update_library_progress.connect(
            self.on_update_update_library_progress)

        self.ui.search_text.textChanged.connect(self.search)
        self.ui.search_result_list.itemSelectionChanged.connect(
            self.selection_change)

        self.ui.library_update.triggered.connect(self.update_library)
        self.process.progress.connect(self.on_progress)

    def open_selected(self):
        item = self.ui.search_result_list.currentItem()
        if item is not None:
            cmd = edocuments.config.get('open_cmd').split(' ')
            cmd.append(edocuments.long_path(item.result.get('path')))
            call(cmd)

    def open_folder(self):
        item = self.ui.search_result_list.currentItem()
        if item is not None:
            cmd = edocuments.config.get('open_cmd').split(' ')
            cmd.append(os.path.dirname(
                edocuments.long_path(item.result.get('path'))))
            call(cmd)

    def selection_change(self):
        item = self.ui.search_result_list.currentItem()
        if item is not None:
            self.ui.search_result_text.document().setHtml(
                item.result.get('highlight'))
        else:
            self.ui.search_result_text.document().setHtml('')

    def search(self, text):
        model = self.ui.search_result_list.model()
        model.removeRows(0, model.rowCount())
        for result in index().search(self.ui.search_text.text()):
            item = QListWidgetItem(result['path'], self.ui.search_result_list)
            item.result = result

    def scan_browse(self, event):
        filename = QFileDialog.getSaveFileName(
            self, "Scan to", directory=self.filename()
        )[0]
        filename = re.sub(r"\.[a-z0-9A-Z]{2,5}$", "", filename)

        filename = edocuments.short_path(filename)
        self.ui.scan_to.setText(filename)

    def update_library(self):
        self.update_library_progress = QProgressDialog(
            "Scanning...", None, 0, 100, self)
        self.update_library_progress.setWindowTitle('Updating the library...')
        self.update_library_progress.setLabelText('Browsing the files...')
        self.update_library_progress.setWindowModality(Qt.WindowModal)
        self.update_library_progress.show()

        t = Thread(target=self._do_update_library)
        t.start()

    def on_update_update_library_progress(self, pos, text):
        self.update_library_progress.setValue(pos)
        self.update_library_progress.setLabelText(text)

    def _do_update_library(self):
        todo = []
        for conv in edocuments.config.get('to_txt'):
            cmds = conv.get("cmds")
            for filename in Path(edocuments.root_folder).rglob(
                    "*." + conv.get('extension')):
                if index().get_nb(str(filename)) == 0:
                    todo.append((str(filename), cmds))
                    self.update_update_library_progress.emit(
                        0, 'Browsing the files (%i)...' % len(todo))

        nb = len(todo)

        results = edocuments.pool.imap_unordered(_to_txt, todo)

        interval = timedelta(
            seconds=edocuments.config.get('save_interval', 60))
        last_save = datetime.now()

        nb_error = 0
        no = 0

        self.update_update_library_progress.emit(
            0, 'Parsing the files %i/%i.' % (no, nb))
        for filename, text in results:
            no += 1
            self.update_update_library_progress.emit(
                no * 100 / nb, 'Parsing the files %i/%i.' % (no, nb))
            print("%i/%i" % (no, nb))

            if text is False:
                nb_error += 1
            else:
                index().add(filename, text)

            if datetime.now() - last_save > interval:
                index().save()
                last_save = datetime.now()

        index().save()

        if nb_error != 0:
            self.scan_error.emit("Finished with %i errors" % nb_error)

    def filename(self):
        return edocuments.long_path(self.ui.scan_to.text())

    def scan_start(self, event=None):
        if pathlib.Path(self.filename()).is_dir():
            err = QErrorMessage(self)
            err.setWindowTitle("eDocuments - Error")
            err.showMessage("The destination is a directory!")
            return

        destination, extension = self.process.destination_filename(
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

    def on_progress(self, no, name, cmd_cmd, cmd):
        if self.progress is not None:
            self.progress.setValue(no)
            self.progress.setLabelText(cmd.get('display', ''))
            if self.progress.wasCanceled() is True:
                print("Cancel")
                self.process.cancel = True
        self.statusBar().showMessage(cmd_cmd)

    def _do_scan(self):
        cmds = self.ui.scan_type.currentData().get("cmds")
        try:
            filename, extension = self.process.process(
                cmds, destination_filename=self.filename(),
            )
        except:
            self.scan_error.emit(str(sys.exc_info()[0]))
            raise

        if filename is None:
            return

        self.scan_end.emit(filename)

        cmds = self.ui.scan_type.currentData().get("postprocess", [])
        try:
            filename, extension = self.process.process(
                cmds, filename=filename,
                destination_filename=self.filename(),
                in_extention=extension,
            )
            conv = [
                c for c in edocuments.config.get('to_txt')
                if c['extension'] == extension
            ]
            if len(conv) >= 1:
                conv = conv[0]
                cmds = conv.get("cmds")
                try:
                    text, extension = self.process.process(
                        cmds, filename=filename, get_content=True,
                    )
                    index().add(filename, text)
                except:
                    self.scan_error.emit(str(sys.exc_info()[0]))
                    raise
        except:
            self.scan_error.emit(str(sys.exc_info()[0]))
            raise

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
        print('Error: %s' % error)
        err = QErrorMessage(self)
        err.setWindowTitle("eDocuments - scan error")
        err.showMessage(error)


def _to_txt(job):
    filename, cmds = job
    try:
        text, extension = Process().process(
            cmds, filename=str(filename), get_content=True,
        )
        if text is None:
            text = ''
        return filename, text
    except:
        traceback.print_exc()
        return filename, False
