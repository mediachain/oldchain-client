from __future__ import unicode_literals
from mediachain.translation.translator import Translator


class SimpleTranslator(Translator):

    @staticmethod
    def translator_id():
        return 'SimpleTranslator/0.1'

    @staticmethod
    def translate(parsed_metadata):
        simple_json = parsed_metadata

        # extract artist Entity
        try:
            artist_name = simple_json['artist']

            artist_entity = {
                u'__mediachain_object__': True,
                u'type': u'entity',
                u'meta': {
                    u'data': {
                        u'name': artist_name
                    }
                }
            }
        except KeyError:
            artist_entity = None

        # extract artwork Artefact
        data = simple_json

        try:
            thumb_uri = [i['uri'] for i in parsed_metadata['display_sizes']
                         if i['name'] == 'thumb'].pop()
            data[u'thumbnail'] = {
                u'__mediachain_asset__': True,
                u'uri': thumb_uri
            }
        except Exception as e:
            pass

        artwork_artefact = {
            u'__mediachain_object__': True,
            u'type': u'artefact',
            u'meta': {'data': data}
        }

        chain = []
        if artist_entity is not None:
            chain.append({u'__mediachain_object__': True,
                          u'type': u'artefactCreatedBy',
                          u'meta': {},
                          u'entity': artist_entity
                          })

        return {
            u'canonical': artwork_artefact,
            u'chain': chain
        }

    @staticmethod
    def can_translate_file(file_path):
        return True

