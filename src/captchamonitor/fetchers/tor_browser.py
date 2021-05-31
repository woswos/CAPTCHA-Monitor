import os
from typing import Any
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from captchamonitor.fetchers.base_fetcher import BaseFetcher
from captchamonitor.utils.exceptions import TorBrowserProfileLocationError


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
        socks_host = self.tor_launcher.ip_address
        socks_port = self.tor_launcher.socks_port
        profile_location = self.config["docker_tor_browser_container_profile_location"]

        container_host = self.config["docker_tor_browser_container_name"]
        container_port = self.config["docker_tor_browser_container_port"]

        self.selenium_executor_url = self.get_selenium_executor_url(
            container_host, container_port
        )

        # Check if the profile location makes sense
        if not os.path.isdir(profile_location):
            raise TorBrowserProfileLocationError

        # If no security level is provided, default to "standard"
        # TODO: Clean this if else mess
        security_levels = {"safest": 1, "safer": 2, "standard": 4}
        if self.options is not None:
            security_level = self.options.get("TorBrowserSecurityLevel", "standard")
            if security_level is None:
                security_level = "standard"
        else:
            security_level = "standard"

        # Convert security level to integer representation
        security_level = security_levels[security_level]

        # Obtain the Tor Browser profile
        tb_profile = FirefoxProfile(profile_location)

        # Install the extensions
        self.install_har_export_extension(tb_profile.extensionsDir)

        # Enable the network monitoring tools to record HAR in Tor Browser
        tb_profile.set_preference("devtools.netmonitor.enabled", True)
        tb_profile.set_preference("devtools.netmonitor.har.compress", False)
        tb_profile.set_preference(
            "devtools.netmonitor.har.includeResponseBodies", False
        )
        tb_profile.set_preference("devtools.netmonitor.har.jsonp", False)
        tb_profile.set_preference("devtools.netmonitor.har.jsonpCallback", False)
        tb_profile.set_preference("devtools.netmonitor.har.forceExport", False)
        tb_profile.set_preference(
            "devtools.netmonitor.har.enableAutoExportToFile", False
        )
        tb_profile.set_preference("devtools.netmonitor.har.pageLoadedTimeout", "2500")

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

        # Set the details for the external Tor
        tb_profile.set_preference("network.proxy.socks", str(socks_host))
        tb_profile.set_preference("network.proxy.socks_port", int(socks_port))

        # Stop updates
        tb_profile.set_preference("app.update.enabled", False)
        tb_profile.set_preference("extensions.torbutton.versioncheck_enabled", False)

        # Set selenium related options for Tor Browser
        self.desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
        self.selenium_options = webdriver.FirefoxOptions()
        self.selenium_options.profile = tb_profile
        self.selenium_options.add_argument("--devtools")

    def connect(self) -> None:
        """
        Connects Selenium driver to Tor Browser Container
        """
        self.connect_to_selenium_remote_web_driver(
            container_name="Tor Browser",
            desired_capabilities=self.desired_capabilities,
            command_executor=self.selenium_executor_url,
            options=self.selenium_options,
        )

    def fetch(self) -> Any:
        """
        Fetches the given URL using Tor Browser
        """
        self.fetch_with_selenium_remote_web_driver()
