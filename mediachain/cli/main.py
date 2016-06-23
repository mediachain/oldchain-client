import sys
import argparse
import os
import traceback
from time import sleep

from mediachain.reader import api
from mediachain.getty import ingest
from mediachain.datastore import set_use_ipfs_for_raw_data
from mediachain.datastore.dynamo import set_aws_config
from mediachain.datastore.ipfs import set_ipfs_config
from mediachain.transactor.client import TransactorClient


def main(arguments=None):
    def configure_aws(ns):
        # aws configuration
        aws = dict()
        attrs = ['aws_access_key_id',
                 'aws_secret_access_key',
                 'endpoint_url',
                 'region_name',
                 'mediachain_table_name']

        # filter unpopulated
        for attr in attrs:
            try:
                aws[attr] = getattr(ns, attr)
            except AttributeError as e:
                pass

        set_aws_config(aws)

    def configure_ipfs(ns):
        try:
            cfg = {'host': getattr(ns, 'ipfs_host'),
                   'port': getattr(ns, 'ipfs_port')
                   }

            set_ipfs_config(cfg)

            if getattr(ns, 'use_ipfs'):
                set_use_ipfs_for_raw_data(True)
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
                        required=True,
                        dest='host')
    parser.add_argument('-p', '--port',
                        type=int,
                        required=True,
                        dest='port')
    parser.add_argument('-r', '--region',
                        type=str,
                        required=False,
                        default='us-east-1',
                        dest='region_name',
                        help='AWS region of DynamoDB instance')
    parser.add_argument('-e', '--endpoint',
                        type=str,
                        required=False,
                        dest='endpoint_url',
                        help='AWS endpoint of DynamoDB instance')
    parser.add_argument('-k', '--key',
                        type=str,
                        required=False,
                        default='',
                        dest='aws_access_key_id',
                        help='AWS access key ID')
    parser.add_argument('-x', '--secret-key',
                        type=str,
                        required=False,
                        default='',
                        dest='aws_secret_access_key',
                        help='AWS secret access key')
    parser.add_argument('-t', '--dynamo-table',
                        type=str,
                        required=False,
                        default='Mediachain',
                        dest='mediachain_table_name',
                        help='Name of dynamo table to work wtih')
    parser.add_argument('-i', '--use_ipfs',
                        dest='use_ipfs',
                        action='store_true',
                        help='If set, upload images and raw metadata ' +
                             'to IPFS'
                        )
    parser.add_argument('--ipfs_host',
                        type=str,
                        default='localhost',
                        help='Hostname or ip address of IPFS api server'
                        )
    parser.add_argument('--ipfs_port',
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
        help='Ingest a directory of scraped Getty JSON data'
    )
    ingest_parser.add_argument('dir',
                               type=str,
                               help='Path to getty json directory root')
    ingest_parser.add_argument('-m', '--max_entries',
                               type=int,
                               dest='max_num',
                               help='Max json entries to parse. ' +
                               'Defaults to 0 (no maximum)',
                               default=0)
    ingest_parser.add_argument('-d', '--download_thumbnails',
                               type=bool,
                               dest='download_thumbs',
                               help='If set, download thumbnails if not found' +
                                    ' on disk.',
                               default=False)

    def get_cmd(ns):
        transactor = TransactorClient(ns.host, ns.port)
        api.get_and_print_object(transactor, ns.object_id)

    SUBCOMMANDS={
        'get': get_cmd,
        'ingest': lambda ns: ingest.ingest(ns.host, ns.port, ns.dir, ns.max_num,
                                           ns.download_thumbs)
    }

    ns = parser.parse_args(arguments)
    fn = SUBCOMMANDS[ns.subcommand]

    configure_aws(ns)
    configure_ipfs(ns)

    try:
        fn(ns)
    except KeyboardInterrupt:
        for line in traceback.format_exception(*sys.exc_info()):
            print line,
        sleep(1)
        os._exit(-1)

if __name__ == "__main__":
    main()
