from grpc.beta import implementations
from mediachain.proto import Transactor_pb2
from mediachain.data_objects import Artefact, Entity, ChainCell, \
    MultihashReference

TIMEOUT_SECS = 120


def assert_canonical(record):
    assert (isinstance(record, Artefact) or isinstance(record, Entity)), \
           "Expected artefact or entity, got " + str(type(record))


def assert_chaincell(cell):
    assert isinstance(cell, ChainCell), \
           "Expected chain cell, got " + str(type(cell))


class TransactorClient(object):

    def __init__(self, host, port):
        channel = implementations.insecure_channel(host, port)
        self.client = Transactor_pb2.beta_create_TransactorService_stub(channel)

    def insert(self, record):
        assert_canonical(record)
        req = Transactor_pb2.InsertRequest(canonicalCbor=record.to_cbor_bytes())
        ref = self.client.InsertCanonicalRecord(req, TIMEOUT_SECS)
        return MultihashReference.from_base58(ref.reference)

    def update(self, cell):
        assert_chaincell(cell)
        req = Transactor_pb2.UpdateRequest(chainCellCbor=cell.to_cbor_bytes())
        ref = self.client.UpdateCanonicalRecord(req, TIMEOUT_SECS)
        return MultihashReference.from_base58(ref.reference)
