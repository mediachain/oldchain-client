import base58
import json
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters.terminal import TerminalFormatter

def dump(obj):
    j = json.dumps(stringify_refs(obj), indent=2)
    print highlight(j, JsonLexer(), TerminalFormatter())


def stringify_refs(obj):
    res = {}
    for k, v in obj.iteritems():
        if isinstance(v, dict):
            v = stringify_refs(v)
        if k == u'@link':
            v = base58.b58encode(v)
        res[k] = v
    return res

