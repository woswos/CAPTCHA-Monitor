from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from captchamonitor.fetchers.base_fetcher import BaseFetcher


class FirefoxBrowser(BaseFetcher):
    """
    Inherits and extends the BaseFetcher class to fetch URLs with Firefox Browser

    :param BaseFetcher: Inherits the BaseFetcher class
    :type BaseFetcher: BaseFetcher class
    """

    method_name_in_db = "firefox_browser"

    def setup(self) -> None:
        """
        Prepares and starts the Firefox Browser for fetching
        """
        socks_host = self._tor_launcher.ip_address
        socks_port = self._tor_launcher.socks_port

        self.container_host = self._config["docker_firefox_browser_container_name"]
        self.container_port = self._config["docker_firefox_browser_container_port"]

        self._selenium_executor_url = self._get_selenium_executor_url(
            self.container_host, self.container_port
        )

        # Create new Firefox profile
        ff_profile = FirefoxProfile()

        # Install the extensions
        self._install_har_export_extension_xpi(ff_profile.extensionsDir)

        # Enable the network monitoring tools to record HAR in Firefox Browser
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
        if self.use_tor:
            ff_profile.set_preference("network.proxy.type", 1)
            ff_profile.set_preference("network.proxy.socks_version", 5)
            ff_profile.set_preference("network.proxy.socks", str(socks_host))
            ff_profile.set_preference("network.proxy.socks_port", int(socks_port))
            ff_profile.set_preference("network.proxy.socks_remote_dns", True)

        # Set selenium related options for Firefox Browser
        self._desired_capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
        self._selenium_options = webdriver.FirefoxOptions()
        self._selenium_options.profile = ff_profile
        self._selenium_options.add_argument("--devtools")

    def connect(self) -> None:
        """
        Connects Selenium driver to Firefox Browser Container
        """
        self._connect_to_selenium_remote_web_driver(
            container_name="Firefox Browser",
            desired_capabilities=self._desired_capabilities,
            command_executor=self._selenium_executor_url,
            options=self._selenium_options,
        )

    def fetch(self) -> None:
        """
        Fetches the given URL using Firefox Browser
        """
        self._fetch_with_selenium_remote_web_driver()
