import json
from os import walk
from os.path import join
from data_objects import Artefact, Entity, ArtefactCreationCell
from datastore.dynamo import DynamoDatastore


def getty_to_mediachain_objects(getty_json, datastore):
    artist_name = getty_json['artist']
    entity = Entity({'name': artist_name})
    entity_ref = datastore.put(entity)

    meta = {'_id': 'getty_' + getty_json['id'],
            'title': getty_json['title'],
            'artist': getty_json['artist'],
            'collection_name': getty_json['collection_name'],
            'caption': getty_json['caption'],
            'editorial_source': getty_json['editorial_source'].get('name', None),
            'keywords':
                [x['text'] for x in getty_json['keywords'] if 'text' in x],
            'date_created': getty_json['date_created']
            }

    artefact = Artefact(meta)
    artefact_ref = datastore.put(artefact)
    creation_cell = ArtefactCreationCell(meta={},
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

            with open(fn) as f:
                try:
                    getty = json.load(f)
                    yield getty_to_mediachain_objects(getty, datastore)
                except ValueError:
                    print "couldn't decode json from {}".format(fn)
                    continue

