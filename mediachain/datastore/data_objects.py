import cbor
from multihash import SHA2_256, encode as multihash_encode
from base58 import b58encode, b58decode
import pprint


class Record(object):
    meta = dict()
    metaSource = None

    @staticmethod
    def mediachain_type():
        raise Exception("mediachain_type must be defined in subclasses")

    @staticmethod
    def required_fields():
        return [u'meta']

    @staticmethod
    def optional_fields():
        return [u'metaSource']

    def __init__(self, meta, meta_source=None):
        self.meta = meta

        if isinstance(meta_source, basestring):
            self.metaSource = MultihashReference.from_base58(meta_source)
        else:
            self.metaSource = meta_source

    def __str__(self):
        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(self.to_map())

    def to_map(self):
        m = {u'type': self.mediachain_type()}

        def add_to_map(k, v):
            if isinstance(v, MultihashReference):
                m[k] = v.to_map()
            else:
                m[k] = v

        for f in self.required_fields():
            if f not in self.__dict__:
                raise Exception("Required field " + f +
                                " is missing, cannot serialize")
            add_to_map(f, self.__dict__[f])

        for f in self.optional_fields():
            if f in self.__dict__:
                add_to_map(f, self.__dict__[f])

        return m

    def to_cbor_bytes(self):
        return cbor.dumps(self.to_map(), sort_keys=True)

    def multihash(self):
        return multihash_encode(self.to_cbor_bytes(), SHA2_256)

    def multihash_base58(self):
        return b58encode(str(self.multihash()))


class Artefact(Record):
    @staticmethod
    def mediachain_type():
        return u'artefact'


class Entity(Record):
    @staticmethod
    def mediachain_type():
        return u'entity'


class MultihashReference(object):
    multihash = None

    @classmethod
    def from_base58(cls, base58str):
        byte_string = b58decode(base58str)
        return cls(byte_string)

    def __init__(self, multihash):
        self.multihash = multihash

    def __str__(self):
        return u'MultihashReference: ' + self.multihash_base58()

    def to_map(self):
        return {u'@link': self.multihash}

    def to_cbor_bytes(self):
        return cbor.dumps(self.to_map(), sort_keys=True)

    def multihash_base58(self):
        return b58encode(str(self.multihash))


class ChainCell(Record):
    ref = None
    chain = None

    @staticmethod
    def required_fields():
        return super(ChainCell, ChainCell).required_fields() + [u'ref']

    @staticmethod
    def optional_fields():
        return super(ChainCell, ChainCell).optional_fields() + [u'chain']

    def __init__(self, meta, ref, chain=None, meta_source=None):
        super(ChainCell, self).__init__(meta, meta_source=meta_source)
        self.ref = ref.to_map()
        if chain is not None:
            self.chain = chain.to_map()


class ArtefactCreationCell(ChainCell):
    entity = None

    @staticmethod
    def mediachain_type():
        return u'artefactCreatedBy'

    @staticmethod
    def required_fields():
        super_fields = super(ArtefactCreationCell, ArtefactCreationCell)\
            .required_fields()
        return super_fields + [u'entity']

    def __init__(self, meta, ref, entity, chain=None, meta_source=None):
        super(ArtefactCreationCell, self).__init__(
            meta, ref, chain, meta_source=meta_source)
        self.entity = entity.to_map()


