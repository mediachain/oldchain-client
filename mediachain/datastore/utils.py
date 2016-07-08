import base58
import cbor
from mediachain.proto import Types_pb2  # pylint: disable=no-name-in-module
from mediachain.datastore.data_objects import MultihashReference


def multihash_ref(ref):
    if isinstance(ref, MultihashReference):
        return ref

    try:
        ref = ref.reference
    except AttributeError:
        pass
    try:
        ref = ref['@link']
    except (TypeError, KeyError):
        pass

    try:
        ref = base58.b58decode(ref)
    except ValueError:
        pass
    return MultihashReference(multihash=ref)


def rpc_ref(ref):
    return Types_pb2.MultihashReference(reference=ref_base58(ref))


def ref_base58(ref):
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
    return ref_str


def bytes_for_object(obj):
    try:
        return obj.to_cbor_bytes()
    except AttributeError:
        pass

    if isinstance(obj, dict):
        try:
            return cbor.dumps(obj)
        except ValueError:
            pass
    return obj


def object_for_bytes(obj_bytes):
    try:
        return cbor.loads(obj_bytes)
    except ValueError:
        return obj_bytes
