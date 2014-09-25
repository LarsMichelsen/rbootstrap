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
import re
import stat

from . import config
from .utils import *
from .exceptions import *

gpgkey = None

def load(codename):
    try:
        execfile(os.path.join(config.distro_path, codename), globals(), globals())
    except Exception, e:
        raise BailOut('Exception in distribution specefication file: %s' % e)

    # Verify that the distro registers all needed things
    for key in [ 'architectures', 'packages', 'mirror', 'install_packages' ]:
        if key not in globals():
            raise BailOut('The distro "%s" does not specify the required key %s' %
                                                                    (codename, key))

def supported_architectures():
    return architectures

def needed_packages():
    return packages

def data_path():
    if 'get_data_path' in globals():
        return get_data_path()
    return mirror_path()

def mirror_path():
    return url(mirror)

def gpgkey_path():
    if gpgkey:
        return url(gpgkey)

def device_nodes():
    """ Returns a list of sextuples, where the fields are defined as follows:
    0: name of the device (=> /dev/<name>)
    1: The file mode to set
    2: the major of the device node
    3: the minor of the device node
    4: owner (either string (user name) or integer (uid))
    5: group (either string (group name) or integer (gid)) """
    return devices

def execute_hooks(what):
    if 'hook_' + what in globals():
        globals()['hook_' + what]()
