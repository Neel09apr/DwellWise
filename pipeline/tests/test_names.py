from dwellwise_pipeline.names import name_key


def test_fadas_fold_to_plain_letters():
    assert name_key("Béal an Mhuirthead") == "bealanmhuirthead"


def test_spelling_variants_match():
    assert name_key("Carrick-On-Shannon") == name_key("Carrick on Shannon")
    assert name_key("Union Hall") == name_key("Unionhall")


def test_case_and_punctuation_are_ignored():
    assert name_key("  CORK City & Suburbs ") == "corkcitysuburbs"
