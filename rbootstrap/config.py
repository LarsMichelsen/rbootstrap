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
