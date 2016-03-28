# -*- coding: utf-8 -*-

RESET = "\x1b[0m"
UNDERLINE = "\x1b[4m"
REVERSE = "\x1b[7m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
LIGHT_RED = "\x1b[1;31m"
LIGHT_GREEN = "\x1b[1;32m"
LIGHT_YELLOW = "\x1b[1;33m"
LIGHT_BLUE = "\x1b[1;34m"
LIGHT_MAGENTA = "\x1b[1;35m"
LIGHT_CYAN = "\x1b[1;36m"

def colorize(text, color, end_color=RESET):
    return color + text + end_color
