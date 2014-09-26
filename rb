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
import sys
import glob
import getopt
import atexit
import traceback

from rbootstrap import repo, jail, config, distro
from rbootstrap.exceptions import *
from rbootstrap.log import *

def version():
    return (
        'rbootstrap version %s, Copyright (C) 2014 Lars Michelsen <lm@larsmichelsen.com>\n\n'
        'rbootstrap comes with ABSOLUTELY NO WARRANTY; for details take a look at the\n'
        'LICENSE file. This is free software, and you are welcome to redistribute it\n'
        'under certain conditions; for details take a look at the LICENSE file.\n' % VERSION
    )

def help(msg = None):
    if msg:
        sys.stderr.write('ERROR: %s\n' % msg)

    sys.stdout.write(
        'Usage: rbootstrap [OPTION...] <CODENAME> <TARGET>\n'
        '\n'
        'rbootstrap is a tool for setting up RPM based Linux distributions in chroot\n'
        'jails. The goal of the project is to have a tool like debootstrap for Debian\n'
        'and Ubuntu for RPM based distributions like CentOS, RedHat, OpenSuSE, SLES\n'
        'and so on.\n'
        '\n'
        'ARGUMENTS:\n'
        '    CODENAME         The codename specifies the Linux distribution and version\n'
        '                     to install. This must be a supported one. Use the command\n'
        '                     "rbootstrap --list-codenames" to get the list of distros.\n'
        '    TARGET           Specifies the path to the target directory to create the\n'
        '                     chroot jail in. This path might already be existant.\n'
        '\n'
        'OPTIONS:\n'
        '  --arch=ARCH        Set the architecture to install (default: x86_64)\n'
        '                     The possible options depend on the architecures supported\n'
        '                     by the distribution to be installed into the jail. Most\n'
        '                     support "x86_64" and "i386".\n'
        '  --include=A,B,C    The packages specified here will be installed using the\n'
        '                     package manager after the initial installation has been\n'
        '                     finished.\n'
        '  --exclude=A,B,C    Remove these package names from the list of packages to\n'
        '                     be installed\n'
        '\n'
        '  --no-check-pkg-sig Do not verify that packages are signed with the GPG key\n'
        '                     retrieved from the repository. By default all packages\n'
        '                     are checked when installing them to the JAIL.\n'
        '  --pre-erase        Completely clear all data in TARGET before setting it up.\n'
        '                     When the jail is still used by mounted filesystems or\n'
        '                     running processes rbootstrap will terminate with an\n'
        '                     error message.\n'
        '                     If you like to perform a forced erasement, use the flag\n'
        '                     "--force-erase" together with this option.\n'
        '                     BE CAREFUL: When you point TARGET to another directory\n'
        '                     than the jail, the data below this directory will be\n'
        '                     removed anyways.\n'
        '  --force-erase      Use this to make "--pre-erase" make the jail unused.\n'
        '                     This means:\n'
        '                     a) Killing all processes accessing files of the jail\n'
        '                     b) Unmounting all filesystems mounted in the jail\n'
        '  --keep-pkgs        Use this to make "--pre-erase" keep the downloaded\n'
        '                     packages. This is useful when you do not want to\n'
        '                     download already loaded packages again.\n'
        '  --force-load-pkgs  By default the locally existing packages are used\n'
        '                     when their checksums match the repositories metadata.\n'
        '                     This prevents duplicate downloading and might save time.\n'
        '                     You can use this flag to ignore all existing packages\n'
        '                     to download them again.\n'
        '\n'
        '  --verbose          Print out details about actions to stdout\n'
        '\n'
        '  --list-codenames   Prints out a list of supported Linux distributions\n'
        '  --print-pkgs       Print the packages to be installed, then exit\n'
        '\n'
        '  -V, --version      Print out version information\n'
        '  -h, --help         Print this help screen\n'
        '\n'
    )
    sys.exit(0)

def list_codenames():
    log('Supported Linux Distributions:\n%s\n' %
       '\n'.join([ '    %s' % d for d in config.distros() ]))
    sys.exit(0)

def parse_opts():
    short_options = ['hV']
    long_options  = ['help', 'version', 'arch=', 'include=', 'exclude=', 'verbose',
                     'list-codenames', 'pre-erase', 'force-erase', 'keep-pkgs',
                     'force-load-pkgs', 'no-check-pkg-sig',
                     'print-pkgs', ]
    try:
        opts, args = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.GetoptError, e:
        raise RBError(str(e))

    options = {}

    for k, v in opts:
        if k == '--arch':
            options['arch'] = v
        elif k == '--include':
            options['include'] = v.split(',')
        elif k == '--exclude':
            options['exclude'] = v.split(',')
        elif k == '--verbose':
            options['verbose'] = True
        elif k == '--no-check-pkg-sig':
            options['check_pkg_sig'] = True
        elif k == '--pre-erase':
            options['pre_erase'] = True
        elif k == '--force-erase':
            options['force_erase'] = True
        elif k == '--keep-pkgs':
            options['keep_pkgs'] = True
        elif k == '--force-load-pkgs':
            options['force_load_pkgs'] = True
        elif k == '--print-pkgs':
            options['only_print_pkgs'] = True

        elif k == '--list-codenames':
            list_codenames()

        elif k in ['-V', '--version']:
            sys.stdout.write(version())
            sys.exit(0)

        elif k in ['-h', '--help']:
            sys.stdout.write(help())

    num_args = len(args)
    if num_args == 0:
        help('Missing CODENAME and TARGET arguments')
    elif num_args == 1:
        help('Missing target argument')
    elif num_args > 2:
        help('Too many arguments provided')

    options['codename'] = args[0]
    options['root']     = args[1]

    return options

def main():
    config.set_opts(parse_opts())
    config.load()

    distro.load(config.codename)

    if os.geteuid() != 0:
        raise BailOut('rbootstrap needs to be run as root')

    if config.arch not in distro.supported_architectures():
        raise BailOut('The requested architecture %s is not supported by %s' %
                                                    (config.arch, config.codename))

    #
    # PHASE 1: Initialize the jail with some basic things like directories etc.
    #

    if not config.only_print_pkgs:
        JAIL = jail.Jail(config.root)

        # Register final cleanup of the jail to be left as plain directory in all cases.
        atexit.register(JAIL.cleanup)

        if config.pre_erase:
            JAIL.erase()
        JAIL.init()

    #
    # PHASE 2: Now access the package repository and use it to resolve all needed packages
    #

    REPO = repo.Repository(distro.mirror_path(), distro.data_path(),
                           distro.gpgkey_path(), config.package_architectures())
    install_packages = REPO.resolve_needed_packages(distro.needed_packages())

    if config.only_print_pkgs:
        step('To be installed')
        log(''.join([ '    %s\n' % p[0] for p in install_packages ]))
        sys.exit(0)

    #
    # PHASE 3: Populate the jail with some basic files to make execution of the
    #          package manager in a chrooted environment posible.
    #

    REPO.download_gpgkey()
    REPO.download_packages(install_packages)
    JAIL.unpack(install_packages)

    #
    # PHASE 4: Perform regular installation of all components (replacing stuff of PHASE 2).
    #

    JAIL.install(install_packages)

try:
    main()
except BailOut, e:
    sys.stderr.write('%s. Terminating!\n' % e)
    sys.exit(1)
except RBError, e:
    sys.stderr.write('ERROR: %s\n' % e)
    sys.exit(1)
except Exception, e:
    sys.stderr.write('Unhandled exception: %s\n' % traceback.format_exc())
    sys.exit(1)
