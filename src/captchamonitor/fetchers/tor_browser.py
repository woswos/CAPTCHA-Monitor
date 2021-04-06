import time
import os
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium import webdriver
from captchamonitor.fetchers.base_fetcher import BaseFetcher
from captchamonitor.utils.exceptions import (
    FetcherConnectionInitError,
    TorBrowserProfileLocationError,
)


class TorBrowser(BaseFetcher):
    """
    Inherits and extends the BaseFetcher class to fetch URLs with Tor Browser

    :param BaseFetcher: Inherits the BaseFetcher class
    :type BaseFetcher: BaseFetcher class
    """

    def setup(self):
        """
        Prepares and starts the Tor Browser for fetching
        """
        socks_host = self.tor_launcher.ip_address
        socks_port = self.tor_launcher.socks_port
        profile_location = self.config["docker_tor_browser_container_profile_location"]

        # Check if the profile location makes sense
        if not os.path.isdir(profile_location):
            raise TorBrowserProfileLocationError

        # If no security level is provided, default to "standard"
        security_levels = {"safest": 1, "safer": 2, "standard": 4}
        if "TorBrowserSecurityLevel" in self.options:
            security_level = self.options["TorBrowserSecurityLevel"]
        else:
            security_level = "standard"

        # Convert security level to integer representation
        security_level = security_levels[security_level]

        # Obtain the Tor Browser profile
        profile = FirefoxProfile(profile_location)

        # Set security level
        profile.set_preference(
            "extensions.torbutton.security_slider", int(security_level)
        )

        # Stop Tor Browser's internal Tor
        profile.set_preference("extensions.torlauncher.start_tor", False)
        profile.set_preference("extensions.torlauncher.prompt_at_startup", False)

        # Let Tor Button connect us to external Tor
        profile.set_preference("extensions.torbutton.local_tor_check", False)
        profile.set_preference("extensions.torbutton.launch_warning", False)
        profile.set_preference("extensions.torbutton.display_circuit", False)
        profile.set_preference("extensions.torbutton.use_nontor_proxy", True)

        # Set the details for the external Tor
        profile.set_preference("network.proxy.socks", str(socks_host))
        profile.set_preference("network.proxy.socks_port", int(socks_port))

        # Stop updates
        profile.set_preference("app.update.enabled", False)
        profile.set_preference("extensions.torbutton.versioncheck_enabled", False)

        self.selenium_options = webdriver.FirefoxOptions()
        self.selenium_options.profile = profile

    def connect(self):
        """
        Connects Selenium driver to Tor Browser Container
        """
        tb_container_host = self.config["docker_tor_browser_container_name"]
        tb_container_port = self.config["docker_tor_browser_container_port"]

        selenium_executor_url = f"http://{tb_container_host}:{tb_container_port}/wd/hub"

        # Connect to Tor Browser Container
        connected = False
        for _ in range(3):
            try:
                self.driver = webdriver.Remote(
                    desired_capabilities=webdriver.DesiredCapabilities.FIREFOX,
                    command_executor=selenium_executor_url,
                    options=self.selenium_options,
                )
                connected = True
                break

            except ConnectionRefusedError as exception:
                self.logger.debug(
                    "Unable to connect to the Tor Browser Container, retrying: %s",
                    exception,
                )
                time.sleep(3)

        # Check if connection was successfull
        if not connected:
            self.logger.warning(
                "Could not connect to the Tor Browser Container after many retries"
            )
            raise FetcherConnectionInitError

        # Set driver timeout
        self.driver.set_page_load_timeout(self.timeout)

        # Log the current status
        self.logger.info("Connected to the Tor Browser Container")

    def fetch(self):
        """
        Fetches the given URL using Tor Browser
        """
        self.driver.get(self.url)

        return self.driver.page_source
