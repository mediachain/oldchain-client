import threading
from base58 import b58encode
from Queue import Queue


class BlockchainFollower(object):
    def __init__(self, block_cache):
        self.cache = block_cache
        self.queue = Queue()
        self.catchup_thread = threading.Thread(name='blockchain-catchup',
                                               target=self._perform_catchup)
        self.catchup_thread.start()

    def update(self, block_ref):
        self.queue.put(block_ref)

    def _perform_catchup(self):
        while True:
            ref = self.queue.get()
            if ref == '__quit__':
                return

            block = self.cache.get(ref)
            if block is None:
                print('Could not get block with ref {}'.format(ref))
                return

            chain = chain_ref(block)
            if chain is None:
                print('Reached genesis block {}'.format(ref))
                return
            self.queue.put(chain)


def chain_ref(block):
    try:
        ref_bytes = bytes(block['chain']['@link'])
        return b58encode(ref_bytes)
    except (KeyError, ValueError):
        return None
