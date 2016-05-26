#!/usr/bin/env python
import os
from setuptools import setup, find_packages

reqs_file = os.path.join(os.path.dirname(os.path.realpath(__file__))
                   , "requirements.txt")

reqs = None
with open(reqs_file) as f:
    reqs = f.readlines()

setup(
    version='0.1.0',
    name='mediachain-reader',
    description='mediachain reader command line interface',
    author='Mediachain Labs',
    packages=find_packages('.'),
    entry_points={
        'console_scripts': [
            'mediachain-reader = mediachain.reader.main:main'
        ]
    },
    url='http://mediachain.io',
    install_requires=reqs,
)
