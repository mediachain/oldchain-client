import sys
import argparse
import os
import traceback
from time import sleep

# Set the GRPC log level to ERROR, unless it's already been set
# This needs to happen before importing anything that will
# import grpc, since it reads the environment var immediately on import
def set_grpc_verbosity():
    level = os.environ.get('GRPC_VERBOSITY', 'ERROR')
    os.environ['GRPC_VERBOSITY'] = level

set_grpc_verbosity()

from mediachain.utils.log import config_logging
config_logging(level=os.environ.get('MEDIACHAIN_VERBOSITY', 'WARNING'))

from mediachain.reader import api
from mediachain.reader.utils import dump
from mediachain.datastore import set_use_ipfs_for_raw_data, get_db
from mediachain.datastore.ipfs import set_ipfs_config
from mediachain.datastore.rpc import set_rpc_datastore_config, close_db
from mediachain.writer import Writer
from mediachain.translation import get_translator
from mediachain.ingestion.directory_iterator import LocalFileIterator
from mediachain.transactor.client import TransactorClient




def main(arguments=None):
    def configure_datastore(ns):
        host = getattr(ns, 'datastore_host')
        if host is None:
            host = getattr(ns, 'host')
        port = getattr(ns, 'datastore_port')
        set_rpc_datastore_config({'host': host, 'port': port})

    def configure_ipfs(ns):
        try:
            cfg = {'host': getattr(ns, 'ipfs_host'),
                   'port': getattr(ns, 'ipfs_port')
                   }

            set_ipfs_config(cfg)

            if getattr(ns, 'disable_ipfs'):
                set_use_ipfs_for_raw_data(False)
        except AttributeError:
            pass

    if arguments == None:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='mediachain',
        description='Mediachain CLI'
    )

    parser.add_argument('-s', '--host',
                        type=str,
                        default='facade.mediachain.io',
                        dest='host')
    parser.add_argument('-p', '--port',
                        type=int,
                        default=10001,
                        dest='port')
    parser.add_argument('--datastore-host',
                        dest='datastore_host',
                        type=str,
                        required=False,
                        help='Hostname or ip address of datastore service. ' +
                        'If not given, will default to the value of --host')
    parser.add_argument('--datastore-port',
                        dest='datastore_port',
                        type=int,
                        default=10002,
                        help='Port to use when connecting to the datastore ' +
                             'service.')
    parser.add_argument('--disable-ipfs',
                        dest='disable_ipfs',
                        action='store_true',
                        help=('If set, do not upload images and raw metadata '
                              'to IPFS')
                        )
    parser.add_argument('--ipfs-host',
                        dest='ipfs_host',
                        type=str,
                        default='localhost',
                        help='Hostname or ip address of IPFS api server'
                        )
    parser.add_argument('--ipfs-port',
                        dest='ipfs_port',
                        type=int,
                        default=5001,
                        help='Port for IPFS api server')

    subparsers = parser.add_subparsers(help='Mediachain Reader SubCommands',
                                       dest='subcommand')

    get_parser = subparsers.add_parser(
        'get',
        help='Get a revision chain for a given artefact/entity id'
    )
    get_parser.add_argument('object_id',
                            type=str,
                            help='The id of the artefact/entity to fetch')

    ingest_parser = subparsers.add_parser(
        'ingest',
        help='Ingest metadata into the system using a schema translator'
    )

    translator_id_help_text = ('identifier for a schema translator'
                               'e.g. getty@QmF00... \n'
                               'Must be in the format of name@hash where '
                               'name is the name of a translator, and '
                               'hash is an ipfs multihash that resolves '
                               'to a specific version of that translator'
                               )

    ingest_parser.add_argument('translator_id',
                               type=str,
                               help=translator_id_help_text)
    ingest_parser.add_argument('input_path',
                               type=str,
                               help=('Path to metadata source.\n'
                                     'Can be a directory or single file'))
    ingest_parser.add_argument('--skip-validation',
                               dest='skip_validation',
                               action='store_true',
                               help=argparse.SUPPRESS)  # hide from --help
    ingest_parser.add_argument('-m', '--max-entries',
                               type=int,
                               dest='max_num',
                               help='Max json entries to parse. ' +
                               'Defaults to 0 (no maximum)',
                               default=0)
    ingest_parser.add_argument('--skip-image-downloads',
                               dest='skip_downloads',
                               action='store_true',
                               help=('If set, images referenced in metadata '
                                     'will not be downloaded and sent to the '
                                     'datastore.'))

    update_parser = subparsers.add_parser(
        'update',
        help=('Update an existing record with new data using a record in an '
              'external format and a schema translator.')
    )
    update_parser.add_argument('object_id',
                               type=str,
                               help=('Multihash reference to a mediachain '
                                     'canonical record'))
    update_parser.add_argument('translator_id',
                               type=str,
                               help=translator_id_help_text)
    update_parser.add_argument('input_path',
                               type=str,
                               help=('Path to metadata source.\n'
                                     'Should be a single file.'))
    update_parser.add_argument('--skip-image-downloads',
                               dest='skip_downloads',
                               action='store_true',
                               help=('If set, images referenced in metadata '
                                     'will not be downloaded and sent to the '
                                     'datastore.'))

    update_direct_parser = subparsers.add_parser(
        'update-direct',
        help='Update an existing record by reading valid mediachain-format '
             'metadata from standard input.'
    )
    update_direct_parser.add_argument('object_id',
                                      type=str,
                                      help=('Multihash reference to a '
                                            'mediachain canonical record'))

    datastore_get_parser = subparsers.add_parser(
        'datastore-get',
        help='Get and print an object from the datastore'
    )
    datastore_get_parser.add_argument('object_id',
                                      type=str,
                                      help='multihash id for datastore object')

    def get_cmd(ns):
        transactor = TransactorClient(ns.host, ns.port)
        api.get_and_print_object(transactor, ns.object_id)

    def datastore_get_cmd(ns):
        datastore = get_db()
        obj = datastore.get(ns.object_id)
        if obj:
            try:
                dump(obj)
            except (ValueError, AttributeError, TypeError):
                print(str(obj))
        else:
            print('No object in datastore matching key {}'.format(ns.object_id))

    def ingest_cmd(args):
        translator = get_translator(args.translator_id)
        iterator = LocalFileIterator(translator, args.input_path, args.max_num)

        transactor = TransactorClient(args.host, args.port)
        writer = Writer(transactor,
                        download_remote_assets=(not args.skip_downloads))

        for refs in writer.write_dataset(iterator):
            print('Inserted canonical: {}'.format(refs['canonical']))

    def update_cmd(args):
        translator = get_translator(args.translator_id)
        iterator = LocalFileIterator(translator, args.input_path)
        transactor = TransactorClient(args.host, args.port)
        writer = Writer(transactor,
                        download_remote_assets=(not args.skip_downloads))
        writer.update_with_translator(args.object_id, iterator)
        get_cmd(args)

    def update_direct_cmd(args):
        transactor = TransactorClient(args.host, args.port)
        writer = Writer(transactor)
        writer.update_artefact_direct(args.object_id, sys.stdin)
        print('updated {ref} with new data. fetching updated record..'.format(
          ref=args.object_id
        ))
        get_cmd(args)


    SUBCOMMANDS={
        'get': get_cmd,
        'ingest': ingest_cmd,
        'datastore-get': datastore_get_cmd,
        'update': update_cmd,
        'update-direct': update_direct_cmd
    }

    ns = parser.parse_args(arguments)
    if getattr(ns, 'skip_validation', False):
        os.environ['MEDIACHAIN_SKIP_SCHEMA_VALIDATION'] = 'true'

    fn = SUBCOMMANDS[ns.subcommand]

    configure_datastore(ns)
    configure_ipfs(ns)

    try:
        fn(ns)
        close_db()
    except KeyboardInterrupt:
        for line in traceback.format_exception(*sys.exc_info()):
            print line,
        sleep(1)
        os._exit(-1)

if __name__ == "__main__":
    main()
