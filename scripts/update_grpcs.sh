#!/bin/bash

REMOTE=protobuf
BASEDIR=$(dirname $0)/..
PROTOBUF_DIR=$BASEDIR/protobuf
PROTOS_OUT_DIR=$BASEDIR/mediachain/proto
VERSION="0.0.1"

mkdir -p $PROTOS_OUT_DIR
rm -f $PROTOS_OUT_DIR/[!_]*

echo "Updating protocol protobuf from upstream ($VERSION)"

git -C $BASEDIR subtree pull --squash -P protobuf $REMOTE $VERSION -m "Updated protobuf to $VERSION"

if [ $? -eq 0 ]
then
    ./build_grpc.sh
fi
