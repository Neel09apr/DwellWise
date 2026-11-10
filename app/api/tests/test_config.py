from pathlib import Path

from dwellwise_api.config import Settings, normalise_database_url


def test_a_raw_password_with_reserved_characters_is_encoded():
    url = "postgresql://postgres.ref:p@ss:w/rd@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
    assert normalise_database_url(url) == (
        "postgresql://postgres.ref:p%40ss%3Aw%2Frd@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
    )


def test_an_encoded_or_missing_password_is_left_alone():
    encoded = "postgresql://u:p%40ss@host:5432/db"
    assert normalise_database_url(encoded) == encoded
    assert normalise_database_url("postgresql://u@host/db") == "postgresql://u@host/db"


def test_the_environment_wins_over_the_dotenv_file(tmp_path: Path):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "# local\nDATABASE_URL='postgresql://u:a@b@file/db'\nFRESHNESS_HOURS=12\n", encoding="utf-8"
    )
    settings = Settings.from_env({"DWELLWISE_DOTENV": str(dotenv), "FRESHNESS_HOURS": "24"})
    assert settings.database_url == "postgresql://u:a%40b@file/db"
    assert settings.freshness_hours == 24
