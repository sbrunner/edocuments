# -*- coding: utf-8 -*-

import os
import sys
import traceback
from pathlib import Path
from threading import Lock
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
    lock = Lock()

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
        docs_date = {}
        with index().index.reader() as reader:
            for num, doc in reader.iter_docs():
                print("Iter doc: " + doc['path_id'])
                if not Path(edocuments.long_path(doc['path_id'])).exists():
                    print("Delete document: " + doc['path_id'])
                    docs_to_rm.append(num)
                else:
                    docs_date[doc['path_id']] = doc['date']

        self.update_library_progress.emit(
            0, 'Adding the directories...', '')
        index_folder = os.path.join(edocuments.root_folder, '.index')
        for directory in Path(edocuments.root_folder).rglob('*'):
            if \
                    str(directory) not in docs_date and \
                    directory.is_dir() and \
                    str(directory) != index_folder:
                ignore = False
                for ignore_pattern in edocuments.config.get('ignore', []):
                    if directory.match(ignore_pattern):
                        ignore = False
                        break
                if not ignore:
                    with index().index.writer() as writer:
                        writer.update_document(
                            path_id=str(directory),
                            content=str(directory),
                            date=directory.stat().st_mtime,
                            directory=True,
                        )

        self.update_library_progress.emit(
            0, 'Browsing the files (0)...', '')
        index_folder += '/'
        todo = []
        for conv in edocuments.config.get('to_txt'):
            cmds = conv.get("cmds")
            for filename in Path(edocuments.root_folder).rglob(
                    "*." + conv.get('extension')):
                ignore = False
                for ignore_pattern in edocuments.config.get('ignore', []):
                    if directory.match(ignore_pattern):
                        ignore = False
                        break
                if not ignore and filename.exists() and str(filename).find(index_folder) != 0:
                    current_date = docs_date.get(edocuments.short_path(filename))
                    new_date = filename.stat().st_mtime
                    if current_date is None or current_date < new_date:
                        todo.append((str(filename), cmds))
                        self.update_library_progress.emit(
                            0, 'Browsing the files (%i)...' % len(todo), str(filename))

        self.nb = len(todo)
        self.nb_error = 0
        self.no = 0

        print('Removes %i old documents.' % len(docs_to_rm))

        with index().index.writer() as writer:
            for num in docs_to_rm:
                writer.delete_document(num)

        self.update_library_progress.emit(
            0, 'Parsing the files %i/%i.' % (self.no, self.nb), '',
        )

        with ThreadPoolExecutor(
            max_workers=edocuments.config.get('nb_process', 8)
        ) as executor:
            future_results = {
                executor.submit(self.to_txt, t):
                t for t in todo
            }
            for feature in as_completed(future_results):
                pass

        self.update_library_progress.emit(
            0, 'Optimise the index...', '',
        )
        index().optimize()

        if self.nb_error != 0:
            self.scan_error.emit("Finished with %i errors" % self.nb_error)
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

            self.lock.acquire()

            self.no += 1
            self.update_library_progress.emit(
                self.no * 100 / self.nb, 'Parsing the files %i/%i.' % (self.no, self.nb),
                edocuments.short_path(filename),
            )
            print("%i/%i" % (self.no, self.nb))

            if text is False:
                print("Error with document: " + filename)
                self.nb_error += 1
            else:
                index().add(filename, text)

            self.lock.release()
        except:
            traceback.print_exc()
            return filename, False

    def optimize_library(self):
        index().optimize()
