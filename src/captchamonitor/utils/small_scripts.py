import os
import pickle
import docker

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
    received_id = docker.from_env().containers.get(hostname()).name.split("_")[-1]

    if not received_id.isnumeric():
        return 0

    return int(received_id)
