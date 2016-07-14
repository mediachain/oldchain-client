#!/usr/bin/env bash

# install rocksdb from source and the pyrocksdb python package
# if installing into a virtualenv, make sure it's active before running
# this script
#
# This assumes you have the necessary build dependencies installed:
# $ sudo apt-get install gcc-4.8 g++-4.8
# $ sudo apt-get install -y libsnappy-dev zlib1g-dev libbz2-dev libgflags-dev

BUILD_ROOT_DIR=${1-"${HOME}/src-dependencies"}
ROCKS_VERSION=${2-"4.8"}
PYROCKSDB_VERSION=${3-"0.4"}
ROCKS_TARBALL=rocksdb-${ROCKS_VERSION}.tar.gz
ROCKS_TARBALL_URL=https://github.com/facebook/rocksdb/archive/${ROCKS_TARBALL}

mkdir -p ${BUILD_ROOT_DIR}
cd ${BUILD_ROOT_DIR}
if [ ! -f ${ROCKS_TARBALL} ]; then
    wget ${ROCKS_TARBALL_URL}
fi
tar xzf ${ROCKS_TARBALL}
cd rocksdb-rocksdb-${ROCKS_VERSION}
make shared_lib

# install pyrocksdb
export CPLUS_INCLUDE_PATH=${CPLUS_INCLUDE_PATH}:`pwd`/include
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:`pwd`
export LIBRARY_PATH=${LIBRARY_PATH}:`pwd`

# Installing with --no-cache-dir forces the pyrocksdb setup
# to find the version of the shared lib at the configured paths
# otherwise it will use the paths it was last installed with, which
# may be an old version
pip install -I -U --no-cache-dir pyrocksdb==${PYROCKSDB_VERSION}
