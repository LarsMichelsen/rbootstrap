
import os
import re

from . import config
from .utils import *

def load(codename):
    execfile(os.path.join(config.distro_path, codename), globals(), globals())

def supported_architectures():
    return architectures

def needed_packages():
    return packages

def mirror_path():
    return mirror

def execute_hooks(what):
    if 'hook_' + what in globals():
        globals()['hook_' + what]()
