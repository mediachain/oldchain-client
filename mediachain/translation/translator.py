

class Translator(object):
    @staticmethod
    def translator_id():
        raise NotImplementedError("subclasses should return a unique string id")

    @staticmethod
    def translate(raw_metadata):
        raise NotImplementedError(
            "subclasses should return dictionary of translated metadata"
        )

    @staticmethod
    def can_translate_file(file_path):
        """
        Called by the ingestor to determine if this translator can accept
        a given local file.
        :param file_path: path to local file
        :return: bool indicating whether translation is possible
        """

        return False
