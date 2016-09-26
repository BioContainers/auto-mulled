#!/usr/bin/env python

"""
Creates shell commands to run involucro.

Usage:

./helpers.py build
./helpers.py all

"""
from __future__ import print_function

import os
import re
import sys
import json
import time
import requests
import subprocess
from conda_build.metadata import MetaData

CHECK_LAST_HOURS = 25


def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html."""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]


def get_tests(pkg_path):
    """Extract test cases given a recipe's meta.yaml file."""
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
            tests = ' && '.join('''perl -e "use %s;"''' % imp for imp in tests_imports)
        tests = tests.replace('$R ', 'Rscript ')
    else:
        pass
    return tests


def get_pkg_name(pkg_path):
    """Extract the package name from a given meta.yaml file."""
    input_dir = os.path.dirname( os.path.join( './bioconda-recipes', pkg_path ) )
    recipe_meta = MetaData(input_dir)
    return recipe_meta.get_value('package/name')


def get_affected_packages(hours=CHECK_LAST_HOURS):
    """Return a list of all meta.yaml file that where modified/created recently.

    Length of time to check for indicated by the ``hours`` parameter.
    """
    cmd = """cd bioconda-recipes && git log --diff-filter=ACMRTUXB --name-only --pretty="" --since="%s hours ago" | grep -E '^recipes/.*/meta.yaml' | sort | uniq"""
    pkg_list = subprocess.check_output(cmd % hours, shell=True)
    ret = list()
    for pkg in pkg_list.strip().split('\n'):
        if pkg and os.path.exists(os.path.join( './bioconda-recipes', pkg )):
            ret.append( (get_pkg_name(pkg), get_tests(pkg)) )
    return ret


def conda_versions(pkg_name, file_name='repodata.json'):
    """Return all conda version strings for a specified package name."""
    j = json.load(open(file_name))
    ret = list()
    for pkg in j['packages'].values():
        if pkg['name'] == pkg_name:
            ret.append('%s--%s' % (pkg['version'], pkg['build']))
    return ret


def quay_versions(pkg_name):
    """Get all version tags for a Docker image stored on quay.io for supplied package name."""
    time.sleep(1)
    url = 'https://quay.io/api/v1/repository/mulled/%s' % pkg_name
    response = requests.get(url, timeout=None)
    data = response.json()
    return [ tag for tag in data['tags'] if tag != 'latest' ]


def new_versions( quay, conda ):
    """Calculate the versions that are in conda but not on quay.io."""
    sconda = set(conda)
    squay = set(quay) if quay else set()
    return sconda - squay  # sconda.symmetric_difference(squay)


def run(build_command, build_last_n_versions=1):
    """Build list of involucro commands (as shell snippet) to run."""
    involucro_cmds = list()
    pkgs = get_affected_packages()
    for pkg_name, pkg_tests in pkgs:
        c = conda_versions( pkg_name )
        # only package the most recent N versions
        c = sorted(c, reverse=True, key=natural_key)[:build_last_n_versions]
        q = quay_versions( pkg_name )
        nvs = new_versions( q, c )
        for tag in nvs:
            version = tag.split('--')[0]
            build = tag.split('--')[1]
            involucro_cmds.append(
                """./involucro -v=2 -set TEST='%s' -set PACKAGE='%s' -set TAG='%s' -set VERSION='%s' -set BUILD='%s' %s """ %
                (pkg_tests, pkg_name, tag, version, build, build_command)
            )

    print('\n'.join(involucro_cmds))


def get_pkg_names():
    """Print package names that would be affected."""
    print('\n'.join([pkg_name for pkg_name, pkg_tests in get_affected_packages()]))


def main(argv=None):
    """Main entry-point for the auto-mulled Python helper."""
    if argv is None:
        argv = sys.argv

    if not os.environ.get('NAMESPACE', False):
        os.environ['NAMESPACE'] = 'mulled'

    if len(sys.argv) <= 1:
        get_pkg_names()
    else:
        run( ' '.join(sys.argv[1:]) )


if __name__ == '__main__':
    main()
