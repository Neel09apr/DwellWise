from ops.dburl import normalise


def test_a_raw_password_with_at_signs_is_encoded():
    url = "postgresql://postgres.ref:pa@ss:w/rd@host.example:5432/postgres"
    assert normalise(url) == "postgresql://postgres.ref:pa%40ss%3Aw%2Frd@host.example:5432/postgres"


def test_an_encoded_or_passwordless_url_is_left_alone():
    assert normalise("postgresql://u:p%40x@h/db") == "postgresql://u:p%40x@h/db"
    local = "postgresql://postgres@localhost:5432/postgres"
    assert normalise(local) == local
