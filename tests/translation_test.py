import pytest
import os
from mediachain.translation.lookup import get_translator, _TRANSLATORS
from mediachain.translation.utils import is_mediachain_object, is_canonical, \
    MEDIACHAIN_OBJECT_TAG

from mediachain.ingestion.directory_iterator import LocalFileIterator
from mediachain.ingestion.getty_dump_iterator import GettyDumpIterator

from jsonschema import ValidationError

_TRANSLATOR_IDS = _TRANSLATORS.keys()


def test_translator_lookup():
    for translator_id in _TRANSLATOR_IDS:
        assert get_translator(translator_id) is not None
    with pytest.raises(LookupError):
        get_translator('NonExistentTranslator')


def get_iterator(data_dir, translator):
    translator_id = translator.translator_id()
    dir_path = os.path.join(data_dir, translator_id)
    if translator_id.startswith('Getty'):
        return GettyDumpIterator(translator, dir_path)
    return LocalFileIterator(translator, dir_path)


# def test_raises_on_nonsense():
#     for translator_id in _TRANSLATOR_IDS:
#         translator = get_translator(translator_id)
#         with pytest.raises(ValidationError):
#             translator.validate({
#                 'some' : 'nonsense'
#                 })


@pytest.fixture(params=_TRANSLATOR_IDS)
def iterator(request):
    translator_id = request.param
    test_dir = os.path.dirname(request.module.__file__)
    data_dir = os.path.join(test_dir, 'data')
    translator = get_translator(translator_id)
    return get_iterator(data_dir, translator)


def test_parses_input(iterator):
    for item in iterator:
        assert_valid_iterator_output(item)
        assert_valid_translation_output(item['translated'])


def assert_valid_iterator_output(output):
    assert output['raw_content'], 'Iterator output missing key: "raw_content"'
    assert output['parsed'], 'Unable to parse raw input'
    assert output['translated'], 'Translator produced no output'


def assert_valid_translation_output(output):
    assert output['canonical'], 'Translator output missing key: "canonical"'
    canonical = output['canonical']
    assert_is_mediachain_object(canonical)
    assert_is_canonical(canonical)
    assert_has_meta_and_type(canonical)

    chain = output.get('chain', [])
    for cell in chain:
        assert_is_mediachain_object(cell)
        assert_has_meta_and_type(cell)


def assert_is_mediachain_object(obj):
    assert is_mediachain_object(obj), \
        'Translated record must contain dict key {}'.format(
            MEDIACHAIN_OBJECT_TAG)


def assert_is_canonical(obj):
    assert is_canonical(obj), 'Translated "canonical" record must' + \
                              'have type "entity" or "artefact"'


def assert_has_meta_and_type(obj):
    assert isinstance(obj['type'], basestring), \
        'Translated object must have "type" string'
    assert isinstance(obj['meta'], dict), \
        'Translated object must have "meta" dictionary'

