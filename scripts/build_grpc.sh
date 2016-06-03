#!/bin/bash

BASEURL=https://raw.githubusercontent.com/mediachain/mediachain/master/protocol/src/main/protobuf/
PROTOBUF_DIR=$(dirname $0)/../protobuf
PROTOS_OUT_DIR=$(dirname $0)/../mediachain/proto
FILES=("Transactor.proto")

mkdir -p $PROTOBUF_DIR
mkdir -p $PROTOS_OUT_DIR
rm $PROTOS_OUT_DIR/[!_]*

echo "Updating protocol protobuf from upstream master..."

for file in $FILES; do
    wget -P $PROTOBUF_DIR $BASEURL/$file
done

echo "Regenerating protobuf..."

for file in $FILES; do
    protoc -I $PROTOBUF_DIR  --python_out=$PROTOS_OUT_DIR --grpc_out=$PROTOS_OUT_DIR --plugin=protoc-gen-grpc=`which grpc_python_plugin` $PROTOBUF_DIR/$file
done

echo "Done!"

