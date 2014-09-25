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
arch        = 'x86_64'
root        = None
tmp_dir     = 'rb.tmp' # must be within root
# FIXME:
#distro_path = '/usr/share/rbootstrap/distros'
distro_path = 'distros'
pre_erase   = False
force_erase = False
keep_pkgs   = False
include     = []
exclude     = []
verbose     = False
only_print_pkgs = False

def load():
    """ Load the specified configuration file """

    # Now use the command line options to override values from the config
    for key, val in opts.items():
        globals()[key] = val

    # Now resolve paths to really be absolute
    for key in [ 'root', 'distro_path' ]:
        globals()[key] = os.path.abspath(globals()[key])

def set_opts(options):
    global opts
    opts = options

def distros():
    return [ f for f in os.listdir(distro_path)
             if f[0] != '.' ]

def package_architectures():
    if arch == 'x86_64':
        return ['x86_64', 'noarch']
    else:
        return ['i586', 'i686', 'noarch']
