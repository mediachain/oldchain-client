import ipfsApi
from tempfile import NamedTemporaryFile
from mediachain.datastore.data_objects import MultihashReference
from mediachain.datastore.utils import multihash_ref, object_for_bytes

__IPFS_CONFIG = {'host': 'localhost', 'port': 5001}


def set_ipfs_config(cfg):
    global __IPFS_CONFIG
    __IPFS_CONFIG = cfg


def get_ipfs_config():
    global __IPFS_CONFIG
    return __IPFS_CONFIG


def get_ipfs_datastore():
    global __IPFS_CONFIG
    return IpfsDatastore(**__IPFS_CONFIG)


class IpfsDatastore(object):
    def __init__(self, host='127.0.0.1', port=5001):
        self.client = ipfsApi.Client(host, port)

    def put(self, data_object):
        try:
            content = data_object.to_cbor_bytes()
        except AttributeError:
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
        return multihash_ref(hashes[0])

    def get(self, ref):
        stream = self.client.cat(str(ref), stream=True)
        byte_string = stream.read()
        return object_for_bytes(byte_string)

