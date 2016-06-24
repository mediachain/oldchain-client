
from grpc.beta import implementations
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError
from mediachain.proto import Datastore_pb2  # pylint: disable=no-name-in-module
from mediachain.datastore.utils import rpc_ref, multihash_ref, \
    bytes_for_object, object_for_bytes
from mediachain.rpc.utils import with_retry

TIMEOUT_SECS = 120


class RpcDatastore(object):
    def __init__(self, host, port):
        channel = implementations.insecure_channel(host, port)
        self.rpc = Datastore_pb2.beta_create_DatastoreService_stub(channel)

    def put(self, data_object, timeout=TIMEOUT_SECS):
        put_with_retry = with_retry(self.rpc.put)
        byte_string = bytes_for_object(data_object)
        req = Datastore_pb2.DataObject(data=byte_string)
        ref = put_with_retry(req, timeout)
        return multihash_ref(ref)

    def get(self, ref, timeout=TIMEOUT_SECS):
        ref = rpc_ref(ref)
        try:
            obj_bytes = self.rpc.get(ref, timeout).data
        except AbortionError as e:
            if e.code == StatusCode.NOT_FOUND:
                return None
            raise
        return object_for_bytes(obj_bytes)
