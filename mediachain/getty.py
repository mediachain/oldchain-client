import json
from os import walk
from os.path import join
from mediachain.data_objects import Artefact, Entity, ArtefactCreationCell, \
    MultihashReference
from mediachain.datastore.dynamo import DynamoDatastore
from datetime import datetime

TRANSLATOR_ID = 'GettyTranslator/0.1'


def getty_to_mediachain_objects(transactor, raw_ref, getty_json, entities):
    common_meta = {'rawRef': raw_ref.to_map(),
                   'translatedAt': datetime.utcnow().isoformat(),
                   'translator': TRANSLATOR_ID}

    artist_name = getty_json['artist']
    if artist_name in entities:
        entity = entities[artist_name]
    else:
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

    # TODO: catch RPC errors here
    entity_ref = transactor.insert(entity)
    artefact_ref = transactor.insert(artefact)
    creation_cell = ArtefactCreationCell(meta=common_meta,
                                         ref=artefact_ref,
                                         entity=entity_ref)

    transactor.update(creation_cell)

    return artefact, entity, creation_cell


def getty_artefacts(transactor,
                    dd='getty/json/images',
                    max_num=0,
                    datastore=DynamoDatastore()):
    entities = dedup_artists(dd, max_num, datastore)

    for content, getty_json in walk_json_dir(dd, max_num):
        raw_ref_str = datastore.put(content)
        raw_ref = MultihashReference.from_base58(raw_ref_str)
        yield getty_to_mediachain_objects(
            transactor, raw_ref, getty_json, entities
        )


def dedup_artists(dd='getty/json/images',
                  max_num=0,
                  datastore=DynamoDatastore()):
    artist_name_map = {}
    for content, getty_json in walk_json_dir(dd, max_num):
        raw_ref_str = datastore.put(content)
        n = getty_json['artist']
        if n is None or n in artist_name_map:
            continue
        artist_name_map[n] = raw_ref_str

    entities = {}
    for n, raw_ref_str in artist_name_map.iteritems():
        meta = {'rawRef': MultihashReference.from_base58(raw_ref_str).to_map(),
                'translatedAt': datetime.utcnow().isoformat(),
                'translator': TRANSLATOR_ID,
                'data': {'name': n}}
        entities[n] = Entity(meta)
    return entities


def walk_json_dir(dd='getty/json/images',
                  max_num=0):
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
                    decoded_json = json.loads(content.decode('utf-8'))
                    yield content, decoded_json
                except ValueError:
                    print "couldn't decode json from {}".format(fn)
                    continue
