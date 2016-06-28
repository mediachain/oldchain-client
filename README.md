# mediachain-client

A minimal client for reading data from and importing data into the current
Mediachain prototype.

## Installation
```
pip install .
```

This will install the `mediachain` command the the mediachain python module.

## Usage

### Configuration

The client communicates with two external services: the mediachain transactor 
network, and the distributed datastore.  The minimum configuration is to set 
the hostname or IP address of the transactor RPC gateway using the `-s` or 
`--host` command line flag.  If the transactor RPC service is using a port
other than the default of `10001`, you'll need to set that with `-p` or 
`--port`.

If datastore service is running on a different host than the transactor service,
 use the `--datastore-host` argument, and use `--datastore-port` if the 
 datastore service uses a port other than `10002`.
 
#### IPFS Configuration

While we're transitioning to using IPFS to store all of our data, IPFS is
 currently only enabled if you pass in the `-i` or `--use-ipfs` flag.  This will
 send raw metadata and media files (thumbnails, etc) to IPFS via the HTTP
 gateway, which by default is assumed to be running on the same machine as
 the client.
 
When IPFS is enabled, the client will still connect to the datastore RPC 
service, since mediachain records and the journal blockchain are not yet
being stored in IPFS.

If you enable IPFS when writing data, you should also enable it when reading,
otherwise thumbnails and other data may fail to load.

### Reading
Mediachain records can be retrieved by id using the `get` command:

```bash
mediachain [config-options] get <record-id>
```

This will return an up-to-date view of the base record with the given id,
with all statements in its chain of updates applied.


### Writing
A "black box" translator for the Getty Images dataset is currently supported.

This client walks a directory containing JSON metadata obtained from the
Getty images API, submitting mediachain records to the transactor network.

You can invoke the importer like so:
```
mediachain [config-options] ingest <getty-json-dir>
```

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
