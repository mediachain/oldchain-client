import boto3
import cbor
from mediachain.data_objects import Record, MultihashReference


class DynamoDatastore(object):
    def __init__(self):
        self.dynamo = boto3.resource('dynamo')

    def get_table(self, name):
        return self.dynamo.Table(name)

    def mediachain_table(self):
        return self.get_table('mediachain')

    def put(self, data_object):
        # TODO: implement chunked writes for large objects
        assert(isinstance(data_object, Record))
        table = self.mediachain_table()
        multihash = data_object.multihash()
        byte_string = data_object.to_cbor_bytes()
        table.put_item(Item={'multihash': multihash, 'data': byte_string})

    def get(self, ref):
        table = self.mediachain_table()

        if isinstance(ref, MultihashReference):
            ref_multihash = ref.multihash
        else:
            ref_multihash = ref

        byte_string = table.get_item(Key={'multihash': ref_multihash})
        if byte_string is None:
            raise KeyError('Could not find key {} in Dynamo'.format(ref))
        return cbor.loads(byte_string)

