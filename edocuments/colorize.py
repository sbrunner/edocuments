# -*- coding: utf-8 -*-

BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7


def colorize(text, color):
    return "\x1b[01;3%im%s\x1b[0m" % (color, text)
