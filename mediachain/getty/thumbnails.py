import requests
import base64
import json
from PIL import Image
from StringIO import StringIO
from os import path


def thumbnail_url(getty_json):
    try:
        thumb = [i['uri'] for i in getty_json['display_sizes']
                 if i['name'] == 'thumb']
        return thumb[0]
    except ValueError:
        return None


def thumb_path(json_file_path):
    base, _, tail = json_file_path.rpartition('/json/images/')
    jpg_fn = path.splitext(tail)[0] + '.jpg'
    return path.join(base, 'downloads', 'thumb', jpg_fn)


def get_thumbnail_data(json_file_path, size=(150, 150), download=False):
    """ Returns the raw, jpeg encoded thumbnail data for the
    image described by the json at the given path.

    First looks on the filesystem for a saved thumbnail at the path
    produced by the indexer's getty dump routine.

    If not present, parses the json for the thumbnail uri and downloads.

    If the image is larger than `size`, scales to fit.
    Returns a byte string of the jpeg-encoded image, or None if the
    image can't be found or downloaded.
    """
    try:
        thumb = thumb_path(json_file_path)
        if path.isfile(thumb):
            img = Image.open(thumb)
        elif download:
            with open(json_file_path) as f:
                getty_json = json.load(f)
            uri = thumbnail_url(getty_json)
            r = requests.get(uri)
            img = Image.open(StringIO(r.content))
        else:
            return None

        if (img.size[0] > size[0]) or (img.size[1] > size[1]):
            img.thumbnail(size, Image.ANTIALIAS)

        # add to ipfs and return the multihash ref
        buf = StringIO()
        img.save(buf, "JPEG")
        buf.seek(0)
        data = buf.read()
        return data
    except (requests.exceptions.RequestException, IOError) as e:
        print("error getting thumbnail data: " + str(e))
        return None


def make_jpeg_data_uri(data):
    return 'data:image/jpeg;base64,' + base64.urlsafe_b64encode(data)
