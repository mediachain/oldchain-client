import boto3
from boto3.dynamodb.types import Binary
import cbor
from mediachain.data_objects import Record, MultihashReference


class DynamoDatastore(object):
    def __init__(self, **kwargs):
        self.dynamo = boto3.resource('dynamodb', **kwargs)

    def get_table(self, name):
        return self.dynamo.Table(name)

    def mediachain_table(self):
        return self.get_table('mediachain')

    def put(self, data_object):
        # TODO: implement chunked writes for large objects
        assert(isinstance(data_object, Record))
        table = self.mediachain_table()
        key = data_object.multihash_base58()
        byte_string = data_object.to_cbor_bytes()
        table.put_item(Item={'multihash': key,
                             'data': Binary(byte_string)})
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

