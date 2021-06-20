import time

from selenium import webdriver

from captchamonitor.fetchers.base_fetcher import BaseFetcher


class OperaBrowser(BaseFetcher):
    """
    Inherits and extends the BaseFetcher class to fetch URLs with Opera Browser

    :param BaseFetcher: Inherits the BaseFetcher class
    :type BaseFetcher: BaseFetcher class
    """

    method_name_in_db = "opera_browser"

    def setup(self) -> None:
        """
        Prepares and starts the Opera Browser for fetching
        """
        socks_host = self._tor_launcher.ip_address
        socks_port = self._tor_launcher.socks_port

        self.container_host = self._config["docker_opera_browser_container_name"]
        self.container_port = self._config["docker_opera_browser_container_port"]

        self._selenium_executor_url = self._get_selenium_executor_url(
            self.container_host, self.container_port
        )

        self._desired_capabilities = webdriver.DesiredCapabilities.OPERA.copy()
        self._selenium_options = webdriver.ChromeOptions()

        # Install the extensions for Opera Browser
        self._install_har_export_extension_crx(self._selenium_options)

        # Enable the network monitoring tools to record HAR in Opera Browser
        self._selenium_options.add_argument("--auto-open-devtools-for-tabs")

        # Set connections to Tor if we need to use Tor with Opera Browser
        if self.use_tor:
            proxy = f"socks5://{socks_host}:{socks_port}"
            self._selenium_options.add_argument(f"--proxy-server={proxy}")

    def connect(self) -> None:
        """
        Connects Selenium driver to Opera Browser Container
        """
        self._connect_to_selenium_remote_web_driver(
            container_name="Opera Browser",
            desired_capabilities=self._desired_capabilities,
            command_executor=self._selenium_executor_url,
            options=self._selenium_options,
        )

        # Allows some time for HAR export trigger extension to initialize.
        # Don't remove this sleep, otherwise HAR export trigger extension returns
        # nothing and causes trouble with Opera Browser
        time.sleep(1)

    def fetch(self) -> None:
        """
        Fetches the given URL using Opera Browser
        """
        self._fetch_with_selenium_remote_web_driver()
