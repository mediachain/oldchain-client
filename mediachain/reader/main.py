import sys
import argparse
import os
from mediachain.reader import api

def main(arguments=None):
    if arguments == None:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='mediachain-reader',
        description='Mediachain Reader CLI'
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

    subparsers = parser.add_subparsers(help='Mediachain Reader SubCommands',
                                       dest='subcommand')

    get_parser = subparsers.add_parser(
        'get',
        help='Get a revision chain for a given artefact/entity id'
    )
    get_parser.add_argument('object_id',
                            type=str,
                            help='The id of the artefact/entity to fetch')

    def get_object(ns):
        aws = dict()
        attrs = ['aws_access_key_id',
                 'aws_secret_access_key',
                 'endpoint_url',
                 'region_name']

        # filter unpopulated
        for attr in attrs:
            try:
                aws[attr] = getattr(ns, attr)
            except AttributeError as e:
                pass

        api.get_object(ns.host, ns.port, ns.object_id, aws)

    SUBCOMMANDS={
        'get': get_object
    }

    ns = parser.parse_args(arguments)
    fn = SUBCOMMANDS[ns.subcommand]
    fn(ns)

if __name__ == "__main__":
    main()
