#!/usr/bin/env python3
# coding: utf8

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import logging
import pexpect


def is_user_root():
    """
        check if the script is run as root
    """
    uid = os.getuid()
    if uid == 0:
        logging.debug("UID=0, root's rights available")
    else:
        logging.debug("UID=%s", uid)
    return uid == 0

def mkfsFAT32(device):
    """
        Format the given device to FAT32
    """
    args = list()
    args.append('mkfs.fat')
    args.append('-I')
    args.append('-F 32')
    args.append(device)
    logging.info("formatting %s in FAT32", device)
    subprocess.check_output(args)

def dd(outputf, size, inputf='/dev/zero', bs=512, skip=None, seek=None):
    """
        Wrapper for the system command 'dd' (see manual for more information)
    """
    count = int(size / bs)
    args = list()
    args.append('dd')
    args.append('if={}'.format(inputf))
    args.append('of={}'.format(outputf))
    args.append('bs={}'.format(bs))
    if skip is not None:
        args.append('skip={}'.format(skip))
    if seek is not None:
        args.append('seek={}'.format(seek))
    args.append('count={}'.format(count))
    logging.info("creating zeroed disk %s", outputf)
    subprocess.check_output(args)

class Mtools(object):
    """
        Mtools context manager
    """

    def __init__(self, disk):
        self._disk = disk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return

    def format(self):
        """
            Format the disk in FAT32
        """
        logging.info("mformat: format to FAT32")
        args = list()
        args.append('mformat')
        args.append('-F')
        args.extend(['-i', self._disk])
        args.extend(['-h', '5'])
        args.extend(['-t', '255'])
        args.extend(['-s', '63'])
        args.extend(['-c', '1'])
        subprocess.check_output(args)

    def copy(self, syspath, fatpath='::'):
        """
            Copy a file or directory to the given FAT path ('/' by default)
        """
        if os.path.isdir(syspath):
            self._copydir(syspath, fatpath)
        else:
            self._copyfile(syspath, fatpath)

    def _copyfile(self, filepath, fatpath='::'):
        logging.info("mcopy: copy %s to %s", filepath, fatpath)
        args = list()
        args.append('mcopy')
        args.extend(['-i', self._disk])
        args.append(filepath)
        args.append(fatpath)
        subprocess.check_output(args)

    def _copydir(self, dirpath, fatpath='::'):
        # Not sure how it works here
        # Investigate and test in the future
        basedir = os.path.basename(dirpath)
        self._mkdir(basedir, fatpath)
        for root, dirs, files in os.walk(dirpath):
            for name in files:
                self._copyfile(name, fatpath + '/' + basedir)

    def _mkdir(self, dirname, fatpath='::'):
        logging.info("mmd: create %s in %s", dirname, fatpath)
        args = list()
        args.append('mmd')
        args.extend(['-i', self._disk])
        args.append(dirname)
        args.append(fatpath)
        subprocess.check_output(args)


class Parted(object):
    """
        Wrapper for the command 'parted' (see manual for more information)
    """

    def __init__(self, disk):
        self._disk = disk
        self._child = None

    def __enter__(self):
        self._child = pexpect.spawn(command='parted',
                                    args=[self._disk],
                                    encoding='utf-8')
        self._child.logfile_read = sys.stdout
        return self

    def __exit__(self, *exc):
        self._child.expect(r"^(parted) ")
        self._child.sendline('quit')
        self._child.expect(pexpect.EOF)
        self._child.close()

    def cmd_newtable(self):
        """
            Create a new Global Partition Table
        """
        logging.info("parted: create new GPT")
        self._child.expect(r"^(parted) ")
        self._child.sendline('mklabel gpt')
        self._child.expect(r"^Yes/No? ")
        self._child.sendline('Y')

    def cmd_newpartition(self, guid):
        """
            Create a new bootable FAT32 partition
        """
        logging.info("gdisk: create new EFI partition")
        self._child.expect(r"^(parted) ")
        self._child.sendline('mkpart {guid} FAT32 2048s 93716s'.format(guid=guid))
        self._child.expect(r"^(parted) ")
        self._child.sendline('toggle 1 boot')

    def cmd_printtable(self):
        """
            Print the partition table
        """
        self._child.expect(r"^(parted) ")
        self._child.sendline('print')


class Gdisk(object):
    """
        Context manager for a GUID partition table (GPT) manipulator.
        Propose the following features:
            - create a GPT
            - create a partition of a given type
            - list the partitions
            - apply changes on disk
    """

    __partition_guids = {
        'EFI': 'ef00'
    }

    def __init__(self, disk):
        self._disk = disk
        self._child = None

    def __enter__(self):
        self._child = pexpect.spawn(command='gdisk',
                                    args=[self._disk],
                                    encoding='utf-8')
        self._child.logfile_read = sys.stdout
        return self

    def __exit__(self, *exc):
        self._child.expect(pexpect.EOF)
        self._child.close()

    def cmd_newtable(self):
        """
            Create a new Global Partition Table
        """
        logging.info("gdisk: create new GPT")
        self._child.expect(r"Command \(\? for help\): ")
        self._child.sendline('o')
        self._child.expect(r"^.*\(Y/N\): ")
        self._child.sendline('Y')

    def cmd_newpartition(self, guid):
        """
            Create a new bootable FAT32 partition
        """
        logging.info("gdisk: create new EFI partition")
        self._child.expect(r"Command \(\? for help\): ")
        self._child.sendline('n')
        self._child.expect(r"Partition number .*, default .*\): ")
        self._child.sendline()
        self._child.expect(r"size\{KMGTP\}: ")
        self._child.sendline()
        self._child.expect(r"size\{KMGTP\}: ")
        self._child.sendline()
        self._child.expect(r"Hex code or GUID.*\): ")
        self._child.sendline(self.__partition_guids[guid])

    def cmd_printtable(self):
        """
            Print the partition table
        """
        self._child.expect(r"Command \(\? for help\): ")
        self._child.sendline('p')

    def cmd_writetable(self):
        """
            Apply the planned changes to the partition table
        """
        logging.info("gdisk: write table to disk")
        self._child.expect(r"Command \(\? for help\): ")
        self._child.sendline('w')
        self._child.expect(r"^.*\(Y/N\): ")
        self._child.sendline('Y')


class Losetup(object):
    """
        Context manager to create a loopback device
    """

    def __init__(self, image):
        self._image = image
        self._reserve_first_available()

    def _reserve_first_available(self):
        args = list()
        args.append('losetup')
        args.append('--find')
        self._loopback_dev = subprocess.check_output(args) \
                                       .decode(sys.stdout.encoding) \
                                       .replace(os.linesep, '')

    def __enter__(self):
        args = list()
        args.append('losetup')
        args.append(self._loopback_dev)
        args.append(self._image)
        subprocess.check_output(args)
        logging.info("losetup: mount %s on %s", self._image, self._loopback_dev)
        # check if partitions are available
        partitions = glob.glob(self._loopback_dev + 'p*')
        for partition in partitions:
            logging.info("\t- %s", partition)
        return (self._loopback_dev, partitions)

    def __exit__(self, *exc):
        args = list()
        args.append('losetup')
        args.append('--detach')
        args.append(self._loopback_dev)
        subprocess.check_output(args)

class Mount(object):
    """
        Mount a device on a given mount point.
        If the mount point is let to None, a temporary directory is created in /tmp
    """

    def __init__(self, device, directory=None):
        self._device = device
        self._mount_point = directory
        self._is_tempdir = False
        if directory is None:
            self._mount_point = tempfile.mkdtemp(prefix='mountpoint')
            self._is_temp_dir = True

    def __enter__(self):
        args = list()
        args.append('mount')
        args.append(self._device)
        args.append(self._mount_point)
        subprocess.check_output(args)
        return self._mount_point

    def __exit__(self, *exc):
        args = list()
        args.append('umount')
        args.append(self._mount_point)
        subprocess.check_output(args)
        if self._is_temp_dir:
            os.rmdir(self._mount_point)

def parse_args():
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

    parser = argparse.ArgumentParser(description='Create a disk file with '\
                                     'the files or directories passed in arguments.')
    parser.add_argument('-o', '--output', metavar='OUTFILE',
                        required=True,
                        help='disk file containing the UEFI partition')
    parser.add_argument('--clean-cache',
                        action='store_true',
                        help='clean the cache')
    parser.add_argument('--force-dd',
                        action='store_true',
                        help='force creation of an empty (zeroed) disk')
    parser.add_argument('--force-format',
                        action='store_true',
                        help='force formatting of the EFI partition')
    parser.add_argument('--force-copy',
                        action='store_true',
                        help='force replacing all files and updating cache')
    parser.add_argument('--tool', nargs=1, metavar='[loopback-device | mtools]',
                        default='loopback-device',
                        help="need root's rights to use loopback-device")
    parser.add_argument('files', nargs='+',
                        type=check_path,
                        metavar='FILE')
    args = parser.parse_args()

    if not os.path.exists(args.output):
        args.clean_cache = True
        args.force_dd = True

    return args

def proceed_as_root(args):
    """
        Create a disk image with root's capabilities using losetup and mount
    """
    diskname = args.output
    with Losetup(diskname) as (device, partitions):
        partition = partitions[0]
        mkfsFAT32(partition)

        with Mount(partition) as mount_point:
            for name in args.files:
                logging.info("copy %s to %s", name, partition)
                if os.path.isdir(name):
                    shutil.copytree(name, mount_point)
                else:
                    shutil.copy(name, mount_point)

def proceed_as_standard_user(args):
    """
        Create a disk image with a standard user's capabilities
    """
    diskname = args.output
    disksize = os.path.getsize(diskname)
    tmp_partition = tempfile.mktemp(dir='/tmp', prefix='partfat32-')
    dd(tmp_partition, disksize - 2048)
    with Mtools(tmp_partition) as mtools:
        mtools.format()
        for name in args.files:
            mtools.copy(name)
    dd(outputf=diskname, size=disksize - 2048, inputf=tmp_partition, seek=2048)
    os.remove(tmp_partition)

def run(args):
    """
        main function
    """
    disk_size = 46 * 1024 * 1024 # MB

    print(args)
    if args.force_dd:
        dd(args.output, disk_size)

        with Gdisk(args.output) as partitioner:
            partitioner.cmd_newtable()
            partitioner.cmd_newpartition('EFI')
            partitioner.cmd_printtable()
            partitioner.cmd_writetable()

    if args.tool == 'loopback-device':
        if is_user_root():
            proceed_as_root(args)
        else:
            raise EnvironmentError("need to be root to use loopback devices")
    else:
        proceed_as_standard_user(args)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    run(parse_args())
