import configparser
import pytest


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    # Read .env file
    with open("/.env") as f:
        file_content = "[dummy_section]\n" + f.read()
    config_parser = configparser.RawConfigParser()
    config_parser.read_string(file_content)

    # Patch current env variables
    for key, value in config_parser["dummy_section"].items():
        monkeypatch.setenv(key.upper(), value)
