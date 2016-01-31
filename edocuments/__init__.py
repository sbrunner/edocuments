# -*- coding: utf-8 -*-

import os
import sys
from yaml import load
from autoupgrade import AutoUpgrade
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QMessageBox

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
    if settings.value("geometry") is not None:
        mw.restoreGeometry(settings.value("geometry"))
    if settings.value("state") is not None:
        mw.restoreState(settings.value("state"))

    au = AutoUpgrade('edocuments')
    if au.check():
        msg = QMessageBox(mw)
        msg.setWindowTitle("eDocuments - Upgrade")
        msg.setText("A new version is available")
        msg.setInformativeText("Do you want to do anupdate and restart?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec()
        if ret == QMessageBox.Yes:
            au.upgrade(dependencies=True)
            au.restart()

    mw.show()
    app.exec()
    settings.setValue("geometry", mw.saveGeometry())
    settings.setValue("state", mw.saveState())
    settings.sync()
