import boto3
import cbor
from grpc.beta import implementations
from mediachain import Transactor_pb2
from collections import namedtuple

Config = namedtuple('Config', ['host', 'port'])

def get_client(host, port):
    channel = implementations.insecure_channel(host, port)
    return Transactor_pb2.beta_create_TransactorService_stub(channel)

def get_chain_head(config, object_id):
    client = get_client(config.host, config.port)
    request = Transactor_pb2.MultihashReference(reference=object_id)
    chain_head = client.FetchObjectChainHead(request)
    return get_object_chain(chain_head.reference)

def get_table(name):
    dynamo = boto3.resource('dynamo')
    return dynamo.Table(name)

def get_object_chain(reference):
    # wip
    table = get_table('mediachain')
    byte_string = table.get_item(Key={'multihash': reference})
    return cbor.loads(byte_string)
