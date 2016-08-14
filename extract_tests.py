#!/usr/bin/env python

"""
Creates a shell command to test a Conda package.

Usage:

./extract_tests.py bioconda-recipes/recipes/perl-aceperl/meta.yaml

"""

import sys
import yaml

a = yaml.load(open(sys.argv[1]))

tests = a.get('test', False)
requirements = a.get('requirements', False)

if tests and requirements:
    if 'commands' in tests:
        print(' && '.join(tests['commands']))
    elif 'imports' in tests and 'python' in requirements['run']:
        print(' && '.join("python -c 'import %s'" % imp for imp in tests['imports']))
    elif 'imports' in tests and ('perl' in requirements['run'] or 'perl-threaded' in requirements['run']):
        print(' && '.join("perl -e 'use %s;'" % imp for imp in tests['imports']))
else:
    sys.exit('No tests defined')
