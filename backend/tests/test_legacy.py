"""Installs from before the rename (Collander 1.x) keep working."""

from app.legacy import adopt_legacy_db, adopt_legacy_env
from app.schemas import Bundle


def test_old_setting_names_are_used_when_new_ones_are_missing(tmp_path):
    env = {
        "COLLANDER_PASSWORD": "pw",
        "COLLANDER_AI_PROVIDER": "ollama",
        "COLANDER_AI_PROVIDER": "none",
    }
    used = adopt_legacy_env(env, tmp_path / ".env")
    assert env["COLANDER_PASSWORD"] == "pw"
    assert env["COLANDER_AI_PROVIDER"] == "none"  # the new name wins
    assert used == ["COLLANDER_PASSWORD"]


def test_old_setting_names_in_dotenv(tmp_path):
    (tmp_path / ".env").write_text(
        "COLLANDER_DATA_DIR=./old\nCOLLANDER_QUEUE_WORKERS=4\nCOLANDER_QUEUE_WORKERS=1\n"
    )
    env = {"COLLANDER_DATA_DIR": "./from-env"}
    adopt_legacy_env(env, tmp_path / ".env")
    assert env["COLANDER_DATA_DIR"] == "./from-env"  # environment beats .env
    # Set by its new name in .env, so it's left to the settings loader.
    assert "COLANDER_QUEUE_WORKERS" not in env


def test_old_database_is_renamed_with_its_wal_files(tmp_path):
    for name in ("collander.db", "collander.db-wal", "collander.db-shm"):
        (tmp_path / name).write_text(name)
    assert adopt_legacy_db(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "colander.db",
        "colander.db-shm",
        "colander.db-wal",
    ]
    assert (tmp_path / "colander.db-wal").read_text() == "collander.db-wal"


def test_existing_new_database_is_left_alone(tmp_path):
    (tmp_path / "collander.db").write_text("old")
    (tmp_path / "colander.db").write_text("new")
    assert not adopt_legacy_db(tmp_path)
    assert (tmp_path / "colander.db").read_text() == "new"
    assert (tmp_path / "collander.db").exists()


def test_old_backups_still_load():
    bundle = Bundle.model_validate(
        {"format": "collander-bundle", "version": 1, "recipes": [{"title": "Soup"}]}
    )
    assert bundle.recipes[0].title == "Soup"
