import sys
import argparse
import os
import mediachain.api

def main(arguments=None):
    if arguments == None:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='mediachain-reader',
        description='Mediachain Reader CLI'
    )
    subparsers = parser.add_subparsers(help='Mediachain Reader SubCommands',
                                       dest='subcommand')

    get_parser = subparsers.add_parser(
        'get',
        help='Get a revision chain for a given artefact/entity id'
    )
    get_parser.add_argument('object_id',
                            type=str,
                            help='The id of the artefact/entity to fetch')

    ns = parser.parse_args(arguments)
    fn = getattr(mediachain.api, ns.subcommand)
    fn(ns)

if __name__ == "__main__":
    main()
