import os
import json
import shutil
import logging
from typing import Any, Union, Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from captchamonitor.utils.config import Config
from captchamonitor.utils.exceptions import HarExportExtensionError
from captchamonitor.utils.tor_launcher import TorLauncher


class BaseFetcher:
    """
    Base fetcher class that will be inherited by the actual fetchers, used to unify
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
        Initializes the fetcher with given arguments and tries to fetch the given URL

        :param config: Config class
        :type config: Config
        :param url: The URL to fetch
        :type url: str
        :param tor_launcher: TorLauncher class
        :type tor_launcher: TorLauncher
        :param page_timeout: Maximum time allowed for a web page to load, defaults to 30
        :type page_timeout: int
        :param script_timeout: Maximum time allowed for a JS script to respond, defaults to 30
        :type script_timeout: int
        :param options: Dictionary of options to pass to the fetcher, defaults to None
        :type options: Optional[dict], optional
        :param use_tor: Should I connect the fetcher to Tor? Has no effect when using Tor Browser, defaults to True
        :type use_tor: bool
        """
        # Public class attributes
        self.url: str = url
        self.use_tor: bool = use_tor
        self.page_timeout: int = page_timeout
        self.script_timeout: int = script_timeout
        self.options: Optional[dict] = options
        self.container_host: str
        self.container_port: str
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

        # Update default options with the specified ones
        if self.options is not None:
            self.page_timeout = self.options.get("page_timeout", page_timeout)
            self.script_timeout = self.options.get("script_timeout", script_timeout)

        # Get the extension path for xpi
        self._har_export_extension_xpi: str = self._config[
            "asset_har_export_extension_xpi"
        ]

        # Get the extension id for xpi
        self._har_export_extension_xpi_id: str = self._config[
            "asset_har_export_extension_xpi_id"
        ]

        # Get the extension path for crx
        self._har_export_extension_crx: str = self._config[
            "asset_har_export_extension_crx"
        ]

        self._check_extension_validity(self._har_export_extension_xpi, ".xpi")
        self._check_extension_validity(self._har_export_extension_crx, ".crx")

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
        """
        # Connect to browser container
        self.driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor=command_executor,
            options=options,
        )

        # Set driver timeout
        self.driver.set_page_load_timeout(self.page_timeout)

        # Set timeout for HAR export trigger extension
        self.driver.set_script_timeout(self.script_timeout)

        # Log the current status
        self._logger.debug("Connected to the %s container", container_name)

    def _check_extension_validity(self, extension: str, endswith: str) -> None:
        """
        Checks if given extension file exists and is valid

        :param extension: Absolute path to the extension file
        :type extension: str
        :param endswith: The file extension for the browser extension
        :type endswith: str
        :raises HarExportExtensionError: If given extension is not valid
        """
        if not os.path.isfile(extension):
            self._logger.warning(
                "Provided extension file doesn't exist: %s",
                extension,
            )
            raise HarExportExtensionError

        if not extension.endswith(endswith):
            self._logger.warning(
                "Provided extension file is not valid: %s",
                extension,
            )
            raise HarExportExtensionError

    def _install_har_export_extension_xpi(self, directory: str) -> None:
        """
        Installs the HAR Export Trigger extension to Firefox based browsers

        :param directory: Absolute directory path to install the extension
        :type directory: str
        """
        addon_path = os.path.join(directory, self._har_export_extension_xpi_id)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chmod(directory, 0o755)
        shutil.copy(self._har_export_extension_xpi, addon_path + ".xpi")

    def _install_har_export_extension_crx(
        self, chrome_options: webdriver.ChromeOptions
    ) -> None:
        """
        Installs the HAR Export Trigger extension to Chromium based browsers

        :param chrome_options: webdriver.ChromeOptions from the Selenium driver
        :type chrome_options: webdriver.ChromeOptions
        """
        chrome_options.add_extension(self._har_export_extension_crx)

    def _fetch_with_selenium_remote_web_driver(self) -> None:
        """
        Fetches the given URL with the remote web driver
        """
        self.driver.get(self.url)

        self.page_source = self.driver.page_source
        self.page_cookies = self.driver.get_cookies()
        self.page_title = self.driver.title
        har_dict = self.driver.execute_async_script(
            """
            var callback = arguments[arguments.length - 1];
            HAR.triggerExport().then((harLog) => { callback(harLog) });
            """
        )
        self.page_har = json.dumps({"log": har_dict})

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

    def close(self) -> None:
        """
        Clean up before going out of scope
        """
        if hasattr(self, "driver"):
            try:
                self.driver.quit()
            except WebDriverException:
                # We can safely ignore "No active session with ID XXXXX" exceptions
                pass
