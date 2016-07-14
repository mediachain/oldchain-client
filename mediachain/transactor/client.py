import cbor
from grpc.beta import implementations
from mediachain.rpc.utils import with_retry
from mediachain.datastore.data_objects import MultihashReference
from mediachain.proto import Transactor_pb2  # pylint: disable=no-name-in-module
from mediachain.proto import Types_pb2  # pylint: disable=no-name-in-module
from mediachain.transactor.blockchain_follower import BlockchainFollower
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
        ref = with_retry(self.client.InsertCanonical, req, timeout)
        return MultihashReference.from_base58(ref.reference)

    def get_chain_head(self, ref, timeout=TIMEOUT_SECS):
        req = Types_pb2.MultihashReference(reference=ref)
        response = with_retry(self.client.LookupChain, req, timeout)
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
        ref = with_retry(self.client.UpdateChain, req, timeout)
        return MultihashReference.from_base58(ref.reference)

    def journal_stream(self, catchup=True, timeout=None):
        """
        A stream of journal events from the mediachain transactor network.
        If `catchup` is True (the default), will fetch the entire history
        of the blockchain and play back all historical events, followed by
        any incoming events.

        If `catchup` is False, only future events will be delivered.

        Defaults to an infinite stream with no timeout; you can force the
        stream to expire by passing in a `timeout` in seconds.

        IMPORTANT:
        You must close the stream by calling the `.cancel()` method on the
        returned `BlockchainFollower` object before exiting the process,
        otherwise the gRPC connection will keep the process alive indefinitely.

        To make cleanup automatic use with/as:
            with client.journal_stream() as stream:
              for event in stream:
                # handle event...


        :param catchup:
        :param timeout:
        :return:
        """
        req = Transactor_pb2.JournalStreamRequest()
        stream = self.client.JournalStream(req, timeout)
        follower = BlockchainFollower(stream, catchup)
        follower.start()
        return follower


    def canonical_stream(self, timeout=600):
        for event in self.journal_stream(timeout=timeout):
            if event.WhichOneof("event") == "updateChainEvent":
                ref = event.updateChainEvent.canonical.reference
                obj = reader.get_object(self, ref)
                yield obj

