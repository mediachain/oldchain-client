# mediachain-client

A client library and minimal command line interface for reading data from and 
importing data into the current Mediachain prototype.

## Installation

To install, first make sure you're using an up-to-date
version of `pip`.  You can update `pip` with itself: `pip install -U pip`.

To install the latest released version of the `mediachain-client` package:

```
pip install mediachain-client
```

To install the development version, from the project root directory:

```
pip install .
```

This will install the `mediachain` command and the mediachain python module.

Please note that if you're installing into a virtualenv, it should be activated
before running the above `pip` commands.  If you're installing into a system-wide
python installation, you may need to run with `sudo` if you get permission errors.

## Command Line Usage

### Configuration

The client communicates with two external services: the mediachain transactor 
network, and the distributed datastore.  By default, the client will connect
to the mediachain testnet.

To connect to another mediachain host, use the `-s` or
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
The command line tool supports ingesting datasets for which a "translator"
exists.  The translator consumes data in its raw format and outputs a
description of the mediachain records and raw media assets to store in
the mediachain network.  The translator output format is available at
[docs/translation.md](docs/translation.md).  To use an existing translator, invoke
the command line `ingest` command, passing the id of a translator and the
location of the raw metadata.

```bash
mediachain [config-options] ingest <translator-id> <metadata-location>
```

The client will run the metadata through the given translator and write the
resulting mediachain records to the transactor network, and will write the
raw metadata to the distributed datastore.

### Metadata Translation

A translator for the Getty Images dataset is currently supported.

To use it, invoke the `mediachain` client with the translator id 
`GettyTranslator/0.1` and pass in a path to a local directory containing
JSON data from the Getty Images API as the `metadata-location`:

```bash
mediachain [config-options] ingest GettyTranslator/0.1 ~/datasets/getty
```

## Internals

The interface between the translation modules and the writer is documented in
[docs/translation.md](docs/translation.md).


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
