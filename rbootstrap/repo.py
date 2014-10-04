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
import re
import shutil
import hashlib

try:
    from xml.etree import cElementTree as elem_tree
except ImportError:
    import cElementTree as elem_tree

from . import config
from .log import *
from .utils import fetch
from .exceptions import *

def ns(name, key):
    return '{http://linux.duke.edu/metadata/%s}%s' % (name, key)

class Repository(object):
    def __init__(self, mirror_path, data_path, gpgkey_path, allowed_arch):
        self._mirror_path  = mirror_path
        self._data_path    = data_path
        self._gpgkey_path  = gpgkey_path
        self._allowed_arch = allowed_arch

        step('Reading repository meta information')
        verbose('Repository: %s\nPackage Architectures: %s' %
                (self._mirror_path, ', '.join(self._allowed_arch)))

        self._get_primary_path()
        self._fetch_primary()

    def _get_primary_path(self):
        """ Parse the repomd.xml to get the path to the "primary" xml file """
        md_path = os.path.join(self._data_path, 'repodata', 'repomd.xml')
        for elem in elem_tree.parse(fetch(md_path)).getroot():
            if elem.get('type') == 'primary':
                location = elem.find(ns('repo', 'location'))
                self._primary_path = os.path.join(self._data_path, location.get('href'))
                return

        raise IOError('Unable to find primary info in "%s"' % md_path)

    def _fetch_primary(self):
        self._primary_root = elem_tree.parse(fetch(self._primary_path)).getroot()

    def _package_provides(self, pkg):
        """ Returns a list of all strings which each identifies a thing which is
        provided by the given rpm """
        provides = set([])
        fmt = pkg.find(ns('common', 'format'))

        # Explicit provide entries
        elements = fmt.find(ns('rpm', 'provides'))
        if elements:
            for entry in elements.findall(ns('rpm', 'entry')):
                provides.add(entry.get('name'))

        # Provided files
        for file_elem in fmt.findall(ns('common', 'file')):
            provides.add(file_elem.text)

        return list(provides)

    def resolve_needed_packages(self, needed):
        providers        = {}
        needed_pkg_elems = []
        already_provided = []
        needed_pkgs      = []

        step('Resolving package dependencies')
        verbose('Requested packages:\n%s' % ''.join([ '    %s\n' % p for p in needed ]))

        # Maybe the user configured to skipping packages which are requested
        # by the distribution specification
        if config.exclude:
            needed = needed[:] # do not modify the original list
            for pkg in config.exclude:
                try:
                    needed.remove(pkg)
                except ValueError:
                    pass

        # First get
        # a) the things each package provides for later dependency resolving
        # b) the package objects for the needed packages
        for pkg in self._primary_root:
            pkg_name = pkg.find(ns('common', 'name')).text

            # Skip packages by architecture
            arch = pkg.find(ns('common', 'arch')).text
            if arch not in self._allowed_arch:
                continue

            # Register all things the current package provides for all packages
            for thing in self._package_provides(pkg):
                providers.setdefault(thing, [])
                providers[thing].append((pkg_name, pkg))

            # Add the needed packages as starting points
            if pkg_name in needed:
                needed_pkg_elems.append(pkg)

        def add_with_required(pkg, lvl = 0):
            pkg_name = pkg.find(ns('common', 'name')).text
            pkg_loc  = pkg.find(ns('common', 'location')).get('href')
            pkg_csum = (pkg.find(ns('common', 'checksum')).text,
                        pkg.find(ns('common', 'checksum')).get('type'))

            if (pkg_name, pkg_loc, pkg_csum) not in needed_pkgs:
                needed_pkgs.append((pkg_name, pkg_loc, pkg_csum))
                already_provided.extend(self._package_provides(pkg))

            fmt = pkg.find(ns('common', 'format'))
            require_elements = fmt.find(ns('rpm', 'requires'))
            if require_elements:
                if lvl == 0:
                    verbose((' ' * lvl) + pkg_name)
                for entry in require_elements.findall(ns('rpm', 'entry')):
                    required = entry.get('name')

                    if required in already_provided:
                        continue # Do not search for already provided requirements

                    add_pkgs = providers.get(required)
                    if not add_pkgs:
                        raise RBError('Unable to resolve required dependency "%s"' % required)
                    elif len(add_pkgs) > 1:
                        # In case there are multiple, but one is in needed, use this one!
                        for provider_name, provider_elem in add_pkgs:
                            if provider_name in needed:
                                verbose((' ' * lvl) + '+ %s' % provider_name)
                                add_with_required(provider_elem, lvl+1)
                                break
                        else:
                            raise RBError('Got multiple providers for "%s": %s' % (required, ', '.join(
                                [ '%s(%s)' % (p[0], p[1].find(ns('common', 'arch')).text) for p in add_pkgs])))
                    else:
                        provider_name, provider_elem = add_pkgs[0]
                        verbose((' ' * lvl) + '+ %s' % provider_name)
                        add_with_required(provider_elem, lvl+1)

        # Now loop all needed packages and resolve their requirements
        verbose('Resolving...')
        for pkg in needed_pkg_elems:
            add_with_required(pkg)

        # Sort the needed_pkgs list (we want to have the packages listed in
        # the packages distros list unpacked first)
        def sorter(e):
            try:
                return needed.index(e[0])
            except ValueError:
                return 1
        needed_pkgs.sort(key=sorter)

        return needed_pkgs

    def _tmp_path(self):
        tmp_path = os.path.join(config.root, config.tmp_dir)
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        return tmp_path

    def download_gpgkey(self):
        if not self._gpgkey_path:
            return
        tmp_path = self._tmp_path()

        step('Loading repositories GPG key')
        verbose('Destination: %s' % tmp_path)

        with open(os.path.join(tmp_path, 'gpg.key'), 'wb') as fp:
            shutil.copyfileobj(fetch(self._gpgkey_path), fp)

    def _use_existing_package(self, target_path, csum, csum_type):
        """Checks whether or not a package needs to be downloaded

        Existing files are checked against the checksum mentioned in
        the repository meta data file.
        """

        if config.force_load_pkgs:
            return False # Checking of existing files disabled

        try:
            try:
                h = hashlib.__dict__[csum_type]()
            except KeyError:
                raise RBError('Hash algorithm "%s" not implemented' % csum_type)

            with open(target_path,'rb') as fp:
                for chunk in iter(lambda: fp.read(8192), b''):
                    h.update(chunk)
                return h.hexdigest() == csum
        except IOError:
            return False

    def download_packages(self, packages):
        tmp_path = self._tmp_path()

        step('Loading packages')
        verbose('Destination: %s' % tmp_path)
        for pkg_name, pkg_loc, pkg_csum in packages:
            pkg_filename = os.path.basename(pkg_loc)
            pkg_path     = os.path.join(self._data_path, pkg_loc)
            target_path  = os.path.join(tmp_path, pkg_filename)

            if self._use_existing_package(target_path, pkg_csum[0], pkg_csum[1]):
                verbose('Use existing %s' % pkg_filename)
                continue

            with open(target_path, 'wb') as fp:
                verbose('Loading %s' % pkg_filename)
                shutil.copyfileobj(fetch(pkg_path), fp)

    def cleanup(self):
        """Removes the temporary directory and all files within"""
        step('Cleaning up downloaded files')
        shutil.rmtree(os.path.join(config.root, config.tmp_dir))
        return True
