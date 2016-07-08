import rocksdb
import cbor
from multihash import encode as multihash_encode, SHA2_256
from base58 import b58encode


class RocksDatastore(object):
    def __init__(self, db_path):
        opts = rocksdb.Options(create_if_missing=True)
        self.db = rocksdb.DB(db_path, opts)

    def get(self, ref):
        try:
            ref = ref.multihash_base58()
        except AttributeError:
            pass

        ref = bytes(ref)
        byte_string = self.db.get(ref)
        try:
            return cbor.loads(byte_string)
        except ValueError:
            return byte_string

    def put(self, data_object, ref=None):
        try:
            ref = ref.multihash_base58()
        except AttributeError:
            pass

        if ref is None:
            try:
                ref = data_object.multihash_base58()
            except AttributeError:
                hash_bytes = multihash_encode(data_object, SHA2_256)
                ref = b58encode(bytes(hash_bytes))

        try:
            content = data_object.to_cbor_bytes()
        except AttributeError:
            content = data_object

        ref = bytes(ref)
        content = bytes(content)
        self.db.put(ref, content)
        return ref
