import json
from os import walk
from os.path import join
from data_objects import Artefact, Entity, ArtefactCreationCell, \
    MultihashReference
from datastore.dynamo import DynamoDatastore
from datetime import datetime

TRANSLATOR_ID = 'GettyTranslator/0.1'


def getty_to_mediachain_objects(raw_ref, getty_json, datastore):
    common_meta = {'rawRef': raw_ref.to_cbor_bytes(),
                   'translatedAt': datetime.utcnow().isoformat(),
                   'translator': TRANSLATOR_ID}

    artist_name = getty_json['artist']
    artist_meta = dict(common_meta, data={'name': artist_name})
    entity = Entity(artist_meta)

    data = {'_id': 'getty_' + getty_json['id'],
            'title': getty_json['title'],
            'artist': getty_json['artist'],
            'collection_name': getty_json['collection_name'],
            'caption': getty_json['caption'],
            'editorial_source': getty_json['editorial_source'].get('name', None),
            'keywords':
                [x['text'] for x in getty_json['keywords'] if 'text' in x],
            'date_created': getty_json['date_created']
            }

    artefact_meta = dict(common_meta, data=data)
    artefact = Artefact(artefact_meta)

    entity_ref = datastore.put(entity)
    artefact_ref = datastore.put(artefact)
    creation_cell = ArtefactCreationCell(meta=common_meta,
                                         ref=artefact_ref,
                                         entity=entity_ref)

    datastore.put(creation_cell)

    return artefact, entity, creation_cell


def getty_artefacts(dd='getty/json/images',
                    max_num=0,
                    datastore=DynamoDatastore()):
    nn = 0
    for dir_name, subdir_list, file_list in walk(dd):
        for fn in file_list:
            nn += 1

            if max_num and (nn + 1 >= max_num):
                print ('ENDING EARLY')
                return

            fn = join(dir_name, fn)

            with open(fn, mode='rb') as f:
                try:
                    content = f.read()
                    raw_ref_str = datastore.put(content)
                    raw_ref = MultihashReference.from_base58(raw_ref_str)
                    getty = json.loads(content.decode('utf-8'))
                    yield getty_to_mediachain_objects(raw_ref, getty, datastore)
                except ValueError:
                    print "couldn't decode json from {}".format(fn)
                    continue

