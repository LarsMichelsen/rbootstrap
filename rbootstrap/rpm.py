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
This module contains code for unpacking RPM packages by hand
into a given path. It extracts the CPIO part of the RPM file
and extracts the data from it.
"""

import os
import bz2
import stat
import zlib
import struct
import shutil
import subprocess

try:
    import lzma as xz
    has_lzma = True
except ImportError:
    try:
        import pylzma as xz
        has_lzma = True
    except ImportError:
        has_lzma = False

from .exceptions import *

def cpio_align(pos):
    return pos + ((4 - (pos % 4)) % 4)

def extract_cpio(data, target_path):
    # http://people.freebsd.org/~kientzle/libarchive/man/cpio.5.txt
    off  = 0
    while True:
        head = data[off:off+110]

        # Extract info from headers
        mode     = int(head[14:22], 16)
        uid      = int(head[22:30], 16)
        gid      = int(head[30:38], 16)
        size     = int(head[54:62], 16)
        name_len = int(head[94:102], 16)

        file_path  = data[off+110:off+110+name_len-1]
        body_start = cpio_align(off+110+name_len)
        body       = data[body_start:body_start+size]
        off        = cpio_align(body_start+size)

        if file_path == 'TRAILER!!!':
            break # Reached end of archive

        target = os.path.join(target_path, file_path.lstrip('/.'))

        # Create directory tree
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))

        # Now write the thing
        if stat.S_ISDIR(mode):
            if not os.path.exists(target):
                os.mkdir(target, mode & 0o777)
        elif stat.S_ISLNK(mode):
            if os.path.exists(target):
                os.unlink(target)
            os.symlink(body, target)
        else:
            # FIXME: Verify checksum
            file(target, 'wb').write(body)
            os.chmod(target, mode)

        os.lchown(target, uid, gid)

def unpack_gz(data):
    return zlib.decompress(data)

def unpack_bz(data):
    return bz2.decompress(data)

def unpack_xz(data):
    if has_lzma:
        return xz.decompress(data)
    else:
        # Now that the local python has no support for lzma,
        # fallback to command line tool
        # FIXME: Add better error message in case xz is not available
        cmd = ['xz', '--decompress', '-f']
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
        return proc.communicate(input=data)[0]

def unpack(rpm_file, target_path):
    """Unpacks the contents of an RPM file to the given target path.

    Information about extracting the CPIO data from the RPM has been
    found in http://afb.users.sourceforge.net/centos/rpm2cpio.py.
    """
    f = file(rpm_file, 'rb')

    head = f.read(96)
    magic, major, minor = struct.unpack("!LBB", head[0:6])
    if magic != 0xedabeedb:
        raise RBError('The file "%s" is no RPM file' % rpm_file)
    if major not in [ 3, 4 ]:
        raise RBError('The RPM file is of an invalid version (%d)' % major)

    head = f.read(16)
    while True:
        magic, ignore, sections, size_b = struct.unpack("!LLLL", head)
        smagic, smagic2 = struct.unpack("!HL", head[0:6])

        if smagic == 0x1f8b:
            uncompress_func = unpack_gz
            break
        elif smagic == 0x425a and (smagic2 & 0xff000000) == 0x68000000:
            uncompress_func = unpack_bz
            break
        elif (smagic == 0xfd37 and smagic2 == 0x7a585a00) or magic != 0x8eade801:
            uncompress_func = unpack_xz
            break

        # Advance to next part
        f.read(16 * sections + size_b)
        while True:
            head = f.read(1)
            if head == '':
                raise RBError('No header found')
            elif (0,) == struct.unpack("B", head):
                continue
            break
        head += f.read(15)

    data = head + f.read()

    if not uncompress_func:
        raise RBError('Unable to detect RPM compression')

    cpio_data = uncompress_func(data)
    extract_cpio(cpio_data, target_path)
