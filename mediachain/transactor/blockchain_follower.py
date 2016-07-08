import threading
import time
from base58 import b58encode
from Queue import Queue
from collections import deque
from mediachain.transactor.block_cache import BlockCache

class BlockchainFollower(object):
    def __init__(self, starting_block_ref, block_cache = None, replay_entries=True):
        if block_cache is None:
            block_cache = BlockCache()

        self.cache = block_cache
        self.ref_queue = Queue()
        self.caught_up = False
        self.catchup_thread = threading.Thread(name='blockchain-catchup',
                                               target=self._perform_catchup)

        self.ref_queue.put(starting_block_ref)
        if replay_entries:
            self.replay_stack = deque()
        else:
            self.replay_stack = None

    def start(self):
        self.catchup_thread.start()

    def cancel(self):
        self.ref_queue.put('__abort__')

    def _perform_catchup(self):
        while True:
            ref = self.ref_queue.get()
            if ref == '__abort__':
                return

            block = self.cache.get(ref)

            if block is None:
                print('Could not get block with ref {}'.format(ref))
                return

            if self.replay_stack is not None:
                self.replay_stack.appendleft(ref)

            chain = chain_ref(block)
            if chain is None:
                print('Reached genesis block {}'.format(ref))
                self.caught_up = True
                return
            self.ref_queue.put(chain)

    def events(self):
        if self.replay_stack is None:
            return

        #  FIXME: add timeout to this to avoid blocking forever!
        while not self.caught_up:
            time.sleep(0.2)

        for block_ref in self.replay_stack:
            block = self.cache.get(block_ref)
            entries = block.get('entries', [])
            for e in entries:
                yield e


def chain_ref(block):
    try:
        ref_bytes = bytes(block['chain']['@link'])
        return b58encode(ref_bytes)
    except (KeyError, ValueError):
        return None
