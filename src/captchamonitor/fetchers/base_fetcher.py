import os
import json
import shutil
import logging
from typing import Any, List, Tuple, Union, Optional

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
        :param page_timeout: Maximum time allowed for a web page to load, defaults to 30
        :type page_timeout: int
        :param script_timeout: Maximum time allowed for a JS script to respond, defaults to 30
        :type script_timeout: int
        :param url_change_timeout: Maximum time allowed while waiting for driver URL to change, defaults to 30
        :type url_change_timeout: int
        :param options: Dictionary of options to pass to the fetcher, defaults to None
        :type options: Optional[dict], optional
        :raises MissingProxy: If use_proxy_type is not None but no proxy provided
        """
        # Public class attributes
        self.url: str = url
        self.use_proxy_type: Optional[str] = use_proxy_type
        self.page_timeout: int = page_timeout
        self.script_timeout: int = script_timeout
        self.url_change_timeout: int = url_change_timeout
        self.options: Optional[dict] = options
        self.gdpr_remove: bool = False
        self.gdpr_wait_for_url_change: bool = False
        self.gdpr_keywords: List[str] = ["Accept"]
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
        self._num_retries_on_fail: int = 3
        self._delay_in_seconds_between_retries: int = 3

        # Check if use_proxy_type is set to True but proxy is not passed
        if (self.use_proxy_type is not None) and (self._proxy is None):
            raise MissingProxy

        # Extract the proxy host and port
        if self._proxy is not None:
            self._proxy_host = str(self._proxy[0])  # type: ignore
            self._proxy_port = int(self._proxy[1])  # type: ignore

        # Update default options with the specified ones
        if self.options is not None:
            self.gdpr_remove = self.options.get("gdpr_remove", self.gdpr_remove)
            self.gdpr_wait_for_url_change = self.options.get(
                "gdpr_wait_for_url_change", self.gdpr_wait_for_url_change
            )
            self.gdpr_keywords = self.options.get("gdpr_keywords", self.gdpr_keywords)
            self.page_timeout = self.options.get("page_timeout", page_timeout)
            self.script_timeout = self.options.get("script_timeout", script_timeout)
            self.url_change_timeout = self.options.get(
                "url_change_timeout", url_change_timeout
            )

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
        self._install_har_export_extension_xpi(ff_profile.extensionsDir)

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
        ff_profile.set_preference("devtools.netmonitor.har.pageLoadedTimeout", "2500")

        # Stop updates
        ff_profile.set_preference("app.update.enabled", False)

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

        # Apply the preferences
        ff_profile.update_preferences()

        # Set selenium related options for Firefox Browser
        self._desired_capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
        self._selenium_options = webdriver.FirefoxOptions()
        self._selenium_options.profile = ff_profile
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
        self._install_har_export_extension_crx(self._selenium_options)

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

    def _remove_gdpr_popup(self) -> None:

        self._logger.debug("Trying to remove the GDPR popup")

        # Produce a similar string using the keywords:
        # ["Souhlasím", "Alle akzeptieren", "Jag godkänner"]
        keywords_str = '", "'.join(map(str, self.gdpr_keywords))
        keywords_array_str = f'arr = ["{keywords_str}"]'

        js_gdpr_remover = (
            keywords_array_str
            + """
                for (var i = 0; i < arr.length; i++) {
                    if (document.documentElement.innerHTML.includes(arr[i])) {
                        s = (arr[i]);
                        path = "//*[contains(., '" + s + "')]";
                        console.log(path);
                        x = document.evaluate(path, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                        for (var j = 0; j < x.snapshotLength; j++) {
                            try {
                                x.snapshotItem(j).click();
                            } catch (err) {
                                console.log(err)
                            }
                        }{'https://weebly.com/': 302, 'https://www.weebly.com/': 200, 'https://www.weebly.com/gdpr/gdprscript.js?buildTime=1626451745': 200, 'https://cdn2.editmysite.com/css/landing-pages/home-com-forward/main.css?buildtime=1626451745': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/shared/navbar/carrot.svg': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/logo.svg': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/shared/navbar/sandwich.svg': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/logotype.svg': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/home-com-forward/masthead/blair/blair-l.webp': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/home-com-forward/masthead/dios/dios-l.webp': 200, 'https://cdn2.editmysite.com/images/landing-pages/global/home-com-forward/square-and-weebly/browser-1680.webp': 200, 'https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js': 200, 'https://cdn2.editmysite.com/js/lang/en/utl.js?buildTime=1626451745&': 200, 'https://www.google.com/recaptcha/api.js': 200, 'https://www.google.com/recaptcha/api.js?render=6LfHYL4UAAAAAM5EkQCS4fcMA7R0TFqsEbLZpAst': 200, 'https://cdn2.editmysite.com/js/landing-pages/main.js?buildTime=1626451745': 200, 'https://www.gstatic.com/recaptcha/releases/vzAt61JclNZYHl6fEWIBqLbe/recaptcha__en.js': 200, 'https://cdn2.editmysite.com/javascript/aragorn-analytics-4.12.7.js': 200, 'https://cdn2.editmysite.com/fonts/SQ_Market/sqmarket-medium.woff2': 200, 'https://cdn2.editmysite.com/fonts/SQ_Market/sqmarket-regular.woff2': 200, 'https://cdn2.editmysite.com/components/ui-framework/fonts/w-icons/w-icons.woff?123597': 200, 'https://cdn.cookielaw.org/scripttemplates/otSDKStub.js': 200, 'https://www.weebly.com/favicon.ico': 200, 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfHYL4UAAAAAM5EkQCS4fcMA7R0TFqsEbLZpAst&co=aHR0cHM6Ly93d3cud2VlYmx5LmNvbTo0NDM.&hl=en&v=vzAt61JclNZYHl6fEWIBqLbe&size=invisible&cb=liiuxv1kebfk': 200, 'https://www.weebly.com/tracking/rtmetrics/aragorn/4.12.7': 200, 'https://www.weebly.com/tracking/v2/gtmdata': 200, 'https://cdn.cookielaw.org/consent/8841470e-8a69-4bca-9d0f-429385a04d0d/8841470e-8a69-4bca-9d0f-429385a04d0d.json': 200, 'https://www.gstatic.com/recaptcha/releases/vzAt61JclNZYHl6fEWIBqLbe/styles__ltr.css': 200, 'https://geolocation.onetrust.com/cookieconsentpub/v1/geo/location': 200, 'https://www.gstatic.com/recaptcha/api2/logo_48.png': 200, 'https://fonts.gstatic.com/s/roboto/v18/KFOmCnqEu92Fr1Mu4mxK.woff2': 200, 'https://fonts.gstatic.com/s/roboto/v18/KFOlCnqEu92Fr1MmEU9fBBc4.woff2': 200, 'https://www.google.com/recaptcha/api2/webworker.js?hl=en&v=vzAt61JclNZYHl6fEWIBqLbe': 200, 'https://cdn.cookielaw.org/scripttemplates/6.16.0/otBannerSdk.js': 200, 'https://cdn.cookielaw.org/consent/8841470e-8a69-4bca-9d0f-429385a04d0d/bc114eb2-c7c6-4142-a09e-abea385e2cf0/en.json': 200, 'https://cdn.cookielaw.org/scripttemplates/6.16.0/assets/otCenterRounded.json': 200, 'https://cdn.cookielaw.org/scripttemplates/6.16.0/assets/v2/otPcCenter.json': 200}

                    }
                }
                """
        )

        # Get a copy of the URL
        old_url = self.driver.current_url

        # Execute the GDPR remover
        self.driver.execute_script(js_gdpr_remover)

        if self.gdpr_wait_for_url_change:
            WebDriverWait(self.driver, self.url_change_timeout).until(
                EC.url_changes(old_url)
            )
            WebDriverWait(self.driver, self.url_change_timeout).until(
                lambda driver: driver.execute_script("return document.readyState")
                == "complete"
            )

    def _fetch_with_selenium_remote_web_driver(self) -> None:
        """
        Fetches the given URL with the remote web driver
        """
        self.driver.get(self.url)

        if self.gdpr_remove:
            self._remove_gdpr_popup()

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
