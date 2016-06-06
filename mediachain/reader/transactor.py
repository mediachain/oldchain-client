import cbor
from grpc.beta import implementations
from grpc.framework.interfaces.face.face import NetworkError
from mediachain.proto import Transactor_pb2 #pylint: disable=no-name-in-module

TIMEOUT_SECS=120

def get_client(host, port):
    channel = implementations.insecure_channel(host, port)
    return Transactor_pb2.beta_create_TransactorService_stub(channel)

def get_chain_head(host, port, object_id):
    client = get_client(host, port)
    request = Transactor_pb2.MultihashReference(reference=object_id)
    try:
        chain_head = client.LookupChain(request, TIMEOUT_SECS).reference
    except NetworkError as e:
        chain_head = None
    return chain_head
