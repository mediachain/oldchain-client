import os
from urlparse import urlparse
import requests
import base64
import mimetypes
from PIL import Image
from StringIO import StringIO


def load_asset(asset):
    try:
        uri = asset['uri']
    except (TypeError, KeyError):
        return None, None

    mime, _ = mimetypes.guess_type(uri)

    if uri.lower().startswith('file://'):
        p = urlparse(uri)
        file_path = os.path.abspath(os.path.join(p.netloc, p.path))

        if not os.path.isfile(file_path):
            return None, None
        try:
            with open(file_path) as f:
                return f.read(), mime
        except IOError as e:
            print('error reading from {}: {}'.format(file_path, e))
            return None, None

    try:
        r = requests.get(uri)
        return r.content, mime
    except requests.exceptions.RequestException as e:
        print('error downloading media from {}: {}'.format(uri, e))

    return None, None


def process_asset(name, asset_data):
    if name == 'thumbnail':
        return resize_image(asset_data, THUMBNAIL_SIZE)
    return asset_data


# size constants for images
THUMBNAIL_SIZE = (1024, 1024)


def resize_image(image_data, size=THUMBNAIL_SIZE):
    img = Image.open(StringIO(image_data))
    if (img.size[0] > size[0]) or (img.size[1] > size[1]):
        img.thumbnail(size, Image.ANTIALIAS)
    buf = StringIO()
    img.save(buf, "JPEG")
    buf.seek(0)
    data = buf.read()
    return data


def make_jpeg_data_uri(data):
    return 'data:image/jpeg;base64,' + base64.urlsafe_b64encode(data)
