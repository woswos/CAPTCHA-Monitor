from selenium import webdriver
from captchamonitor.fetchers.base_fetcher import BaseFetcher


class ChromeBrowser(BaseFetcher):
    """
    Inherits and extends the BaseFetcher class to fetch URLs with Chrome Browser

    :param BaseFetcher: Inherits the BaseFetcher class
    :type BaseFetcher: BaseFetcher class
    """

    def setup(self):
        """
        Prepares and starts the Chrome Browser for fetching
        """
        socks_host = self.tor_launcher.ip_address
        socks_port = self.tor_launcher.socks_port

        container_host = self.config["docker_chrome_browser_container_name"]
        container_port = self.config["docker_chrome_browser_container_port"]

        self.selenium_executor_url = self.get_selenium_executor_url(
            container_host, container_port
        )

        self.desired_capabilities = webdriver.DesiredCapabilities.CHROME
        self.selenium_options = webdriver.ChromeOptions()

        # Set connections to Tor if we need to use Tor
        if self.use_tor:
            proxy = f"socks5://{socks_host}:{socks_port}"
            self.selenium_options.add_argument(f"--proxy-server={proxy}")

    def connect(self):
        """
        Connects Selenium driver to Chrome Browser Container
        """
        self.connect_to_selenium_remote_web_driver(
            container_name="Chrome Browser",
            desired_capabilities=self.desired_capabilities,
            command_executor=self.selenium_executor_url,
            options=self.selenium_options,
        )

    def fetch(self):
        """
        Fetches the given URL using Chrome Browser
        """
        return self.fetch_with_selenium_remote_web_driver()
