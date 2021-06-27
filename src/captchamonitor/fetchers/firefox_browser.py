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
        self.container_host = self._config["docker_firefox_browser_container_name"]
        self.container_port = self._config["docker_firefox_browser_container_port"]

        # Create new Firefox profile
        ff_profile = FirefoxProfile()

        # Perform the rest of the common setup procedures
        self._setup_common_firefox_based_fetcher(ff_profile)

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
