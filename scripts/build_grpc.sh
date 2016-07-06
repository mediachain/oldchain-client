#!/bin/bash

PYTHON=${1:-"/usr/bin/env python"}

BASEDIR=$(dirname $0)/..
PROTOBUF_DIR=$BASEDIR/protobuf
PROTOS_OUT_DIR=$BASEDIR/mediachain/proto

mkdir -p $PROTOS_OUT_DIR
rm -f $PROTOS_OUT_DIR/[!_]*

echo "Regenerating protobuf..."

if [ ! -d $PROTOBUF_DIR ]
then
    echo "Could not find protobuf sources, distribution incomplete"
    exit 1
fi

for file in `ls $PROTOBUF_DIR`; do
    $PYTHON -m grpc.tools.protoc -I $PROTOBUF_DIR  --python_out=$PROTOS_OUT_DIR --grpc_python_out=$PROTOS_OUT_DIR $PROTOBUF_DIR/$file
    if [ $? -ne 0 ]
    then
        echo "Failed to generate protobuf for $file!"
        exit $?
    fi
done

echo "Done!"
