# -*- coding: utf-8 -*-

import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.qparser import QueryParser
from whoosh.query import Term


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
# KEYWORD(lowercase=True)
            self.index = create_in("/home/sbrunner/.docindex", schema)
        else:
            self.index = open_dir("/home/sbrunner/.docindex")
        self.writer = self.index.writer()

    def add(self, path, text_file):
        with self.index.searcher() as searcher:

            query = Term("path_id", path)
# TODO: update
# http://pythonhosted.org//Whoosh/indexing.html#updating-documents
            if len(searcher.search(query)) == 0:
                with text_file.open() as f:
                    self.writer.add_document(
                        path_id=path.__str__(),
                        path=path.__str__(),
                        content="%s\n%s" % (path.__str__(), f.read()),
                        date=path.stat().st_mtime)
                    self.dirty = True

    def save(self):
        if self.dirty:
            self.writer.commit(optimize=True)

    def search(self, text):
        with self.index.searcher() as searcher:
            query = self.parser_path.parse(text)

            results = searcher.search(query)
            if len(results) == 0:
                query = self.parser_content.parse(text)
                return searcher.search(query)
            return results

index = Index()
