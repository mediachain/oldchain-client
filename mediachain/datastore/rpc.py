import io
import functools
from grpc.beta import implementations
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError
from mediachain.proto import Datastore_pb2  # pylint: disable=no-name-in-module
from mediachain.datastore.data_objects import MultihashReference
from mediachain.datastore.utils import rpc_ref, multihash_ref, \
    bytes_for_object, object_for_bytes
from mediachain.rpc.utils import with_retry

TIMEOUT_SECS = 120

__RPC_STORE_CONFIG = None
__RPC_STORE_INSTANCE = None


def set_rpc_datastore_config(cfg):
    global __RPC_STORE_CONFIG
    __RPC_STORE_CONFIG = cfg


def get_rpc_datastore_config():
    global __RPC_STORE_CONFIG
    return __RPC_STORE_CONFIG


def get_db():
    global __RPC_STORE_INSTANCE
    if __RPC_STORE_INSTANCE is not None:
        return __RPC_STORE_INSTANCE

    cfg = get_rpc_datastore_config()
    try:
        host = cfg['host']
        port = int(cfg['port'])
    except (TypeError, LookupError, ValueError):
        raise RuntimeError('No RPC datastore configuration has been set. ' +
                           'please call set_rpc_datastore_config before ' +
                           'calling get_db')

    __RPC_STORE_INSTANCE = RpcDatastore(host, port)
    return __RPC_STORE_INSTANCE


def close_db():
    """
    Cleanup the global RpcDatastore instance.
    Must be called before program exit, otherwise the connection will never
    be closed, and grpc will hang indefinitely.
    """
    global __RPC_STORE_INSTANCE
    __RPC_STORE_INSTANCE = None


class RpcDatastore(object):
    def __init__(self, host, port):
        channel = implementations.insecure_channel(host, port)
        self.rpc = Datastore_pb2.beta_create_DatastoreService_stub(channel)
        self.put_cache = set()

    def put(self, data_object, timeout=TIMEOUT_SECS):
        put_with_retry = functools.partial(with_retry, self.rpc.put)
        byte_string = bytes_for_object(data_object)
        content_hash = MultihashReference.for_content(byte_string)
        if content_hash.multihash in self.put_cache:
            return content_hash

        req = Datastore_pb2.DataObject(data=byte_string)
        ref = multihash_ref(put_with_retry(req, timeout))
        self.put_cache.add(ref.multihash)
        return ref

    def get(self, ref, timeout=TIMEOUT_SECS, retry_if_missing=False):
        ref = rpc_ref(ref)
        get_with_retry = functools.partial(with_retry, self.rpc.get)
        extra_retry_status_codes = []
        if retry_if_missing:
            extra_retry_status_codes.append(StatusCode.NOT_FOUND)

        try:
            obj_bytes = get_with_retry(ref, timeout, extra_retry_status_codes=extra_retry_status_codes).data
        except AbortionError as e:
            if e.code == StatusCode.NOT_FOUND:
                return None
            raise
        return object_for_bytes(obj_bytes)

    def open(self, ref, timeout=TIMEOUT_SECS):
        """
        Return a file-like object with the binary representation of the
        object identified by the given ref
        :param ref: A multihash reference to a binary object in the datastore
        :param timeout: Seconds to wait before aborting the RPC call
        :return: A file-like object with the data returned
        :raises: IOError if no object is found for the given key.
        """
        obj_bytes = bytes_for_object(self.get(ref, timeout=timeout))
        if obj_bytes is None:
            raise IOError('Unable to fetch object with key {}'.format(ref))
        return io.BytesIO(obj_bytes)