import cbor
import base58
from grpc.beta import implementations
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError
from mediachain.proto import Datastore_pb2  # pylint: disable=no-name-in-module
from mediachain.proto import Types_pb2  # pylint: disable=no-name-in-module
from mediachain.datastore.data_objects import MultihashReference


TIMEOUT_SECS = 120


class RpcDatastore(object):
    def __init__(self, host, port):
        channel = implementations.insecure_channel(host, port)
        self.rpc = Datastore_pb2.beta_create_DatastoreService_stub(channel)

    def put(self, data_object, timeout=TIMEOUT_SECS):
        byte_string = object_bytes(data_object)
        req = Datastore_pb2.DataObject(bytes=byte_string)
        ref = self.rpc.put(req, timeout)
        return MultihashReference.from_base58(ref.reference)

    def get(self, ref, timeout=TIMEOUT_SECS):
        ref = rpc_ref(ref)
        try:
            obj_bytes = self.rpc.get(ref, timeout).data
        except AbortionError as e:
            if e.code == StatusCode.NOT_FOUND:
                return None
            raise
        try:
            return cbor.loads(obj_bytes)
        except ValueError:
            return obj_bytes


def rpc_ref(ref):
    ref_str = ref
    try:
        ref_str = ref.multihash_base58()
    except AttributeError:
        pass
    try:
        ref_str = ref.reference
    except AttributeError:
        pass
    try:
        ref_str = base58.b58encode(ref['@link'])
    except (KeyError, ValueError, TypeError):
        pass
    return Types_pb2.MultihashReference(reference=ref_str)


def object_bytes(obj):
    try:
        return obj.to_cbor_bytes()
    except AttributeError:
        pass

    if isinstance(object, dict):
        try:
            return cbor.dumps(obj)
        except ValueError:
            pass
    return obj
