from __future__ import unicode_literals
import rocksdb
import tempfile
import shutil
from mediachain.datastore import get_db
from mediachain.datastore.utils import ref_base58, bytes_for_object, \
    object_for_bytes
from mediachain.datastore.data_objects import MultihashReference

class BlockCache(object):
    """
    A read-through cache for mediachain journal blocks.
    When a block is read, it gets written to a local RocksDB cache.
    """
    def __init__(self, datastore=None, cache_path=None):
        if datastore is None:
            datastore = get_db()
        if cache_path is None:
            cache_path = tempfile.mktemp('-mchain-cache.rocksdb')
            self._delete_cache_on_cleanup = True

        self.datastore = datastore
        self.cache_path = cache_path
        opts = rocksdb.Options(create_if_missing=True)
        self.cache_db = rocksdb.DB(cache_path, opts)

    def __del__(self):
        self.cache_db = None
        if getattr(self, '_delete_cache_on_cleanup'):
            shutil.rmtree(self.cache_path)

    def put(self, block, ref=None):
        block_bytes = bytes_for_object(block)
        if ref is None:
            ref = MultihashReference.for_content(block_bytes)
        ref = ref_base58(ref)

        self.cache_db.put(bytes(ref), bytes(block_bytes))

    def get(self, block_ref):
        block_ref = bytes(ref_base58(block_ref))
        cached = self.cache_db.get(block_ref)
        if cached is not None:
            return object_for_bytes(cached)

        block = self.datastore.get(block_ref)
        self.put(block, block_ref)
        return object_for_bytes(block)
