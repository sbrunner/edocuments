# -*- coding: utf-8 -*-

import os
from pathlib import Path
from datetime import datetime
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.qparser import QueryParser
from whoosh.query import Term
import edocuments


class Index:
    directory = os.path.expanduser(
        '~/.local/share/applications/edocuments/index')
    dirty = False

    def __init__(self):
        schema = Schema(
            path_id=ID(stored=True, unique=True),
            path=TEXT(stored=True),
            content=TEXT(stored=True),
            date=STORED
        )
        self.parser_path = QueryParser("path_id", schema)
        self.parser_content = QueryParser("content", schema)

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            self.index = create_in(self.directory, schema)
        else:
            self.index = open_dir(self.directory)
        self.writer = self.index.writer()

    def get_nb(self, filename):
        if filename[:len(edocuments.root_folder)] == edocuments.root_folder:
            filename = filename[len(edocuments.root_folder) + 1:]
        with self.index.searcher() as searcher:
            return len(searcher.search(Term("path_id", filename)))

# TODO: update
# http://pythonhosted.org//Whoosh/indexing.html#updating-documents
    def add(self, filename, text):
        date = Path(filename).stat().st_mtime
        if filename[:len(edocuments.root_folder)] == edocuments.root_folder:
            filename = filename[len(edocuments.root_folder) + 1:]
        if self.get_nb(filename) == 0:
            self.writer.add_document(
                path_id=filename,
                path=filename,
                content="%s\n%s" % (filename, text),
                date=date)
            self.dirty = True

    def save(self):
        if self.dirty:
            print('Save index.')
            self.writer.commit(optimize=True)
            self.writer = self.index.writer()

    def search(self, text):
        start = datetime.now()
        try:
            with self.index.searcher() as searcher:
                query = self.parser_path.parse(text)

                results = searcher.search(query)
                if len(results) == 0:
                    query = self.parser_content.parse(text)
                    results = searcher.search(query)
                return [{
                    'path': r.get('path'),
                    'content': r.get('content'),
                    'highlight': r.highlights('content'),
                } for r in results]
        finally:
            print('search in %s.' % (datetime.now() - start))

index = Index()
