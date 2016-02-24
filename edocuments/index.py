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
            content=TEXT(stored=True),
            date=STORED,
            directory=STORED,
        )
        self.parser_path = QueryParser("path_id", schema)
        self.parser_content = QueryParser("content", schema)

        if not exists_in(self.directory):
            os.makedirs(self.directory)
            self.index = create_in(self.directory, schema)
        else:
            self.index = open_dir(self.directory)
            if 'path' in self.index.schema.names():
                with self.index.writer() as writer:
                    writer.remove_field('path')
            if 'directory' not in self.index.schema.names():
                with self.index.writer() as writer:
                    writer.add_field('directory', STORED)
            print(
                'Field length:\npath: %i\ncontent: %i\ndate: %i\n'
                'directory: %i' % (
                    self.index.field_length("path_id"),
                    self.index.field_length("content"),
                    self.index.field_length("date"),
                    self.index.field_length("directory"),
                )
            )

# http://whoosh.readthedocs.org/en/latest/schema.html#modifying-the-schema-after-indexing

    def get_date(self, filename):
        filename = edocuments.short_path(filename)
        with self.index.searcher() as searcher:
            results = searcher.search(Term("path_id", filename))
            if len(results) == 0:
                return None
            assert(len(results) == 1)
            assert(results[0].get('date') is not None)
            return results[0].get('date')

    def add(self, filename, text):
        date = Path(filename).stat().st_mtime
        filename = edocuments.short_path(filename)
        with self.index.writer() as writer:
            writer.update_document(
                path_id=filename,
                content="%s\n%s" % (filename, text),
                date=date,
                directory=False,
            )

    def optimize(self):
        self.index.optimize()

    def clear(self):
        with self.index.writer() as writer:
            writer.mergetype = writing.CLEAR

    def search(self, text):
        with self.index.searcher() as searcher:
            query = self.parser_content.parse(text)
            results = searcher.search(query, terms=True, limit=200)
            return [{
                'path': r.get('path_id'),
                'content': r.get('content'),
                'directory': r.get('directory'),
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
