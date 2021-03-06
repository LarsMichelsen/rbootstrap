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
import gzip
import subprocess
import urllib2
from StringIO import StringIO

from . import config
from .exceptions import *

def quote_shell_string(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"

def fetch(path):
    """ Either reads a requested file from the local system or a URL via http or ftp.
        When the file path endswith .gz, the file is assumed to be gzipped and automatically
        uncompressed. """

    if path.startswith('http') or path.startswith('ftp'):
        try:
            response = urllib2.urlopen(path)
        except urllib2.HTTPError, e:
            # Want to have the URL in the exception str
            e.msg += ' (%s)' % e.filename
            raise
    else:
        response = file(path)

    if path.endswith('.gz'):
        # Would be better to be able to stream this, but it is not possible with python 2
        fh = StringIO(response.read())
        return gzip.GzipFile(fileobj = fh)

    return response

def read_file(path):
    """Reads the content of a file from the jail"""
    return file(os.path.join(config.root, path[1:])).read()

def rm_file(path):
    """Remove a file from the jail"""
    os.unlink(os.path.join(config.root, path[1:]))

def read_link(path):
    """Returns the target of a symlink located in the jail"""
    return os.readlink(os.path.join(config.root, path[1:]))

def list_dir(path):
    """Lists the contents of a directory located in the jail"""
    return os.listdir(os.path.join(config.root, path[1:]))

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

def call_jailed(handler, *args):
    """ Execute a python function "jailed". Means chroot into the jail path
    and unchroot afterwards """
    cwd = os.getcwd()
    root = os.open('/', os.O_RDONLY)
    os.chroot(config.root)
    os.chdir('/')

    handler(*args)

    os.fchdir(root)
    os.chroot('.')
    os.chdir(cwd)

def execute_jailed(cmd):
    """ Executes a command within the context of the jail """
    if subprocess.call('setarch %s chroot %s bash -l -c %s' % (config.arch, config.root, quote_shell_string(cmd)), shell=True) != 0:
        raise RBError('JAIL: Failed to execute: %s' % cmd)

def _chown_jailed(path, user, group):
    """ Changes the owner / group of a file by accepting user and group
    either as string (name) or integer (id of the user/group). Resolves
    the names in the context of the jail """
    if type(user) != int:
        user = pwd.getpwnam(user).pw_uid
    if type(group) != int:
        group = grp.getgrnam(group).gr_gid
    os.chown(path, user, group)

def chown(path, user, group, jailed = True):
    """ Changes ownership of a path within the context of the jail """
    if jailed:
        call_jailed(_chown_jailed, path, user, group)
    else:
        os.chown(os.path.join(config.root, path[1:]),
            pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)

def chmod(path, mode):
    """ Changes permissions of a path within the context of the jail """
    os.chmod(os.path.join(config.root, path[1:]), mode)

def url(path):
    return path % {
        'arch'          : config.arch,
        'codename'      : config.codename,
        'distro'        : config.distro_name(),
        'version'       : config.distro_version(),
        'version_major' : config.distro_version().split('.', 1)[0],
    }
