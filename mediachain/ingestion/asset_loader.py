import os
from urlparse import urlparse
import requests
import base64
import mimetypes
from mediachain.utils.log import get_logger


def load_asset(asset):
    logger = get_logger(__name__)

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
            logger.error('error reading from {}: {}'.format(file_path, e))
            return None, None

    try:
        r = requests.get(uri)
        return r.content, mime
    except requests.exceptions.RequestException as e:
        logger.error('error downloading media from {}: {}'.format(uri, e))

    return None, None


def make_jpeg_data_uri(data):
    return 'data:image/jpeg;base64,' + base64.urlsafe_b64encode(data)
