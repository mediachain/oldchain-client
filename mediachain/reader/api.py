from mediachain.datastore import get_db, get_raw_datastore
from mediachain.ingestion.asset_loader import make_jpeg_data_uri
import copy
import base58
import json
from pygments import highlight
from utils import dump

def get_and_print_object(transactor, object_id):
    obj = get_object(transactor, object_id, fetch_images=False)
    dump(obj)


def get_object(transactor, object_id, fetch_images=True):
    db = get_db()
    base = db.get(object_id)
    head = transactor.get_chain_head(object_id)
    chain = get_object_chain(head, [])
    obj = reduce(chain_folder, chain, base)

    try:
        entity_id = obj['entity']
        obj['entity'] = get_object(transactor, entity_id, fetch_images)
    except KeyError as e:
        pass

    if fetch_images and obj.get('type') == 'artefact':
        return fetch_thumbnails(obj)
    return obj


def fetch_thumbnails(obj):
    def with_fallback():
        o = copy.deepcopy(obj)
        if 'meta' not in o:
            o['meta'] = {}
        if 'data' not in o['meta']:
            o['meta']['data'] = {}

        o['meta']['data']['thumbnail_base64'] = 'NO_IMAGE'
        return o

    try:
        thumb_ref_bytes = obj['meta']['data']['thumbnail']['@link']
        thumb_ref = base58.b58encode(thumb_ref_bytes)
        db = get_raw_datastore()
        thumb = db.get(thumb_ref)
    except (ValueError, LookupError):
        return with_fallback()

    with open('/tmp/thumbnail.jpg', 'wb') as f:
        f.write(thumb)

    with_thumb = copy.deepcopy(obj)
    with_thumb['meta']['data']['thumbnail_base64'] = make_jpeg_data_uri(thumb)
    return with_thumb


def apply_update_cell(acc, cell):
    result = copy.deepcopy(acc)
    cell = copy.deepcopy(cell)

    for k, v in cell['meta'].iteritems():
        result['meta'][k] = v

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
    obj = db.get(reference)

    try:
        next_ref = obj['chain']['@link']
        next_ref = base58.b58encode(next_ref)
    except KeyError as e:
        next_ref = None

    return get_object_chain(next_ref, acc + [obj])
