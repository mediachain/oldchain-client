import os
import sys
import traceback
from dataset_iterator import DatasetIterator


class DirectoryIterator(DatasetIterator):
    def __init__(self, translator, dir_path, limit=None):
        super(DirectoryIterator, self).__init__(translator, limit=limit)
        self.dir_path = dir_path

    def __iter__(self):
        nn = 0
        limit = self.limit
        for dir_name, subdir_list, file_list in os.walk(self.dir_path):
            for fn in file_list:
                fn = os.path.join(dir_name, fn)
                if not self.translator.can_translate_file(fn):
                    continue

                if limit and (nn + 1 >= limit):
                    print('ingested {} records, ending'.format(nn))
                    return

                try:
                    with open(fn, mode='rb') as f:
                        content = f.read()

                    nn += 1
                    parsed = self.translator.parse(content)
                    translated = self.translator.translate(parsed)
                    local_assets = self.get_local_assets(fn, parsed)

                    yield {
                        'success': True,
                        'translated': translated,
                        'raw_content': content,
                        'parsed': parsed,
                        'local_assets': local_assets
                    }
                except Exception as e:
                    trace = traceback.format_exception(*sys.exc_info())
                    yield {
                        'success': False,
                        'error': e,
                        'error_details': e.message,
                        'error_traceback': trace
                    }

    @staticmethod
    def get_local_assets(metadata_filepath, parsed_metadata):
        return {}
