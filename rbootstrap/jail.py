#!/usr/bin/env python
# encoding: utf-8
#
# rbootstrap - Install RPM based Linux into chroot jails
# Copyright (C) 2014 Lars Michelsen <lm@larsmichelsen.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import stat
import shutil

from . import distro, config
from .utils import *
from .exceptions import *

class Jail(object):
    def __init__(self, path):
        self._path = path

        if self._path == '/':
            raise RBError('Won\'t continue. "/" as chroot target seems strange.')

    def init(self):
        """ Perform some initializations of the jail, for example creating
        device nodes below /dev or mount the /proc filesystem. """
        for d in [ 'dev', 'etc', 'proc' ]:
            path = os.path.join(self._path, d)
            if not os.path.exists(path):
                os.makedirs(path)

        chown('/', 'root', 'root', jailed=False)

        distro.execute_hooks('pre_init')
        copy_file('/etc/resolv.conf')
        copy_file('/etc/hostname')
        self.setup_devices()
        self.setup_proc()
        distro.execute_hooks('post_init')

    def setup_devices(self):
        # Prevent problems when creating files with os.mknod(), which uses
        # mknod(2) of the system which takes care about the umask of this process.
        old_umask = os.umask(0)
        for path, perm, major, minor, user, group in [
            ('console',  0600|stat.S_IFCHR, 5,  1, 'root', 'tty'),
            ('full',     0666|stat.S_IFCHR, 1,  7, 'root', 'root'),
            ('kmem',     0640|stat.S_IFCHR, 1,  2, 'root', 'kmem'),
            ('loop0',    0660|stat.S_IFBLK, 7,  0, 'root', 'disk'),
            ('loop1',    0660|stat.S_IFBLK, 7,  1, 'root', 'disk'),
            ('loop2',    0660|stat.S_IFBLK, 7,  2, 'root', 'disk'),
            ('loop3',    0660|stat.S_IFBLK, 7,  3, 'root', 'disk'),
            ('loop4',    0660|stat.S_IFBLK, 7,  4, 'root', 'disk'),
            ('loop5',    0660|stat.S_IFBLK, 7,  5, 'root', 'disk'),
            ('loop6',    0660|stat.S_IFBLK, 7,  6, 'root', 'disk'),
            ('loop7',    0660|stat.S_IFBLK, 7,  7, 'root', 'disk'),
            ('mem',      0640|stat.S_IFCHR, 1,  1, 'root', 'kmem'),
            ('null',     0666|stat.S_IFCHR, 1,  3, 'root', 'root'),
            ('port',     0640|stat.S_IFCHR, 1,  4, 'root', 'kmem'),
            ('ptmx',     0666|stat.S_IFCHR, 5,  2, 'root', 'tty'),
            ('ram0',     0660|stat.S_IFBLK, 1,  0, 'root', 'disk'),
            ('ram1',     0660|stat.S_IFBLK, 1,  1, 'root', 'disk'),
            ('ram2',     0660|stat.S_IFBLK, 1,  2, 'root', 'disk'),
            ('ram3',     0660|stat.S_IFBLK, 1,  3, 'root', 'disk'),
            ('ram4',     0660|stat.S_IFBLK, 1,  4, 'root', 'disk'),
            ('ram5',     0660|stat.S_IFBLK, 1,  5, 'root', 'disk'),
            ('ram6',     0660|stat.S_IFBLK, 1,  6, 'root', 'disk'),
            ('ram7',     0660|stat.S_IFBLK, 1,  7, 'root', 'disk'),
            ('ram8',     0660|stat.S_IFBLK, 1,  8, 'root', 'disk'),
            ('ram9',     0660|stat.S_IFBLK, 1,  9, 'root', 'disk'),
            ('ram10',    0660|stat.S_IFBLK, 1, 10, 'root', 'disk'),
            ('ram11',    0660|stat.S_IFBLK, 1, 11, 'root', 'disk'),
            ('ram12',    0660|stat.S_IFBLK, 1, 12, 'root', 'disk'),
            ('ram13',    0660|stat.S_IFBLK, 1, 13, 'root', 'disk'),
            ('ram14',    0660|stat.S_IFBLK, 1, 14, 'root', 'disk'),
            ('ram15',    0660|stat.S_IFBLK, 1, 15, 'root', 'disk'),
            ('ram16',    0660|stat.S_IFBLK, 1, 16, 'root', 'disk'),
            ('random',   0666|stat.S_IFCHR, 1,  8, 'root', 'root'),
            ('tty',      0666|stat.S_IFCHR, 5,  0, 'root', 'tty'),
            ('tty0',     0600|stat.S_IFCHR, 4,  0, 'root', 'tty'),
            ('urandom',  0666|stat.S_IFCHR, 1,  9, 'root', 'root'),
            ('zero',     0666|stat.S_IFCHR, 1,  5, 'root', 'root'),
           ]:
            dest_path = os.path.join(self._path, 'dev', path)
            if not os.path.exists(dest_path):
                os.mknod(dest_path, perm, os.makedev(major, minor))
                chown(os.path.join('/dev', path), user, group)
        os.umask(old_umask)

    def setup_proc(self):
        os.system('mount -t proc proc %s/proc' % self._path)
        # FIXME: Maybe mount /sys

    def get_mounts(self):
        """ Returns a list of mountpoints mounted in the jail """
        mounts = []
        for l in file('/proc/mounts'):
            if l.split()[1].startswith(self._path):
                mounts.append(l.split()[1])
        return mounts

    def unmount(self):
        """ Tries to unmount all mounted filesystems within the jail. Sort the filesystem by
        length of the mount point string to first unmount the deeper ones """
        for mp in sorted([p.split('/') for p in self.get_mounts()], key = len, reverse = True):
            os.system('umount -f %s' % '/'.join(mp))

    def get_processes(self):
        """ Returns a list of process ids which are currently using files within this jail. """
        # FIXME
        return []

    def kill_processes(self, enforce = False):
        """ Tries to terminate all processes using files within this jail. """
        # FIXME
        pass

    def erase(self):
        if not os.path.exists(self._path):
            return

        if config.force_erase:
            self.cleanup() # Only cleanup resources when configured

        if self.get_mounts():
            raise RBError('Can not be erased. There are still file systems mounted within the jail.')

        if self.get_processes():
            raise RBError('Can not be erased. There are running processes using this jail.')

        for thing in os.listdir(self._path):
            path = os.path.join(self._path, thing)
            if os.path.isfile(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)

    def unpack_package(self, pkg_path):
        """ Simply unpack the given package to the jail path. This does not try to create
        adapt the installation mechanism, for example the pre/post scripts are missing. This
        is just needed to create a minimalistics system to be able to perform the chroot into
        and use the installer afterwards. """
        # FIXME: Use python libs?
        os.system('rpm2cpio %s | (cd %s ; cpio -dim --quiet)' % (pkg_path, self._path))

    def unpack(self, packages):
        for pkg_name, pkg_loc in packages:
            pkg_path = os.path.join(self._path, config.tmp_dir, pkg_loc.split('/')[-1])
            self.unpack_package(pkg_path)
        distro.execute_hooks('post_unpack')

    def install(self, packages):
        distro.execute_hooks('pre_install')

        if distro.gpgkey_path():
            execute_jailed('rpm --import %s' % os.path.join(config.tmp_dir, 'gpg.key'))

        # Now install the packages again to fix file permissions and make all pre/post
        # being executed
        packages = [
            os.path.join(config.tmp_dir, pkg_loc.split('/')[-1])
            for pkg_name, pkg_loc in packages
        ]
        execute_jailed('rpm -ivh %s' % ' '.join(packages))

        if config.include:
            distro.install_packages(config.include)

        distro.execute_hooks('post_install')

    def cleanup(self):
        """ Is executed to make the jail completely unused by the running system (remove
        all mounted filesystems and all processes using this jail. Then verify it and return
        either True or False depending on success """
        self.unmount()
        self.kill_processes()

        # Now check whether or not this was successful
        # FIXME: wait some time, test again, then force killing, wait some time again,
        # test again and then succeed or fail
        return True
