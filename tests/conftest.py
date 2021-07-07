import configparser

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import insert_fixtures, get_random_http_proxy


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
        config_local = Config()
        database = Database(
            config_local["db_host"],
            config_local["db_port"],
            config_local["db_name"],
            config_local["db_user"],
            config_local["db_password"],
        )
        db_session_local = database.session()

        # Wipe the database tables and reset the autoincrement counters
        meta = database.model.metadata
        for table in meta.tables.keys():
            db_session_local.execute(
                f"TRUNCATE TABLE {table.lower()} RESTART IDENTITY CASCADE;"
            )

        # Commit the changes
        db_session_local.commit()
        db_session_local.close()


@pytest.fixture(scope="session")
def tor_proxy():
    config_local = Config()
    tor_launcher = TorLauncher(config_local)
    proxy = (tor_launcher.ip_address, tor_launcher.socks_port)
    yield proxy
    tor_launcher.close()


@pytest.fixture(scope="session")
def http_proxy():
    proxy = get_random_http_proxy()
    return proxy


@pytest.fixture(scope="session")
def config():
    config_local = Config()
    return config_local


@pytest.fixture()
def db_session():
    config_local = Config()
    database = Database(
        config_local["db_host"],
        config_local["db_port"],
        config_local["db_name"],
        config_local["db_user"],
        config_local["db_password"],
    )
    db_session_local = database.session()
    insert_fixtures(db_session_local, config_local, "metadata.json")
    yield db_session_local
    db_session_local.close()
