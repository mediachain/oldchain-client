import cbor
from multihash import SHA2_256, encode as multihash_encode
from base58 import b58encode, b58decode


class MultihashReference(object):
    multihash = None

    @classmethod
    def for_content(cls, content_bytes):
        content_hash = multihash_encode(bytes(content_bytes), SHA2_256)
        return cls(content_hash)

    @classmethod
    def from_base58(cls, base58str):
        byte_string = b58decode(base58str)
        return cls(byte_string)

    def __init__(self, multihash):
        self.multihash = bytes(multihash)

    def __repr__(self):
        return u'MultihashReference: ' + self.multihash_base58()

    def __str__(self):
        return self.multihash_base58()

    def to_map(self):
        return {u'@link': self.multihash}

    def to_cbor_bytes(self):
        return cbor.dumps(self.to_map(), sort_keys=True)

    def multihash_base58(self):
        return b58encode(self.multihash)
