import os
import sys
import pickle
import traceback
from typing import Any, Tuple

import docker
import requests

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
        received_id = docker.from_env().containers.get(hostname()).name.split("_")[-1]

        if received_id.isnumeric():
            id_value = int(received_id)

    except docker.errors.NotFound:
        # If we don't have access to Docker, assume we are running in CI
        pass

    return id_value


def get_random_http_proxy() -> Tuple[str, int]:
    """
    Queries pubproxy.com and returns a random HTTP proxy that supports HTTPS

    :return: A random HTTP proxy host and port
    :rtype: Tuple[str, int]
    """
    api_url = "http://pubproxy.com/api/proxy?https=true"
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
    return hasattr(given_object, f"_{given_object.__class__.__name__}{attribute}")
