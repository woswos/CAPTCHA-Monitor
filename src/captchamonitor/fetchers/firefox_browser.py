from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from captchamonitor.fetchers.base_fetcher import BaseFetcher


class FirefoxBrowser(BaseFetcher):
    """
    Inherits and extends the BaseFetcher class to fetch URLs with Firefox Browser

    :param BaseFetcher: Inherits the BaseFetcher class
    :type BaseFetcher: BaseFetcher class
    """

    def setup(self):
        """
        Prepares and starts the Firefox Browser for fetching
        """
        socks_host = self.tor_launcher.ip_address
        socks_port = self.tor_launcher.socks_port

        container_host = self.config["docker_firefox_browser_container_name"]
        container_port = self.config["docker_firefox_browser_container_port"]

        self.selenium_executor_url = self.get_selenium_executor_url(
            container_host, container_port
        )

        # Create new Firefox profile
        profile = FirefoxProfile()

        # Install the extensions
        self.install_har_export_extension(profile.extensionsDir)

        # Enable the network monitoring tools to record HAR
        profile.set_preference("devtools.netmonitor.enabled", True)
        profile.set_preference("devtools.netmonitor.har.compress", False)
        profile.set_preference("devtools.netmonitor.har.includeResponseBodies", False)
        profile.set_preference("devtools.netmonitor.har.jsonp", False)
        profile.set_preference("devtools.netmonitor.har.jsonpCallback", False)
        profile.set_preference("devtools.netmonitor.har.forceExport", False)
        profile.set_preference("devtools.netmonitor.har.enableAutoExportToFile", False)
        profile.set_preference("devtools.netmonitor.har.pageLoadedTimeout", "2500")

        # Stop updates
        profile.set_preference("app.update.enabled", False)

        # Set connections to Tor if we need to use Tor
        if self.use_tor:
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.socks_version", 5)
            profile.set_preference("network.proxy.socks", str(socks_host))
            profile.set_preference("network.proxy.socks_port", int(socks_port))
            profile.set_preference("network.proxy.socks_remote_dns", True)

        self.desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
        self.selenium_options = webdriver.FirefoxOptions()
        self.selenium_options.profile = profile
        self.selenium_options.add_argument("--devtools")

    def connect(self):
        """
        Connects Selenium driver to Firefox Browser Container
        """
        self.connect_to_selenium_remote_web_driver(
            container_name="Firefox Browser",
            desired_capabilities=self.desired_capabilities,
            command_executor=self.selenium_executor_url,
            options=self.selenium_options,
        )

    def fetch(self):
        """
        Fetches the given URL using Firefox Browser
        """
        self.fetch_with_selenium_remote_web_driver()
