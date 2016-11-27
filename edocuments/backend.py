# -*- coding: utf-8 -*-

import os
import sys
import time
import hashlib
import traceback
import threading
import subprocess
import bashcolor
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QObject, pyqtSignal
import edocuments
from metatask.process import Process
from edocuments.index import index, PATH, CONTENT, DATE, DIRECTORY, MD5


class Backend(QObject):
    update_library_progress = pyqtSignal(int, str, str)
    scan_error = pyqtSignal(str)
    process = Process()
    postprocess_process = Process()
    lock = Lock()

    def do_scan(self, filename, cmds, postprocess):
        try:
            filename, extension = self.process.process(
                cmds, destination_filename=filename,
            )
        except:
            traceback.print_exc()
            self.scan_error.emit(str(sys.exc_info()[1]))
            raise

        if filename is None:
            return

        ret, filename, destination, extension, destinations = self.scan_end(filename, postprocess)
        filename, extension = self.postprocess_process.process(
            postprocess, filenames=filename,
            in_extention=extension,
        )
        if ret == 0 and len(destinations) > 1:  # => merge
            Merger(destination, extension, destinations, self)
        else:
            self.tolib(filename, extension)

    def tolib(self, filename, extension):
        try:
            conv = [
                c for c in edocuments.config.get('to_txt')
                if c['extension'] == extension
            ]
            if len(conv) >= 1:
                conv = conv[0]
                cmds = conv.get("cmds")
                try:
                    text, extension = self.postprocess_process.process(
                        cmds, filenames=filename, get_content=True,
                    )
                    new_md5 = hashlib.md5()
                    new_date = Path(filename).stat().st_mtime
                    with open(str(filename), "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            new_md5.update(chunk)
                    index().add(
                        filename, text,
                        new_date,
                        new_md5.hexdigest()
                    )
                except:
                    traceback.print_exc()
                    self.scan_error.emit(str(sys.exc_info()[1]))
                    raise
        except:
            traceback.print_exc()
            self.scan_error.emit(str(sys.exc_info()[1]))
            raise

    def do_update_library(self):
        docs_to_rm = []
        docs_date = {}
        with index().index.reader() as reader:
            for num, doc in reader.iter_docs():
                if \
                        doc[PATH] in docs_date or \
                        not Path(edocuments.long_path(doc[PATH])).exists() or \
                        doc[PATH] != edocuments.short_path(doc[PATH]):
                    print("Delete document: " + doc[PATH])
                    docs_to_rm.append(num)
                else:
                    docs_date[doc[PATH]] = (doc.get(DATE), doc.get(MD5))

        self.update_library_progress.emit(
            0, 'Adding the directories...', '')
        index_folder = '.index'
        for directory in Path(edocuments.root_folder).rglob('*'):
            dir_ = edocuments.short_path(directory)
            if \
                    dir_ not in docs_date and \
                    directory.is_dir() and \
                    directory != index_folder:
                ignore = False
                for ignore_pattern in edocuments.config.get('ignore', []):
                    if directory.match(ignore_pattern):
                        ignore = False
                        break
                if not ignore:
                    with index().index.writer() as writer:
                        writer.update_document(**{
                            PATH: dir_,
                            CONTENT: dir_,
                            DATE: directory.stat().st_mtime,
                            DIRECTORY: True,
                        })

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
                    current_date, md5 = docs_date.get(edocuments.short_path(filename), (None, None))
                    new_date = filename.stat().st_mtime
                    new_md5 = hashlib.md5()
                    with open(str(filename), "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            new_md5.update(chunk)

                    if current_date is None or new_date > current_date:
                        if current_date is not None and (md5 is None or md5 == new_md5.hexdigest()):
                            doc = index().get(filename)
                            index().add(
                                filename,
                                doc[CONTENT],
                                max(new_date, current_date),
                                new_md5.hexdigest()
                            )
                        else:
                            print("Add document: " + edocuments.short_path(filename))
                            todo.append((str(filename), cmds, new_date, new_md5.hexdigest()))
                            self.update_library_progress.emit(
                                0,
                                'Browsing the files ({0:d})...'.format(len(todo)),
                                edocuments.short_path(filename),
                            )

        self.nb = len(todo)
        self.nb_error = 0
        self.no = 0

        print('Removes {0:d} old documents.'.format(len(docs_to_rm)))

        with index().index.writer() as writer:
            for num in docs_to_rm:
                writer.delete_document(num)

        self.update_library_progress.emit(
            0, 'Parsing the files {0:d}/{1:d}.'.format(self.no, self.nb), '',
        )

        print('Process {0:d} documents.'.format(len(todo)))

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
            self.scan_error.emit("Finished with {0:d} errors".format(self.nb_error))
        else:
            self.update_library_progress.emit(
                100, 'Finish', '',
            )

    def to_txt(self, job):
        filename, cmds, date, md5 = job
        try:
            text, extension = self.postprocess_process.process(
                cmds, filenames=[str(filename)], get_content=True,
            )
            if text is None:
                text = ''

            self.lock.acquire()

            self.no += 1
            self.update_library_progress.emit(
                self.no * 100 / self.nb, 'Parsing the files {0:d}/{1:d}.'.format(self.no, self.nb),
                edocuments.short_path(filename),
            )
            print("{0:d}/{1:d}".format(self.no, self.nb))

            if text is False:
                print("Error with document: " + filename)
                self.nb_error += 1
            else:
                index().add(
                    filename,
                    "{0!s}\n{1!s}".format(filename, text),
                    date, md5
                )

            self.lock.release()
        except:
            traceback.print_exc()
            return filename, False

    @staticmethod
    def optimize_library():
        index().optimize()

class Cmd(QObject):
    def __init__(self, dialog, cmd, process):
        self.dialog = dialog
        self.cmd = cmd
        self.process = process
        super(Cmd, self).__init__(dialog)

    def exec_(self):
        filename, extension = self.process.process(
            [self.cmd], filenames=[self.dialog.image],
        )
        self.dialog.set_image(filename)

class Merger:
    def __init__(self, destination, extension, sources, backend):
        self.destination = destination
        self.extension = extension
        self.sources = sources
        self.backend = backend
        t = threading.Thread(
            target=self.do,
        )
        t.start()

    def do(self):
        while True:
            ok = True
            for src in self.sources:
                ok = ok & os.path.exists(src)

            if ok:
                cmd = ["pdftk"] + self.sources + ["output", self.destination, "compress"]
                print("{}: {}".format(
                    bashcolor.colorize("merge", bashcolor.BLUE),
                    " ".join(cmd)
                ))
                subprocess.check_call(cmd)
                cmd = ["rm"] + self.sources
                print("{}: {}".format(
                    bashcolor.colorize("clean", bashcolor.BLUE),
                    " ".join(cmd)
                ))
                subprocess.check_call(cmd)
                self.backend.tolib(self.destination, self.extension)
                return
            else:
                time.sleep(1)
