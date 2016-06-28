from os import path
from directory_iterator import DirectoryIterator
import pathlib


class GettyDumpIterator(DirectoryIterator):
    @staticmethod
    def get_local_assets(metadata_filepath, parsed_metadata):
        return {
            'thumbnail': {
                '__mediachain_asset__': True,
                'uri': local_thumb_uri(metadata_filepath)
            }
        }


def local_thumb_uri(json_file_path):
    base, _, tail = json_file_path.rpartition('/json/images/')
    jpg_fn = path.splitext(tail)[0] + '.jpg'
    file_path = path.abspath(path.join(base, 'downloads', 'thumb', jpg_fn))
    return pathlib.Path(file_path).as_uri()
