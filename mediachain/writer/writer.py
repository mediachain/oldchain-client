from __future__ import unicode_literals

from copy import deepcopy
from datetime import datetime
import re
from pprint import PrettyPrinter

from base58 import b58decode
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
            local_assets = result.get('local_assets', {})
            self.submit_translator_output(translator_id, translated,
                                          raw, local_assets)

    def submit_translator_output(self,
                                 translator_id,
                                 translated,
                                 raw_content,
                                 local_assets):
        common_meta = {'translator': translator_id}
        meta_source = self.store_raw(raw_content)

        canonical = translated['canonical']
        canonical = self.flatten_record(canonical, meta_source, local_assets)
        canonical_ref = self.submit_object(canonical)

        chain = translated.get('chain', [])
        for cell in chain:
            cell = self.flatten_record(cell)
            cell['ref'] = canonical_ref
            self.submit_object(cell)

    def flatten_record(self, record, meta_source, local_assets):
        if '__mediachain_object__' not in record:
            raise ValueError('value is not a mediachain object')

        assets = {k: v for k, v in record.iteritems()
                  if is_asset(v)}

        objects = {k: v for k, v in record.iteritems()
                   if is_mediachain_object(v)}

        for k, a in assets.iteritems():
            a = local_assets.get(k, a)
            ref = self.store_asset(a)
            if ref is None:
                print('Unable to store asset with key {}, removing'.format(k))
                del record[k]
            else:
                record[k] = ref

        for k, o in objects.iteritems():
            o = self.flatten_record(o, meta_source, local_assets)
            ref = self.submit_object(o)
            record[k] = ref

        del record['__mediachain_object__']
        record['metaSource'] = meta_source
        return record

    def store_raw(self, raw_content):
        ref = self.datastore.put(raw_content)
        return string_ref_to_map(ref)

    def store_asset(self, asset):
        data = load_asset(asset, download_remote=self.download_remote_assets)
        if data is None:
            return None
        return string_ref_to_map(self.datastore.put(data))

    def submit_object(self, obj):
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

