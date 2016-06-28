import os
import requests
import base64
from PIL import Image
from StringIO import StringIO


def load_media(local_media_paths, remote_media_locations,
               download_remote=False):
    media_data = {}
    for name, path in local_media_paths.iteritems():
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                media_data[name] = f.read()
        except IOError as e:
            print('error reading from {}: {}'.format(path, e))
            pass

    if download_remote:
        for name, uri in remote_media_locations:
            if name in media_data:
                continue  # don't download if we have it locally

            try:
                r = requests.get(uri)
                media_data[name] = r.content
            except requests.exceptions.RequestException as e:
                print('error downloading media from {}: {}'.format(uri, e))
    return process_media(media_data)


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
