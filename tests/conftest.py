import os.path
import configparser
import pytest
from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    # Use if the user specified env file, if exists
    if os.path.isfile("/.env"):
        target_env_file = "/.env"
    elif os.path.isfile("/.env.example"):
        target_env_file = "/.env.example"
    elif os.path.isfile(".env"):
        target_env_file = ".env"
    else:
        target_env_file = ".env.example"

    config_parser = configparser.RawConfigParser()

    # Read .env file
    with open(target_env_file) as f:
        file_content = "[dummy_section]\n" + f.read()
        config_parser.read_string(file_content)

    # Patch current env variables
    for key, value in config_parser["dummy_section"].items():
        monkeypatch.setenv(key.upper(), value)

    # Let the tests use a test database
    monkeypatch.setenv("CM_DB_NAME".upper(), "cm_test_database")


@pytest.mark.order(1)
@pytest.fixture(autouse=True)
def wipe_test_db_tables(monkeypatch):
    # Connect to the database
    config = Config()
    database = Database(
        config["db_host"],
        config["db_port"],
        config["db_name"],
        config["db_user"],
        config["db_password"],
    )

    session = database.session()

    # Wipe the database tables
    meta = database.model.metadata
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()
