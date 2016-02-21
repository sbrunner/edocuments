# -*- coding: utf-8 -*-

import os
from pathlib import Path
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.qparser import QueryParser
from whoosh.query import Term
from whoosh import writing
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
# http://whoosh.readthedocs.org/en/latest/schema.html#modifying-the-schema-after-indexing

    def get_date(self, filename):
        filename = edocuments.short_path(filename)
        with self.index.searcher() as searcher:
            results = searcher.search(Term("path_id", filename))
            if len(results) == 0:
                return None
            assert(len(results) == 1)
            return results[0].get('date')

    def add(self, filename, text):
        date = Path(filename).stat().st_mtime
        filename = edocuments.short_path(filename)
        with self.index.writer() as writer:
            writer.update_document(
                path_id=filename,
                path=filename,
                content="%s\n%s" % (filename, text),
                date=date)

    def optimize(self):
        self.index.optimize()
        with self.index.writer() as writer:
            writer.mergetype = writing.CLEAR

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
