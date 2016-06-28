#!/bin/bash

BASEDIR=$(dirname $0)/..
PROTOBUF_DIR=$BASEDIR/protobuf
PROTOS_OUT_DIR=$BASEDIR/mediachain/proto

mkdir -p $PROTOS_OUT_DIR
rm -f $PROTOS_OUT_DIR/[!_]*

echo "Regenerating protobuf..."

for file in `ls $PROTOBUF_DIR`; do
    protoc -I $PROTOBUF_DIR  --python_out=$PROTOS_OUT_DIR --grpc_out=$PROTOS_OUT_DIR --plugin=protoc-gen-grpc=`which grpc_python_plugin` $PROTOBUF_DIR/$file
done

echo "Done!"
