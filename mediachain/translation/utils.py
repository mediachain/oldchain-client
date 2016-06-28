
MEDIACHAIN_OBJECT_TAG = '__mediachain_object__'
MEDIACHAIN_ASSET_TAG = '__mediachain_asset__'


def is_tagged_dict(tag, value):
    if not isinstance(value, dict):
        return False
    return tag in value


def is_asset(value):
    return is_tagged_dict(MEDIACHAIN_ASSET_TAG, value)


def is_mediachain_object(value):
    return is_tagged_dict(MEDIACHAIN_OBJECT_TAG, value)


def is_canonical(obj):
    return obj['type'] == 'artefact' or obj['type'] == 'entity'