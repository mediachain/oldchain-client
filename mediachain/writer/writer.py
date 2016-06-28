from __future__ import unicode_literals

from copy import deepcopy
from datetime import datetime
from pprint import PrettyPrinter

from base58 import b58decode
from mediachain.ingestion.media_loader import load_media
from mediachain.datastore.dynamo import get_db


class Writer(object):
    def __init__(self, transactor, datastore=None):
        self.transactor = transactor
        self.datastore = datastore or get_db()

    def write_dataset(self, dataset_iterator, download_remote_media=False):
        translator_id = dataset_iterator.translator.translator_id()

        for result in dataset_iterator:
            translated = result['translated']
            raw = result['raw_content']
            media = load_media(result['local_media'],
                               result['remote_media'],
                               download_remote=download_remote_media)

            self.write_translated(translator_id, translated, raw, media)

    def write_translated(self,
                         translator_id,
                         translated_metadata,
                         raw_metadata,
                         media=None):
        meta_source = string_ref_to_map(self.datastore.put(raw_metadata))

        common_meta = {
            'translator': unicode(translator_id),
            'date_translated': unicode(datetime.utcnow().isoformat())
        }

        obj = deepcopy(translated_metadata['object'])
        merge_meta(obj, common_meta)
        if media is not None:
            media = self.write_media(media)
            obj['meta']['data'].update(media)

        pp = PrettyPrinter(indent=2)

        obj['metaSource'] = meta_source
        print('inserting object: ')
        pp.pprint(obj)
        obj_ref = self.transactor.insert_canonical(obj)
        related = translated_metadata.get('related', [])

        refs = {'object': obj_ref.multihash_base58(), 'related': []}

        for r in related:
            rel = r['relationship']
            rel_obj = r['object']
            rel_obj['metaSource'] = meta_source
            merge_meta(rel_obj, common_meta)

            print('inserting related entity:')
            pp.pprint(rel_obj)
            # TODO: catch journal errors for duplicate canonicals
            rel_obj_ref = self.transactor.insert_canonical(rel_obj)
            rel_obj_type = rel_obj['type']

            cell = {'type': rel,
                    'ref': obj_ref.to_map(),
                    'meta': deepcopy(common_meta),
                    'metaSource': meta_source,
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

    def write_media(self, media_data):
        media_refs = {}
        for name, data in media_data.iteritems():
            ref_str = self.datastore.put(data)
            media_refs[name] = string_ref_to_map(ref_str)
        return media_refs


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

