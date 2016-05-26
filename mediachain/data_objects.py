import cbor


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

    def to_cbor_bytes(self):
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

        cbor.dumps(m, sort_keys=True)


class Artefact(Record):
    @staticmethod
    def mediachain_type():
        return "artefact"


class Entity(Record):
    @staticmethod
    def mediachain_type():
        return "entity"


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
        self.ref = ref
        self.chain = chain

