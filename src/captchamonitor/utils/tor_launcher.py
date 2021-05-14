import logging
import time
import docker
import port_for
import stem
from stem.control import Controller
from captchamonitor.utils.exceptions import (
    TorLauncherInitError,
    StemConnectionInitError,
)


class TorLauncher:
    """
    Launch Tor with given configuration values
    """

    def __init__(self, config):
        """
        Initialize Tor Launcher
        """
        # Public class attributes
        self.ip_address = None
        self.socks_port = None
        self.control_port = None

        self.__logger = logging.getLogger(__name__)
        self.__config = config

        try:
            self.__docker_network_name = self.__config["docker_network"]

        except Exception as exception:
            self.__logger.warning("Could not connect to Tor:\n %s", exception)
            raise TorLauncherInitError from exception

        self.__launch_tor_container()
        self.__bind_stem_to_tor_container()

    def __launch_tor_container(self):
        """
        Launches a new Tor container with the given configuration

        :raises TorLauncherInitError: If it cannot figure out the right Docker network
        """
        # Obtain the Docker client from the environment
        client = docker.from_env()

        # Find the CAPTCHA Monitor network
        networks = client.networks.list(names=[self.__docker_network_name])

        if len(networks) == 0:
            self.__logger.warning(
                "Could not find the Docker network for CAPTCHA Monitor"
            )
            raise TorLauncherInitError

        if len(networks) != 1:
            self.__logger.warning(
                "There are multiple Docker networks for CAPTCHA Monitor, I don't know which one to choose"
            )
            raise TorLauncherInitError

        # Find unused ports
        self.socks_port = str(port_for.select_random())
        self.control_port = str(port_for.select_random())

        # Initialize a new Tor container
        self.__container = client.containers.run(
            image=self.__config["docker_tor_container_image"],
            command=[
                "/usr/bin/tor",
                "--SocksPort",
                f"0.0.0.0:{self.socks_port}",
                "--ControlPort",
                f"0.0.0.0:{self.control_port}",
                "--HashedControlPassword",
                str(self.__config["docker_tor_authentication_password_hashed"]),
                # "--DataDirectory '/var/lib/tor'",
                # "--CookieAuthentication 1",
                # "--PathsNeededToBuildCircuits 0.95",
                # "--LearnCircuitBuildTimeout 10",
                # "--CircuitBuildTimeout 10",
                # # "__DisablePredictedCircuits 1",
                # # "__LeaveStreamsUnattached 1",
                # "--FetchHidServDescriptors 0",
                # "--MaxCircuitDirtiness 10",
                # "--UseMicroDescriptors 1",
            ],
            network=networks[0].id,
            detach=True,
            auto_remove=True,
            ports={
                f"{self.socks_port}/tcp": int(self.socks_port),
                f"{self.control_port}/tcp": int(self.control_port),
            },
        )

        # Reload container attributes
        self.__container.reload()
        # Now obtain the IP address
        container_networks = self.__container.attrs["NetworkSettings"]["Networks"]
        self.ip_address = str(list(container_networks.values())[0]["IPAddress"])

        self.__logger.debug(
            "Initialized new Tor container at %s with %s as socks port and %s as control port",
            self.ip_address,
            self.socks_port,
            self.control_port,
        )

    def __bind_stem_to_tor_container(self):
        """
        Binds Tor Stem to the Tor Container launched earlier
        """
        self.__tor_password = self.__config["docker_tor_authentication_password"]

        # Try connecting 3 times
        connected = False
        for _ in range(3):
            try:
                self.__controller = Controller.from_port(
                    address=str(self.ip_address), port=int(self.control_port)
                )
                self.__controller.authenticate(password=self.__tor_password)
                connected = True
                break

            except stem.SocketError as exception:
                self.__logger.debug(
                    "Unable to connect to the Tor Container, retrying: %s",
                    exception,
                )
                time.sleep(3)

        # Check if connection was successfull
        if not connected:
            self.__logger.warning(
                "Could not connect to the Tor Container after many retries"
            )
            raise StemConnectionInitError

        self.__logger.debug(
            "Connected to the Tor Container, the Tor version running on the container is %s",
            self.__controller.get_version(),
        )

    def __del__(self):
        # Close connection
        self.__controller.close()

        # Kill the container
        self.__container.kill()
