import os

from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from captchamonitor.utils.exceptions import TorBrowserProfileLocationError
from captchamonitor.fetchers.base_fetcher import BaseFetcher


class TorBrowser(BaseFetcher):
    """
    Inherits and extends the BaseFetcher class to fetch URLs with Tor Browser

    :param BaseFetcher: Inherits the BaseFetcher class
    :type BaseFetcher: BaseFetcher class
    """

    method_name_in_db = "tor_browser"

    def setup(self) -> None:
        """
        Prepares and starts the Tor Browser for fetching

        :raises TorBrowserProfileLocationError: If provided Tor Browser location is not valid
        """
        self.container_host = self._config["docker_tor_browser_container_name"]
        self.container_port = self._config["docker_tor_browser_container_port"]

        profile_location = self._config["docker_tor_browser_container_profile_location"]

        # Check if the profile location makes sense
        if not os.path.isdir(profile_location):
            raise TorBrowserProfileLocationError

        # If no security level is provided, default to "standard"
        # TODO: Clean this if else mess
        security_levels = {"safest": 1, "safer": 2, "standard": 4}
        if self.options is not None:
            security_level = self.options.get("tbb_security_level", "standard")
            if security_level is None:
                security_level = "standard"
        else:
            security_level = "standard"

        # Convert security level to integer representation
        security_level = security_levels[security_level]

        # Obtain the Tor Browser profile and create a copy of it in /tmp
        tb_profile = FirefoxProfile(profile_location)

        # Set security level
        tb_profile.set_preference(
            "extensions.torbutton.security_slider", int(security_level)
        )

        # Stop Tor Browser's internal Tor
        tb_profile.set_preference("extensions.torlauncher.start_tor", False)
        tb_profile.set_preference("extensions.torlauncher.prompt_at_startup", False)

        # Let Tor Button connect us to external Tor
        tb_profile.set_preference("extensions.torbutton.local_tor_check", False)
        tb_profile.set_preference("extensions.torbutton.launch_warning", False)
        tb_profile.set_preference("extensions.torbutton.display_circuit", False)
        tb_profile.set_preference("extensions.torbutton.use_nontor_proxy", True)

        # Stop updates
        tb_profile.set_preference("extensions.torbutton.versioncheck_enabled", False)

        # Perform the rest of the common setup procedures
        self._setup_common_firefox_based_fetcher(tb_profile)

    def connect(self) -> None:
        """
        Connects Selenium driver to Tor Browser Container
        """
        self._connect_to_selenium_remote_web_driver(
            container_name="Tor Browser",
            desired_capabilities=self._desired_capabilities,
            command_executor=self._selenium_executor_url,
            options=self._selenium_options,
        )

    def fetch(self) -> None:
        """
        Fetches the given URL using Tor Browser
        """
        self._fetch_with_selenium_remote_web_driver()
