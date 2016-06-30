
# Schema translation for mediachain records

This document is an overview of the schema ingestion and translation process
 in the mediachain client library.  This is a work in progress, and will be
 updated as needed to reflect changes to the interfaces and data formats.

## Overview

There are three main phases involved when writing data from an external dataset
into the mediachain system.  First, the raw metadata is acquired, either from
an API or by loading data from the local filesystem.  That data is then fed
to a "translator" module, which outputs data in the format 
[described below](#translator-output-format).  Finally, the translator output is
consumed by a "writer" module, which submits mediachain records to the transactor
network and the distributed datastore.

### Ingestion

The `mediachain.ingestion` python module contains the `DatasetIterator` 
interface for consuming data from a dataset. A `DatasetIterator` is initialized
with a [translator](#translation), and when iterated, produces dictionaries 
describing each record in the dataset:

```python
{'raw_content': raw_data_bytes,
 'parsed': python_dict_representation_of_raw_content,
 'translated': output_of_translation_module
 }
```

The `raw_content` is the raw, unmodified bytes received from the external API
or loaded from disk.  Those raw bytes are then fed into the translator and 
parsed from their native format (json, xml, etc) into a python data structure.
The parser output is stored in under the `parsed` key, and is also fed back
into the translator to produce data in the 
[translator output format](#translator-output-format), accessible at the
`translated` key.

The output of a `DatasetIterator` may also include a `local_assets` key, which,
 if present will contain "asset descriptions"
 with file uris for media assets  (images, etc) that may be
 present on the local disk.  No guarantees are made about whether the files at 
 these uris actually exist; they should be considered a "best guess" as to where
 the `DatasetIterator` expects to find media for a given record.
 
 For example, when downloading data from an external API, you might want to
 fetch thumbnail images and store them in a local directory.  However, you
 may want an option to disable that functionality for efficiency.  The
 iterator should return a uri where it would expect to find the
 image, regardless of whether it was actually downloaded or not.
  
 A generic `DirectoryIterator` can be used to walk a local directory and
 attempt to parse its contents.  If you're not hitting an external API, you
 can either use it directly or customize it by subclassing.  For a concrete
 example, see the [`GettyDumpIterator`](../mediachain/ingestion/getty_dump_iterator.py)
 class in the `mediachain.ingestion` module, which extends `DirectoryIterator` to 
 provide `local_asset` uris relative to the metadata files in the dataset archive.


### Translation

The translation process is designed to be lightweight and idempotent.
Because the original raw metadata is always preserved when adding records to
the system it's not necessary to extract every field or assign semantic 
meaning to every piece of the original metadata.

The goal of the translator is to pull a subset of fields out of the original
metadata to enable efficient indexing and search by other mediachain clients.
 
#### Translator IDs
Each translator should have a unique string identifier that can be used by
clients to figure out the source of the data.  The string should contain a
version number, which should be updated whenever the translator is updated.
For example, the current Getty images translator has the identifier 
`GettyTranslator/0.1`.

The id of the translator is written into the mediachain records to help
clients understand how they were created.
 
The [mediachain data format][mediachain-format-docs] consists of a collection
of immutable data records, with updates applied in "chains" that form a 
reverse linked list.  The translator output format is very close to the final
mediachain object representation, with some changes to be able to represent
links between objects without knowing their final content hash.

#### Translator output format

Here's an example of the output format that will result in three mediachain
records being written to the datastore:

```python
{'canonical': { 
  '__mediachain_object__': True,
  'type': 'artefact',
  'meta': {
    'data': {
      'title': 'The Last Supper',
      'thumbnail': {
        '__mediachain_asset__': True,
        'uri': 'http://example.com/last_supper.jpg'
      }
    }
  },
  
  'chain': [
    {
      '__mediachain_object__': True,
      'type': 'artefactCreatedBy',
      'meta': {},
      'entity': {
        '__mediachain_object__': True,
        'meta': {
          'data': {
            'name': 'Leonardo da Vinci'
          }
        }
      }
    }
  ]
}
```

There are two special keys indicate to the writer that the containing objects
need special processing.  Dictionaries tagged with `__mediachain_object__`
will be submitted to the transactor network, and they will be replaced by
a multihash link in the containing object.

The same is true of objects tagged with `__mediachain_asset__`, however instead
 of being sent to the transactor, the writer will attempt to resolve the `uri` 
 and submit the contents to the datastore directly.  Remote assets produced
 by the translator may be superseded by local assets from the `DatasetIterator`
 if they exist.

The tagged objects are submitted to the transactor depth-first, and the
`canonical` is submitted before any entries in the `chain`.  So in the above
example, first the `thumbnail` asset would be sent to the datastore, and the
asset description object would be replaced with a multihash link, resulting in
something similar to this:

```python
{ 
  'type': 'artefact',
  'meta': {
    'translator': 'FooTranslator/0.2',
    'data': {
      'title': 'The Last Supper',
      'thumbnail': {
        '/': 'QmAAA...AAA'
      }
    }
  }
}
```

Where `'QmAAA...AAA'` is the hash of the thumbnail's contents.  


Note that the `__mediachain_object__` tag is removed before submitting; 
it's an internal marker that doesn't get written out to the datastore.

Also, notice that the `meta` field now contains the translator id under the
`translator` key; this is supplied by the writer, and does not need to appear
in the translator output.

After the `canonical` is submitted, each entry in the `chain` list is processed
in the same fashion, resulting in chain cells that will extend the `canonical`
with more information.  In the above example, the da Vinci `Entity` will be
created if it does not already exist, and linked to the `Artefact` with an 
`ArtefactCreationCell`.

[mediachain-format-docs]: http://github.com/mediachain/mediachain/blob/master/docs/data-structures.md
