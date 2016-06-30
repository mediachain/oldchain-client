from getty.translator import GettyTranslator

_TRANSLATORS = {
    GettyTranslator.translator_id(): GettyTranslator
}


def get_translator(translator_id):
    try:
        return _TRANSLATORS[translator_id]
    except LookupError:
        raise LookupError(
            "No translator with id {}".format(translator_id)
        )