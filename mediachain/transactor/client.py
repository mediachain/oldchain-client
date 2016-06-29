import cbor
from grpc.beta import implementations

from mediachain.datastore.data_objects import MultihashReference
from mediachain.proto import Transactor_pb2  # pylint: disable=no-name-in-module
from mediachain.proto import Types_pb2  # pylint: disable=no-name-in-module
import mediachain.reader.api as reader

TIMEOUT_SECS = 120


class TransactorClient(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        channel = implementations.insecure_channel(host, port)
        self.client = Transactor_pb2.beta_create_TransactorService_stub(channel)

    def insert_canonical(self, record, timeout=TIMEOUT_SECS):
        try:
            cbor_bytes = record.to_cbor_bytes()
        except AttributeError:
            cbor_bytes = cbor.dumps(record)

        req = Transactor_pb2.InsertRequest(canonicalCbor=cbor_bytes)
        ref = self.client.InsertCanonical(req, timeout)
        return MultihashReference.from_base58(ref.reference)

    def get_chain_head(self, ref, timeout=TIMEOUT_SECS):
        req = Types_pb2.MultihashReference(reference=ref)
        response = self.client.LookupChain(req, timeout)
        if response.WhichOneof('reference') == 'chain':
            return MultihashReference.from_base58(
                response.chain.reference
            )
        return None

    def update_chain(self, cell, timeout=TIMEOUT_SECS):
        try:
            cbor_bytes = cell.to_cbor_bytes()
        except AttributeError:
            cbor_bytes = cbor.dumps(cell)

        req = Transactor_pb2.UpdateRequest(chainCellCbor=cbor_bytes)
        ref = self.client.UpdateChain(req, timeout)
        return MultihashReference.from_base58(ref.reference)

    def journal_stream(self, timeout=TIMEOUT_SECS):
        req = Transactor_pb2.JournalStreamRequest()
        return self.client.JournalStream(req, timeout)

    def canonical_stream(self, timeout=TIMEOUT_SECS):
        for event in self.journal_stream(timeout):
            if event.WhichOneof("event") == "updateChainEvent":
                ref = event.updateChainEvent.canonical.reference
                obj = reader.get_object(self, ref)
                yield obj
