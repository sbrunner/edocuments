# -*- coding: utf-8 -*-

import os
import sys
from yaml import load
from PyQt5.QtCore import QSettings
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
settings = None


def gui_main():
    global config, root_folder, settings
    with open(CONFIG_PATH) as f:
        config = load(f.read())
    root_folder = "%s/%s/" % (
        os.path.expanduser('~'),
        config.get("root_folder"),
    )
    settings = QSettings("org", "edocuments")

    app = QApplication(sys.argv)
    mw = MainWindow()
    print (settings.value("geometry"))
    if settings.value("geometry") is not None:
        mw.restoreGeometry(settings.value("geometry"))
    if settings.value("state") is not None:
        mw.restoreState(settings.value("state"))
    mw.show()
    app.exec()
    print (mw.saveGeometry())
    settings.setValue("geometry", mw.saveGeometry())
    settings.setValue("state", mw.saveState())
    settings.sync()
