import cbor
from mediachain.reader import dynamo
from mediachain.reader.transactor import get_chain_head
import copy
import base58

def get_object(host, port, object_id, aws_config):
    base = dynamo.get_object(object_id, aws_config)
    head = get_chain_head(host, port, object_id)
    chain = get_object_chain(head, [], aws_config)
    obj = reduce(chain_folder, chain, base)

    try:
        entity_id = obj['entity']
        obj['entity'] = get_object(host, port, entity_id, aws_config)
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
        result['entity'] = update['entity']
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

def get_object_chain(reference, acc, aws_config):
    if reference is None:
        return acc

    obj = dynamo.get_object(reference, aws_config)

    try:
        next_ref = obj['chain']['@link']
        next_ref = base58.b58encode(next_ref)
    except KeyError as e:
        next_ref = None

    return get_object_chain(next_ref, acc + [obj], aws_config)
