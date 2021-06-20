import time
import logging
from typing import Optional

import docker
import timeout_decorator


class ContainerManager:
    """
    Manages the Docker container with the given container name. It expects the
    containers to be already running.
    """

    def __init__(self, container_name: str) -> None:
        """
        Initializes the container manager

        :param container_name: The Docker container name to manage
        :type container_name: str
        """
        # Public class attributes
        self.container_name: str = container_name
        self.container_id: str

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__client = docker.APIClient(base_url="unix://var/run/docker.sock")

        # Calls to the class methods
        self.__get_container_id()

    @timeout_decorator.timeout(15)
    def __get_container_id(self) -> None:
        """
        Searches and finds the container ID based on the provided container name
        """
        while True:
            for container in self.__client.containers():
                if self.container_name in container["Names"][0]:
                    self.container_id = container["Id"]
                    return

    def __get_logs(self, tail: Optional[int] = 5) -> str:
        """
        Returns the logs of the container with the given ID

        :param tail: Last number of lines of logs to return, defaults to 5
        :type tail: int, optional
        :return: Logs
        :rtype: str
        """
        return str(self.__client.logs(container=self.container_id, tail=tail))

    @timeout_decorator.timeout(30)
    def __wait_until_healthy(self, healthy_message: str) -> None:
        """
        Blocks the execution until the container is healthy based on its logs

        :param healthy_message: The log message that indicates a healthy state
        :type healthy_message: str
        """
        self.__logger.info(
            "Waiting for container (%s) to become healthy",
            self.container_name,
        )

        while healthy_message not in self.__get_logs(tail=20):
            time.sleep(1)

        self.__logger.info(
            "Container (%s) is healthy now",
            self.container_name,
        )

    def __restart_container_if_unhealthy(
        self,
        unhealthy_message: str,
        healthy_message: str,
        force_restart: Optional[bool] = False,
    ) -> None:
        """
        Restarts the given container if it is healthy based on its log messages.
        Waits until the container becomes healthy after restart.

        :param unhealthy_message: The log message that indicates an unhealthy state
        :type unhealthy_message: str
        :param healthy_message: The log message that indicates a healthy state
        :type healthy_message: str
        :param force_restart: Should I restart the container even if it is healthy, defaults to False
        :type force_restart: bool, optional
        """
        # Check if the container has an error
        if (unhealthy_message in self.__get_logs(tail=5)) or force_restart:
            self.__logger.info(
                "Container (%s) is unhealthy",
                self.container_name,
            )
            self.restart_container()

            self.__wait_until_healthy(healthy_message=healthy_message)

    def restart_container(self) -> None:
        """
        Restarts the container with the given ID and updates the container ID
        based on the new container.
        """
        self.__logger.info("Restarting %s", self.container_name)

        # Restart the container
        self.__client.restart(self.container_id)

        # Get the new container id
        self.__get_container_id()

    def restart_browser_container_if_unhealthy(
        self, force_restart: Optional[bool] = False
    ) -> None:
        """
        Restarts a browser container if it is unhealthy

        :param force_restart: Should I restart the container even if it is healthy, defaults to False
        :type force_restart: bool, optional
        """
        self.__restart_container_if_unhealthy(
            unhealthy_message="Exiting due to channel error",
            healthy_message="Selenium Server is up and running",
            force_restart=force_restart,
        )
