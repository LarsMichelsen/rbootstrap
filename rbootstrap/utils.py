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

"""
Contains useful helper functions to be used withn the Jail class and the
hook functions of the distro specifications.
"""

import os
import pwd
import grp

from . import config

def read_file(path):
    return file(os.path.join(config.root, path[1:])).read()

def write_file(path, data, force = False):
    """ Write a file to the chroot (when file does not exist yet) """
    dest_path = os.path.join(config.root, path[1:])
    if force or not os.path.exists(dest_path):
        file(dest_path, 'w').write(data)

def copy_file(path):
    """ Copies a file from the outer system to the chroot (when file does not exist yet) """
    dest_path = os.path.join(config.root, path[1:])
    if not os.path.exists(dest_path):
        file(dest_path, 'w').write(file(path).read())

def execute_jailed(cmd):
    """ Executes a command within the context of the jail """
    os.system('chroot %s %s' % (config.root, cmd))

def chown(path, user, group):
    """ Changes ownership of a path within the context of the jail """
    os.chown(os.path.join(config.root, path),
        pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)

def chmod(path, mode):
    """ Changes permissions of a path within the context of the jail """
    os.chmod(os.path.join(config.root, path), mode)
