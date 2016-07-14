import json
import os
from jsonschema import validate as validate_schema
from mediachain.translation.utils import is_mediachain_object, is_canonical


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
        if not os.environ.get('MEDIACHAIN_SKIP_SCHEMA_VALIDATION', False):
            validated = cls.validate(res)
            print "Found {} valid Mediachain cells".format(validated)

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

    @classmethod
    def get_schema(self):
        # TODO: set BASE_DIR somewhere sane
        schema_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'schema.json'))
        if not hasattr(self, '_schema'):
            with open(schema_path) as schema_file:
                self._schema = json.load(schema_file)
        return self._schema

    @classmethod
    def validate(self, obj):
        if type(obj) in (int, str, bool, unicode):
            return 0

        validated = 0

        # TODO: (or is_update...)
        if is_mediachain_object(obj) and is_canonical(obj):
            validate_schema(obj['meta'], self.get_schema())
            validated = 1

        objects = {k: v for k, v in obj.iteritems()
                    if isinstance(v, dict)}

        lists = {k: v for k,v in obj.iteritems()
                    if isinstance(v, list)}
        objects_from_lists = [item for sublist in lists.values() for item in sublist]

        for o in objects.values() + objects_from_lists:
            validated = validated + self.validate(o)

        return validated

