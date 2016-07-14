from __future__ import unicode_literals
import os
from mediachain.datastore import get_db
from mediachain.datastore.utils import ref_base58, bytes_for_object, \
    object_for_bytes
from mediachain.datastore.data_objects import MultihashReference
from mediachain.utils.file import mkdir_p, system_cache_dir


class InMemoryCache(object):
    def __init__(self):
        self.cache = dict()

    def get(self, key):
        return self.cache.get(key, None)

    def put(self, key, value):
        self.cache[key] = value


def open_db(path):
    try:
        import rocksdb
        opts = rocksdb.Options(create_if_missing=True)
        return rocksdb.DB(path, opts)
    except ImportError:
        print('using in-memory blockchain cache. please install '
              'rocksdb to enable persistent cache')
        return InMemoryCache()


__SHARED_BLOCK_CACHE = None


def get_block_cache():
    global __SHARED_BLOCK_CACHE
    if __SHARED_BLOCK_CACHE is None:
        __SHARED_BLOCK_CACHE = BlockCache()
    return __SHARED_BLOCK_CACHE


class BlockCache(object):
    """
    A read-through cache for mediachain journal blocks.
    When a block is read, it gets written to a local RocksDB cache.
    """
    def __init__(self, datastore=None, cache_path=None):
        if datastore is None:
            datastore = get_db()
        if cache_path is None:
            cache_dir = system_cache_dir('io.mediachain')
            mkdir_p(cache_dir)
            cache_path = os.path.join(cache_dir, 'block-cache.db')

        self.datastore = datastore
        self.cache_path = cache_path
        self.cache_db = open_db(cache_path)

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
