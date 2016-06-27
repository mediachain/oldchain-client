#!/bin/bash

REMOTE=protobuf
PROTOBUF_DIR=$(dirname $0)/../protobuf
PROTOS_OUT_DIR=$(dirname $0)/../mediachain/proto
VERSION="0.0.1"
#FILES=("Transactor.proto")

mkdir -p $PROTOS_OUT_DIR
rm $PROTOS_OUT_DIR/[!_]*

echo "Updating protocol protobuf from upstream ($VERSION)"

git subtree pull -P $PROTOBUF_DIR $REMOTE $VERSION

if [ $? -eq 0 ]
then
    echo "Regenerating protobuf..."

    for file in $FILES; do
        protoc -I $PROTOBUF_DIR  --python_out=$PROTOS_OUT_DIR --grpc_out=$PROTOS_OUT_DIR --plugin=protoc-gen-grpc=`which grpc_python_plugin` $PROTOBUF_DIR/$file
    done

    echo "Done!"
else
    echo "Could not update, make sure working tree is clean and tag exists upstream"
fi
