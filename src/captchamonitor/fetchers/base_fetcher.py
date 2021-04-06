import time
import logging
from selenium import webdriver
from captchamonitor.utils.exceptions import FetcherConnectionInitError


class BaseFetcher:
    """
    Base fetcher class that will inherited by the actual fetchers, used to unify
    the fetcher interfaces
    """

    def __init__(
        self, config, url, tor_launcher, timeout=30, options=None, use_tor=True
    ):
        """
        Initializes the fetcher with given arguments and tries to fetch the given
        URL

        :param url: The URL to fetch
        :type url: str
        :param tor_launcher: TorLauncher class
        :type tor_launcher: TorLauncher class
        :param timeout: Maximum time allowed for a web page to load, defaults to 30
        :type timeout: int, optional
        :param options: Dictionary of options to pass to the fetcher, defaults to None
        :type options: dict, optional
        :param use_tor: Should I connect the fetcher to Tor? Has no effect when using Tor Browser, defaults to True
        :type use_tor: bool, optional
        """
        # Public attributes
        self.url = url
        self.use_tor = use_tor
        self.timeout = timeout
        self.options = options
        self.driver = None

        # Other required attributes
        self.tor_launcher = tor_launcher
        self.config = config
        self.selenium_options = None
        self.selenium_executor_url = None

        self.logger = logging.getLogger(__name__)

    @staticmethod
    def get_selenium_executor_url(container_host, container_port):
        """
        Returns the command executor URL that will be used by Selenium remote webdriver

        :param container_host: Host to the Selenium remote webdriver
        :type container_host: str
        :param container_port: Port to the Selenium remote webdriver
        :type container_port: str
        :return: Command executor URL
        :rtype: str
        """
        return f"http://{container_host}:{container_port}/wd/hub"

    def connect_to_selenium_remote_web_driver(
        self, container_name, desired_capabilities, command_executor, options
    ):
        """
        Connects Selenium remote driver to a browser container

        :param container_name: Name of the target browser, just will be used for logging
        :type container_name: str
        :param desired_capabilities: webdriver.DesiredCapabilities object from Selenium
        :type desired_capabilities: webdriver.DesiredCapabilities object
        :param command_executor: Command executor URL for Selenium
        :type command_executor: str
        :param options: webdriver.Options from Selenium
        :type options: webdriver.Options object
        :raises FetcherConnectionInitError: If it wasn't able to connect to the webdriver
        """
        # Connect to browser container
        connected = False
        for _ in range(3):
            try:
                self.driver = webdriver.Remote(
                    desired_capabilities=desired_capabilities,
                    command_executor=command_executor,
                    options=options,
                )
                connected = True
                break

            except ConnectionRefusedError as exception:
                self.logger.debug(
                    "Unable to connect to the %s container, retrying: %s",
                    container_name,
                    exception,
                )
                time.sleep(3)

        # Check if connection was successfull
        if not connected:
            self.logger.warning(
                "Could not connect to the %s container after many retries",
                container_name,
            )
            raise FetcherConnectionInitError

        # Set driver timeout
        self.driver.set_page_load_timeout(self.timeout)

        # Log the current status
        self.logger.info("Connected to the %s container", container_name)

    def fetch_with_selenium_remote_web_driver(self):
        """
        Fetches the given URL with the remote web driver
        """
        self.driver.get(self.url)

        return self.driver.page_source

    def __del__(self):
        if self.driver is not None:
            self.driver.quit()
