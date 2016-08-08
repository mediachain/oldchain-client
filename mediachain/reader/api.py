from mediachain.datastore import get_db, get_raw_datastore
from mediachain.datastore.utils import multihash_ref
import copy
import base58
import requests
import contextlib
from io import BytesIO
from utils import dump

def get_and_print_object(transactor, object_id):
    obj = get_object(transactor, object_id)
    dump(obj)


def get_object(transactor, object_id):
    db = get_db()
    base = db.get(object_id, retry_if_missing=True)
    head = transactor.get_chain_head(object_id)
    chain = get_object_chain(head, [])
    obj = reduce(chain_folder, chain, base)

    try:
        entity_id = obj['entity']
        obj['entity'] = get_object(transactor, entity_id)
    except (KeyError, TypeError):
        pass

    return obj


def open_binary_asset(asset, timeout=10):
    if not asset.get('binary_asset', False):
        return None

    # try to load from ipfs if `link` is present
    try:
        ref = multihash_ref(asset['link'])
        db = get_raw_datastore()
        return contextlib.closing(db.open(ref, timeout=timeout))
    except (LookupError, ValueError, requests.exceptions.RequestException):
        pass

    # If not, try to get the http url if present
    try:
        uri = asset['uri']
        resp = requests.get(uri, timeout=timeout)
        f = BytesIO(resp.content)
        return contextlib.closing(f)
    except (LookupError, requests.exceptions.RequestException):
        pass

    # return None if no ipfs link or uri, or if there's a download error
    return None


def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

def apply_update_cell(acc, cell):
    result = copy.deepcopy(acc)
    cell = copy.deepcopy(cell)

    merge(result['meta'], cell['meta'])

    return result

def apply_creation_cell(acc, update):
    result = copy.deepcopy(acc)

    try:
        result['entity'] = base58.b58encode(update['entity']['@link'])
    except KeyError as e:
        pass

    return result

def chain_folder(acc, x):
    cell_type = x.get('type')

    fn_map = {
        u'artefactCreatedBy': apply_creation_cell,
        u'artefactUpdate': apply_update_cell,
        u'entityUpdate': apply_update_cell
    }

    try:
        # apply a transform if we have one
        return fn_map[cell_type](acc, x)
    except KeyError as e:
        # otherwise, skip
        return acc

def get_object_chain(reference, acc):
    if reference is None:
        return acc

    db = get_db()
    obj = db.get(reference, retry_if_missing=True)

    try:
        next_ref = obj['chain']['@link']
        next_ref = base58.b58encode(next_ref)
    except KeyError as e:
        next_ref = None

    return get_object_chain(next_ref, [obj] + acc)
