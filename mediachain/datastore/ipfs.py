import ipfsApi
from requests.exceptions import ConnectionError
from tempfile import NamedTemporaryFile
from mediachain.datastore.utils import multihash_ref, object_for_bytes, \
    bytes_for_object

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


TIMEOUT_SECS = 120


class IpfsDatastore(object):
    def __init__(self, host='localhost', port=5001):
        self.client = ipfsApi.Client(host, port)
        try:
            self.client.id()
        except ConnectionError:
            raise Exception(
                'Unable to connect to ipfs API at {}:{} \n'
                'For ipfs installation instructions see '
                'https://ipfs.io/docs/install'.format(host, port)
            )

    def put(self, data_object, timeout=TIMEOUT_SECS):
        content = bytes_for_object(data_object)

        with NamedTemporaryFile() as f:
            f.write(content)
            f.flush()
            result = self.client.add(f.name, timeout=timeout)

        if isinstance(result, basestring):
            return result

        # when adding a file, we only want the entry pointing to the file's
        # contents, not the entries for the intermediate directories.
        # if the result is a list, the first entry will be, e.g:
        # {u'Bytes': 22, u'Name': u'/tmp/foo/bar/tmp7Hobfu'}
        # followed by entries for the file, plus entries for '/tmp', '/tmp/foo',
        # etc.
        # This handles legacy and latest version of ipfs-api repository
        header = result.pop(0) if type(result) is list else result
        if 'Hash' in header:
            return header['Hash']

        name = header['Name']
        hashes = [h['Hash'] for h in result if h['Name'] == name]
        return multihash_ref(hashes[0])

    def get(self, ref, timeout=TIMEOUT_SECS, retry_if_missing=False):
        stream = self.open(ref, timeout=timeout)
        byte_string = stream.read()
        return object_for_bytes(byte_string)

    def open(self, ref, timeout=TIMEOUT_SECS):
        """
        Return a file-like object with the binary representation of the
        object identified by the given ref
        :param ref: A multihash reference to a binary object in the datastore
        :param timeout: Seconds to wait for ipfs to return the object
        :return: A file-like object with the data returned
        """
        stream = self.client.cat(str(ref), stream=True, timeout=timeout)
        return stream
