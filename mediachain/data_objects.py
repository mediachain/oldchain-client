import cbor
from multihash import SHA2_256, encode as multihash_encode
import pprint
import hashlib


class Record(object):
    meta = dict()

    @staticmethod
    def mediachain_type():
        raise Exception("mediachain_type must be defined in subclasses")

    @staticmethod
    def required_fields():
        return ["meta"]

    @staticmethod
    def optional_fields():
        return []

    def __init__(self, meta):
        self.meta = meta

    def __str__(self):
        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(self.to_map())

    def to_map(self):
        m = {"type": self.mediachain_type()}

        for f in self.required_fields():
            val = self.__dict__[f]
            if val is None:
                raise Exception("Required field " + f +
                                " is missing, cannot serialize")
            m[f] = val

        for f in self.optional_fields():
            val = self.__dict__[f]
            if val:
                m[f] = val
        return m

    def to_cbor_bytes(self):
        return cbor.dumps(self.to_map(), sort_keys=True)

    def multihash(self):
        return multihash_for_bytes(self.to_cbor_bytes())


class Artefact(Record):
    @staticmethod
    def mediachain_type():
        return "artefact"


class Entity(Record):
    @staticmethod
    def mediachain_type():
        return "entity"


class MultihashReference(object):
    multihash = None

    def __init__(self, multihash):
        self.multihash = multihash

    def to_map(self):
        return {'@link': self.multihash}

    def to_cbor_bytes(self):
        return cbor.dumps(self.to_map(), sort_keys=True)


class ChainCell(Record):
    ref = None
    chain = None

    @staticmethod
    def required_fields():
        return super(ChainCell, ChainCell).required_fields() + ["ref"]

    @staticmethod
    def optional_fields():
        return super(ChainCell, ChainCell).optional_fields() + ["chain"]

    def __init__(self, meta, ref, chain=None):
        super(ChainCell, self).__init__(meta)
        self.ref = canonical_reference(ref)

        self.chain = chain


class ArtefactCreationCell(ChainCell):
    entity = None

    @staticmethod
    def mediachain_type():
        return "artefactCreatedBy"

    @staticmethod
    def required_fields():
        super_fields = super(ArtefactCreationCell, ArtefactCreationCell)\
            .required_fields()
        return super_fields + ["entity"]

    def __init__(self, meta, ref, entity, chain=None):
        super(ArtefactCreationCell, self).__init__(meta, ref, chain)
        self.entity = canonical_reference(entity)


# Helpers
def multihash_for_bytes(content_bytes):
    h = hashlib.sha256()
    h.update(content_bytes)
    return multihash_encode(h.digest(), SHA2_256)


def canonical_reference(ref_or_record):
    if isinstance(ref_or_record, MultihashReference):
        return ref_or_record

    if isinstance(ref_or_record, Entity) or isinstance(ref_or_record, Artefact):
        return MultihashReference(ref_or_record.multihash())

    raise Exception(
        'Expected Entity, Artefact, or MultihashReference, got {}'
        .format(type(ref_or_record))
    )
