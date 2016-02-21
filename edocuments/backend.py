# -*- coding: utf-8 -*-

import sys
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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
                    index().save()
                except:
                    self.scan_error.emit(str(sys.exc_info()[0]))
                    raise
        except:
            self.scan_error.emit(str(sys.exc_info()[0]))
            raise

    def do_update_library(self):
        todo = []
        with index().index.reader() as reader:
            docs_to_rm = [
                num for num, doc in reader.iter_docs()
                if not Path(edocuments.long_path(doc['path'])).exists()
            ]

        for conv in edocuments.config.get('to_txt'):
            cmds = conv.get("cmds")
            for filename in Path(edocuments.root_folder).rglob(
                    "*." + conv.get('extension')):
                if index().get_nb(str(filename)) == 0:
                    todo.append((str(filename), cmds))
                    self.update_library_progress.emit(
                        0, 'Browsing the files (%i)...' % len(todo))

        nb = len(todo)

        with ThreadPoolExecutor(
            max_workers=edocuments.config.get('nb_process', 8)
        ) as executor:
            nb_error = 0
            no = 0

            with index().index.writer() as writer:
                for num in docs_to_rm:
                    writer.delete_document(num)

            self.update_library_progress.emit(
                0, 'Parsing the files %i/%i.' % (no, nb))

            future_results = {
                executor.submit(self.to_txt, t):
                t for t in todo
            }

            for feature in as_completed(future_results):
                filename, text = future_results[feature]
                no += 1
                self.update_library_progress.emit(
                    no * 100 / nb, 'Parsing the files %i/%i.' % (no, nb))
                print("%i/%i" % (no, nb))

                if text is False:
                    nb_error += 1
                else:
                    index().add(filename, text)

        index().optimize()

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