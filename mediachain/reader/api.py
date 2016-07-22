from mediachain.datastore import get_db
import copy
import base58
from utils import dump

def get_and_print_object(transactor, object_id):
    obj = get_object(transactor, object_id)
    dump(obj)


def get_object(transactor, object_id):
    db = get_db()
    base = db.get(object_id)
    head = transactor.get_chain_head(object_id)
    chain = get_object_chain(head, [])
    obj = reduce(chain_folder, chain, base)

    try:
        entity_id = obj['entity']
        obj['entity'] = get_object(transactor, entity_id)
    except KeyError as e:
        pass

    return obj


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
