# -*- coding: utf-8 -*-

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path
from yaml import load
from argparse import ArgumentParser
from bottle import mako_template
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
main_window = None


def short_path(filename):
    global root_folder
    filename = str(filename)
    if filename[:len(root_folder)] == root_folder:
        return filename[len(root_folder):]
    return filename


def long_path(filename):
    global root_folder
    if len(filename) == 0 or filename[0] != '/':
        return os.path.join(root_folder, filename)
    return filename


def gui_main():
    global config, root_folder, settings, main_window
    with open(CONFIG_PATH) as f:
        config = load(f.read())
    root_folder = os.path.expanduser(config.get("root_folder"))
    if root_folder[-1] != '/':
        root_folder += '/'
    settings = QSettings("org", "edocuments")

    app = QApplication(sys.argv)
    main_window = MainWindow()
    if settings.value("geometry") is not None:
        main_window.restoreGeometry(settings.value("geometry"))
    if settings.value("state") is not None:
        main_window.restoreState(settings.value("state"))

    main_window.show()
    app.exec()
    settings.setValue("geometry", main_window.saveGeometry())
    settings.setValue("state", main_window.saveState())
    settings.sync()


def cmd_main():
    parser = ArgumentParser(
        description='eDocuments - a simple and productive personal documents '
        'library.',
        prog=sys.argv[0]
    )
    parser.add_argument(
        '--install', action='store_true',
        help='Install the application icon, the required packages, '
        'and default config file',
    )
    parser.add_argument(
        '--lang3', default='eng', metavar='LANG',
        help='the language used by the OCR',
    )
    parser.add_argument(
        '--list-available-lang3', action='store_true',
        help='List the available language used by the OCR.',
    )
    options = parser.parse_args()

    if options.list_available_lang3:
        if Path('/usr/bin/apt-cache').exists():
            result = subprocess.check_output([
                '/usr/bin/apt-cache', 'search', 'tesseract-ocr-'])
            result = str(result)[1:].strip("'")
            result = result.replace('\\n', '\n')
            result = re.sub(
                '\ntesseract-ocr-all - [^\n]* packages\n',
                '', result, flags=re.MULTILINE)
            result = re.sub(r'tesseract-ocr-', '', result)
            result = re.sub(r' - tesseract-ocr language files ', ' ', result)
            print(result)
        else:
            exit('Works only on Debian base OS')

    if options.install:
        if input(
            'Create desktop and icon files (edocuments.desktop and '
            'edocuments.png in ~/.local/share/applications)?\n'
        ) in ['y', 'Y']:
            if not Path(os.path.expanduser(
                        '~/.local/share/applications')).exists():
                os.makedirs(os.path.expanduser('~/.local/share/applications'))
            ressource_dir = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), 'ressources')
            shutil.copyfile(
                os.path.join(ressource_dir, 'edocuments.desktop'),
                os.path.expanduser(
                    '~/.local/share/applications/edocuments.desktop')
            )
            shutil.copyfile(
                os.path.join(ressource_dir, 'edocuments.png'),
                os.path.expanduser(
                    '~/.local/share/applications/edocuments.png')
            )
        if input(
            'Create the basic configuration '
            '(~/.config/edocuments.yaml)?\n'
        ) in ['y', 'Y']:
            config = mako_template(
                os.path.join(ressource_dir, 'config.yaml'),
                lang=options.lang3
            )
            with open(
                os.path.expanduser('~/.config/edocuments.yaml'), 'w'
            ) as file_open:
                file_open.write(config)

        if Path('/usr/bin/apt-get').exists():
            installed_packages = []
            for line in str(subprocess.check_output(['dpkg', '-l'])) \
                    .split(r'\n'):
                if line.find('ii ') == 0:
                    installed_packages.append(re.split(r' +', line)[1])

            packages = [p for p in [
                'python3-pyqt5', 'sane-utils', 'imagemagick',
                'tesseract-ocr', 'tesseract-ocr-' + options.lang3,
                'optipng', 'poppler-utils', 'odt2txt',
                'docx2txt',
            ] if p not in installed_packages]
            print(packages)
            if len(packages) != 0:
                if input(
                    'Install the requires packages (%s)?\n' %
                    ', '.join(packages)
                ) in ['y', 'Y']:
                    subprocess.check_call([
                        'sudo', 'apt-get', 'install',
                    ] + packages)
        else:
            print(
                'WARNING: the package installation works only on Debian '
                'base OS')
