import os
import json
import time
import shutil
import logging
from typing import Any, Tuple, Union, Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from captchamonitor.utils.config import Config
from captchamonitor.utils.exceptions import MissingProxy, HarExportExtensionError


class BaseFetcher:
    """
    Base fetcher class that will be inherited by the actual fetchers, used to unify
    the fetcher interfaces
    """

    def __init__(
        self,
        config: Config,
        url: str,
        proxy: Optional[Tuple[str, int]] = None,
        use_proxy_type: Optional[str] = None,
        page_timeout: int = 30,
        script_timeout: int = 30,
        url_change_timeout: int = 30,
        explicit_wait_duration: int = 5,
        export_har: bool = True,
        remove_gdpr: bool = True,
        disable_javascript: bool = False,
        disable_cookies: bool = False,
        options: Optional[dict] = None,
    ) -> None:
        """
        Initializes the fetcher with given arguments and tries to fetch the given URL

        :param config: Config class
        :type config: Config
        :param url: The URL to fetch
        :type url: str
        :param proxy: Proxy host and port, defaults to None
        :type proxy: Optional[Tuple[str, int]], optional
        :param use_proxy_type: Proxy type to use: "tor" or "http", defaults to None
        :type use_proxy_type: Optional[str], optional
        :param page_timeout: Maximum time allowed in seconds for a web page to load, defaults to 30
        :type page_timeout: int
        :param script_timeout: Maximum time allowed in seconds for a JS script to respond, defaults to 30
        :type script_timeout: int
        :param url_change_timeout: Maximum time allowed in seconds while waiting for driver URL to change, defaults to 30
        :type url_change_timeout: int
        :param explicit_wait_duration: Amount of time in seconds to wait after fetching a page, defaults to 5
        :type explicit_wait_duration: int
        :param export_har: Should I record and export the HAR file?, defaults to True
        :type export_har: bool
        :param remove_gdpr: Should I click or remove GDPR cookie related popups?, defaults to True
        :type remove_gdpr: bool
        :param disable_javascript: Disable JavaScript completely, defaults to False
        :type disable_javascript: bool
        :param disable_cookies: Disable cookies completely, defaults to False
        :type disable_cookies: bool
        :param options: Dictionary of additional options to pass to the fetcher, defaults to None
        :type options: Optional[dict], optional
        :raises MissingProxy: If use_proxy_type is not None but no proxy provided
        """
        # Public class attributes
        self.url: str = url
        self.use_proxy_type: Optional[str] = use_proxy_type
        self.page_timeout: int = page_timeout
        self.script_timeout: int = script_timeout
        self.url_change_timeout: int = url_change_timeout
        self.explicit_wait_duration: int = explicit_wait_duration
        self.export_har: bool = export_har
        self.remove_gdpr: bool = remove_gdpr
        self.disable_javascript: bool = disable_javascript
        self.disable_cookies: bool = disable_cookies
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
        self._proxy: Optional[Tuple[str, int]] = proxy
        self._proxy_host: str
        self._proxy_port: int
        self._config: Config = config
        self._selenium_options: Any
        self._selenium_executor_url: str
        self._desired_capabilities: webdriver.DesiredCapabilities

        # Check if use_proxy_type is set to True but proxy is not passed
        if (self.use_proxy_type is not None) and (self._proxy is None):
            raise MissingProxy

        # Extract the proxy host and port
        if self._proxy is not None:
            self._proxy_host = str(self._proxy[0])  # type: ignore
            self._proxy_port = int(self._proxy[1])  # type: ignore

        # Update default options with the specified ones
        if self.options is not None:
            self.export_har = self.options.get("export_har", export_har)
            self.remove_gdpr = self.options.get("remove_gdpr", remove_gdpr)

            self.disable_javascript = self.options.get(
                "disable_javascript", disable_javascript
            )
            self.disable_cookies = self.options.get("disable_cookies", disable_cookies)

            self.page_timeout = self.options.get("page_timeout", page_timeout)
            self.script_timeout = self.options.get("script_timeout", script_timeout)
            self.url_change_timeout = self.options.get(
                "url_change_timeout", url_change_timeout
            )
            self.explicit_wait_duration = self.options.get(
                "explicit_wait_duration", explicit_wait_duration
            )

        # Add the extensions only if JavaScript is enabled
        if not self.disable_javascript:
            self._add_extensions()
        else:
            self._logger.info(
                "Extensions rely on JavaScript and disabled the extensions since `disable_javascript` is set to True"
            )
            self.export_har = False
            self.remove_gdpr = False

    def _add_extensions(self) -> None:
        """
        Locate and verify the extensions for the browsers
        """
        # Add "HAR export trigger" extension
        self._har_export_extension_xpi: str = self._config[
            "asset_har_export_extension_xpi"
        ]
        self._har_export_extension_xpi_id: str = self._config[
            "asset_har_export_extension_xpi_id"
        ]
        self._har_export_extension_crx: str = self._config[
            "asset_har_export_extension_crx"
        ]

        # Add "I don't care about cookies" extension
        self._gdpr_extension_xpi: str = self._config["asset_gdpr_extension_xpi"]
        self._gdpr_extension_xpi_id: str = self._config["asset_gdpr_extension_xpi_id"]
        self._gdpr_extension_crx: str = self._config["asset_gdpr_extension_crx"]

        if self.export_har:
            self._check_extension_validity(self._har_export_extension_xpi, ".xpi")
            self._check_extension_validity(self._har_export_extension_crx, ".crx")

        if self.remove_gdpr:
            self._check_extension_validity(self._gdpr_extension_xpi, ".xpi")
            self._check_extension_validity(self._gdpr_extension_crx, ".crx")

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

    @staticmethod
    def _install_xpi_extension(
        extension_xpi: str, extension_id: str, directory: str
    ) -> None:
        """
        Installs extensions to Firefox based browsers

        :param extension_xpi: Absolute path to the XPI file for the extension
        :type extension_xpi: str
        :param extension_id: ID of the extension (found in manifest.json of the extension)
        :type extension_id: str
        :param directory: Absolute directory path to install the extension
        :type directory: str
        """
        addon_path = os.path.join(directory, extension_id)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chmod(directory, 0o755)
        shutil.copy(extension_xpi, addon_path + ".xpi")

    @staticmethod
    def _install_crx_extension(
        extension_crx: str, chrome_options: webdriver.ChromeOptions
    ) -> None:
        """
        Installs extensions to Chromium based browsers

        :param extension_crx: Absolute path to the CRX file for the extension
        :type extension_crx: str
        :param chrome_options: webdriver.ChromeOptions from the Selenium driver
        :type chrome_options: webdriver.ChromeOptions
        """
        chrome_options.add_extension(extension_crx)

    def _setup_common_firefox_based_fetcher(self, ff_profile: FirefoxProfile) -> None:
        """
        Performs the common setup procedures for Firefox based fetchers, including Firefox itself

        :param ff_profile: Firefox Profile created for the webdriver
        :type ff_profile: FirefoxProfile
        """
        # Get the executor URL
        self._selenium_executor_url = self._get_selenium_executor_url(
            self.container_host, self.container_port
        )

        # Install the extensions
        if self.remove_gdpr:
            self._install_xpi_extension(
                self._gdpr_extension_xpi,
                self._gdpr_extension_xpi_id,
                ff_profile.extensionsDir,
            )

        if self.export_har:
            self._install_xpi_extension(
                self._har_export_extension_xpi,
                self._har_export_extension_xpi_id,
                ff_profile.extensionsDir,
            )

            # Enable the network monitoring tools to record HAR
            ff_profile.set_preference("devtools.netmonitor.enabled", True)
            ff_profile.set_preference("devtools.toolbox.selectedTool", "netmonitor")
            ff_profile.set_preference("devtools.netmonitor.har.compress", False)
            ff_profile.set_preference(
                "devtools.netmonitor.har.includeResponseBodies", False
            )
            ff_profile.set_preference("devtools.netmonitor.har.jsonp", False)
            ff_profile.set_preference("devtools.netmonitor.har.jsonpCallback", False)
            ff_profile.set_preference("devtools.netmonitor.har.forceExport", False)
            ff_profile.set_preference(
                "devtools.netmonitor.har.enableAutoExportToFile", False
            )
            ff_profile.set_preference(
                "devtools.netmonitor.har.pageLoadedTimeout", "2500"
            )

        # Stop updates
        ff_profile.set_preference("app.update.enabled", False)

        # Disable JSON view page
        ff_profile.set_preference("devtools.jsonview.enabled", False)

        # Set connections to Tor if we need to use Tor
        if self.use_proxy_type == "tor":
            ff_profile.set_preference("network.proxy.type", 1)
            ff_profile.set_preference("network.proxy.socks_version", 5)
            ff_profile.set_preference("network.proxy.socks", str(self._proxy_host))
            ff_profile.set_preference("network.proxy.socks_port", int(self._proxy_port))
            ff_profile.set_preference("network.proxy.socks_remote_dns", True)

        elif self.use_proxy_type == "http":
            ff_profile.set_preference("network.proxy.type", 1)
            ff_profile.set_preference("network.proxy.proxy_over_tls", True)
            ff_profile.set_preference("network.proxy.share_proxy_settings", False)
            ff_profile.set_preference("network.proxy.http", str(self._proxy_host))
            ff_profile.set_preference("network.proxy.http_port", int(self._proxy_port))
            ff_profile.set_preference("network.proxy.ssl", str(self._proxy_host))
            ff_profile.set_preference("network.proxy.ssl_port", int(self._proxy_port))
            ff_profile.set_preference("network.proxy.ftp", str(self._proxy_host))
            ff_profile.set_preference("network.proxy.ftp_port", int(self._proxy_port))

        if self.disable_cookies:
            ff_profile.set_preference("network.cookie.cookieBehavior", 2)

        # Apply the preferences
        ff_profile.update_preferences()

        # Set selenium related options for Firefox Browser
        self._desired_capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
        self._selenium_options = webdriver.FirefoxOptions()
        self._selenium_options.profile = ff_profile

        if self.disable_javascript:
            self._selenium_options.preferences.update(
                {
                    "javascript.enabled": False,
                }
            )

        if self.export_har:
            self._selenium_options.add_argument("--devtools")

    def _setup_common_chromium_based_fetcher(self) -> None:
        """
        Performs the common setup procedures for Chromium based fetchers, including Chromium itself
        """
        # Get the executor URL
        self._selenium_executor_url = self._get_selenium_executor_url(
            self.container_host, self.container_port
        )

        self._selenium_options = webdriver.ChromeOptions()

        # Install the extensions
        if self.remove_gdpr:
            self._install_crx_extension(
                self._gdpr_extension_crx, self._selenium_options
            )

        if self.export_har:
            self._install_crx_extension(
                self._har_export_extension_crx, self._selenium_options
            )

            # Enable the network monitoring tools to record HAR
            self._selenium_options.add_argument("--auto-open-devtools-for-tabs")

        # Set connections to Tor if we need to use Tor
        if self.use_proxy_type == "tor":
            # Set Tor as proxy
            proxy = f"socks5://{self._proxy_host}:{self._proxy_port}"
            self._selenium_options.add_argument(f"--proxy-server={proxy}")

        elif self.use_proxy_type == "http":
            proxy = f"{self._proxy_host}:{self._proxy_port}"
            self._desired_capabilities["proxy"] = {
                "httpProxy": proxy,
                "ftpProxy": proxy,
                "sslProxy": proxy,
                "proxyType": "MANUAL",
            }
            self._desired_capabilities["acceptSslCerts"] = True

        prefs = {}
        if self.disable_javascript:
            prefs["profile.managed_default_content_settings.javascript"] = 2

        if self.disable_cookies:
            prefs["profile.managed_default_content_settings.cookies"] = 2

        if len(prefs) > 0:
            self._selenium_options.add_experimental_option("prefs", prefs)

    def _fetch_with_selenium_remote_web_driver(self) -> None:
        """
        Fetches the given URL with the remote web driver
        """
        # Get a copy of the URL
        old_url = self.driver.current_url

        # Fetch the target URL
        self.driver.get(self.url)

        # Make sure that the page was fetched and the URL was changed
        WebDriverWait(self.driver, self.url_change_timeout).until(
            EC.url_changes(old_url),
            message="The URL didn't change within the specified timeout duration for fetching",
        )

        # Wait more to allow finalizing any ongoing background connections
        time.sleep(self.explicit_wait_duration)

        self.page_source = self.driver.page_source
        self.page_cookies = self.driver.get_cookies()
        self.page_title = self.driver.title

        if self.export_har:
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
