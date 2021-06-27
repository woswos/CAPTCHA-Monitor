import unittest

from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


class TestFirefoxBrowser(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.target_url = "https://check.torproject.org/"

    def test_firefox_browser_without_tor(self):
        firefox_browser = FirefoxBrowser(
            config=self.config,
            url=self.target_url,
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        self.assertIn("Sorry. You are not using Tor.", firefox_browser.page_source)

        firefox_browser.close()

    def test_firefox_browser_with_tor(self):
        tor_launcher = TorLauncher(self.config)
        proxy = (
            tor_launcher.ip_address,
            tor_launcher.socks_port,
        )

        firefox_browser = FirefoxBrowser(
            config=self.config,
            url=self.target_url,
            proxy=proxy,
            use_proxy_type="tor",
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            firefox_browser.page_source,
        )

        firefox_browser.close()
