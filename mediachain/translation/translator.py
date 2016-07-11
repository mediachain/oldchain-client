import json
import os
from jsonschema import validate as validate_schema


class Translator(object):
    @staticmethod
    def translator_id():
        """
        :return: A unique string identifier for the translator
        """
        raise NotImplementedError("subclasses should return a unique string id")

    @staticmethod
    def parse(raw_metadata_bytes):
        """
        Parse a bytestring containing the raw metadata into a dict that's
         usable by the `translate` method.

         The default implementation is to parse the input as a uft-8 formatted
         json string.  Subclasses can override if they need to accept other
         formats.

        :param raw_metadata_bytes: a bytestring containing the raw metadata
        :return: a dict representation of the raw metadata
        """
        try:
            return json.loads(raw_metadata_bytes, 'utf-8')
        except (TypeError, ValueError):
            raise NotImplementedError(
                "subclasses should parse raw metadata if they accept formats" +
                " other than utf-8 json text"
            )

    @staticmethod
    def _translate(parsed_metadata):
        """
        Transforms the parsed metadata into a format suitable for writing to
        the mediachain network.
        :param parsed_metadata: a dict containing un-translated metadata
        :return: a dict containing mediachain records.


        e.g:
        {"object": {"type": "artefact", "meta": {}},
         "related": {
           "artefactCreatedBy": {
             "object": {"type": "entity", "meta": {}}
           }
         }
        }
        """
        raise NotImplementedError(
            "subclasses should return dictionary of translated metadata"
        )

    @classmethod
    def translate(cls, parsed_metadata):
        """
        Public wrapper for _translate. Don't override this
        """
        res = cls._translate(parsed_metadata)
        cls.validate(res['canonical']['meta'])
        return res

    @staticmethod
    def can_translate_file(file_path):
        """
        Called by the ingestor to determine if this translator can accept
        a given local file.
        :param file_path: path to local file
        :return: bool indicating whether translation is possible
        """

        return False

    @staticmethod
    def validate(obj):
        # TODO: move to initializer, set BASE_DIR somewhere sane
        scehma_path = os.path.dirname(os.path.dirname(__file__)) + '/../schema.json'
        with open(scehma_path) as schema_file:
            schema = json.load(schema_file)
        validate_schema(obj, schema)
