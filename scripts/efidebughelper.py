#/usr/bin/env python3
# coding: utf8

import os
import re
import io
from collections import namedtuple
import argparse
import gdb

class EFISections(object):

    Section = namedtuple('Section', ['begin', 'end'])
    _sections = dict()

    def add(self, name, begin, end):
        self._sections[name] = self.Section(begin, end)

    def __getitem__(self, key):
        return self._sections[key]

def unload_executable():
    gdb.execute('file')

def set_architecture():
    gdb.execute('set architecture i386:x86-64:intel')

def load_debugsymbols(libname, image_base, sections):
    text_section = int(image_base, 16) + int(sections['.text'].begin, 16)
    data_section = int(image_base, 16) + int(sections['.data'].begin, 16)
    gdb.execute('add-symbol-file {} {:#x} -s .data {:#x}'.format(libname,
                                                                 text_section,
                                                                 data_section))

def getSections():
    import sys
    info_sections = gdb.execute('info files', to_string=True)
    #print(type(info_sections))
    if sys.version_info.major == 2 and sys.version_info.minor <= 7:
        #print(type(info_sections.decode('utf-8')))
        info_sections = info_sections.decode('utf-8')
    buf = io.StringIO(info_sections)
    compiled_pattern = re.compile(r'^\s+(0x[0-9A-Fa-f]+)[\s\-]+(0x[0-9A-Fa-f]+)\sis\s(\.[a-z_]+)$')
    efi_sections = EFISections()
    for line in buf.readlines():
        result = compiled_pattern.match(line)
        if result is not None:
            efi_sections.add(result.group(3), result.group(1), result.group(2))
    return efi_sections

def parse_args(arguments):
    """
        Parse the script arguments
    """
    def check_path(path):
        """
            Paths checker
        """
        if not os.path.exists(path):
            raise ValueError("{path} does not exist".format(path=path))
        return path

    parser = argparse.ArgumentParser(description='Set up GDB for EFI debugging.')
    parser.add_argument('-f', '--file-with-symbols',
                        metavar='FILE_WITH_SYMBOLS',
                        required=True,
                        type=check_path,
                        help='PE executable with debug symbols')
    parser.add_argument('-b', '--image-base',
                        metavar='IMAGE_BASE',
                        required=True,
                        help='Image base')
    args = parser.parse_args(arguments)
    return args


class EFIDebugHelper(gdb.Command):
    """
        EFI debug helper

    """

    def __init__(self):
        super(EFIDebugHelper, self).__init__('efidebug', gdb.COMMAND_FILES)

    def invoke(self, argument, from_tty):
        args = parse_args(argument.split())
        efi_sections = getSections()
        unload_executable()
        load_debugsymbols(args.file_with_symbols, args.image_base, efi_sections)
        set_architecture()


gdb.write("EFI debug helper\n", gdb.STDOUT)
gdb.write("----------------\n", gdb.STDOUT)
gdb.write(" * efidebug -f <file with debug symbols> -b <image base>\n", gdb.STDOUT)
EFIDebugHelper()
