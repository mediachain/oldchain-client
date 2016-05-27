import boto3
from boto3.dynamodb.types import Binary
import cbor
from mediachain.data_objects import Record, MultihashReference
from multihash import encode as multihash_encode, SHA2_256
from base58 import b58encode


class DynamoDatastore(object):
    def __init__(self, mediachain_table_name='mediachain', **kwargs):
        self.mediachain_table_name = mediachain_table_name
        self.dynamo = boto3.resource('dynamodb', **kwargs)

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

