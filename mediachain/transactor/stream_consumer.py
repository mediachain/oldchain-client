import threading

class JournalStreamConsumer(object):
    def __init__(self, stream, event_callback=None):
        self.stream = stream
        self.consumer_thread = threading.Thread(
            name='journal-stream-consumer',
            target=self._consumer
        )
        self._cancelled = False
        if event_callback is not None:
            self.on_event = event_callback
            self.event_cache = None
        else:
            self.event_cache = list()
            self.event_index = 0
            def on_event(event):
                self.event_cache.append(event)
            self.on_event = on_event

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cancel()

    def __iter__(self):
        return self

    def next(self):
        if self.event_cache is None:
            raise StopIteration
        try:
            event = self.event_cache[self.event_index]
            self.event_index += 1
            return event
        except IndexError:
            raise StopIteration

    def start(self):
        try:
            self.stream.start()
        except AttributeError:
            pass
        self.consumer_thread.start()

    def cancel(self):
        self._cancelled = True
        self.stream.cancel()

    def _consumer(self):
        while not self._cancelled:
            try: event = next(self.stream)
            except StopIteration: return
            self.on_event(event)