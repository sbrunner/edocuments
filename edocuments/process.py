# -*- coding: utf-8 -*-


import os
import re
from tempfile import NamedTemporaryFile
from subprocess import check_call
from shutil import copyfile
from PyQt5.QtCore import QObject, pyqtSignal
import edocuments


class Process(QObject):
    progress = pyqtSignal(int, str, str, dict)
    cancel = False

    def process(
            self, names, filename=None, destination_filename=None,
            in_extention=None, get_content=False):
        cmds = edocuments.config.get("cmds", {})
        out_ext = in_extention

        original_filename = filename
        if destination_filename is None:
            destination_filename = filename
        for no, name in enumerate(names):
            cmd = cmds.get(name)
            if cmd is None:
                raise "Missing command '%s' in `cmds`" % name

            if isinstance(cmd, str):
                cmd = dict(cmd=cmd)

            if cmd.get('type') == 'rename':
                destination_filename = self._rename(cmd, destination_filename)
            else:
                if 'out_ext' in cmd:
                    out_ext = cmd['out_ext']

                inplace = cmd.get('inplace', False)
                cmd_cmd = cmd.get('cmd')

                if inplace:
                    out_name = filename
                else:
                    if out_ext is None:
                        out_name = NamedTemporaryFile(mode='w+b').name
                    else:
                        out_name = NamedTemporaryFile(
                            mode='w+b',
                            suffix='.' + out_ext
                        ).name

                params = {}

                if filename is not None:
                    params["in"] = "'%s'" % filename.replace("'", "'\"'\"'")

                if not inplace:
                    params["out"] = "'%s'" % out_name.replace("'", "'\"'\"'")

                try:
                    cmd_cmd = cmd_cmd.format(**params)
                except:
                    print("Error in {name}: {cmd}, with {params}".format(
                        name=name, cmd=cmd_cmd, params=params))
                    raise

                if self.cancel is True:
                    return None, None
                print("{name}: {cmd}".format(name=name, cmd=cmd_cmd))
                self.progress.emit(no, name, cmd_cmd, cmd)
                check_call(cmd_cmd, shell=True)

                filename = out_name

        if get_content:
            content = None
            if os.path.exists(filename):
                with open(filename) as f:
                    content = f.read()
                if original_filename is None or original_filename != filename:
                    os.unlink(filename)
            return content, out_ext
        else:
            if original_filename is not None and original_filename != filename:
                os.unlink(original_filename)
            if out_ext is not None:
                destination_filename = "%s.%s" % (re.sub(
                    r"\.[a-z0-9A-Z]{2,5}$", "",
                    destination_filename
                ), out_ext)
            if filename != destination_filename:
                directory = os.path.dirname(destination_filename)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                copyfile(filename, destination_filename)
                os.unlink(filename)

            return destination_filename, out_ext

    def _rename(self, cmd, destination_filename):
        from_re = cmd.get('from')
        to_re = cmd.get('to')
        if cmd.get('format') in ['upper', 'lower']:
            def format_term(term):
                if cmd.get('format') == 'upper':
                    return term.upper()
                else:
                    return term.lower()
            to_re = lambda m: format_term(m.group(0))
        return re.sub(from_re, to_re, destination_filename)

    def destination_filename(self, names, filename, extension=None):
        cmds = edocuments.config.get("cmds", {})

        for name in names:
            cmd = cmds.get(name)
            if cmd is None:
                raise "Missing command '%s' in `cmds`" % name

            if isinstance(cmd, str):
                cmd = {}

            if cmd.get('type') == 'rename':
                filename = self._rename(cmd, filename)
            else:
                if 'out_ext' in cmd:
                    extension = cmd['out_ext']

        if extension is not None:
            filename = "%s.%s" % (re.sub(
                r"\.[a-z0-9A-Z]{2,5}$", "",
                filename
            ), extension)
        return filename, extension
