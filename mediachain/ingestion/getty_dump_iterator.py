from os import path
from directory_iterator import DirectoryIterator


class GettyDumpIterator(DirectoryIterator):
    @staticmethod
    def get_local_media_paths(metadata_filepath, parsed_metadata):
        return {
            'thumbnail': thumb_path(metadata_filepath)
        }


def thumb_path(json_file_path):
    base, _, tail = json_file_path.rpartition('/json/images/')
    jpg_fn = path.splitext(tail)[0] + '.jpg'
    return path.join(base, 'downloads', 'thumb', jpg_fn)
