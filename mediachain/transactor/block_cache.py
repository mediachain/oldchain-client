from __future__ import unicode_literals
import cbor
from mediachain.datastore.rocks import RocksDatastore


class BlockCache(object):
    """
    A read-through cache for mediachain journal blocks.
    When a block is read, it gets written to a local RocksDB cache.
    """
    def __init__(self, datastore, cache_file):
        self.datastore = datastore
        self.cache_db = RocksDatastore(cache_file)

    def put(self, block, block_ref):
        try:
            block = block.to_cbor_bytes()
        except AttributeError:
            if isinstance(block, dict):
                try:
                    block = cbor.dumps(block)
                except ValueError:
                    pass

        self.cache_db.put(bytes(block), ref=bytes(block_ref))

    def get(self, block_ref):
        cached = self.cache_db.get(block_ref)
        if cached is not None:
            return cached

        block = self.datastore.get(block_ref)
        self.put(block, block_ref)
        return block
