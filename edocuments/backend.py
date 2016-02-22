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
    update_library_progress = pyqtSignal(int, str, str)
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
                except:
                    self.scan_error.emit(str(sys.exc_info()[0]))
                    raise
        except:
            self.scan_error.emit(str(sys.exc_info()[0]))
            raise

    def do_update_library(self):
        docs_to_rm = []
        with index().index.reader() as reader:
            for num, doc in reader.iter_docs():
                if not Path(edocuments.long_path(doc['path_id'])).exists():
                    print("Delete document: " + doc['path_id'])
                    docs_to_rm.append(num)

        self.update_library_progress.emit(
            0, 'Adding the directories...', '')
        with index().index.writer() as writer:
            for directory in Path(edocuments.root_folder).rglob('*'):
                if \
                        directory.is_dir() and \
                        index().get_date(directory) is None:
                    writer.add_document(
                        path_id=str(directory),
                        content=str(directory),
                        date=directory.stat().st_mtime,
                        directory=True,
                    )

        todo = []
        for conv in edocuments.config.get('to_txt'):
            cmds = conv.get("cmds")
            for filename in Path(edocuments.root_folder).rglob(
                    "*." + conv.get('extension')):
                current_date = index().get_date(filename)
                new_date = filename.stat().st_mtime
                if current_date is None or current_date < new_date:
                    todo.append((str(filename), cmds))
                    self.update_library_progress.emit(
                        0, 'Browsing the files (%i)...' % len(todo), str(filename))

        nb = len(todo)
        nb_error = 0
        no = 0

        print('Removes %i old documents.' % len(docs_to_rm))

        with index().index.writer() as writer:
            for num in docs_to_rm:
                writer.delete_document(num)

        self.update_library_progress.emit(
            0, 'Parsing the files %i/%i.' % (no, nb), '',
        )

        with ThreadPoolExecutor(
            max_workers=edocuments.config.get('nb_process', 8)
        ) as executor:
            future_results = {
                executor.submit(self.to_txt, t):
                t for t in todo
            }

            for feature in as_completed(future_results):
                filename, text = future_results[feature]
                no += 1
                self.update_library_progress.emit(
                    no * 100 / nb, 'Parsing the files %i/%i.' % (no, nb),
                    edocuments.short_path(filename),
                )
                print("%i/%i" % (no, nb))

                if text is False:
                    nb_error += 1
                else:
                    index().add(filename, text)

        index().optimize()

        if nb_error != 0:
            self.scan_error.emit("Finished with %i errors" % nb_error)
        else:
            self.update_library_progress.emit(
                100, 'Finish', '',
            )

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
