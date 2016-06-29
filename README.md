# mediachain-client

A client library and minimal command line interface for reading data from and 
importing data into the current Mediachain prototype.

## Installation
Please see the [prerequisites section](#prerequisites) below before installing.

```
pip install .
```

This will install the `mediachain` command and the mediachain python module.

### Prerequisites
This project uses [grpc](https://grpc.io) to communicate with remote services.

The next release of grpc is expected to have much improved python developer
tooling, but until then, the best way to get a compatible version of grpc 
installed is to build it from source.  There are three main components to the
installation: grpc core, the protobuf compiler, and the grpcio python package.

#### grpc core
Follow the [grpc install instructions](https://github.com/grpc/grpc/blob/master/INSTALL.md) to build from source, 
first installing the prerequisites for your platform.

#### protobuf compiler

If you already have a version of `protoc` that's compatible with protobuf 3,
you can skip this step.

The grpc source includes a compatible protobuf compiler; 
to install it, first `cd` to the root of the grpc source you checked out above, 
then:

```bash
cd third_party/protobuf
make install
```

#### grpcio python package
The python grpc runtime needs to be installed as well.  If you're on OS X, you
may be able to skip this step, but the currently released version of the 
`grpcio` python module has connection issues when running on linux.
 
 Make sure you have the python development headers installed for your system
 (`apt-get install python-dev` on debian and ubuntu-like systems).

In the grpc source root:

```bash
pip install -r requirements.txt
GRPC_PYTHON_BUILD_WITH_CYTHON=1 pip install .
```

Please note that if you're installing into a virtualenv, it should be activated
before running the above `pip` commands.  If you're installing into a system-wide
python installation, you may need to run with `sudo` if you get permission errors.

## Command Line Usage

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
The command line tool supports ingesting datasets for which a "translator"
exists.  The translator consumes data in its raw format and outputs a
description of the mediachain records and raw media assets to store in
the mediachain network.  The translator output format is 
[detailed below](#translator-format).  To use an existing translator, invoke
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

TBD

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
