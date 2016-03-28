# -*- coding: utf-8 -*-

import sys
import os
import re
import shutil
import glob
import json
import datetime
import shutil
import subprocess
import argparse
import locale
from edocuments.colorize import colorize, RED, GREEN, BLUE
from edocuments.utils.common import print_diff, files, confirm, read_metadata



def format_num_on_demon(fract):
    if fract is None:
        return ''
    if fract == '':
        return ''
    if type(fract) == int:
        return "%02d" % fract
    if type(fract) == dict:
        print(fract)
    s = fract.split("/")
    if len(s) == 1:
        return "%02d" % int(s[0])
    elif len(s) == 2:
        n, d = s
        return ("%0" + str(len(d)) + "d") % int(n)
    else:
        return fract

def format(metadata, text, jinja):
    try:
        if metadata is None:
            return text
        if jinja:
            from jinja2 import Template
            template = Template(text)
            return template.render(m=metadata, len=len, str=str, format_num_on_demon=format_num_on_demon)
        else:
            return text.format(**metadata)
    except:
        #print('Enable to format {}.'.format(text))
        return text


def mkdir_p(path):
    if path == '':
        return
    try:
        os.makedirs(path)
    except FileExistsError as e:
        pass
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def replace(rflags, rfrom, rto, dst, metadata, jinja):
    flags = 0;
    flags |= re.I if 'i' in rflags else 0
    flags |= re.L if 'l' in rflags else 0
    flags |= re.M if 'm' in rflags else 0
    flags |= re.S if 's' in rflags else 0
    flags |= re.U if 'u' in rflags else 0
    flags |= re.X if 'x' in rflags else 0
    try:
        return re.sub(
            format(metadata, rfrom, jinja),
            format(metadata, rto, jinja),
            dst,
            flags=flags
        )
    except:
        print('Enable to sub {}, {}, {}, {}.'.format(
            format(metadata, rfrom, jinja),
            format(metadata, rto, jinja),
            dst,
            flags
        ))
        raise


def main():
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())
    
    parser = argparse.ArgumentParser(
        description='Rename the file using metadata.',
        usage='''
Jpeg:
rename:
metarenamer --metadata --rename "{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - {FileName}" --replace "i/img_/" "i/dscn/" "/_HDR/ hdr" "i/{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - {DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - /{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - " "i/{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - {DateTimeOriginal:%%Y%%m%%d}_/{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - " --ignore-dir @eaDir 
move:
metarenamer --metadata --move-to "{DateTimeOriginal:%%Y}/{DateTimeOriginal:%%m %%B}" --rename "{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - {FileName}" --replace "i/ - IMG_[0-9]{4}\.jpg/.jpeg" --ignore-dir @eaDir
rm dupplicate:
metarenamer --metadata --replace "i/{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - {DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - /{DateTimeOriginal:%%Y-%%m-%%d %%H:%%M:%%S} - " --ignore-dir @eaDir
Jpeg errors: 
metarenamer --dry-run --replace "/20[01][0-9].*20[01][0-9]/" --ignore-dir @eaDir 
Video Mov:
metarenamer --metadata --move-to "{MediaCreateDate:%%Y}/{MediaCreateDate:%%m %%B}" --rename "{MediaCreateDate:%%Y-%%m-%%d %%H:%%M:%%S} - {FileName}" --ignore-dir @eaDir 

MediaCreateDate
MP3:
metarenamer --jinja --metadata --move-to "{{ m.get('Genre', 'undefined').replace('/', '-') }} - {{ m.get('Artist', m.get('AlbumArtist', 'undefined')).replace('/', '-') }}/{{ m.get('Year', '0000') }} - {{ m.get('Album', m.get('AlbumTitle', 'undefined')).replace('/', '-') }}" --rename "{{ format_num_on_demon(m.get('Track')).replace('/', '-') }} - {%% if m.get('Title', '') == '' %%}{{ m.get('FileName', 'undefined').replace('/', '-') }}{%% else %%}{{ m.get('Title', 'undefined').replace('/', '-') }}{%% endif %%}.{{ m.get('FileType').lower() }}" --replace "/ Piste [0-9]*/" "/.{{ m.get('FileType').lower() }}.{{ m.get('FileType').lower() }}/.{{ m.get('FileType').lower() }}" "/_/ " "/  \+/ " --ignore-dir @eaDir
Some fix:
metarenamer --replace "i/_HDR/ hdr" "i/^img_/"  "i/^dsc_/" "/_/ " "/  / " "i/\.nef$/.nef" "i/\.jpg$/.jpeg" "i/\.jpg\.jpeg/.jpeg" "i/\.CR2/.cr2" --ignore-dir @eaDir

SetMatadata:
metarenamer --metadata --meta-name DateTimeOriginal --meta-value "/(20[01][0-9])([0-9]{2})([0-9]{2}) ([0-9]{2})([0-9]{2})([0-9]{2})/\1-\2-\3 \4:\5:\6" *.jpeg
metarenamer --metadata --meta-name MediaCreateDate --meta-value "/(20[01][0-9])([0-9]{2})([0-9]{2}) ([0-9]{2})([0-9]{2})([0-9]{2})/\1-\2-\3 \4:\5:\6" *.mp


IMG-20140930-WA0000.jpeg
VID-20140531-WA0000.mp4
Laetitia phone WhatsApp Media WhatsApp Images Sent 20140930-WA0000.jpeg
Laetitia phone WhatsApp Media WhatsApp Video 20140531-WA0000.mp4

''')
    parser.add_argument(
        'directory', nargs='*', default=['.'],
        help='root foldrers'
    )
    parser.add_argument(
        '--view', action='store_true',
        help='view the available tags'
    )
    parser.add_argument(
        '--metadata', action='store_true',
        help='view the available tags'
    )
    parser.add_argument(
        '--apply', action='store_true',
        help='apply the change'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='just see the diff'
    )
    parser.add_argument(
        '--rename', nargs=1,
        help='rename to'
    )
    parser.add_argument(
        '--replace', nargs='*', default=[],
        help='''replace in the file name pattern `flags/from/to`
flags can contains:
i => Perform case-insensitive matching.
l => Make \w, \W, \b, \B, \s and \S dependent on the current locale.
m => Multiline.
s => Make the '.' special character match any character at all.
u => Make \w, \W, \b, \B, \d, \D, \s and \S dependent on the Unicode character properties database.
x => Verbose
See also: https://docs.python.org/2/library/re.html#module-contents'''
    )
    parser.add_argument(
        '--move-to', nargs=1,
        help='move to (from base folder)'
    )
    parser.add_argument(
        '--relative-move', nargs=1,
        help='move to (relative to current folder)'
    )
    parser.add_argument(
        '--ignore-dir', nargs='*', default=[],
        help='ignore the following dirrectories',
    )
    parser.add_argument(
        '--jinja', action='store_true',
        help='use jinja templates'
    )
    parser.add_argument(
        '--meta-name',
        help='The metadata name to set'
    )
    parser.add_argument(
        '--meta-value',
        help='The metadata value to set from filename, see --replace'
    )

    args = parser.parse_args()
    args.replace = [r.split('/') for r in args.replace]
    false = [r for r in args.replace if len(r) != 3]
    if len(false) > 0:
        print("Error in --replace:\n%s" % "\n".join(["/".join(r) for r in false]))
        exit(1);
    
    rename_list = []

    for f, f_ in files(args.directory, args.ignore_dir):
        if os.path.isfile(f):
            try:
                metadata = None
                if args.metadata or args.view:
                    metadata = read_metadata(j, args.view)
                    if args.view:
                        print(json.dumps(metadata, indent=4))
                        exit()

                try:
                    if args.meta_name is not None and args.meta_value is not None:
                        meta_value = args.meta_value.split('/')
                        if len(meta_value) != 3:
                            print(args.meta_value)
                            print("Error in --meta_value: %s" % args.meta_value)
                            exit(1)
                        rflags, rfrom, rto = meta_value
                        value = replace(rflags, "^.*%s.*$" % rfrom, rto, f_, metadata, args.jinja)
                        if metadata is not None and args.meta_name in metadata:
                            old_value = metadata[args.meta_name]
                            if isinstance(old_value, datetime.datetime):
                                old_value = datetime.datetime.strftime(old_value, "%Y-%m-%d %H:%M:%S")
                            if value != old_value:
                                print(f)
                                print_diff(old_value, value)
                                rename_list.append((None, f, None, value))
                        else:
                            print(f)
                            print("Set the metadata '%s' to '%s'." % (
                                colorize(args.meta_name, BLUE),
                                colorize(value, GREEN)))
                            rename_list.append((None, f, None, value))
                    else:
                        if args.rename is not None:
                            dst = format(metadata, args.rename[0], args.jinja)
                        else:
                            dst = f_

                        for rflags, rfrom, rto in args.replace:
                            dst = replace(rflags, rfrom, rto, dst, metadata, args.jinja)
                            
                        if args.move_to is not None:
                            to_dir = format(metadata, args.move_to[0], args.jinja)
                        elif args.relative_move is not None:
                            to_dir = re.sub("^\./", "",format(metadata, os.path.join(path, args.relative_move[0]), args.jinja))
                        else:
                            to_dir = "" if path == "." else re.sub("^\./", "", path)
                            
                        full_dest = os.path.join(to_dir, dst)

                        if f != full_dest:
                            print_diff(f, full_dest)
                            if os.path.exists(full_dest):
                                sys.stderr.write("Destination already exists")
                            elif len([i for i in rename_list if i[1] == full_dest]) != 0:
                                sys.stderr.write("Destination will already exists")
                            else:
                                rename_list.append((to_dir, f, full_dest, None))
                except KeyError as e:
                    sys.stderr.write("%s: %s not found in %s\n" % (f, e, ", ".join(metadata.keys())))
                    pass
            except subprocess.CalledProcessError as e:
                sys.stderr.write("Error on getting metadata on '%s'.\n" % f)
#    except Exception as e:
#        sys.stderr.write("%s\n" % str(e))
#        raise e
            
    if len(rename_list) != 0 and not args.dry_run and (args.apply or confirm()):
        for to_dir, src, dst, meta_value in rename_list:
            if to_dir is not None:
                mkdir_p(to_dir)
                shutil.move(src, dst)
            elif meta_value is not None:
                subprocess.check_output(['exiftool', '-%s=%s' % (args.meta_name, meta_value), src])

if __name__ == "__main__":
    main()
