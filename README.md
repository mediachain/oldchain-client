# mediachain-client

A minimal client for reading data from and importing data into the current
Mediachain prototype.

## Installation
```
pip install .
```

## Usage

### Reading
TODO

### Writing
A "black box" translator for the Getty Images dataset is currently supported.

This client walks a directory containing JSON metadata obtained from the
Getty images API.  It connects via [gRPC][grpc] to a mediachain service, 
which in turn communicates with a mediachain transactor cluster.  This
client communicates directly with the datastore, which during the prototype
phase is implemented on Amazon DynamoDB.

You will either need valid AWS credentials for the mediachain testnet, or
an install of [dynamo local][dynamo-local] with a local mediachain transactor.

You can invoke the importer like so:
```
python -m mediachain.getty.main -s <mediachain-rpc-host> -p <mediachain-rpc-port> ingest <getty-json-dir>
```

If you're using a local dynamo db for testing, you should also pass
`-d http://localhost:8000` (assuming you're using the default port).  For
real dynamo, you should use the [aws command line tools][aws-cli] to set
the appropriate access credentials before running the importer.

The `<getty-json-dir>` argument should be a path to the root of a directory
structure containing getty json metadata, with one json file per record.


## Known issues

Trying to stop the import with CTRL-C will often fail to kill the process.  This
is an [issue](https://github.com/grpc/grpc/issues/4705) with grpc which should
 be resolved in the next release.
 
 
## Unknown issues

This project is under active development, and likely contains bugs and other 
rough edges.  If you encounter something broken, or if this readme goes stale,
please open an issue and let us know.



[grpc]: https://grpc.io
[dynamo-local]: http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html
[aws-cli]: https://aws.amazon.com/cli/
