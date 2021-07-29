# pylint: disable=C0115,C0116,W0212,W0621,W0702

import logging
import configparser

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Proxy, Relay, Domain, Fetcher
from captchamonitor.utils.database import Database
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import (
    insert_fixtures,
    get_random_http_proxy,
    get_traceback_information,
)
from captchamonitor.core.update_fetchers import UpdateFetchers

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--ci-mode",
        action="store_true",
        default=False,
        help="Run in CI mode and skip tests that require Docker",
    )


@pytest.fixture(autouse=True)
def _0_env_setup(monkeypatch, pytestconfig):
    """
    Patch environment variables to let tests use a separate database
    """
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


@pytest.fixture(autouse=True)
def _1_wipe_test_db_tables(pytestconfig):
    """
    Wipe all tables before each test function
    """
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
def __http_proxies(tor_proxy):
    """
    Meant to be only used by `insert_domains_fetchers_relays_proxies` in order to
    prevent repeated calls to the external proxy API
    """
    config_local = Config()
    return get_random_http_proxy(
        config=config_local, tor_proxy=tor_proxy, country="US", multiple=True
    )


@pytest.fixture()
def insert_domains_fetchers_relays_proxies(db_session, __http_proxies):
    """
    Insert fetchers before each test function
    """
    config_local = Config()

    relays = ["A53C46F5B157DD83366D45A8E99A244934A14C46"]
    domains = [
        "check.torproject.org",
        "duckduckgo.com",
        "stupid.urlextension",
        "api.ipify.org",
    ]
    proxy_country = "US"
    http_proxies = __http_proxies

    UpdateFetchers(config=config_local, db_session=db_session)

    for relay in relays:
        db_session.add(
            Relay(
                fingerprint=relay,
                ipv4_address="127.0.0.1",
                ipv4_exiting_allowed=True,
                ipv6_exiting_allowed=False,
            )
        )

    for domain in domains:
        db_session.add(
            Domain(
                domain=domain,
                supports_http=True,
                supports_https=True,
                supports_ftp=False,
                supports_ipv4=True,
                supports_ipv6=False,
                requires_multiple_requests=True,
            )
        )

    for proxy in http_proxies:
        db_session.add(
            Proxy(
                host=proxy[0],
                port=proxy[1],
                country=proxy_country,
                google_pass=False,
                anonymity="N",
                incoming_ip_different_from_outgoing_ip=False,
                ssl=True,
            )
        )

    db_session.commit()


@pytest.fixture()
def firefox_id(db_session):
    # pylint: disable=C0121
    return (
        db_session.query(Fetcher)
        .filter(Fetcher.method == "firefox_browser")
        .filter(Fetcher.uses_proxy_type == None)
        .one()
        .id
    )


@pytest.fixture()
def firefox_tor_proxy_id(db_session):
    return (
        db_session.query(Fetcher)
        .filter(Fetcher.method == "firefox_browser")
        .filter(Fetcher.uses_proxy_type == "tor")
        .one()
        .id
    )


@pytest.fixture()
def firefox_http_proxy_id(db_session):
    return (
        db_session.query(Fetcher)
        .filter(Fetcher.method == "firefox_browser")
        .filter(Fetcher.uses_proxy_type == "http")
        .one()
        .id
    )


@pytest.fixture()
def tor_browser_id(db_session):
    return (
        db_session.query(Fetcher)
        .filter(Fetcher.method == "tor_browser")
        .filter(Fetcher.uses_proxy_type == "tor")
        .one()
        .id
    )


@pytest.fixture(scope="session")
def tor_proxy():
    """
    Connect to the Tor container and return connection details
    """
    config_local = Config()
    tor_launcher = TorLauncher(config_local)
    proxy = (tor_launcher.ip_address, tor_launcher.socks_port)
    yield proxy
    tor_launcher.close()


@pytest.fixture()
def tor_proxy_to_relay(request, config):
    """
    Request parameter is used for specifying a list of exit relays. Tor Launcher
    tries to connect to one of the specified relays.
    """
    tor_launcher = TorLauncher(config)

    # Connect to a specific relay if any specified
    # Check https://docs.pytest.org/en/stable/example/parametrize.html#indirect-parametrization
    assert hasattr(
        request, "param"
    ), "You need to provide a 'list' of relay fingerprint(s)"
    assert isinstance(
        request.param, list
    ), "You need to provide the relay fingerprint(s) in a list"

    connected = False
    for relay in request.param:
        try:
            tor_launcher.create_new_circuit_to(relay)
            connected = True
            logger.info("Connected to exit relay %s", relay)
        except:
            error = get_traceback_information()
            logger.info("Couldn't connect to exit relay %s:\n %s", relay, error)
        else:
            break

    # Make sure that the connection is successfull
    assert connected is True, "Could not connect to any of the provided exit relays"

    proxy = (tor_launcher.ip_address, tor_launcher.socks_port)
    yield proxy
    tor_launcher.close()


@pytest.fixture(scope="module")
def http_proxy(request, tor_proxy):
    """
    Find and return random HTTP proxies
    """
    config_local = Config()
    if hasattr(request, "param"):
        country = request.param.get("country", None)
        multiple = request.param.get("multiple", False)
        return get_random_http_proxy(
            config=config_local,
            tor_proxy=tor_proxy,
            country=country,
            multiple=multiple,
        )
    return get_random_http_proxy(config=config_local, tor_proxy=tor_proxy)


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
