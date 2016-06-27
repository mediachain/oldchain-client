import os
from mediachain.translation.translator import Translator


class GettyTranslator(Translator):

    @staticmethod
    def translator_id():
        return u'GettyTranslator/0.1'

    @staticmethod
    def translate(raw_metadata):
        return {}

    @staticmethod
    def can_translate_file(file_path):
        ext = os.path.splitext(file_path)[-1]
        return ext.lower() == '.json'
