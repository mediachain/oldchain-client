import cbor
from grpc.beta import implementations
from mediachain.proto import Transactor_pb2

TIMEOUT_SECS=120

def get_client(host, port):
    channel = implementations.insecure_channel(host, port)
    return Transactor_pb2.beta_create_TransactorService_stub(channel)

def get_chain_head(host, port, object_id):
    client = get_client(host, port)
    request = Transactor_pb2.MultihashReference(reference=object_id)
    chain_head = client.FetchObjectChainHead(request, TIMEOUT_SECS)
    return chain_head.reference
