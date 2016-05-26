import boto3
import cbor
from grpc.beta import implementations
from mediachain.proto import Transactor_pb2

TIMEOUT_SECS=120

def get_client(host, port):
    channel = implementations.insecure_channel(host, port)
    return Transactor_pb2.beta_create_TransactorService_stub(channel)

def get_chain_head(ns):
    client = get_client(ns.host, ns.port)
    request = Transactor_pb2.MultihashReference(reference=ns.object_id)
    chain_head = client.FetchObjectChainHead(request, TIMEOUT_SECS)
    return get_object_chain_from_head(chain_head.reference)

def get_table(name):
    dynamo = boto3.resource('dynamo')
    return dynamo.Table(name)

def get_object(reference):
    table = get_table('mediachain')
    byte_string = table.get_item(Key={'multihash': reference})
    if byte_string is None:
        raise KeyError('Could not find key <%s> in Dyanmo'.format(reference))
    return cbor.loads(byte_string)

def get_object_chain_from_head(reference, acc=[]):
    if reference is None:
        return acc

    obj = get_object(reference)
    next_ref = obj.get('chain')

    return get_object_chain(next_ref, acc + [obj])
