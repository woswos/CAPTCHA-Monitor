import time
import random
import logging
from typing import Any, List, Optional

import docker
import port_for
import stem.control
from stem import SocketError, DescriptorUnavailable
from stem.control import Controller
from stem.util.log import get_logger

from captchamonitor.utils.config import Config
from captchamonitor.utils.exceptions import (
    TorLauncherInitError,
    StemConnectionInitError,
    StemDescriptorUnavailableError,
)
from captchamonitor.utils.small_scripts import hasattr_private


class TorLauncher:
    """
    Launch Tor with given configuration values
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize Tor Launcher

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :raises TorLauncherInitError: If Tor launcher wasn't able connect to the Tor container
        """
        # Public class attributes
        self.ip_address: str
        self.socks_port: int
        self.control_port: int
        self.relay_fingerprints: List[Any]

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__circuit_id: Controller.new_circuit
        self.__num_retries_on_fail: int = 3
        self.__delay_in_seconds_between_retries: int = 3

        try:
            self.__docker_network_name = self.__config["docker_network"]

        except Exception as exception:
            self.__logger.warning("Could not connect to Tor:\n %s", exception)
            raise TorLauncherInitError from exception

        # Silence the stem logger
        stem_logger = get_logger()
        stem_logger.propagate = False

        # Execute the private methods
        self.__launch_tor_container()
        self.__bind_stem_to_tor_container()

    def __launch_tor_container(self) -> None:
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
        self.socks_port = int(port_for.select_random())
        self.control_port = int(port_for.select_random())

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
                f"{self.socks_port}/tcp": self.socks_port,
                f"{self.control_port}/tcp": self.control_port,
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

    def __bind_stem_to_tor_container(self) -> None:
        """
        Binds Tor Stem to the Tor Container launched earlier

        :raises StemConnectionInitError: If stem wasn't initialized correctly
        """
        self.__tor_password = self.__config["docker_tor_authentication_password"]

        # Try connecting multiple times
        connected = False
        for _ in range(self.__num_retries_on_fail):
            try:
                self.__controller = Controller.from_port(
                    address=str(self.ip_address), port=int(self.control_port)
                )
                self.__controller.authenticate(password=self.__tor_password)
                connected = True
                break

            except SocketError as exception:
                self.__logger.debug(
                    "Unable to connect to the Tor Container, retrying: %s",
                    exception,
                )
                time.sleep(self.__delay_in_seconds_between_retries)

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

    def update_relay_descriptors(self) -> None:
        """
        Gets a copy of the current relay descriptors from the Tor Container using
        stem

        :raises StemDescriptorUnavailableError: If stem wasn't able to get relay descriptors
        """
        # Try connecting multiple times
        connected = False
        for _ in range(self.__num_retries_on_fail):
            try:
                self.relay_fingerprints = [
                    desc.fingerprint
                    for desc in self.__controller.get_network_statuses()
                ]
                connected = True
                break

            except DescriptorUnavailable as exception:
                self.__logger.debug(
                    "Unable to get relay descriptors, retrying: %s", exception
                )
                time.sleep(self.__delay_in_seconds_between_retries)

        # Check if connection was successfull
        if not connected:
            self.__logger.warning("Could not get relay descriptors after many retries")
            raise StemDescriptorUnavailableError

    # pylint: disable=E1101
    def __attach_stream(self, stream: stem.control.EventType.STREAM) -> None:
        """
        Attaches streams to the circuit id specified

        :param stream: stem.control.EventType.STREAM
        :type stream: stem.control.EventType.STREAM
        """
        if stream.status == "NEW":
            self.__controller.attach_stream(stream.id, self.__circuit_id)

    def create_new_circuit_to(
        self, exit_relay: str, guard_relay: Optional[str] = None
    ) -> None:
        """
        Create a two hop circuit between a guard relay and an exit relay. Uses the
        given exit relay and randomly chooses a guard relay if not provided one.

        :param exit_relay: Fingerprint of the exit relay to use
        :type exit_relay: str
        :param guard_relay: Fingerprint of the guard relay to use, defaults to None
        :type guard_relay: str, optional
        """
        # Get a fresh copy of the descriptors
        self.update_relay_descriptors()

        # Choose a guard relay randomly if not specified
        if guard_relay is None:
            while True:
                guard_relay = random.choice(self.relay_fingerprints)
                # Make sure the chosen guard relay is not same as the exit relay
                if guard_relay != exit_relay:
                    break

        self.__circuit_id = self.__controller.new_circuit(
            [guard_relay, exit_relay], await_build=True
        )

        # pylint: disable=E1101
        self.__controller.add_event_listener(
            self.__attach_stream, stem.control.EventType.STREAM
        )

        # leave stream management to us
        self.__controller.set_conf("__LeaveStreamsUnattached", "1")

    def reset_configuration(self) -> None:
        """
        Resets stem back to its original state
        """
        self.__controller.remove_event_listener(self.__attach_stream)
        self.__controller.reset_conf("__LeaveStreamsUnattached")

    def close(self) -> None:
        """
        Perform cleanup before going out of scope
        """
        if hasattr_private(self, "__controller"):
            # Close connection
            self.__controller.close()

            # Kill the container
            self.__container.kill()
