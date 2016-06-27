from os import path, walk
from mediachain.datastore.dynamo import get_db
from mediachain.translation import get_translator


class Writer(object):
    def __init__(self, transactor, datastore=None):
        self.transactor = transactor
        self.datastore = datastore or get_db()

    @staticmethod
    def translate_dir(translator_id, data_dir, limit=None):
        translator = get_translator(translator_id)
        nn = 0
        for dir_name, subdir_list, file_list in walk(data_dir):
            for fn in file_list:
                fn = path.join(dir_name, fn)
                if not translator.can_translate_file(fn):
                    continue

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
                translated = translator.translate(content)
                yield translated, translator_id

    def write_translated(self, translated_metadata, translator_id):
        raise NotImplementedError("need to think about this some more")
