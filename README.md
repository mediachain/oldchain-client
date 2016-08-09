# mediachain-client

A client library and minimal command line interface for reading data from and 
importing data into the current Mediachain prototype.

## Usage

#### Optional dependencies
The mediachain client uses [rocksdb](http://rocksdb.org/) to store a local
cache of the transactor blockchain.  This cache is not needed for most simple
operations, and is therefore optional.  To enable the cache, you'll need to
install rockdb, and the [pyrocksdb python module](https://github.com/stephan-hof/pyrocksdb)

On macOS, via [homebrew](http://brew.sh/):
```bash
$ brew install rocksdb
$ pip install pyrocksdb
```

Linux users should follow the [rocksdb installation instructions](https://github.com/facebook/rocksdb/blob/master/INSTALL.md)
and install from source.

#### Installation

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

While we're transitioning to using ipfs to store all of our data, ipfs is
currently only used for binary assets (thumbnails, etc) and raw metadata.
You can opt-out of storing things in ipfs by passing the `--disable-ipfs`
flag, but please note that ipfs will still be required when writing records
using a translator, since it's used when resolving translators by their
version ids.

By default the ipfs daemon is assumed to be running on the same machine as
the client.  Use `--ipfs-host` and `--ipfs-port` flags if you want to connect
to an ipfs daemon running on another machine or on a non-standard port.


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

The current set of schema translators lives in the [schema-translators repository](https://github.com/mediachain/schema-translators).
When ingesting records, you need to provide the name and ipfs hash of a published translator,
which will be fetched via ipfs and used to extract information from a dataset.  By cloning that
repository and running `python setup.py publish_translators`, you can get a list of the latest
translators and their most current version hashes.

When ingesting data, you provide a `name@version` identifier for the translator you want to use.

For example, to use the translator for the Artsy API json at version `QmTvzPcDjKyAP9nx3tLnE3k9kMmB4QXF7hzZTM2vLDHtUA`,
you would use the translator id `artsy@QmTvzPcDjKyAP9nx3tLnE3k9kMmB4QXF7hzZTM2vLDHtUA`:

```bash
mediachain [config-options] ingest artsy@QmTvzPcDjKyAP9nx3tLnE3k9kMmB4QXF7hzZTM2vLDHtUA ~/datasets/artsy/1.json
```

## Internals

The interface between the translation modules and the writer is documented in
[docs/translation.md](docs/translation.md).



## Unknown issues

This project is under active development, and likely contains bugs and other 
rough edges.  If you encounter something broken, or if this readme goes stale,
please open an issue and let us know.



[grpc]: https://grpc.io
[dynamo-local]: http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html
[aws-cli]: https://aws.amazon.com/cli/
