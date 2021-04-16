import os
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

    def setup(self):
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
        security_levels = {"safest": 1, "safer": 2, "standard": 4}
        if "TorBrowserSecurityLevel" in self.options:
            security_level = self.options["TorBrowserSecurityLevel"]
        else:
            security_level = "standard"

        # Convert security level to integer representation
        security_level = security_levels[security_level]

        # Obtain the Tor Browser profile
        profile = FirefoxProfile(profile_location)

        # Install the extensions
        self.install_har_export_extension(profile.extensionsDir)

        # Enable the network monitoring tools to record HAR
        profile.set_preference("devtools.netmonitor.enabled", True)
        profile.set_preference("devtools.netmonitor.har.compress", False)
        profile.set_preference("devtools.netmonitor.har.includeResponseBodies", False)
        profile.set_preference("devtools.netmonitor.har.jsonp", False)
        profile.set_preference("devtools.netmonitor.har.jsonpCallback", False)
        profile.set_preference("devtools.netmonitor.har.pageLoadedTimeout", "2500")

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

        self.desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
        self.selenium_options = webdriver.FirefoxOptions()
        self.selenium_options.profile = profile
        self.selenium_options.add_argument("--devtools")

    def connect(self):
        """
        Connects Selenium driver to Tor Browser Container
        """
        self.connect_to_selenium_remote_web_driver(
            container_name="Tor Browser",
            desired_capabilities=self.desired_capabilities,
            command_executor=self.selenium_executor_url,
            options=self.selenium_options,
        )

    def fetch(self):
        """
        Fetches the given URL using Tor Browser
        """
        self.fetch_with_selenium_remote_web_driver()
