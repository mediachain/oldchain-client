from __future__ import unicode_literals
from os import path, walk
from copy import deepcopy
from datetime import datetime
from base58 import b58decode
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

    def write_translated(self,
                         translated_metadata,
                         translator_id,
                         raw_metadata,
                         thumbnail_data=None):
        meta_source = self.datastore.put(raw_metadata)

        common_meta = {
            u'translator': unicode(translator_id),
            u'date_translated': unicode(datetime.utcnow().isoformat())
        }

        obj = deepcopy(translated_metadata['object'])
        merge_meta(obj, common_meta)
        if thumbnail_data is not None:
            obj['meta']['data']['thumbnail'] = thumbnail_data

        obj['metaSource'] = string_ref_to_map(meta_source)
        obj_ref = string_ref_to_map(self.transactor.insert_canonical(obj))
        related = translated_metadata.get('related', [])

        for r in related:
            rel = r['relationship']
            rel_obj = r['object']
            merge_meta(rel_obj, common_meta)

            # TODO: catch journal errors for duplicate canonicals
            rel_obj_ref = string_ref_to_map(
                self.transactor.insert_canonical(obj))

            rel_obj_type = rel_obj['type']

            cell = {'type': rel, 'ref': obj_ref, rel_obj_type: rel_obj_ref}
            self.transactor.update_chain(cell)


def merge_meta(obj, meta):
    merged = {'data': {}}
    merged.update(meta)
    if 'meta' in obj:
        merged.update(obj['meta'])
    obj['meta'] = merged


def string_ref_to_map(string_ref):
    return {
        '@link': b58decode(string_ref)
    }
