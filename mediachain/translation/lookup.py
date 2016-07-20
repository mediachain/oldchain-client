from mediachain.datastore.ipfs import get_ipfs_datastore
import sys
import os
from os.path import expanduser, join


class ChDir(object):
    """
    Step into a directory temporarily
    """
    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.old_dir)


def get_translator(translator_id):
    try:
        name, version = translator_id.split('@')
    except ValueError:
        raise LookupError(
            "Bad translator id `{}`, must be `name@multihash` format".format(translator_id)
        )

    path = join(expanduser('~'), '.mediachain')
    if not os.path.exists(path):
        os.makedirs(path)

    try:
        return load_translator(path, name, version)
    except ImportError:
        pass

    ipfs = get_ipfs_datastore() # FIXME: memoize this
    with ChDir(path):
        translator = ipfs.client.get(version) # FIXME: timeout, error handling

    return load_translator(path, name, version)


def load_translator(base_path, name, version):
    if base_path not in sys.path:
        sys.path.append(base_path)

    module_path = version + '.translator'
    translator_module = __import__(module_path, globals(), locals(), [name])
    translator = getattr(translator_module, name.capitalize())
    return translator
