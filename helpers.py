#!/usr/bin/env python

"""
Creates shell commands to run involucro.

Usage:

./helpers.py build
./helpers.py all

"""

import os
import sys
import json
import time
import requests
import subprocess
from conda_build.metadata import MetaData

CHECK_LAST_HOURS = 25

def get_tests( pkg_path ):
    """
        extract test cases given a meta.yaml file
    """
    tests = ""
    input_dir = os.path.dirname( os.path.join( './bioconda-recipes', pkg_path ) )
    recipe_meta = MetaData(input_dir)

    tests_commands = recipe_meta.get_value('test/commands')
    tests_imports = recipe_meta.get_value('test/imports')
    requirements = recipe_meta.get_value('requirements/run')

    if tests_imports or tests_commands:
        if tests_commands:
            tests = ' && '.join(tests_commands)
        elif tests_imports and 'python' in requirements:
            tests = ' && '.join('python -c "import %s"' % imp for imp in tests_imports)
        elif tests_imports and ('perl' in requirements or 'perl-threaded' in requirements):
            tests = ' && '.join("perl -e 'use %s;'" % imp for imp in tests_imports)
    else:
        print('No tests defined for: %s' % pkg_path)
    return tests


def get_pkg_name( pkg_path ):
    """
        extracts the package name from a given meta.yaml file
    """
    input_dir = os.path.dirname( os.path.join( './bioconda-recipes', pkg_path ) )
    recipe_meta = MetaData(input_dir)
    return recipe_meta.get_value('package/name')


def get_affected_packages( hours = CHECK_LAST_HOURS):
    """
        returns a list of all meta.yaml file that where modified/created in the last X hours
    """

    cmd = """cd bioconda-recipes && git log --diff-filter=ACMRTUXB --name-only --pretty="" --since="%s hours ago" | grep -E '^recipes/.*/meta.yaml' | sort | uniq"""
    pkg_list = subprocess.check_output(cmd % hours, shell=True)
    ret = list()
    for pkg in pkg_list.strip().split('\n'):
        if pkg and os.path.exists(os.path.join( './bioconda-recipes', pkg )):
            ret.append( (get_pkg_name(pkg), get_tests(pkg)) )
    return ret

def conda_versions( pkg_name, file_name='repodata.json' ):
    """
        returns all conda version strings of a package name
    """
    j = json.load(open(file_name))
    ret = list()
    for pkg in j['packages'].values():
        if pkg['name'] == pkg_name:
            ret.append('%s--%s' % (pkg['version'], pkg['build']))
    return ret


def quay_versions( pkg_name ):
    """
        get all version tags from a Docker Image stored on quay.io given a package name
    """
    time.sleep(1)
    url = 'https://quay.io/api/v1/repository/mulled/%s' % pkg_name
    response = requests.get(url, timeout=None)
    data = response.json()
    return [ tag for tag in data['tags'] if tag != 'latest' ]


def new_versions( quay, conda ):
    """
        calculates the versions that are in conda but not on quay.io
    """
    sconda = set(conda)
    squay = set(quay) if quay else set()
    return sconda.symmetric_difference(squay)


def run( build_command, build_last_n_versions = 1 ):

    involucro_cmds = list()
    pkgs = get_affected_packages()
    for pkg_name, pkg_tests in pkgs:
        c = conda_versions( pkg_name )
        q = quay_versions( pkg_name )
        nvs = new_versions( q, c )
        # only package the most recent N versions
        nvs = sorted(list(nvs), reverse=True)[:build_last_n_versions]
        for tag in nvs:
            version = tag.split('--')[0]
            build = tag.split('--')[1]
            involucro_cmds.append("""./involucro -set TEST='%s' -set PACKAGE='%s' -set TAG='%s' -set VERSION='%s' -set BUILD='%s' %s """ %
                            (pkg_tests, pkg_name, tag, version, build, build_command))

    print '\n'.join(involucro_cmds)


def get_pkg_names():
    print( '\n'.join([pkg_name for pkg_name, pkg_tests in get_affected_packages()]) )

if __name__ == '__main__':

    if not os.environ.get('NAMESPACE', False):
        os.environ['NAMESPACE'] = 'mulled'

    if len(sys.argv) <= 1:
        get_pkg_names()
    else:
        run( ' '.join(sys.argv[1:]) )







