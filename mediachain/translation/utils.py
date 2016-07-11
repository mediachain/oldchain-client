import json
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters.terminal import TerminalFormatter


MEDIACHAIN_OBJECT_TAG = '__mediachain_object__'
MEDIACHAIN_ASSET_TAG = '__mediachain_asset__'


def is_tagged_dict(tag, value):
    if not isinstance(value, dict):
        return False
    return tag in value


def is_asset(value):
    return is_tagged_dict(MEDIACHAIN_ASSET_TAG, value)


def is_mediachain_object(value):
    return is_tagged_dict(MEDIACHAIN_OBJECT_TAG, value)


def is_canonical(obj):
    return obj['type'] == 'artefact' or obj['type'] == 'entity'



def stringify_refs(obj):
    res = {}
    for k, v in obj.iteritems():
        if isinstance(v, dict):
            v = stringify_refs(v)
        if k == u'@link':
            v = base58.b58encode(v)
        res[k] = v
    return res


def dump(obj):
    j = json.dumps(stringify_refs(obj), indent=2)
    print highlight(j, JsonLexer(), TerminalFormatter())