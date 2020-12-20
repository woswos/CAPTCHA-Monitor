import os

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options

import captchamonitor.utils.exceptions as exceptions
from captchamonitor.fetchers.fetchers_base import BaseFetcher


class TorBrowser(BaseFetcher):
    """
    Fetch a given URL using selenium and Tor Browser

    :param BaseFetcher: The base fetcher class
    :type BaseFetcher: object
    """

    def __init__(
        self,
        url,
        fetcher_path,
        security_level,
        additional_headers=None,
        timeout=30,
    ):
        """
        Extends the base init method to add security level

        :param url: The website URL to fetch including the URL scheme
        :type url: str
        :param fetcher_path: The absolute path to folder on the file system that contains the fetcher binary
        :type fetcher_path: str
        :param security_level: The security level for Tor Browser: low, medium, high
        :type security_level: str
        :param additional_headers: The headers to overwrite while performing requests, defaults to None
        :type additional_headers: dict, optional
        :param timeout: Maximum time allowed for a web page to load, defaults to 30
        :type timeout: int, optional
        """

        super().__init__(url, fetcher_path, additional_headers, timeout)

        # If no security level was passed, use low as default
        if security_level is None:
            security_level = "low"

        security_levels = {"high": 1, "medium": 2, "low": 4}
        self.security_level = security_levels[security_level]

    def setup(self):
        """
        Contains the necessary setup functionality before fetching the web page.
        Has to be called before fetch.
        """

        # Set the Tor Browser binary
        self.binary = FirefoxBinary(
            os.path.join(self.fetcher_path, "tor-browser_en-US/Browser/firefox")
        )

        # Set the Tor Browser profile
        self.profile = FirefoxProfile(
            os.path.join(
                self.fetcher_path,
                "tor-browser_en-US/Browser/TorBrowser/Data/Browser/profile.default",
            )
        )

        # Set the security level
        self.profile.set_preference(
            "extensions.torbutton.security_slider",
            self.security_level,
        )

        # Stop Tor Browser's internal Tor
        self.profile.set_preference("extensions.torlauncher.start_tor", False)
        self.profile.set_preference(
            "extensions.torlauncher.prompt_at_startup", False
        )
        self.profile.set_preference(
            "extensions.torbutton.inserted_button", True
        )
        self.profile.set_preference(
            "extensions.torbutton.launch_warning", False
        )

        # Set the details for the external Tor
        self.profile.set_preference(
            "extensions.torbutton.settings_method", "custom"
        )
        self.profile.set_preference(
            "extensions.torbutton.custom.socks_host", self.tor_socks_host
        )
        self.profile.set_preference(
            "extensions.torbutton.custom.socks_port", int(self.tor_socks_port)
        )
        self.profile.set_preference(
            "extensions.torbutton.socks_port", int(self.tor_socks_port)
        )
        self.profile.set_preference(
            "network.proxy.socks_port", int(self.tor_socks_port)
        )

        # Stop updates
        self.profile.set_preference("app.update.enabled", False)
        self.profile.set_preference(
            "extensions.torbutton.versioncheck_enabled", False
        )

        # Set the download folder and disable pop up windows
        self.profile.set_preference("browser.download.folderList", 2)
        self.profile.set_preference("browser.download.useDownloadDir", True)
        self.profile.set_preference(
            "browser.download.dir", self.download_folder.name
        )
        self.profile.set_preference(
            "browser.download.defaultFolder", self.download_folder.name
        )

        # Required to run our custom HTTP-Header-Live extension
        self.profile.set_preference("xpinstall.signatures.required", False)
        self.profile.set_preference("xpinstall.whitelist.required", False)
        self.profile.set_preference(
            "app.update.lastUpdateTime.xpi-signature-verification", 0
        )
        self.profile.set_preference("extensions.autoDisableScopes", 10)
        self.profile.set_preference("extensions.enabledScopes", 15)
        self.profile.set_preference("extensions.blocklist.enabled", False)
        self.profile.set_preference("extensions.blocklist.pingCountVersion", 0)

        # Choose the headless mode
        self.options = Options()
        self.options.headless = True

    def fetch(self):
        """
        Fetches the web page using the specified method. .setup() method has to be
        called before fetching.

        :raises exceptions.BrowserInitErr: If the webdriver wasn't initialized as expected
        :raises exceptions.WebDriverGetErr: If the webdriver wasn't able to fetch the page due to an error
        """

        try:
            self.driver = webdriver.Firefox(
                firefox_profile=self.profile,
                firefox_binary=self.binary,
                options=self.options,
            )

        except Exception as err:
            self.logger.error(
                "Couldn't initialize the browser, check if there is enough memory available: %s",
                err,
            )
            raise exceptions.BrowserInitErr

        # Install the HTTP-Header-Live extension
        self.driver.install_addon(
            self.http_header_live_extension_xpi, temporary=True
        )

        # Set driver page load timeout
        self.driver.implicitly_wait(self.timeout)

        # Try sending a request to the server and get server's response
        try:
            self.driver.get(self.url)

        except Exception as err:
            self.force_quit_driver(self.driver)
            self.logger.error("webdriver.Firefox.get() says: %s", err)
            raise exceptions.WebDriverGetErr

        # Parse the headers
        self.parse_headers_via_http_header_live_extension()

        # Record the results
        self.html_data = self.driver.page_source
        self.requests = self.format_requests_tb(self.requests_data, self.url)

        # Cleanup
        self.force_quit_driver(self.driver)
