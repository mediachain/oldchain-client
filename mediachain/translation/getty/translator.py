from __future__ import unicode_literals
import os
from mediachain.translation.translator import Translator


class GettyTranslator(Translator):

    @staticmethod
    def translator_id():
        return 'GettyTranslator/0.1'

    @staticmethod
    def translate(parsed_metadata):
        getty_json = parsed_metadata

        # extract artist Entity
        artist_name = getty_json['artist']
        artist_entity = {
            'type': 'entity',
            'meta': {
                'data': {
                    'name': artist_name
                }
            }
        }

        # extract artwork Artefact
        data = {'_id': u'getty_' + getty_json['id'],
                'title': getty_json['title'],
                'artist': getty_json['artist'],
                'collection_name': getty_json['collection_name'],
                'caption': getty_json['caption'],
                'editorial_source':
                    getty_json['editorial_source'].get('name', None),
                'keywords':
                    [x['text'] for x in getty_json['keywords'] if 'text' in x],
                'date_created': getty_json['date_created']
                }

        artwork_artefact = {
            'type': 'artefact',
            'meta': {'data': data}
        }

        return {
            'object': artwork_artefact,
            'related': [
                {'relationship': 'artefactCreatedBy',
                 'object': artist_entity
                 }
            ]
        }

    @staticmethod
    def can_translate_file(file_path):
        ext = os.path.splitext(file_path)[-1]
        return ext.lower() == '.json'

    @staticmethod
    def get_media_locations(parsed_metadata):
        try:
            thumb = [i['uri'] for i in parsed_metadata['display_sizes']
                     if i['name'] == 'thumb']
            return {'thumbnail': thumb}
        except ValueError:
            return {}
