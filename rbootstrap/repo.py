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
import urllib2
import re
import gzip
import shutil
from StringIO import StringIO

try:
    from xml.etree import cElementTree as elem_tree
except ImportError:
    import cElementTree as elem_tree

from . import config
from .exceptions import *

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

def ns(name, key):
    return '{http://linux.duke.edu/metadata/%s}%s' % (name, key)

class Repository(object):
    def __init__(self, mirror_path, gpgkey_path, allowed_arch):
        self._mirror_path  = mirror_path
        self._gpgkey_path  = gpgkey_path
        self._allowed_arch = allowed_arch

        self._get_data_path()
        self._get_primary_path()
        self._fetch_primary()

    def _get_data_path(self):
        repo_content_path = os.path.join(self._mirror_path, 'content')
        for l in fetch(repo_content_path):
            if l.startswith('DATADIR'):
                self._data_path = os.path.join(self._mirror_path, l.rstrip().split()[1])
                return

        raise IOError('Unable to find DATADIR in primary info in "%s"' % repo_content_path)


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
        needed_pkgs      = set([])

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

        def add_with_required(pkg):
            pkg_name = pkg.find(ns('common', 'name')).text
            pkg_loc  = pkg.find(ns('common', 'location')).get('href')
            if (pkg_name, pkg_loc) not in needed_pkgs:
                needed_pkgs.add((pkg_name, pkg_loc))
                already_provided.extend(self._package_provides(pkg))

            fmt = pkg.find(ns('common', 'format'))
            require_elements = fmt.find(ns('rpm', 'requires'))
            if require_elements:
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
                                add_with_required(provider_elem)
                                break
                        else:
                            raise RBError('Got multiple providers for "%s": %s' % (required, ', '.join(
                                [ '%s(%s)' % (p[0], p[1].find(ns('common', 'arch')).text) for p in add_pkgs])))
                    else:
                        provider_name, provider_elem = add_pkgs[0]
                        add_with_required(provider_elem)

        # Now loop all needed packages and resolve their requirements
        for pkg in needed_pkg_elems:
            add_with_required(pkg)

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
        with open(os.path.join(tmp_path, 'gpg.key'), 'wb') as fp:
            shutil.copyfileobj(fetch(self._gpgkey_path), fp)

    def download_packages(self, packages):
        tmp_path = self._tmp_path()
        for pkg_name, pkg_loc in packages:
            pkg_filename = os.path.basename(pkg_loc)
            pkg_path = os.path.join(self._data_path, pkg_loc)

            with open(os.path.join(tmp_path, pkg_filename), 'wb') as fp:
                shutil.copyfileobj(fetch(pkg_path), fp)
