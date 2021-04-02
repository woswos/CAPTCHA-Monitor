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
        self.logger = logging.getLogger(__name__)
        self.config = config

        try:
            self.docker_network_name = self.config["docker_network"]

        except Exception as exception:
            self.logger.warning("Could not connect to Tor:\n %s", exception)
            raise TorLauncherInitError from exception

        self.launch_tor_container()
        self.bind_stem_to_tor_container()

    def launch_tor_container(self):
        """
        Launches a new Tor container with the given configuration

        :raises TorLauncherInitError: If it cannot figure out the right Docker network
        """
        # Obtain the Docker client from the environment
        client = docker.from_env()

        # Find the CAPTCHA Monitor network
        networks = client.networks.list(names=[self.docker_network_name])

        if len(networks) == 0:
            self.logger.warning("Could not find the Docker network for CAPTCHA Monitor")
            raise TorLauncherInitError

        if len(networks) != 1:
            self.logger.warning(
                "There are multiple Docker networks for CAPTCHA Monitor, I don't know which one to choose"
            )
            raise TorLauncherInitError

        # Find unused ports
        self.socks_port = str(port_for.select_random())
        self.control_port = str(port_for.select_random())
        self.tor_dir = "/var/lib/tor"

        # Initialize a new Tor container
        self.container = client.containers.run(
            image=self.config["docker_tor_container_image"],
            command=[
                "/usr/bin/tor",
                "--SocksPort",
                f"0.0.0.0:{self.socks_port}",
                "--ControlPort",
                f"0.0.0.0:{self.control_port}",
                "--HashedControlPassword",
                str(self.config["docker_tor_authentication_password_hashed"]),
                # f"--DataDirectory {self.tor_dir}",
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
        self.container.reload()
        # Now obtain the IP address
        container_networks = self.container.attrs["NetworkSettings"]["Networks"]
        self.ip_address = str(list(container_networks.values())[0]["IPAddress"])

        self.logger.debug(
            "Initialized new Tor container at %s with %s as socks port and %s as control port",
            self.ip_address,
            self.socks_port,
            self.control_port,
        )

    def bind_stem_to_tor_container(self):
        """
        Binds Tor Stem to the Tor Container launched earlier
        """

        # Make sure the container was actually intialized
        assert hasattr(self, "container")
        assert hasattr(self, "socks_port")
        assert hasattr(self, "control_port")
        assert hasattr(self, "tor_dir")
        assert hasattr(self, "ip_address")

        self.tor_password = self.config["docker_tor_authentication_password"]

        # Try connecting 3 times
        for _ in range(3):
            try:
                self.controller = Controller.from_port(
                    address=str(self.ip_address), port=int(self.control_port)
                )
                self.controller.authenticate(password=self.tor_password)
                break
            except stem.SocketError as exception:
                self.logger.debug(
                    "Unable to connect to the Tor Container, retrying: %s",
                    exception,
                )
                time.sleep(3)

        # Check if database connection was made
        if not hasattr(self, "controller"):
            self.logger.warning(
                "Could not connect to the Tor Container after many retries"
            )
            raise StemConnectionInitError

        self.logger.info(
            "Connected to the Tor Container, the Tor version running on the container is %s",
            self.controller.get_version(),
        )

    def __del__(self):
        # Close connection
        self.controller.close()

        # Kill the container
        self.container.kill()
