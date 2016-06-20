from __future__ import unicode_literals

from copy import deepcopy
from datetime import datetime
import re
from pprint import PrettyPrinter

from base58 import b58decode
from mediachain.ingestion.media_loader import load_media
from mediachain.ingestion.asset_loader import load_asset
from mediachain.datastore.dynamo import get_db
from mediachain.datastore.data_objects import MultihashReference
from grpc.framework.interfaces.face.face import NetworkError

class Writer(object):
    def __init__(self, transactor, datastore=None,
                 download_remote_assets=False):
        self.transactor = transactor
        self.datastore = datastore or get_db()
        self.download_remote_assets = download_remote_assets

    def write_dataset(self, dataset_iterator):
        translator_id = dataset_iterator.translator.translator_id()

        for result in dataset_iterator:
            translated = result['translated']
            raw = result['raw_content']
            media = load_media(result['local_media'],
                               result['remote_media'],
                               download_remote=self.download_remote_assets)

            self.write_translated(translator_id, translated, raw, media)

    def write_translated(self,
                         translator_id,
                         translated_metadata,
                         raw_metadata,
                         media=None):
        meta_source = string_ref_to_map(self.datastore.put(raw_metadata))

        common_meta = {
            'translator': unicode(translator_id),
            # 'date_translated': unicode(datetime.utcnow().isoformat())
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

    def flatten_record(self, record):
        if '__mediachain_object__' not in record:
            raise ValueError('value is not a mediachain object')

        assets = {k: v for k, v in record.iteritems()
                  if is_asset(v)}

        objects = {k: v for k, v in record.iteritems()
                   if is_mediachain_object(v)}

        for k, a in assets.iteritems():
            ref = self.store_asset(a)
            if ref is None:
                print('Unable to store asset with key {}, removing'.format(k))
                del record[k]
            else:
                record[k] = ref

        for k, o in objects.iteritems():
            o = self.flatten_record(o)
            ref = self.submit_object(o)
            record[k] = ref

        del record['__mediachain_object__']
        return record

    def store_asset(self, asset):
        data = load_asset(asset, download_remote=self.download_remote_assets)
        if data is None:
            return None
        return string_ref_to_map(self.datastore.put(data))

    def submit_object(self, obj):
        # TODO: catch duplicate insert
        try:
            if is_canonical(obj):
                ref = self.transactor.insert_canonical(obj)
            else:
                ref = self.transactor.update_chain(obj)
        except NetworkError as e:
            ref = duplicate_canonical_ref(e)
            if ref is None:
                raise

        return ref

    def flatten_translator_output(self, translated):
        canonical = translated['canonical']


def is_tagged_dict(tag, value):
    try:
        return tag in value
    except TypeError:
        return False


def is_asset(value):
    return is_tagged_dict('__mediachain_asset__', value)


def is_mediachain_object(value):
    return is_tagged_dict('__mediachain_object__', value)


def is_canonical(obj):
    return obj['type'] == 'artefact' or obj['type'] == 'entity'


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

# TODO(yusef): replace string parsing hack with grpc error metadata
# requires support in grpc-java (in master but not yet released)

# this regex will only work for base58 encoded sha2-256 hashes,
# and will break if we ever change the error message :(
duplicate_insert_pattern = re.compile(
    'Duplicate Journal Insert.*(Qm[1-9a-zA-Z][^OIl]{44})'
)


def duplicate_canonical_ref(grpc_error):
    m = re.match(duplicate_insert_pattern, grpc_error.details)
    if not m:
        return None
    ref_str = m.group(1)
    return MultihashReference.from_base58(ref_str)

