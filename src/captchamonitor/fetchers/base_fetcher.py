import os
import shutil
import logging
from typing import Optional, Union, Any
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import (
    Retrying,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    after_log,
)
from captchamonitor.utils.exceptions import (
    FetcherConnectionInitError,
    FetcherURLFetchError,
    HarExportExtensionXpiError,
)


class BaseFetcher:
    """
    Base fetcher class that will inherited by the actual fetchers, used to unify
    the fetcher interfaces
    """

    def __init__(
        self,
        config: Config,
        url: str,
        tor_launcher: TorLauncher,
        page_timeout: int = 30,
        script_timeout: int = 30,
        options: Optional[dict] = None,
        use_tor: bool = True,
    ) -> None:
        """
        Initializes the fetcher with given arguments and tries to fetch the given
        URL

        :param url: The URL to fetch
        :type url: str
        :param tor_launcher: TorLauncher class
        :type tor_launcher: TorLauncher class
        :param page_timeout: Maximum time allowed for a web page to load, defaults to 30
        :type page_timeout: int, optional
        :param script_timeout: Maximum time allowed for a JS script to respond, defaults to 30
        :type script_timeout: int, optional
        :param options: Dictionary of options to pass to the fetcher, defaults to None
        :type options: dict, optional
        :param use_tor: Should I connect the fetcher to Tor? Has no effect when using Tor Browser, defaults to True
        :type use_tor: bool, optional
        """
        # Public attributes
        self.url: str = url
        self.use_tor: bool = use_tor
        self.page_timeout: int = page_timeout
        self.script_timeout: int = script_timeout
        self.options: Optional[dict] = options
        self.driver: webdriver.Remote
        self.page_source: str
        self.page_cookies: str
        self.page_title: str
        self.page_har: str

        # Protected class attributes
        self._logger = logging.getLogger(__name__)
        self._tor_launcher: TorLauncher = tor_launcher
        self._config: Config = config
        self._selenium_options: Any
        self._selenium_executor_url: str
        self._desired_capabilities: webdriver.DesiredCapabilities
        self._num_retries_on_fail: int = 3
        self._delay_in_seconds_between_retries: int = 3
        self._retryer: Retrying = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(3),
            retry=(retry_if_exception_type(ConnectionRefusedError)),
            after=after_log(self._logger, logging.DEBUG),
            reraise=True,
        )

        # Get the extension path
        self._har_export_extension_xpi = self._config["asset_har_export_extension_xpi"]

        # Get the extension id
        self._har_export_extension_xpi_id = self._config[
            "asset_har_export_extension_xpi_id"
        ]

        # Check if the har extension path is a file and a xpi file
        if not os.path.isfile(self._har_export_extension_xpi):
            self._logger.warning(
                "Provided extension file doesn't exist: %s",
                self._har_export_extension_xpi,
            )
            raise HarExportExtensionXpiError

        if not self._har_export_extension_xpi.endswith(".xpi"):
            self._logger.warning(
                "Provided extension file is not valid: %s",
                self._har_export_extension_xpi,
            )
            raise HarExportExtensionXpiError

    @staticmethod
    def _get_selenium_executor_url(container_host: str, container_port: str) -> str:
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

    def _connect_to_selenium_remote_web_driver(
        self,
        container_name: str,
        desired_capabilities: webdriver.DesiredCapabilities,
        command_executor: str,
        options: Optional[list] = None,
    ) -> None:
        """
        Connects Selenium remote driver to a browser container

        :param container_name: Name of the target browser, just will be used for logging
        :type container_name: str
        :param desired_capabilities: webdriver.DesiredCapabilities object from Selenium
        :type desired_capabilities: webdriver.DesiredCapabilities object
        :param command_executor: Command executor URL for Selenium
        :type command_executor: str
        :param options: webdriver.Options from Selenium, defaults to None
        :type options: webdriver.Options object, optional
        :raises FetcherConnectionInitError: If it wasn't able to connect to the webdriver
        """
        # Connect to browser container
        try:
            self.driver = self._retryer(
                webdriver.Remote,
                desired_capabilities=desired_capabilities,
                command_executor=command_executor,
                options=options,
            )

        except ConnectionRefusedError as exception:
            self._logger.warning(
                "Could not connect to the %s container after many retries: %s",
                container_name,
                exception,
            )
            raise FetcherConnectionInitError from exception

        # Set driver timeout
        self.driver.set_page_load_timeout(self.page_timeout)

        # Set timeout for HAR export trigger
        self.driver.set_script_timeout(self.script_timeout)

        # Log the current status
        self._logger.debug("Connected to the %s container", container_name)

    def _install_har_export_extension(self, directory: str) -> None:
        """
        Installs the HAR Export Trigger extension

        :param directory: Absolute directory path to install the extension
        :type directory: str
        """
        addon_path = os.path.join(directory, self._har_export_extension_xpi_id)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chmod(directory, 0o755)
        shutil.copy(self._har_export_extension_xpi, addon_path + ".xpi")

    def _fetch_with_selenium_remote_web_driver(self) -> None:
        """
        Fetches the given URL with the remote web driver
        """
        try:
            self.driver.get(self.url)

        except WebDriverException as exception:
            self._logger.debug("Unable to fetch %s because of: %s", self.url, exception)
            raise FetcherURLFetchError(exception) from exception

        self.page_source = self.driver.page_source
        self.page_cookies = self.driver.get_cookies()
        self.page_title = self.driver.title
        self.page_har = self.driver.execute_async_script(
            """
            var callback = arguments[arguments.length - 1];
            HAR.triggerExport().then((harLog) => { callback(harLog) });
            """
        )

    def get_selenium_logs(self) -> dict:
        """
        Obtains and returns all kinds of available Selenium logs

        :return: Dictionary of logs with different log types
        :rtype: dict
        """
        logs = {}
        for log_type in self.driver.log_types:
            logs[log_type] = self.driver.get_log(log_type)
        return logs

    def get_screenshot_from_selenium_remote_web_driver(
        self, image_type: Optional[str] = "base64"
    ) -> Union[str, bytes]:
        """
        Takes a screenshot of the current page

        :param image_type: Type of screenshot to return, defaults to "base64"
        :type image_type: str, optional
        :return: Screenshot as png file or base64 encoded depending on selected type]
        :rtype: png file or str depending on selected type
        """
        if image_type == "base64":
            return self.driver.get_screenshot_as_base64()
        # else
        return self.driver.get_screenshot_as_png()

    def __del__(self) -> None:
        if hasattr(self, "driver"):
            self.driver.quit()
