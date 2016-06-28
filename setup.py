#!/usr/bin/env python
import os, sys
from setuptools import setup, find_packages
from setuptools.command.install import install as _install  

reqs_file = os.path.join(os.path.dirname(os.path.realpath(__file__))
                   , "requirements.txt")

reqs = None
with open(reqs_file) as f:
    reqs = f.readlines()

def _pre_install(dir):
    from subprocess import check_call
    check_call(['scripts/build_grpc.sh'],
            cwd=dir) 

class install(_install):
    def run(self):
        self.execute(_pre_install, [os.path.dirname(__file__)],
                     msg="Generating protobuf")
        _install.run(self)

setup(
    version='0.1.0',
    name='mediachain-client',
    description='mediachain reader command line interface',
    author='Mediachain Labs',
    packages=find_packages('.'),
    entry_points={
        'console_scripts': [
            'mediachain = mediachain.cli.main:main'
        ]
    },
    url='http://mediachain.io',
    install_requires=reqs,
    cmdclass={'install': install},
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
