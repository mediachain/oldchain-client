#!/usr/bin/env python
import os, sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

reqs_file = os.path.join(os.path.dirname(os.path.realpath(__file__))
                   , "requirements.txt")

reqs = None
with open(reqs_file) as f:
    reqs = f.readlines()

def _pre_build_py(dir):
    from subprocess import check_call
    check_call(['scripts/build_grpc.sh', sys.executable],
            cwd=dir)

class build_py(_build_py):
    def run(self):
        self.execute(_pre_build_py, [os.path.dirname(__file__)],
                     msg="Generating protobuf")
        _build_py.run(self)

setup(
    version='0.1.4',
    name='mediachain-client',
    description='mediachain reader command line interface',
    author='Mediachain Labs',
    packages=find_packages('.'),
    package_data={
        '': ['*.json']
    },
    author_email = 'hello@mediachainlabs.com',
    entry_points={
        'console_scripts': [
            'mediachain = mediachain.cli.main:main'
        ]
    },
    url='http://mediachain.io',
    install_requires=reqs,
    cmdclass={'build_py': build_py},
    setup_requires=['pytest-runner>=2.8'],
    tests_require=['pytest>=2.9.2'],
)
