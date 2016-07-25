from mediachain.datastore.ipfs import get_ipfs_datastore
import sys
import os
import shutil
from os.path import expanduser, dirname, join


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


def touch(path):
    open(path, 'a').close()


def get_translator(translator_id):
    try:
        name, version = translator_id.split('@')
    except ValueError:
        raise LookupError(
            "Bad translator id `{}`, must be `name@multihash` format".format(
                translator_id)
        )

    base_path = join(expanduser('~'), '.mediachain')
    path = join(base_path, '_mediachain', 'translation', name)
    if not os.path.exists(path):
        os.makedirs(path)
        touch(join(path, '__init__.py'))
        touch(join(dirname(path), '__init__.py'))
        touch(join(dirname(dirname(path)), '__init__.py'))

    if not os.path.exists(join(path, version)):
        with ChDir(path):
            ipfs = get_ipfs_datastore()  # FIXME: memoize this
            # FIXME: timeout, error handling
            translator = ipfs.client.get(version)

    sys.path.insert(1, base_path)

    full_name = '_mediachain.translation.{name}.{version}.translator'.format(
        name=name,
        version=version
    )
    translator_module = __import__(full_name, globals(), locals(), [name])
    translator = getattr(translator_module, name.capitalize())
    translator.set_version(version)

    return translator
