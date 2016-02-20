# -*- coding: utf-8 -*-

import os
from pathlib import Path
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.qparser import QueryParser
from whoosh.query import Term
import edocuments


class Index:

    def __init__(self):
        self.directory = os.path.join(edocuments.root_folder, '.index')
        self.dirty = False
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

    def get_nb(self, filename):
        filename = edocuments.short_path(filename)
        with self.index.searcher() as searcher:
            return len(searcher.search(Term("path_id", filename)))

# TODO: update
# http://pythonhosted.org//Whoosh/indexing.html#updating-documents
    def add(self, filename, text):
        date = Path(filename).stat().st_mtime
        filename = edocuments.short_path(filename)
        if self.get_nb(filename) == 0:
            self.writer().add_document(
                path_id=filename,
                path=filename,
                content="%s\n%s" % (filename, text),
                date=date)
            self.dirty = True

    def writer(self):
        if self._writer is None:
            self._writer = self.index.writer()
        return self._writer

    def save(self):
        if self.dirty:
            print('Saving index.')
            self.writer.commit(optimize=True)
            self.writer.close()
            self.writer = None

    def search(self, text):
        with self.index.searcher() as searcher:
            query = self.parser_content.parse(text)
            results = searcher.search(query, terms=True, limit=200)
            return [{
                'path': r.get('path'),
                'content': r.get('content'),
                'highlight': r.highlights(
                    'path' if 'path_in' in r.matched_terms() else 'content'
                ),
            } for r in results]


_index = None


def index():
    global _index
    if _index is None:
        _index = Index()
    return _index
