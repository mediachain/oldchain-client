import sys
import argparse
import os
import mediachain.reader.api
from mediachain.reader.api import Config

def main(arguments=None):
    if arguments == None:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='mediachain-reader',
        description='Mediachain Reader CLI'
    )

    parser.add_argument('-h', '--host',
                        type=str,
                        required=True,
                        dest='host')
    parser.add_argument('-p', '--port',
                        type=int,
                        required=True,
                        dest='port')

    subparsers = parser.add_subparsers(help='Mediachain Reader SubCommands',
                                       dest='subcommand')

    get_parser = subparsers.add_parser(
        'get',
        help='Get a revision chain for a given artefact/entity id'
    )
    get_parser.add_argument('object_id',
                            type=str,
                            help='The id of the artefact/entity to fetch')

    SUBCOMMANDS={
        'get': 'get_chain_head'
    }

    ns = parser.parse_args(arguments)
    cfg = Config(host=ns.host, port=ns.port)
    fn = getattr(mediachain.reader.api, SUBCOMMANDS[ns.subcommand])
    fn(ns)

if __name__ == "__main__":
    main()
