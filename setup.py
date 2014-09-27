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

from distutils.core import setup
import os
setup(name='rbootstrap',
      version='0.1',
      description='Install RPM based Linux into Chroot Jails',
      long_description='rbootstrap is a tool for setting up RPM based Linux distributions in chroot ' \
                       'jails. The goal of the project is to have a tool like debootstrap for Debian and ' \
                       'Ubuntu for RPM based distributions like CentOS, RedHat, OpenSuSE, SLES and so on.',
      author='Lars Michelsen',
      author_email='lm@larsmichelsen.com',
      url='https://github.com/LaMi-/rbootstrap',
      license='GPLv2',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: Software Development :: Embedded Systems',
          'Topic :: Software Development :: Testing',
          'Topic :: Software Development :: Build Tools',
          'Topic :: System :: Installation/Setup',
          'Topic :: System :: Software Distribution',
          'Topic :: Utilities',
      ],
      packages=['rbootstrap'],
      data_files=[
          ('/usr/sbin', ['scripts/rbootstrap']),
          ('/usr/share/rbootstrap/distros', [ 'distros/' + f for f in os.listdir('distros')]),
          ('/usr/share/doc/rbootstrap', ['LICENSE', 'README.md']),
          ('/usr/share/man/man8', ['rbootstrap.8.gz']),
      ],
)
