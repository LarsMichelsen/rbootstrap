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
import sys

from .exceptions import *

# Hardcoded default configuration which can be overwritten by configuration
# files and/or command line options
codename    = None
arch        = 'amd64'
root        = None
tmp_dir     = 'rb.tmp'
distro_path = '/usr/share/rbootstrap/distros'

def load(path = '/etc/rbootstrap.conf'):
    """ Load the specified configuration file """
    # FIXME: Use other config format
    try:
        execfile(path, globals(), globals())
    except:
        raise RBError('Unable to read config file "%s": %s\n' % (path, e))

    # Now resolve paths to really be absolute
    for key in [ 'root', 'distro_path' ]:
        globals()[key] = os.path.abspath(globals()[key])

def distros():
    return os.listdir(distro_path)

def package_architectures():
    if arch == 'amd64':
        return ['x86_64', 'noarch']
    else:
        return ['i586', 'i686', 'noarch']
