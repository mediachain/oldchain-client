import sys
import argparse
from mediachain.getty.ingest import ingest


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='mediachain-getty-writer',
        description='Mediachain writer for Getty Images'
    )

    parser.add_argument('-s', '--host',
                        type=str,
                        required=True,
                        dest='host')
    parser.add_argument('-p', '--port',
                        type=int,
                        required=True,
                        dest='port')

    parser.add_argument('-d', '--datastore_url',
                        type=str,
                        required=False,
                        dest='datastore_url')

    subparsers = parser.add_subparsers(help='Mediachain writer subcommands',
                                       dest='subcommand')

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

    subcommands = {
        'ingest': lambda ns:
            ingest(ns.host, ns.port, ns.dir, ns.datastore_url, ns.max_num)
    }

    ns = parser.parse_args(arguments)
    fn = subcommands[ns.subcommand]
    fn(ns)


if __name__ == '__main__':
    main()
