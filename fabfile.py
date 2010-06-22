#!/usr/bin/env python
"""
Fabric build/deploy script for logtools
"""

import os
import sys
import tarfile
import logging
import datetime

from fabric.api import run, env, cd
from fabric.operations import put, sudo, prompt, local
from fabric.decorators import hosts

log = logging.getLogger(__name__)

def dist():
    """Create distributable"""
    local('python setup.py bdist_egg')

def deploy(deploydir, virtualenv=None):
    """Deploy distributable on target machine.
    Specify 'virtualenv' as path to the virtualenv (if any),
    Specify 'deploydir' as directory to push egg file to."""
    _mkenv(); _find_dist();
    put("dist/%s" % env.dist_fname, deploydir)
    source_me = ''
    if virtualenv:
        source_me = 'source {0}/bin/activate && '.format(virtualenv)
    run(source_me + 'easy_install -U {0}/{1}'.format(deploydir, env.dist_fname))

def _mkenv():
    """Create our environment"""
    env.proj_name = 'logtools'

def _find_dist():
    """Find latest version of our distributable and point to it in env"""
    _dist_fname = local("ls -tr dist/%s*.egg | tail -n1" % env.proj_name.replace("-", "_"))
    if _dist_fname.failed == True:
        return -1
    _dist_fname = os.path.basename(_dist_fname.strip())
    env.dist_fname = _dist_fname
