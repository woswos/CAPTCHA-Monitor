import os
import pickle
from typing import cast, Any
import docker
import tenacity

# Add typing to tenacity functions
Retrying = cast(Any, tenacity.Retrying)
retry = cast(Any, tenacity.retry)
stop_after_attempt = cast(Any, tenacity.stop_after_attempt)
wait_fixed = cast(Any, tenacity.wait_fixed)
retry_if_exception_type = cast(Any, tenacity.retry_if_exception_type)
after_log = cast(Any, tenacity.after_log)

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
