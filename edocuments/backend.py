# -*- coding: utf-8 -*-

import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
import edocuments
from edocuments.process import Process
from edocuments.index import index


class Backend(QObject):
    update_library_progress = pyqtSignal(int, str)
    scan_end = pyqtSignal(str)
    scan_error = pyqtSignal(str)
    process = Process()

    def do_scan(self, filename, cmds, postprocess):
        try:
            filename, extension = self.process.process(
                cmds, destination_filename=filename,
            )
        except:
            self.scan_error.emit(str(sys.exc_info()[0]))
            raise

        if filename is None:
            return

        self.scan_end.emit(filename)

        try:
            filename, extension = self.process.process(
                postprocess, filename=filename,
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

    def do_update_library(self):
        todo = []
        for conv in edocuments.config.get('to_txt'):
            cmds = conv.get("cmds")
            for filename in Path(edocuments.root_folder).rglob(
                    "*." + conv.get('extension')):
                if index().get_nb(str(filename)) == 0:
                    todo.append((str(filename), cmds))
                    self.update_library_progress.emit(
                        0, 'Browsing the files (%i)...' % len(todo))

        nb = len(todo)

        results = edocuments.pool.imap_unordered(self.to_txt, todo)

        interval = timedelta(
            seconds=edocuments.config.get('save_interval', 60))
        last_save = datetime.now()

        nb_error = 0
        no = 0

        self.update_library_progress.emit(
            0, 'Parsing the files %i/%i.' % (no, nb))
        for filename, text in results:
            no += 1
            self.update_library_progress.emit(
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

    def to_txt(self, job):
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
