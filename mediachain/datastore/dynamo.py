import boto3
import cbor
import copy
from base58 import b58encode
from boto3.dynamodb.types import Binary
from multihash import encode as multihash_encode, SHA2_256

from mediachain.datastore.data_objects import Record, MultihashReference

AWS_CONFIG={
    'mediachain_table_name': 'Mediachain'
}
__DB_INSTANCE=None

def set_aws_config(cfg):
    global AWS_CONFIG
    AWS_CONFIG = cfg

def get_db():
    global __DB_INSTANCE

    if __DB_INSTANCE is None:
        __DB_INSTANCE = DynamoDatastore()

    return __DB_INSTANCE

class DynamoDatastore(object):
    def __init__(self, **kwargs):
        cfg = copy.deepcopy(AWS_CONFIG)
        cfg.update(kwargs)
        self.mediachain_table_name = cfg.pop('mediachain_table_name')
        self.dynamo = boto3.resource('dynamodb', **cfg)

    def get_table(self, name):
        return self.dynamo.Table(name)

    def mediachain_table(self):
        return self.get_table(self.mediachain_table_name)

    def put(self, data_object):
        # TODO: implement chunked writes for large objects
        table = self.mediachain_table()

        if isinstance(data_object, Record):
            key = data_object.multihash_base58()
            content = data_object.to_cbor_bytes()
        else:
            hash_bytes = multihash_encode(data_object, SHA2_256)
            key = b58encode(str(hash_bytes))
            content = data_object

        table.put_item(Item={'multihash': key,
                             'data': Binary(content)})
        return key

    def get(self, ref):
        table = self.mediachain_table()

        if isinstance(ref, MultihashReference):
            ref_multihash = ref.multihash_base58()
        else:
            ref_multihash = ref

        item = table.get_item(Key={'multihash': ref_multihash})
        if item is None:
            raise KeyError('Could not find key {} in Dynamo'.format(ref))
        byte_string = bytes(item['Item']['data'])
        return cbor.loads(byte_string)

