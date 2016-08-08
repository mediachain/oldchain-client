import threading
import time
from base58 import b58encode
from Queue import Queue, LifoQueue, Empty as QueueEmpty
from mediachain.transactor.block_cache import get_block_cache
from mediachain.proto import Transactor_pb2  # pylint: disable=no-name-in-module
from mediachain.datastore.utils import ref_base58
from mediachain.rpc.utils import with_retry
from mediachain.utils.log import get_logger
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError


class BlockchainFollower(object):
    def __init__(self,
                 stream_func,
                 catchup = True,
                 last_known_block_ref=None,
                 block_cache = None,
                 event_map_fn = None,
                 max_retry=20):
        if block_cache is None:
            block_cache = get_block_cache()

        self.max_retry = max_retry
        self.cache = block_cache
        self.stream_func = stream_func
        self.block_ref_queue = Queue()
        self.incoming_event_queue = Queue()
        self.block_replay_stack = LifoQueue()
        self.catchup_begin = threading.Event()
        self.catchup_complete = threading.Event()
        self.cancel_flag = threading.Event()

        self.should_catchup = catchup
        self.last_known_block_ref = ref_base58(last_known_block_ref)
        if event_map_fn is None:
            self.event_map_fn = lambda x: x
        else:
            self.event_map_fn = event_map_fn
        self.catchup_thread = threading.Thread(
                name='blockchain-catchup',
                target=self._perform_catchup)
        self.incoming_event_thread = threading.Thread(
            name='journal-stream-listener',
            target=self._receive_incoming_events)
        self._event_iterator = self._event_stream()

    def __iter__(self):
        return self

    def next(self):
        return next(self._event_iterator)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cancel()
        return False

    def start(self):
        self.catchup_thread.start()
        self.incoming_event_thread.start()

    def cancel(self):
        logger = get_logger(__name__)
        logger.info('BlockchainFollower canceled')
        self.cancel_flag.set()

    def _clear_queues(self):
        if self.cancel_flag.is_set():
            return

        with self.block_ref_queue.mutex:
            self.block_ref_queue.queue.clear()
        with self.block_replay_stack.mutex:
            del self.block_replay_stack.queue[:]
        with self.incoming_event_queue.mutex:
            self.incoming_event_queue.queue.clear()

    def _perform_catchup(self):
        if not self.should_catchup:
            self.catchup_complete.set()
            return

        logger = get_logger(__name__)
        while True:
            if self.cancel_flag.is_set():
                return

            # block until the event consumer thread tells us to start the
            # blockchain catchup process
            self.catchup_begin.wait()

            ref = self.block_ref_queue.get()
            if self.cancel_flag.is_set():
                return

            if ref_base58(ref) == self.last_known_block_ref:
                logger.debug('hit last known block: {}'.format(
                    self.last_known_block_ref
                ))
                self.catchup_complete.set()
                continue

            block = self.cache.get(ref)

            if block is None:
                logger.error('Could not get block with ref {}'.format(ref))
                return

            self.block_replay_stack.put(ref)

            chain = chain_ref(block)
            if chain is None:
                logger.debug('Reached genesis block {}'.format(ref))
                self.catchup_complete.set()
                continue

            self.block_ref_queue.put(chain)

    def _receive_incoming_events(self):
        def event_receive_worker():
            # first clear out all the queues, and event state,
            # in case we're being called from the retry helper after a stream
            # interruption
            if self.should_catchup:
                self.catchup_complete.clear()
                self.catchup_begin.clear()
            self._clear_queues()
            first_event_received = False

            try:
                stream = self.stream_func()
                for event in stream:
                    if self.cancel_flag.is_set():
                        stream.cancel()
                        return

                    if not first_event_received:
                        first_event_received = True
                        block_ref = block_event_ref(event)
                        if block_ref is None:
                            self.catchup_complete.set()
                        else:
                            self.block_ref_queue.put(block_ref)
                            self.catchup_begin.set()

                    self.incoming_event_queue.put(event)
            except AbortionError as e:
                if self.cancel_flag.is_set() and e.code == StatusCode.CANCELLED:
                    return
                else:
                    raise
        with_retry(event_receive_worker, max_retry_attempts=self.max_retry)

    def _event_stream(self):
        logger = get_logger(__name__)
        while True:
            if self.cancel_flag.is_set():
                return
            # wait until catchup process signals that it's complete
            # this will be immediate if catchup is not in progress
            if self.should_catchup:
                self.catchup_complete.wait()

                # get all values from the catchup queue and yield their entries
                while not self.block_replay_stack.empty():
                    if self.cancel_flag.is_set():
                        return
                    block_ref = self.block_replay_stack.get()
                    logger.debug('Replaying block: {}'.format(block_ref))
                    block = self.cache.get(block_ref)
                    entries = block.get('entries', [])
                    for e in entries:
                        e = self.event_map_fn(block_event_to_rpc_event(e))
                        if e is not None:
                            yield e
                    self.last_known_block_ref = block_ref
                    block_event = Transactor_pb2.JournalEvent()
                    block_event.journalBlockEvent.reference = ref_base58(block_ref)
                    block_event = self.event_map_fn(block_event)
                    if block_event is not None:
                        yield block_event

            if self.cancel_flag.is_set():
                return
            # Try to pull an event off of the incoming event queue
            # If there's no event received within a second, loop back.
            try:
                e = self.incoming_event_queue.get(block=False, timeout=1)
                block_ref = block_event_ref(e)
                if block_ref is not None:
                    self.last_known_block_ref = block_ref

                e = self.event_map_fn(e)
                if e is not None:
                    yield e
            except QueueEmpty:
                pass


def chain_ref(block):
    try:
        ref_bytes = bytes(block['chain']['@link'])
        return b58encode(ref_bytes)
    except (KeyError, ValueError):
        return None


def block_event_ref(rpc_event):
    if rpc_event.WhichOneof('event') != 'journalBlockEvent':
        return None
    return rpc_event.journalBlockEvent.reference


def block_event_to_rpc_event(event):
    rpc_event = Transactor_pb2.JournalEvent()
    if event['type'] == 'insert':
        rpc_event.insertCanonicalEvent.reference = ref_base58(event['ref'])
    elif event['type'] == 'update':
        rpc_event.updateChainEvent.canonical.reference = ref_base58(
            event['ref'])
        rpc_event.updateChainEvent.chain.reference = ref_base58(event['chain'])
        if 'chainPrevious' in event:
            rpc_event.updateChainEvent.chainPrevious.reference = ref_base58(
                event['chainPrevious'])
    else:
        raise ValueError('unknown journal event type: {}'.format(
            event['type']
        ))
    return rpc_event