from ops.dburl import for_terraform, normalise


def test_a_raw_password_with_at_signs_is_encoded():
    url = "postgresql://postgres.ref:pa@ss:w/rd@host.example:5432/postgres"
    assert normalise(url) == "postgresql://postgres.ref:pa%40ss%3Aw%2Frd@host.example:5432/postgres"


def test_an_encoded_or_passwordless_url_is_left_alone():
    assert normalise("postgresql://u:p%40x@h/db") == "postgresql://u:p%40x@h/db"
    local = "postgresql://postgres@localhost:5432/postgres"
    assert normalise(local) == local


def test_terraform_gets_tls_required_unless_the_url_chooses():
    assert for_terraform("postgresql://u:p@h:5432/db") == "postgresql://u:p@h:5432/db?sslmode=require"
    assert (
        for_terraform("postgresql://u:p@h/db?connect_timeout=5")
        == "postgresql://u:p@h/db?connect_timeout=5&sslmode=require"
    )
    assert (
        for_terraform("postgresql://u:p@h/db?sslmode=verify-full")
        == "postgresql://u:p@h/db?sslmode=verify-full"
    )
    assert for_terraform("postgresql://u:pa@ss@h/db") == "postgresql://u:pa%40ss@h/db?sslmode=require"
