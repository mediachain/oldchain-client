from getty.translator import GettyTranslator


def get_translator(translator_id):
    if translator_id == GettyTranslator.translator_id():
        return GettyTranslator()

    raise LookupError(
        "No translator with id {}".format(translator_id)
    )
