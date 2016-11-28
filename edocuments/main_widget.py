# -*- coding: utf-8 -*-

import os
import pathlib
from threading import Thread
from subprocess import call
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QMainWindow, QFileDialog, \
    QErrorMessage, QMessageBox, QProgressDialog, QListWidgetItem
import edocuments
from edocuments.backend import Backend
from edocuments.index import index
from edocuments.ui.main import Ui_MainWindow
from edocuments.label_dialog import Dialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.backend = Backend()

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

        self.image_dialog = Dialog(self.backend.process)

        self.backend.scan_end.connect(self.end_scan)
        self.backend.scan_error.connect(self.on_scan_error)
        self.backend.update_library_progress.connect(
            self.on_update_update_library_progress)

        self.ui.search_text.textChanged.connect(self.search)
        self.ui.search_result_list.itemSelectionChanged.connect(
            self.selection_change)

        self.ui.library_update.triggered.connect(self.update_library)
        self.ui.library_optimize.triggered.connect(
            self.backend.optimize_library)
        self.ui.library_reset.triggered.connect(self.reset_library)
        self.backend.process.progress.connect(self.on_progress)

        self.progress = QProgressDialog(
            "Scanning...", "Cancel", 0, 1, self)
        self.progress.setWindowTitle("Scanning...")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setLabelText('Scanning...')
        self.progress.setAutoClose(False)
        self.progress.setAutoReset(False)
        self.progress.canceled.connect(self.no_cancel)
        self.progress.reset()

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

    def reset_library(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Reset the library...")
        msg.setInformativeText("Are you sure to reset all you index?")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msg.exec() == QMessageBox.Ok:
            index().clear()

    def search(self, text):
        model = self.ui.search_result_list.model()
        model.removeRows(0, model.rowCount())
        raw_results = index().search(self.ui.search_text.text())
        dirs = dict([
            (r.get('path'), -1)
            for r in raw_results if r.get('directory')
        ])
        results = {}
        for index_, result in enumerate(raw_results):
            path_ = result.get('path')
            dir_ = os.path.dirname(path_)
            if dir_ not in dirs:
                results[path_] = [result, float(index_) / len(raw_results)]
            else:
                dirs[dir_] += 1

        for dir_, count in dirs.items():
            if dir_ in results:
                results[dir_][1] += count

        results = sorted(results.values(), key=lambda x: -x[1])

        for result, count in results:
            postfix = ' (%i)' % (count + 1) if result.get('directory') else ''
            item = QListWidgetItem(
                result['path'] + postfix,
                self.ui.search_result_list
            )
            item.result = result

    def scan_browse(self, event):
        filename = QFileDialog.getSaveFileName(
            self, "Scan to", directory=self.filename()
        )[0]
        if filename == '':
            return
        filename = edocuments.short_path(filename)
        self.ui.scan_to.setText(filename)

    def update_library(self):
        self.update_library_progress = QProgressDialog(
            "Update Library...", None, 0, 100, self)
        self.update_library_progress.setWindowTitle('Updating the library...')
        self.update_library_progress.setLabelText('Browsing the files...')
        self.update_library_progress.setWindowModality(Qt.WindowModal)
        self.update_library_progress.show()

        t = Thread(target=self.backend.do_update_library)
        t.start()

    def on_update_update_library_progress(self, pos, text, status):
        self.update_library_progress.setValue(pos)
        self.update_library_progress.setLabelText(text)
        self.statusBar().showMessage(status)

    def filename(self):
        return edocuments.long_path(self.ui.scan_to.text())

    def scan_start(self, event=None):
        self.backend.process.cancel = False
        if pathlib.Path(self.filename()).is_dir():
            err = QErrorMessage(self)
            err.setWindowTitle("eDocuments - Error")
            err.showMessage("The destination is a directory!")
            return

        destination1, extension, _, _ = self.backend.process.destination_filename(
            self.ui.scan_type.currentData().get("cmds"),
            self.filename()
        )
        src_name, src_ext = os.path.splitext(self.filename())
        if "." + extension != src_ext:
            destination1, extension, _, _ = self.backend.process.destination_filename(
                self.ui.scan_type.currentData().get("cmds"),
                self.filename() + "." + extension
            )

        destination2, extension, _, _ = self.backend.process.destination_filename(
            self.ui.scan_type.currentData().get("postprocess", {}),
            destination1
        )

        if pathlib.Path(destination1).is_file() or pathlib.Path(destination2).is_file():
            msg = QMessageBox(self)
            msg.setWindowTitle("Scanning...")
            msg.setText("The destination file already exists")
            msg.setInformativeText("Do you want to overwrite it?")
            msg.setStandardButtons(
                QMessageBox.Ok | QMessageBox.Cancel | QMessageBox.Open)
            ret = msg.exec()
            if ret == QMessageBox.Ok:
                if pathlib.Path(destination1).is_file():
                    os.unlink(destination1)
                if pathlib.Path(destination2).is_file():
                    os.unlink(destination2)
                self._scan()
            elif ret == QMessageBox.Open:
                if pathlib.Path(destination1).is_file():
                    cmd = edocuments.config.get('open_cmd').split(' ')
                    cmd.append(destination1)
                    call(cmd)
                if pathlib.Path(destination2).is_file():
                    cmd = edocuments.config.get('open_cmd').split(' ')
                    cmd.append(destination2)
                    call(cmd)
        else:
            self._scan()

    def _scan(self):
        cmds = self.ui.scan_type.currentData().get("cmds")

        self.progress.setMaximum(len(cmds))
        self.progress.show()

        t = Thread(
            target=self.backend.do_scan,
            args=[
                self.filename(),
                self.ui.scan_type.currentData().get("cmds"),
                self.ui.scan_type.currentData().get("postprocess", []),
            ],
        )
        t.start()

    def no_cancel(self):
        self.progress.show()
        self.backend.process.cancel = True
        self.progress.setLabelText('Canceling...')

    def on_progress(self, no, name, cmd_cmd, cmd):
        if self.progress is not None:
            if self.progress.wasCanceled() is True:
                self.progress.hide()
                self.statusBar().showMessage("")
                return
            self.progress.setValue(no)
            self.progress.setLabelText(cmd.get('display', ''))
        self.statusBar().showMessage(cmd_cmd)

    def end_scan(self, filename, postprocess):
        self.progress.hide()
        self.progress.reset()

        self.image_dialog.set_image(filename, postprocess)
        self.statusBar().showMessage('')
        ret = self.image_dialog.exec()
        destination = None
        extension = None
        destinations = self.image_dialog.destinations
        if ret == 0:  # finish
            if len(self.image_dialog.destinations) >= 1:
                destination, extension, _, _ = self.backend.process.destination_filename(
                    postprocess,
                    self.image_dialog.image
                )
                self.image_dialog._add()
            self.image_dialog.destinations = []
        else:
            self.scan_start()

        Thread(
            target=self.backend.finalize_document,
            args=[
                ret,
                self.image_dialog.image,
                destination,
                extension,
                destinations,
                postprocess
            ],
        ).start()

    def on_scan_error(self, error):
        print('Error: %s' % error)
        self.progress.hide()
        err = QErrorMessage(self)
        err.setWindowTitle("eDocuments - scan error")
        err.showMessage(error)
