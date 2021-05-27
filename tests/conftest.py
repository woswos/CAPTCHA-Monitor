import os.path
import configparser
import pytest


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

    # Read .env file
    with open(target_env_file) as f:
        file_content = "[dummy_section]\n" + f.read()
    config_parser = configparser.RawConfigParser()
    config_parser.read_string(file_content)

    # Patch current env variables
    for key, value in config_parser["dummy_section"].items():
        monkeypatch.setenv(key.upper(), value)
