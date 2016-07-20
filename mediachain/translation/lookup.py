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

def get_translator(translator_id):
	try:
		name, version = translator_id.split('@')
	except ValueError:
		raise LookupError(
			"Bad translator id `{}`, must be `name@multihash` format".format(translator_id)
		)

	ipfs = get_ipfs_datastore() # FIXME: memoize this

	base_path = join(expanduser('~'), '.mediachain')
	path = join(base_path, '_mediachain', 'translation')
	if not os.path.exists(path):
	    os.makedirs(path)
	    # print join(path, '__init__.py')
	    open(join(path, '__init__.py'), 'a').close()
	    # print join(dirname(path), '__init__.py')
	    open(join(dirname(path), '__init__.py'), 'a').close()

	if not os.path.exists(path):
	    os.makedirs(path)

	with ChDir(path):
		shutil.rmtree(name, ignore_errors=True)
		translator = ipfs.client.get(version) # FIXME: timeout, error handling
		os.rename(version, name) # ipfsApi doesn't support -o

	sys.path.insert(1, base_path)

	full_name = '_mediachain.translation.' + name + '.translator'
	translator_module = __import__(full_name, globals(), locals(), [name])
	translator = getattr(translator_module, name.capitalize())

	return translator
