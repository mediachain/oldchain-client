import cbor
from mediachain.reader import dynamo
from mediachain.reader.transactor import get_chain_head
import copy

def get_object(host, port, object_id):
    base = dynamo.get_object(object_id)
    head = get_chain_head(host, port, object_id)
    chain = get_object_chain(head)
    obj = reduce(chain_folder, chain, base)

    try:
        entity_id = obj['entity']
        obj['entity'] = get_object(host, port, entity_id)
    except KeyError as e:
        pass

    print(obj)

def apply_update_cell(acc, cell):
    result = copy.deepcopy(acc)
    cell = copy.deepcopy(cell)

    for attr in ['type', 'artefact', 'entity']:
        del cell[attr]

    for k, v in cell.iteritems():
        result[k] = v

    return result

def apply_creation_cell(acc, update):
    result = copy.deepcopy(acc)

    result['entity'] = update['entity']
    return result

def chain_folder(acc, x):
    cell_type = x.get('type')

    fn_map = {
        'artefactCreationCell': apply_creation_cell,
        'artefactUpdateCell': apply_update_cell,
        'entityUpdateCell': apply_update_cell
    }

    try:
        # apply a transform if we have one
        return fn_map[cell_type](acc, x)
    except KeyError as e:
        # otherwise, skip
        return acc

def get_object_chain(reference, acc=[]):
    if reference is None:
        return acc

    obj = dynamo.get_object(reference)
    next_ref = obj.get('chain')

    return get_object_chain(next_ref, acc + [obj])
