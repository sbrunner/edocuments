import re
from os import unlink
from tempfile import NamedTemporaryFile
from subprocess import check_call
from shutil import copyfile
#from subprocess import check_output, check_call


def process(self, cmds, names, file_name, out_ext=None):
    original_file_name = file_name
    destination_file_name = file_name
    for name in names:
        cmd = cmds.get(name)
        if cmd is None:
            raise "Missing command '%s' in `cmds`" % name

        if isinstance(cmd, str):
            cmd = dict(cmd=cmd)

        if cmd.get('type') == 'rename':
            from_re = cmd.get('from')
            to_re = cmd.get('to')
            if cmd.get('format') in ['upper', 'lower']:
                def format_term(term):
                    if cmd.get('format') == 'upper':
                        return term.upper()
                    else:
                        return term.lower()
                to_re = lambda m: format_term(m.group(0))
            destination_file_name = re.sub(from_re, to_re, destination_file_name)
        else:
            if 'out_ext' in cmd:
                out_ext = cmd['out_ext']

            inplace = cmd.get('inplace', False)
#        out_type = cmd.get('out')
#        in_type = cmd.get('in')
            cmd_cmd = cmd.get('cmd')

#        if out_type == 'inplace':
            if inplace:
                out_name = file_name
            else:
                if out_ext is None:
                    out_name = NamedTemporaryFile(mode='w+b').name
                else:
                    out_name = NamedTemporaryFile(mode='w+b', suffix='.' + out_ext).name

            params = {}

#        if in_type != 'pipe':
            params["in"] = "'%s'" % file_name.replace("'", "'\''")

#        if out_type not in ['pipe', 'inplace']:
            if not inplace:
                params["out"] = "'%s'" % out_name.replace("'", "'\''")

            cmd_cmd = cmd_cmd.format(**params)

#        if in_type == 'pipe':
#            raise "in_type as pipe is not supported"

#        if out_type == 'pipe':
#            with open(out_name) as to:
#                to.write(check_output(cmd_cmd, shell=True))
#        else:
            check_call(cmd_cmd, shell=True)

            file_name = out_name

    if original_file_name != file_name:
        unlink(original_file_name)
        copyfile(file_name, destination_file_name)
        unlink(file_name)
