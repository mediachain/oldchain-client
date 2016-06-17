from __future__ import unicode_literals
from os import path, walk
from copy import deepcopy
from datetime import datetime
from base58 import b58decode
from mediachain.datastore.dynamo import get_db
from mediachain.translation import get_translator
from pprint import PrettyPrinter


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
                parsed = translator.parse(content)
                translated = translator.translate(parsed)
                yield translated, content, fn

    def write_dir(self, translator_id, data_dir, limit=None,
                  download_thumbs=False):
        for translated, raw, filename in self.translate_dir(
            translator_id, data_dir, limit
        ):
            # print("translated metadata: {}".format(
            #     pp.pformat(translated)
            # ))

            # TODO: try to get thumbnail data
            self.write_translated(translator_id, translated, raw)

    def write_translated(self,
                         translator_id,
                         translated_metadata,
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

        pp = PrettyPrinter(indent=2)

        obj['metaSource'] = string_ref_to_map(meta_source)
        print('inserting object: ')
        pp.pprint(obj)
        obj_ref = self.transactor.insert_canonical(obj)
        related = translated_metadata.get('related', [])

        refs = {'object': obj_ref.multihash_base58(), 'related': []}

        for r in related:
            rel = r['relationship']
            rel_obj = r['object']
            merge_meta(rel_obj, common_meta)

            print('inserting related entity:')
            pp.pprint(rel_obj)
            # TODO: catch journal errors for duplicate canonicals
            rel_obj_ref = self.transactor.insert_canonical(rel_obj)
            rel_obj_type = rel_obj['type']

            cell = {'type': rel,
                    'ref': obj_ref.to_map(),
                    'meta': deepcopy(common_meta),
                    rel_obj_type: rel_obj_ref.to_map()
                    }

            print('updating chain with cell: ')
            pp.pprint(cell)
            cell_ref = self.transactor.update_chain(cell)

            refs['related'].append({
                'cell': cell_ref.multihash_base58(),
                'object': rel_obj_ref.multihash_base58()
            })

        print('insert complete.  refs: ')
        pp.pprint(refs)
        return refs


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
