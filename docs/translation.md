
# Schema translation for mediachain records

This document is an overview of the data ingestion and translation process
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
 can either use it directly or customize it by subclassing.


### Translation

The translation process is designed to be lightweight and idempotent.
Because the original raw metadata is always preserved when adding records to
the system it's not necessary to extract every field or assign semantic 
meaning to every piece of the original metadata.

The goal of the translator is to pull a subset of fields out of the original
metadata to enable efficient indexing and search by other mediachain clients.
 
#### Translator IDs
Translators should have a unique string identifier, which will be combined with a
version hash and written to the mediachain records.

Please see [this document](https://github.com/mediachain/mediachain/blob/master/docs/translators.md#translator-lifecycle)
for more on how translators are versioned and distributed.

The id of the translator is written into the mediachain records to help
clients understand how they were created.

#### Translator output format

The [mediachain data format][mediachain-format-docs] consists of a collection
of immutable data records, with updates applied in "chains" that form a
reverse linked list.  The translator output format is very close to the final
mediachain object representation, with some changes to be able to represent
links between objects without knowing their final content hash.

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
}
```

#### Tagged dictionaries
There are two special keys that indicate to the writer that the containing objects
need special processing.  Dictionaries tagged with `__mediachain_object__`
will be submitted to the transactor network, and they will be replaced by
a multihash link in the containing object.

##### Binary asset links
The `__mediachain_asset__` tag is used when you want to include a reference to
a binary asset, for example, a thumbnail image.  These should include a `uri`
field, which may be either a remote http(s) url, or a file uri.  By default,
the writer will attempt to download remote assets and store them in ipfs,
and it will include a multihash link so that other clients can fetch the asset.
If possible, the writer will also include `mime-type`, `content_size` and
`hash_sha256` fields to provide more information to readers.

If remote downloads are disabled, only the `uri` field will be included, and
readers can try to retrieve the asset themselves.


The tagged objects are submitted depth-first, and the
`canonical` is submitted before any entries in the `chain`.  So in the above
example, first the `thumbnail` asset would be sent to the datastore, and the
asset description object would be replaced with a multihash link, resulting in
something similar to this:

```python
{ 
  'type': 'artefact',
  'meta': {
    'translator': 'FooTranslator@QmF00',
    'data': {
      'title': 'The Last Supper',
      'thumbnail': {
        'link': {'@link': 'QmAAA...AAA'},
        'content_size': 12345678,
        'hash_sha256': 'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447',
        'mime-type': 'image/jpeg'
      }
    }
  }
}
```


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
