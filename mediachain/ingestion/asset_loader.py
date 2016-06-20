import os
from urlparse import urlparse
import requests
import base64
from PIL import Image
from StringIO import StringIO


def load_asset(asset, download_remote=False):
    try:
        uri = asset['uri']
    except KeyError:
        return None

    if uri.lower().startswith('file://'):
        p = urlparse(uri)
        file_path = os.path.abspath(os.path.join(p.netloc, p.path))
        try:
            with open(file_path) as f:
                return f.read()
        except IOError as e:
            print('error reading from {}: {}'.format(file_path, e))

    if download_remote:
        try:
            r = requests.get(uri)
            return r.content
        except requests.exceptions.RequestException as e:
            print('error downloading media from {}: {}'.format(uri, e))

    return None


def process_media(media_data):
    processed = {}
    for name, data in media_data.iteritems():
        if name == 'thumbnail':
            processed[name] = resize_image(data, THUMBNAIL_SIZE)
        else:
            processed[name] = data
    return processed


# size constants for images
THUMBNAIL_SIZE = (150, 150)


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
