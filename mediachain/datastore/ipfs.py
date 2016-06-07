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

        if isinstance(result, basestring):
            return result

        # when adding a file, we only want the entry pointing to the file's
        # contents, not the entries for the intermediate directories.
        # if the result is a list, the first entry will be, e.g:
        # {u'Bytes': 22, u'Name': u'/tmp/foo/bar/tmp7Hobfu'}
        # followed by entries for the file, plus entries for '/tmp', '/tmp/foo',
        # etc.
        header = result.pop(0)
        if 'Hash' in header:
            return header['Hash']

        name = header['Name']
        hashes = [h['Hash'] for h in result if h['Name'] == name]
        return hashes[0]

    def get(self, ref):
        if isinstance(ref, MultihashReference):
            ref_multihash = ref.multihash_base58()
        else:
            ref_multihash = ref

        byte_string = self.client.object_data(ref_multihash)
        return cbor.loads(byte_string)
