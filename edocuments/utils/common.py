# -*- coding: utf-8 -*-

import os
import re
from edocuments.colorize import colorize, RED, GREEN, REVERSE

def common_start(str1, str2):

    if len(str2) > len(str1):
        str1, str2 = (str2, str1)

    start = ""

    for index in range(len(str2)):
        if str1[index] != str2[index]:
            break
        start += str1[index]

    return start


def different(str_, start, end):
    if end == "":
        return str_[len(start):]
    else:
        return str_[len(start):-len(end)]


def print_diff(str1, str2):
    start = common_start(str1, str2)
    end = common_start(str1[::-1], str2[::-1])[::-1]

    # Fix end that recover start ...
    small_str = str1 if len(str1) < len(str2) else str2
    if len(start) + len(end) > len(small_str):
        end = end[len(start) + len(end) - len(small_str):]

    print("- %s%s%s" % (
        colorize(start, RED),
        colorize(colorize(different(str1, start, end), REVERSE), RED),
        colorize(end, RED)
    ))
    print("+ %s%s%s" % (
        colorize(start, GREEN),
        colorize(colorize(different(str2, start, end), REVERSE), GREEN),
        colorize(end, GREEN)
    ))


def files(directories, ignore_dir, filenames=['.*']):
    for directory in directories:
        if os.path.isdir(directory):
            # for f in glob.iglob(args.directory, recursive=True):
            for (path, dirs, files) in os.walk(directory):
                if len(set(path.split('/')) & set(ignore_dir)) > 0:
                    continue
                for f_ in files:
                    for filename in filenames:
                        if re.match(filename, f_):
                            full_path = re.sub("^\./", "", os.path.join(path, f_))
                            yield full_path, f_
                            break
        elif os.path.isfile(directory):
            yield directory, os.path.split(directory)[-1]
            

def confirm(prompt=None, resp=False):
    """
    Prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n: 
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: 
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True
    """
    
    if prompt is None:
        prompt = "Confirm"

    if resp:
        prompt = "%s [%s]|%s: " % (prompt, "y", "n")
    else:
        prompt = "%s [%s]|%s: " % (prompt, "n", "y")
        
    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ["y", "Y", "n", "N"]:
            print("please enter y or n.")
            continue
        if ans == "y" or ans == "Y":
            return True
        if ans == "n" or ans == "N":
            return False


def read_metadata(filename, read_types):
    metadata = json.loads(str(subprocess.check_output(["/usr/bin/exiftool", "-json", f]), encoding='utf-8', errors='strict'))[0]
    if read_types:
        if args.meta_name is not None and args.meta_value is not None:
            for k in metadata.keys():
                if type(metadata[k]) == str:
                    try:
                        metadata[k] = datetime.datetime.strptime(metadata[k], "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        try:
                            metadata[k] = datetime.datetime.strptime(metadata[k], "%Y:%m:%d %H:%M:%S%z")
                        except ValueError:
                            try:
                                metadata[k] = datetime.datetime.strptime(metadata[k], "%d/%m/%Y %H:%M:%S")
                            except ValueError:
                                pass
