# -*- coding: utf-8 -*-

import os
import sys
from yaml import load
from PyQt5.QtWidgets import QApplication

from edocuments.main_widget import MainWindow

CONFIG_FILENAME = "edocuments.yaml"

if 'APPDATA' in os.environ:
    CONFIG_PATH = os.path.join(os.environ['APPDATA'], CONFIG_FILENAME)
elif 'XDG_CONFIG_HOME' in os.environ:
    CONFIG_PATH = os.path.join(os.environ['XDG_CONFIG_HOME'], CONFIG_FILENAME)
else:
    CONFIG_PATH = os.path.join(os.environ['HOME'], '.config', CONFIG_FILENAME)

config = {}
root_folder = None


def gui_main():
    global config, root_folder
    with open(CONFIG_PATH) as f:
        config = load(f.read())
    root_folder = "%s/%s/" % (
        os.path.expanduser('~'),
        config.get("root_folder"),
    )
    print(root_folder)

    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    app.exec()
