

class DatasetIterator(object):
    def __init__(self, translator, limit=None):
        self.translator = translator
        self.limit = limit

    def __iter__(self):
        raise NotImplementedError(
            'subclasses should yield translated metadata'
        )
