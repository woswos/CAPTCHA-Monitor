import unittest

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.chrome_browser import ChromeBrowser


class TestChromeBrowser(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.tor_launcher = TorLauncher(self.config)
        self.target_url = "https://check.torproject.org/"

    def test_chrome_browser_without_tor(self):
        chrome_browser = ChromeBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={},
            use_tor=False,
        )

        chrome_browser.setup()
        chrome_browser.connect()
        chrome_browser.fetch()

        self.assertIn("Sorry. You are not using Tor.", chrome_browser.page_source)

        chrome_browser.close()

    def test_chrome_browser_with_tor(self):
        chrome_browser = ChromeBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={},
            use_tor=True,
        )

        chrome_browser.setup()
        chrome_browser.connect()
        chrome_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            chrome_browser.page_source,
        )

        chrome_browser.close()
