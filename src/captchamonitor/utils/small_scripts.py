import os
import sys
import json
import pickle
import importlib
import traceback
from typing import Any, Tuple

import docker
import requests
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config

# Deep copies objects
deep_copy = lambda obj: pickle.loads(pickle.dumps(obj))


def hostname() -> str:
    """
    Get the current hostname

    :return: current hostname
    :rtype: str
    """
    return os.popen("hostname").read().strip()


def node_id() -> int:
    """
    Get the node id of the current container

    :return: Node id of the current container
    :rtype: int
    """
    id_value = 0

    try:
        received_id = (
            docker.from_env().containers.get(hostname()).name.split("_")[-1]
        )

        if received_id.isnumeric():
            id_value = int(received_id)

    except docker.errors.NotFound:
        # If we don't have access to Docker, assume we are running in CI
        pass

    return id_value


def get_random_http_proxy(country: str = None) -> Tuple[str, int]:
    """
    Queries pubproxy.com and returns a random HTTP proxy that supports HTTPS

    :param country: Country Code, if nothing is given, still the api will fetch a ip and proxy
    :type country: str
    :return: A random HTTP proxy host and port
    :rtype: Tuple[str, int]
    """
    api_url = f"http://pubproxy.com/api/proxy?https=true&last_check=5&speed=10&type=http&country={country}"
    result = requests.get(api_url).json()
    proxy = result["data"][0]
    return (str(proxy["ip"]), int(proxy["port"]))


def get_traceback_information() -> str:
    """
    Returns the most recent traceback information in string format

    :return: Most recent traceback information in string format
    :rtype: str
    """
    # Get traceback information
    T, V, TB = sys.exc_info()
    error = "".join(traceback.format_exception(T, V, TB))
    return error


def hasattr_private(given_object: Any, attribute: str) -> bool:
    """
    Returns True if the given private attribute exists

    :param given_object: The class object
    :type given_object: Any
    :param attribute: Name of the private class attribute
    :type attribute: str
    :return: True is class attribute exists
    :rtype: bool
    """
    return hasattr(
        given_object, f"_{given_object.__class__.__name__}{attribute}"
    )


def insert_fixtures(
    db_session: sessionmaker,
    config: Config,
    fixture_file: str,
    models_module: str = "captchamonitor.utils.models",
) -> None:
    """
    Inserts given JSON formatted fixture file into the database

    :param db_session: Database session used to connect to the database
    :type db_session: sessionmaker
    :param config: The config class instance that contains global configuration values
    :type config: Config
    :param fixture_file: Absolute path to the fixture file
    :type fixture_file: str
    :param models_module: The location of the file that stores the database models, defaults to "captchamonitor.utils.models"
    :type models_module: str
    :raises Exception: If there there was an issue with database inserting
    """
    fixture_file_path = os.path.join(config["fixture_location"], fixture_file)

    with open(fixture_file_path, "r") as file:
        fixture = json.loads(file.read())

    instances = []
    for data in fixture:
        if "model" in data:
            module = importlib.import_module(models_module)
            model = getattr(module, data["model"])
            instance = model(**data["fields"])
            instances.append(instance)

    try:
        for instance in instances:
            db_session.merge(instance)
            db_session.flush()
            db_session.commit()

    except Exception:
        db_session.rollback()
        raise
