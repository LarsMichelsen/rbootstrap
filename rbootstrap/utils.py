"""
Contains useful helper functions to be used withn the Jail class and the
hook functions of the distro specifications.
"""

import os
import pwd
import grp

from . import config

def read_file(path):
    return file(os.path.join(config.root, path[1:])).read()

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

def execute_jailed(cmd):
    """ Executes a command within the context of the jail """
    os.system('chroot %s %s' % (config.root, cmd))

def chown(path, user, group):
    """ Changes ownership of a path within the context of the jail """
    os.chown(os.path.join(config.root, path),
        pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)

def chmod(path, mode):
    """ Changes permissions of a path within the context of the jail """
    os.chmod(os.path.join(config.root, path), mode)
