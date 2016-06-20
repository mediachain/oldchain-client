import ipfsApi
import cbor
from tempfile import NamedTemporaryFile
from mediachain.datastore.data_objects import Record, MultihashReference


class IpfsDatastore(object):
    def __init__(self, host='127.0.0.1', port=5001):
        self.client = ipfsApi.Client(host, port)

    def put(self, data_object):
        if isinstance(data_object, Record):
            content = data_object.to_cbor_bytes()
        else:
            content = data_object

        with NamedTemporaryFile() as f:
            f.write(content)
            f.flush()
            result = self.client.add(f.name)
        return result[1][u'Hash']

    def get(self, ref):
        if isinstance(ref, MultihashReference):
            ref_multihash = ref.multihash_base58()
        else:
            ref_multihash = ref

        byte_string = self.client.object_data(ref_multihash)
        return cbor.loads(byte_string)
