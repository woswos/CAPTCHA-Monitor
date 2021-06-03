import logging
import random
from typing import Optional, Any, List
import docker
import port_for
import stem
import stem.control
from stem.util.log import get_logger
from stem.control import Controller
from captchamonitor.utils.config import Config
from captchamonitor.utils.small_scripts import (
    retry,
    Retrying,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    after_log,
)
from captchamonitor.utils.exceptions import (
    TorLauncherInitError,
    StemConnectionInitError,
    StemDescriptorUnavailableError,
)


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
        self.socks_port: str
        self.control_port: str
        self.relay_fingerprints: List[Any]

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__circuit_id: Controller.new_circuit
        self.__retryer: Retrying = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(3),
            retry=(
                retry_if_exception_type(stem.SocketError)
                | retry_if_exception_type(stem.DescriptorUnavailable)
            ),
            after=after_log(self.__logger, logging.DEBUG),
            reraise=True,
        )

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        retry=retry_if_exception_type(stem.SocketError),
        reraise=True,
    )
    def __get_stem_controller_from_port(self) -> Controller:
        return Controller.from_port(
            address=str(self.ip_address), port=int(self.control_port)
        )

    def __bind_stem_to_tor_container(self) -> None:
        """
        Binds Tor Stem to the Tor Container launched earlier

        :raises StemConnectionInitError: If stem wasn't initialized correctly
        """

        self.__tor_password = self.__config["docker_tor_authentication_password"]

        # Try connecting to the Tor container
        try:
            self.__controller = self.__get_stem_controller_from_port()

        except stem.SocketError as exception:
            self.__logger.warning(
                "Could not connect to the Tor Container after many retries: %s",
                exception,
            )
            raise StemConnectionInitError from exception

        # Authenticate
        self.__controller.authenticate(password=self.__tor_password)

        self.__logger.debug(
            "Connected to the Tor Container, the Tor version running on the container is %s",
            self.__controller.get_version(),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        retry=retry_if_exception_type(stem.DescriptorUnavailable),
        reraise=True,
    )
    def __get_network_statuse_from_stem(self) -> List[object]:
        return self.__controller.get_network_statuses

    def update_relay_descriptors(self) -> None:
        """
        Gets a copy of the current relay descriptors from the Tor Container using
        stem

        :raises StemDescriptorUnavailableError: If stem wasn't able to get relay descriptors
        """
        # Try retrieving the descriptors
        try:
            network_statuses = self.__get_network_statuse_from_stem()

        except stem.DescriptorUnavailable as exception:
            self.__logger.warning(
                "Could not get relay descriptors after many retries: %s",
                exception,
            )
            raise StemDescriptorUnavailableError from exception

        self.relay_fingerprints = [desc.fingerprint for desc in network_statuses]

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

    def __del__(self) -> None:
        """
        Perform cleanup before going out of scope
        """
        if hasattr(self, "__controller"):
            # Close connection
            self.__controller.close()

            # Kill the container
            self.__container.kill()
