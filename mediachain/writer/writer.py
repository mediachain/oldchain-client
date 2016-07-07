from __future__ import unicode_literals
from __future__ import print_function

from copy import deepcopy
import re
from mediachain.ingestion.asset_loader import load_asset, process_asset
from mediachain.translation.utils import is_asset, is_canonical, \
    is_mediachain_object
from mediachain.datastore import get_db, get_raw_datastore
from grpc.framework.interfaces.face.face import AbortionError
from mediachain.datastore.utils import multihash_ref
import sys
import traceback


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


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
            try:
                refs = self.submit_translator_output(translator_id, translated,
                                                     raw, local_assets)
                yield refs
            except AbortionError:
                for line in traceback.format_exception(*sys.exc_info()):
                    print_err(line.rstrip('\n'))

    def submit_translator_output(self,
                                 translator_id,
                                 translated,
                                 raw_content,
                                 local_assets):
        meta_source = multihash_ref(self.datastore.put(raw_content))

        raw_ref = self.store_raw(raw_content)

        common_meta = {'translator': translator_id}
        canonical_meta = common_meta.copy()
        canonical_meta.update({'raw_ref': raw_ref.to_map()})

        canonical = translated['canonical']
        canonical = self.flatten_record(canonical, canonical_meta,
                                        local_assets, meta_source=meta_source)
        canonical_ref = self.submit_object(canonical)

        chain = translated.get('chain', [])
        chain_refs = []
        for cell in chain:
            cell = self.flatten_record(cell, common_meta, local_assets)
            cell['ref'] = canonical_ref.to_map()
            chain_ref = self.submit_object(cell)
            chain_refs += chain_ref.multihash_base58()
        return {
            'canonical': canonical_ref.multihash_base58(),
            'chain': chain_refs
        }

    def flatten_record(self, record, common_meta, local_assets,
                       meta_source=None):
        record = deepcopy(record)
        assets = {k: v for k, v in record.iteritems()
                  if is_asset(v)}

        for k, a in assets.iteritems():
            local = local_assets.get(k, None)
            ref = self.store_asset(k, local, a)
            if ref is None:
                # print('Unable to store asset with key {}, removing'.format(k))
                del record[k]
            else:
                record[k] = ref.to_map()

        objects = {k: v for k, v in record.iteritems()
                   if isinstance(v, dict)}

        for k, o in objects.iteritems():
            flat = self.flatten_record(o, common_meta,
                                       meta_source, local_assets)
            if is_mediachain_object(o):
                ref = self.submit_object(flat)
                record[k] = ref.to_map()
            else:
                record[k] = flat

        if is_mediachain_object(record):
            del record['__mediachain_object__']
            try:
                record['metaSource'] = meta_source.to_map()
            except (TypeError, AttributeError):
                pass
            record['meta'].update(common_meta)
        return record

    def store_raw(self, raw_content):
        store = get_raw_datastore()
        ref = store.put(raw_content)
        return multihash_ref(ref)

    def store_asset(self, name, local_asset, remote_asset):
        data = load_asset(local_asset)
        if data is None and self.download_remote_assets:
            data = load_asset(remote_asset)
        if data is None:
            return None
        data = process_asset(name, data)
        return self.store_raw(data)

    def submit_object(self, obj):
        try:
            if is_canonical(obj):
                return self.transactor.insert_canonical(obj)
            else:
                return self.transactor.update_chain(obj)
        except AbortionError as e:
            ref_str = duplicate_canonical_ref(e.details)
            if ref_str is None:
                raise

        return multihash_ref(ref_str)


def merge_meta(obj, meta):
    merged = {'data': {}}
    merged.update(meta)
    if 'meta' in obj:
        merged.update(obj['meta'])
    obj['meta'] = merged


# TODO(yusef): replace string parsing hack with grpc error metadata
# requires support in grpc-java (in master but not yet released)

# this regex will only work for base58 encoded sha2-256 hashes,
# and will break if we ever change the error message :(
duplicate_insert_pattern = re.compile(
    '.*Duplicate Journal Insert.*(Qm[1-9a-km-zA-HJ-NP-Z]{44}).*'
)


def duplicate_canonical_ref(grpc_error_str):
    m = re.match(duplicate_insert_pattern, grpc_error_str)
    if not m:
        return None
    return m.group(1)


