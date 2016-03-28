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
import edocuments
from edocuments.process import Process
from edocuments.colorize import colorize, RED, GREEN, BLUE
from edocuments.utils.common import files, read_metadata, print_diff, confirm
from concurrent.futures import ThreadPoolExecutor, as_completed


def main():
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())
    
    parser = argparse.ArgumentParser(
        description='Rename the file using metadata.',
        usage='''
Task to do:
name: Predifined command in the config file.
TODO:
rename/<new name>/<flag>
replace/<old>/<new>/<flag>
moveto/<path>/<flag>
movetorelatve/<path>/<flag>
setmeta/<name>/<value>/<flag>

flags can contains:
j => Jinja template.
i => Perform case-insensitive matching.
l => Make \w, \W, \b, \B, \s and \S dependent on the current locale.
m => Multiline.
s => Make the '.' special character match any character at all.
u => Make \w, \W, \b, \B, \d, \D, \s and \S dependent on the Unicode character properties database.
x => Verbose
See also: https://docs.python.org/2/library/re.html#module-contents''')
    '''


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

'''
    parser.add_argument(
        'directory', nargs='*', default=['.'],
        help='root foldrers'
    )
    parser.add_argument(
        '--ignore-dir', nargs='*', default=None,
        help='ignore the following dirrectories',
    )
    parser.add_argument(
        '--filename', nargs='*', default=['.*'],
        help='The filename regexp',
    )
    parser.add_argument(
        '--metadata', action='store_true',
        help='view the available tags'
    )
    parser.add_argument(
        '--view', action='store_true',
        help='view the available tags'
    )
    parser.add_argument(
        '--view-meta',
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
        '--do', nargs='*', default=[],
        help='What we want to do',
    )
    parser.add_argument(
        '--config-file', default=None,
        help='The configuration file',
    )

    args = parser.parse_args()
    
    edocuments.init(args.config_file)
    job_files = []
    process = Process()

    for f, f_ in files(args.directory, args.ignore_dir or edocuments.config.get('ignore_dir', []), args.filename):
        if os.path.isfile(f):
            try:
                metadata = None
                if args.metadata or args.view:
                    metadata = read_metadata(j, args.view)
                    if args.view:
                        print(json.dumps(metadata, indent=4))
                        exit()

                full_dest, extension, task = process.destination_filename(args.do, f)

                if f != full_dest:
                    print_diff(f, full_dest)
                    if os.path.exists(full_dest):
                        sys.stderr.write(colorize("Destination already exists", RED))
                        continue
                    elif len([i for i in job_files if i[1] == full_dest]) != 0:
                        sys.stderr.write(colorize("Destination will already exists", RED))
                        continue                    
                elif task is True:
                    print(colorize(f, BLUE))
                else:
                    continue
                job_files.append(f)
            except subprocess.CalledProcessError as e:
                sys.stderr.write("Error on getting metadata on '%s'.\n" % f)

    if len(job_files) != 0 and not args.dry_run and (args.apply or confirm()):
        progress = Progress(len(job_files), args.do, process)
        progress.run_all(job_files)


class Progress:
    def __init__(self, nb, cmds, process):
        self.nb = nb
        self.no = 0
        self.cmds = cmds
        self.process = process
    
    def run(self, filename):
        result = self.process.process(self.cmds, filename)
        self.no += 1
        print("%i/%i" % (self.no, self.nb))
        return result
        
    def run_all(self, job_files):
        with ThreadPoolExecutor(
            max_workers=edocuments.config.get('nb_process', 8)
        ) as executor:
            future_results = {
                executor.submit(self.run, f):
                f for f in job_files
            }
            for feature in as_completed(future_results):
                pass

if __name__ == "__main__":
    main()
