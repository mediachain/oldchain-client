import os
from dataset_iterator import DatasetIterator


class LocalFileIterator(DatasetIterator):
    def __init__(self, translator, root_path, limit=None):
        super(LocalFileIterator, self).__init__(translator, limit=limit)
        if not os.path.exists(root_path):
            raise ValueError('File at path {} does not exist'.format(root_path))
        
        self.root_path = root_path

    def __iter__(self):
        nn = 0
        limit = self.limit

        fns = []
        if os.path.isdir(self.root_path):
            for dir_name, subdir_list, file_list in os.walk(self.root_path):
                for fn in file_list:
                    fn = os.path.join(dir_name, fn)
                    if self.translator.can_translate_file(fn):
                        fns.append(fn)
        else:
            if self.translator.can_translate_file(self.root_path):
                fns.append(self.root_path)

        for fn in fns:
            if limit and (nn + 1 >= limit):
                print('ingested {} records, ending'.format(nn))
                return

            with open(fn, mode='rb') as f:
                try:
                    content = f.read()
                except IOError as e:
                    print('error reading from {}: {}'.format(
                        fn, str(e)
                    ))
                    continue

            nn += 1
            parsed = self.translator.parse(content)
            translated = self.translator.translate(parsed)
            local_assets = self.get_local_assets(fn, parsed)

            yield {
                'translated': translated,
                'raw_content': content,
                'parsed': parsed,
                'local_assets': local_assets
            }

    @staticmethod
    def get_local_assets(metadata_filepath, parsed_metadata):
        return {}
