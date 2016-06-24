import functools
from grpc.beta import implementations
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError
from mediachain.proto import Datastore_pb2  # pylint: disable=no-name-in-module
from mediachain.datastore.utils import rpc_ref, multihash_ref, \
    bytes_for_object, object_for_bytes
from mediachain.rpc.utils import with_retry

TIMEOUT_SECS = 120

__RPC_STORE_CONFIG = None


def set_rpc_datastore_config(cfg):
    global __RPC_STORE_CONFIG
    __RPC_STORE_CONFIG = cfg


def get_rpc_datastore_config():
    global __RPC_STORE_CONFIG
    return __RPC_STORE_CONFIG


def get_db():
    cfg = get_rpc_datastore_config()
    try:
        host = cfg['host']
        port = int(cfg['port'])
    except (TypeError, LookupError, ValueError):
        raise RuntimeError('No RPC datastore configuration has been set. ' +
                           'please call set_rpc_datastore_config before ' +
                           'calling get_db')

    return RpcDatastore(host, port)


class RpcDatastore(object):
    def __init__(self, host, port):
        channel = implementations.insecure_channel(host, port)
        self.rpc = Datastore_pb2.beta_create_DatastoreService_stub(channel)

    def put(self, data_object, timeout=TIMEOUT_SECS):
        put_with_retry = functools.partial(with_retry, self.rpc.put)
        byte_string = bytes_for_object(data_object)
        req = Datastore_pb2.DataObject(data=byte_string)
        ref = put_with_retry(req, timeout)
        return multihash_ref(ref)

    def get(self, ref, timeout=TIMEOUT_SECS):
        ref = rpc_ref(ref)
        get_with_retry = functools.partial(with_retry, self.rpc.get)
        try:
            obj_bytes = get_with_retry(ref, timeout).data
        except AbortionError as e:
            if e.code == StatusCode.NOT_FOUND:
                return None
            raise
        return object_for_bytes(obj_bytes)
