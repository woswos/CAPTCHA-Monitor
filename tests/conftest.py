import os.path
import configparser

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database


def pytest_addoption(parser):
    parser.addoption(
        "--ci-mode",
        action="store_true",
        default=False,
        help="Run in CI mode and skip tests that require Docker",
    )


@pytest.fixture(autouse=True)
def env_setup(monkeypatch, pytestconfig):
    if not pytestconfig.getoption("--ci-mode"):
        target_env_file = "/.env"
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
def wipe_test_db_tables(pytestconfig):
    # Only run this if we are not running in CI mode
    if not pytestconfig.getoption("--ci-mode"):
        # Connect to the database
        config = Config()
        database = Database(
            config["db_host"],
            config["db_port"],
            config["db_name"],
            config["db_user"],
            config["db_password"],
        )
        db_session = database.session()

        # Wipe the database tables and reset the autoincrement counters
        meta = database.model.metadata
        for table in meta.tables.keys():
            db_session.execute(
                f"TRUNCATE TABLE {table.lower()} RESTART IDENTITY CASCADE;"
            )

        # Commit the changes
        db_session.commit()
        db_session.close()
