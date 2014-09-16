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

VERSION = '0.1'

import os
import glob
import traceback

from rbootstrap import repo, jail, config, distro
from rbootstrap.exceptions import *

def version():
    sys.stdout.write(
        'rbootstrap version %s, Copyright (C) 2014 Lars Michelsen <lm@larsmichelsen.com>'
        'rbootstrap with ABSOLUTELY NO WARRANTY; for details take a look at the LICENSE file.'
        'This is free software, and you are welcome to redistribute it'
        'under certain conditions; for details take a look at the LICENSE file.'
    )
    sys.exit(0)

def help():
    pass # FIXME

def main():
    if os.geteuid() != 0:
        raise BailOut('rbootstrap can only run as root')

    # FIXME: Add parameter
    config.load('rbootstrap.conf')
    distro.load(config.codename)

    if config.arch not in distro.supported_architectures():
        raise BailOut('The requested architecture %s is not supported by %s' %
                                                    (config.arch, config.codename))

    # FIXME: Check for root permissions

    REPO = repo.Repository(distro.mirror_path(), config.package_architectures())

    #
    # PHASE 1: Initialize the jail with some basic things like directories etc.
    #

    JAIL = jail.Jail(config.root)
    JAIL.erase()
    JAIL.init()

    install_packages = REPO.resolve_needed_packages(distro.needed_packages())

    #
    # PHASE 2: Populate the jail with some basic files to make execution of the
    #          package manager in a chrooted environment posible.
    #

    REPO.download_packages(install_packages)
    JAIL.unpack(install_packages)

    #
    # PHASE 3: Perform regular installation of all components (replacing stuff of PHASE 2).
    #

    JAIL.install(install_packages)

    #
    # PHASE 4: Cleanup jail to be left as plain directory.
    #

    JAIL.cleanup()
    #FIXME: On exception verify to unmount everything

try:
    main()
except BailOut, e:
    sys.stderr.write('%s. Terminating!\n' % e)
    sys.exit(1)
except Exception, e:
    sys.stderr.write('Unhandled exception: %s\n' % traceback.format_exc())
    sys.exit(1)
