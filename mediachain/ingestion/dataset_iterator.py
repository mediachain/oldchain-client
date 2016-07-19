

class DatasetIterator(object):
    def __init__(self, translator, limit=None):
        self.translator = translator
        self.limit = limit
        self._iterator = None

    def __iter__(self):
        return self

    def next(self):
        if self._iterator is None:
            self._iterator = self.generator()
        return next(self._iterator)

    def generator(self):
        raise NotImplementedError(
            'subclasses should yield translated metadata and supporting data'
        )
